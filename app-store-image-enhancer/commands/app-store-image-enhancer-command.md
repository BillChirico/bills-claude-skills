---
description: "Enhance image quality for app stores, screenshots, or social media. Usage: /enhance-image <path> [mode]"
globs:
  - "*.png"
  - "*.jpg"
  - "*.jpeg"
  - "*.webp"
---

Use the `app-store-image-enhancer` skill to improve image quality.

## Arguments

- `path` (required): Path to the image file or directory to enhance
- `mode` (optional): Enhancement preset - one of:
  - `app-icon` - Optimizes for app store icons (resizes to 1024x1024, max sharpness)
  - `screenshot` - Optimizes for documentation/blog screenshots
  - `general` - Default balanced enhancement

## Examples

```
/enhance-image ./assets/icon.png app-icon
```

```
/enhance-image ./screenshots/ screenshot
```

```
/enhance-image logo.jpg
```

## Workflow

1. Analyze the source image(s) to determine current quality metrics
2. Apply the enhancement pipeline based on the selected mode
3. Save enhanced images with `-enhanced` suffix (preserving originals)
4. Report the changes made and output file locations

Arguments: $ARGUMENTS
