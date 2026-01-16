---
name: image-generation
description: Generate images using OpenAI's gpt-image-1.5 model. Use when users request image creation, artwork, illustrations, marketing graphics, icons, or any visual content. Supports transparent backgrounds, multiple sizes, and quality levels.
---

# Image Generation

Generate images using OpenAI's gpt-image-1.5 model with support for transparency, custom sizes, and quality settings.

## Quick Start

Generate an image:

```bash
python scripts/generate_image.py "a futuristic city at sunset" --size 1024x1024
```

## Parameters

### Model
- `gpt-image-1.5` - State of the art (default)
- `gpt-image-1` - Previous generation
- `gpt-image-1-mini` - Faster, lower cost

### Size Options
- `1024x1024` - Square (default)
- `1536x1024` - Landscape
- `1024x1536` - Portrait
- `auto` - Let model decide

### Quality Options
- `auto` - Model decides (default)
- `low` - Fast, ~$0.02/image
- `medium` - Balanced, ~$0.07/image
- `high` - Detailed, ~$0.19/image

### Background Options
- `auto` - Model decides (default)
- `transparent` - For icons/logos (requires png/webp output)
- `opaque` - Solid background

### Output Format
- `png` - Default, supports transparency
- `webp` - Smaller files, supports transparency
- `jpeg` - Smallest files, no transparency

## Usage Examples

**Basic generation:**
```bash
python scripts/generate_image.py "a cute robot mascot"
```

**Transparent icon:**
```bash
python scripts/generate_image.py "app icon for a weather app" \
  --background transparent --size 1024x1024 --quality high
```

**Marketing banner (landscape):**
```bash
python scripts/generate_image.py "modern tech startup banner with blue gradient" \
  --size 1536x1024 --quality high
```

**Portrait artwork:**
```bash
python scripts/generate_image.py "oil painting of a mountain landscape" \
  --size 1024x1536 --quality high
```

## Output

Images are saved to `/home/ec2-user/mega-agent2/generated_images/` with timestamped filenames.

The script returns:
- `image_path` - Local file path
- `revised_prompt` - The prompt as interpreted by the model
- `size` - Actual dimensions
