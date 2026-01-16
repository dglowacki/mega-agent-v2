#!/usr/bin/env python3
"""
Image Generation Script using OpenAI gpt-image-1.5

Usage:
    python generate_image.py "prompt" [options]

Options:
    --model         Model: gpt-image-1.5, gpt-image-1, gpt-image-1-mini (default: gpt-image-1.5)
    --size          Size: 1024x1024, 1536x1024, 1024x1536, auto (default: 1024x1024)
    --quality       Quality: low, medium, high, auto (default: auto)
    --background    Background: transparent, opaque, auto (default: auto)
    --format        Output format: png, jpeg, webp (default: png)
    --output-dir    Output directory (default: /home/ec2-user/mega-agent2/generated_images)

Examples:
    python generate_image.py "a futuristic city at sunset"
    python generate_image.py "app icon" --background transparent --quality high
    python generate_image.py "landscape banner" --size 1536x1024
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    sys.exit(1)


DEFAULT_OUTPUT_DIR = "/home/ec2-user/mega-agent2/generated_images"


def generate_image(
    prompt: str,
    model: str = "gpt-image-1.5",
    size: str = "1024x1024",
    quality: str = "auto",
    background: str = "auto",
    output_format: str = "png",
    output_dir: str = DEFAULT_OUTPUT_DIR,
    n: int = 1
) -> dict:
    """
    Generate an image using OpenAI's gpt-image-1.5 model.

    Args:
        prompt: Text description of the image to generate
        model: Model to use (gpt-image-1.5, gpt-image-1, gpt-image-1-mini)
        size: Image size (1024x1024, 1536x1024, 1024x1536, auto)
        quality: Image quality (low, medium, high, auto)
        background: Background type (transparent, opaque, auto)
        output_format: Output format (png, jpeg, webp)
        output_dir: Directory to save the image
        n: Number of images to generate (1-10)

    Returns:
        dict with image_path, revised_prompt, and metadata
    """
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY environment variable not set", "status": "failed"}

    client = OpenAI(api_key=api_key)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # Build API call parameters
        params = {
            "model": model,
            "prompt": prompt,
            "n": n,
        }

        # Add optional parameters for gpt-image models
        if size != "auto":
            params["size"] = size
        if quality != "auto":
            params["quality"] = quality
        if background != "auto":
            params["background"] = background
        if output_format != "png":
            params["output_format"] = output_format

        # Generate image
        response = client.images.generate(**params)

        results = []
        for i, image_data in enumerate(response.data):
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = f"_{i+1}" if n > 1 else ""
            filename = f"image_{timestamp}{suffix}.{output_format}"
            image_path = output_path / filename

            # Save image (gpt-image models return base64)
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                image_bytes = base64.b64decode(image_data.b64_json)
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
            elif hasattr(image_data, 'url') and image_data.url:
                # Fallback for URL response
                import requests
                img_response = requests.get(image_data.url, timeout=60)
                img_response.raise_for_status()
                with open(image_path, 'wb') as f:
                    f.write(img_response.content)
            else:
                return {"error": "No image data in response", "status": "failed"}

            result = {
                "image_path": str(image_path),
                "revised_prompt": getattr(image_data, 'revised_prompt', prompt),
                "size": size,
                "quality": quality,
                "model": model,
                "status": "success"
            }
            results.append(result)

        if n == 1:
            return results[0]
        return {"images": results, "count": len(results), "status": "success"}

    except Exception as e:
        return {
            "error": str(e),
            "prompt": prompt,
            "status": "failed"
        }


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using OpenAI gpt-image-1.5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_image.py "a futuristic city at sunset"
  python generate_image.py "app icon" --background transparent --quality high
  python generate_image.py "landscape banner" --size 1536x1024 --format webp
        """
    )

    parser.add_argument("prompt", help="Text description of the image to generate")
    parser.add_argument("--model", default="gpt-image-1.5",
                        choices=["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"],
                        help="Model to use (default: gpt-image-1.5)")
    parser.add_argument("--size", default="1024x1024",
                        choices=["1024x1024", "1536x1024", "1024x1536", "auto"],
                        help="Image size (default: 1024x1024)")
    parser.add_argument("--quality", default="auto",
                        choices=["low", "medium", "high", "auto"],
                        help="Image quality (default: auto)")
    parser.add_argument("--background", default="auto",
                        choices=["transparent", "opaque", "auto"],
                        help="Background type (default: auto)")
    parser.add_argument("--format", dest="output_format", default="png",
                        choices=["png", "jpeg", "webp"],
                        help="Output format (default: png)")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("-n", type=int, default=1,
                        help="Number of images to generate (1-10, default: 1)")
    parser.add_argument("--json", action="store_true",
                        help="Output result as JSON")

    args = parser.parse_args()

    result = generate_image(
        prompt=args.prompt,
        model=args.model,
        size=args.size,
        quality=args.quality,
        background=args.background,
        output_format=args.output_format,
        output_dir=args.output_dir,
        n=args.n
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("status") == "success":
            if "images" in result:
                print(f"Generated {result['count']} images:")
                for img in result["images"]:
                    print(f"  {img['image_path']}")
            else:
                print(f"Image generated: {result['image_path']}")
                if result.get('revised_prompt') != args.prompt:
                    print(f"Revised prompt: {result['revised_prompt']}")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
