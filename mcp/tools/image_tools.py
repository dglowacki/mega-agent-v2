"""
Image Generation Tools - AI image generation via gpt-image-1.5.

Provides image generation capabilities for the voice assistant.
"""

import base64
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_openai_client = None
DEFAULT_OUTPUT_DIR = "/home/ec2-user/mega-agent2/generated_images"


def _get_openai():
    """Get OpenAI client."""
    global _openai_client
    if _openai_client is None:
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY not set")
                return None
            _openai_client = OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to init OpenAI: {e}")
            return None
    return _openai_client


def image_generate(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "auto",
    background: str = "auto"
) -> str:
    """
    Generate an image using OpenAI's gpt-image-1.5 model.

    Args:
        prompt: Text description of the image to generate
        size: Image size (1024x1024, 1536x1024, 1024x1536)
        quality: Quality level (low, medium, high, auto)
        background: Background type (transparent, opaque, auto)

    Returns:
        String with result message and image path
    """
    client = _get_openai()
    if not client:
        return "Error: OpenAI not configured. Set OPENAI_API_KEY environment variable."

    try:
        # Create output directory
        output_path = Path(DEFAULT_OUTPUT_DIR)
        output_path.mkdir(parents=True, exist_ok=True)

        # Build API parameters
        params = {
            "model": "gpt-image-1.5",
            "prompt": prompt,
            "n": 1,
        }

        # Add optional parameters
        if size and size != "auto":
            params["size"] = size
        if quality and quality != "auto":
            params["quality"] = quality
        if background and background != "auto":
            params["background"] = background

        # Generate image
        logger.info(f"Generating image: {prompt[:50]}...")
        response = client.images.generate(**params)

        image_data = response.data[0]

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_{timestamp}.png"
        image_path = output_path / filename

        # Save image (gpt-image-1.5 returns base64)
        if hasattr(image_data, 'b64_json') and image_data.b64_json:
            image_bytes = base64.b64decode(image_data.b64_json)
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
        elif hasattr(image_data, 'url') and image_data.url:
            import requests
            img_response = requests.get(image_data.url, timeout=60)
            img_response.raise_for_status()
            with open(image_path, 'wb') as f:
                f.write(img_response.content)
        else:
            return "Error: No image data in response"

        revised = getattr(image_data, 'revised_prompt', prompt)

        result = f"Image generated successfully!\n"
        result += f"  Path: {image_path}\n"
        result += f"  Size: {size}\n"
        if revised != prompt:
            result += f"  Revised prompt: {revised[:100]}..."

        logger.info(f"Image saved to {image_path}")
        return result

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return f"Error generating image: {str(e)}"


def image_generate_icon(
    description: str,
    style: str = "modern"
) -> str:
    """
    Generate an app icon or logo with transparent background.

    Args:
        description: Description of the icon/logo
        style: Style (modern, minimal, playful, professional)

    Returns:
        String with result message and image path
    """
    prompt = f"{style} app icon: {description}, clean design, centered, suitable for app store"
    return image_generate(
        prompt=prompt,
        size="1024x1024",
        quality="high",
        background="transparent"
    )


def image_generate_banner(
    description: str,
    orientation: str = "landscape"
) -> str:
    """
    Generate a marketing banner or header image.

    Args:
        description: Description of the banner content
        orientation: landscape or portrait

    Returns:
        String with result message and image path
    """
    size = "1536x1024" if orientation == "landscape" else "1024x1536"
    prompt = f"marketing banner: {description}, professional, high quality"
    return image_generate(
        prompt=prompt,
        size=size,
        quality="high",
        background="opaque"
    )


def register_image_tools(server) -> int:
    """Register image generation tools."""

    server.register_tool(
        name="image_generate",
        description="Generate an image using AI. Provide a detailed text description of what you want to create.",
        input_schema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Detailed description of the image to generate"
                },
                "size": {
                    "type": "string",
                    "description": "Image size",
                    "enum": ["1024x1024", "1536x1024", "1024x1536"],
                    "default": "1024x1024"
                },
                "quality": {
                    "type": "string",
                    "description": "Quality level (low=fast/cheap, high=detailed/expensive)",
                    "enum": ["low", "medium", "high", "auto"],
                    "default": "auto"
                },
                "background": {
                    "type": "string",
                    "description": "Background type (transparent for icons/logos)",
                    "enum": ["transparent", "opaque", "auto"],
                    "default": "auto"
                }
            },
            "required": ["prompt"]
        },
        handler=image_generate,
        requires_approval=True,
        category="image"
    )

    server.register_tool(
        name="image_generate_icon",
        description="Generate an app icon or logo with transparent background.",
        input_schema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the icon or logo"
                },
                "style": {
                    "type": "string",
                    "description": "Visual style",
                    "enum": ["modern", "minimal", "playful", "professional"],
                    "default": "modern"
                }
            },
            "required": ["description"]
        },
        handler=image_generate_icon,
        requires_approval=True,
        category="image"
    )

    server.register_tool(
        name="image_generate_banner",
        description="Generate a marketing banner or header image.",
        input_schema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the banner content"
                },
                "orientation": {
                    "type": "string",
                    "description": "Banner orientation",
                    "enum": ["landscape", "portrait"],
                    "default": "landscape"
                }
            },
            "required": ["description"]
        },
        handler=image_generate_banner,
        requires_approval=True,
        category="image"
    )

    return 3
