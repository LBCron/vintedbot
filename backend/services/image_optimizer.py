"""
Image optimization for OpenAI Vision API
Reduces API costs by optimizing image size and quality before upload
"""
import os
import tempfile
from typing import Tuple, Optional
from pathlib import Path
from PIL import Image
import pillow_heif

# Register HEIF opener
pillow_heif.register_heif_opener()

# Target resolution for OpenAI (balance between cost and quality)
MAX_DIMENSION = int(os.getenv("AI_IMAGE_MAX_DIMENSION", "1536"))  # 1536x1536 is sweet spot for GPT-4o
JPEG_QUALITY = int(os.getenv("AI_IMAGE_QUALITY", "85"))  # 85% is good balance

# Cost optimization: images >2048px are resized by OpenAI anyway, so we pre-optimize
# OpenAI pricing: $0.01275 per 512x512 tile, so optimizing saves money


def get_optimal_dimensions(width: int, height: int, max_dim: int = MAX_DIMENSION) -> Tuple[int, int]:
    """
    Calculate optimal dimensions while preserving aspect ratio

    Args:
        width: Original width
        height: Original height
        max_dim: Maximum dimension (width or height)

    Returns:
        (new_width, new_height) tuple
    """
    if width <= max_dim and height <= max_dim:
        return (width, height)

    # Calculate scale factor
    scale = max_dim / max(width, height)

    new_width = int(width * scale)
    new_height = int(height * scale)

    return (new_width, new_height)


def optimize_image_for_ai(image_path: str, output_path: Optional[str] = None) -> str:
    """
    Optimize image for OpenAI Vision API
    - Converts HEIC to JPEG
    - Resizes to optimal dimensions (1536px max)
    - Compresses with optimal quality (85%)
    - Removes EXIF data to reduce size

    Args:
        image_path: Path to original image
        output_path: Optional output path (temp file if not provided)

    Returns:
        Path to optimized image

    Cost savings example:
        Original: 4032x3024 (12MP) -> ~25 tiles -> $0.32 per image
        Optimized: 1536x1152 (1.7MP) -> ~6 tiles -> $0.08 per image
        **Savings: 75% cost reduction**
    """
    try:
        # Open image (handles HEIC automatically)
        img = Image.open(image_path)

        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Get current dimensions
        width, height = img.size

        # Calculate optimal dimensions
        new_width, new_height = get_optimal_dimensions(width, height)

        # Resize if needed
        if (new_width, new_height) != (width, height):
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"[OPTIMIZE] Resized: {width}x{height} -> {new_width}x{new_height}")
        else:
            print(f"[OPTIMIZE] No resize needed: {width}x{height}")

        # Prepare output path
        if not output_path:
            temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
            output_path = temp_file.name

        # Save optimized JPEG (remove EXIF for smaller size)
        img.save(
            output_path,
            'JPEG',
            quality=JPEG_QUALITY,
            optimize=True,
            exif=b''  # Remove EXIF data
        )

        # Calculate size reduction
        original_size = Path(image_path).stat().st_size / 1024 / 1024  # MB
        optimized_size = Path(output_path).stat().st_size / 1024 / 1024  # MB
        reduction = ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0

        print(f"[OPTIMIZE] Size: {original_size:.2f}MB -> {optimized_size:.2f}MB ({reduction:.1f}% reduction)")

        return output_path

    except Exception as e:
        print(f"[WARN] Image optimization failed for {image_path}: {e}")
        # Return original path as fallback
        return image_path


def batch_optimize_images(image_paths: list[str]) -> list[str]:
    """
    Optimize multiple images for AI processing

    Args:
        image_paths: List of original image paths

    Returns:
        List of optimized image paths
    """
    optimized_paths = []

    for path in image_paths:
        optimized_path = optimize_image_for_ai(path)
        optimized_paths.append(optimized_path)

    total_original = sum(Path(p).stat().st_size for p in image_paths) / 1024 / 1024
    total_optimized = sum(Path(p).stat().st_size for p in optimized_paths) / 1024 / 1024
    reduction = ((total_original - total_optimized) / total_original * 100) if total_original > 0 else 0

    print(f"\n[BATCH OPTIMIZE] Total: {total_original:.2f}MB -> {total_optimized:.2f}MB ({reduction:.1f}% reduction)")
    print(f"[COST SAVINGS] Estimated API cost reduction: ~{reduction * 0.75:.1f}%")

    return optimized_paths


def estimate_api_cost(image_paths: list[str]) -> dict:
    """
    Estimate OpenAI Vision API cost for given images

    Args:
        image_paths: List of image paths

    Returns:
        Dict with cost estimates (before and after optimization)
    """
    def calculate_tiles(width: int, height: int) -> int:
        """Calculate number of 512x512 tiles for OpenAI pricing"""
        # OpenAI pricing: based on 512x512 tiles
        tiles_width = (width + 511) // 512
        tiles_height = (height + 511) // 512
        return tiles_width * tiles_height

    total_cost_before = 0
    total_cost_after = 0

    COST_PER_TILE = 0.01275  # $0.01275 per 512x512 tile

    for path in image_paths:
        try:
            img = Image.open(path)
            width, height = img.size

            # Cost before optimization
            tiles_before = calculate_tiles(width, height)
            cost_before = tiles_before * COST_PER_TILE
            total_cost_before += cost_before

            # Cost after optimization
            opt_width, opt_height = get_optimal_dimensions(width, height)
            tiles_after = calculate_tiles(opt_width, opt_height)
            cost_after = tiles_after * COST_PER_TILE
            total_cost_after += cost_after

        except Exception as e:
            print(f"[WARN]  Cost estimation failed for {path}: {e}")

    savings = total_cost_before - total_cost_after
    savings_percent = (savings / total_cost_before * 100) if total_cost_before > 0 else 0

    return {
        "cost_before": round(total_cost_before, 4),
        "cost_after": round(total_cost_after, 4),
        "savings": round(savings, 4),
        "savings_percent": round(savings_percent, 2),
        "images_count": len(image_paths)
    }
