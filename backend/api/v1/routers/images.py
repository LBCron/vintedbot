"""
Bulk Image Editing API (Dotb feature)
Handles batch photo operations: crop, rotate, brightness, watermark, background removal
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import List, Optional
from backend.core.auth import get_current_user, User
from pydantic import BaseModel, Field
from datetime import datetime
import os
import uuid
from pathlib import Path
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import traceback

router = APIRouter(prefix="/images", tags=["images"])


# Pydantic models for image editing operations
class BulkCropRequest(BaseModel):
    """Request to crop multiple images"""
    image_paths: List[str]
    x: int = Field(..., ge=0, description="X coordinate of crop start")
    y: int = Field(..., ge=0, description="Y coordinate of crop start")
    width: int = Field(..., gt=0, description="Width of crop area")
    height: int = Field(..., gt=0, description="Height of crop area")


class BulkRotateRequest(BaseModel):
    """Request to rotate multiple images"""
    image_paths: List[str]
    angle: int = Field(..., description="Rotation angle in degrees (90, 180, 270, or custom)")


class BulkAdjustRequest(BaseModel):
    """Request to adjust brightness/contrast for multiple images"""
    image_paths: List[str]
    brightness: float = Field(1.0, ge=0.0, le=2.0, description="Brightness factor (1.0 = no change)")
    contrast: float = Field(1.0, ge=0.0, le=2.0, description="Contrast factor (1.0 = no change)")
    saturation: Optional[float] = Field(None, ge=0.0, le=2.0, description="Saturation factor (optional)")


class BulkWatermarkRequest(BaseModel):
    """Request to add watermark to multiple images"""
    image_paths: List[str]
    text: str = Field(..., max_length=100, description="Watermark text")
    position: str = Field("bottom-right", description="Position: top-left, top-right, bottom-left, bottom-right, center")
    opacity: float = Field(0.5, ge=0.0, le=1.0, description="Watermark opacity (0.0 to 1.0)")
    font_size: int = Field(24, gt=0, le=200, description="Font size in pixels")


class BulkRemoveBackgroundRequest(BaseModel):
    """Request to remove background from multiple images"""
    image_paths: List[str]
    mode: str = Field("auto", description="Mode: auto, white, transparent")


@router.post("/bulk/crop")
async def bulk_crop_images(
    request: BulkCropRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Crop multiple images to the same dimensions (Dotb feature)

    Useful for creating uniform product photos.
    All images will be cropped to the same area.

    Request body:
    - image_paths: List of image paths to crop
    - x, y: Top-left corner of crop area
    - width, height: Dimensions of crop area
    """
    try:
        results = {
            "success": [],
            "failed": [],
            "total": len(request.image_paths)
        }

        for path in request.image_paths:
            try:
                # Validate file exists
                if not os.path.exists(path):
                    results["failed"].append({
                        "path": path,
                        "error": "File not found"
                    })
                    continue

                # Open image
                img = Image.open(path)

                # Validate crop dimensions
                img_width, img_height = img.size
                if request.x + request.width > img_width or request.y + request.height > img_height:
                    results["failed"].append({
                        "path": path,
                        "error": f"Crop area exceeds image dimensions ({img_width}x{img_height})"
                    })
                    continue

                # Crop image
                cropped = img.crop((
                    request.x,
                    request.y,
                    request.x + request.width,
                    request.y + request.height
                ))

                # Save cropped image (overwrite original)
                cropped.save(path, quality=95, optimize=True)

                results["success"].append({
                    "path": path,
                    "operation": "crop",
                    "dimensions": f"{request.width}x{request.height}",
                    "original_size": f"{img_width}x{img_height}"
                })

                print(f"[IMAGE] Cropped {path} to {request.width}x{request.height}")

            except Exception as e:
                results["failed"].append({
                    "path": path,
                    "error": str(e)
                })
                print(f"[ERROR] Failed to crop {path}: {e}")

        return {
            "ok": True,
            "message": f"Cropped {len(results['success'])} images ({len(results['failed'])} failed)",
            "results": results
        }

    except Exception as e:
        print(f"[ERROR] Bulk crop failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Bulk crop failed: {str(e)}")


@router.post("/bulk/rotate")
async def bulk_rotate_images(
    request: BulkRotateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Rotate multiple images by the same angle (Dotb feature)

    Common angles: 90, 180, 270 degrees.
    Useful for correcting photo orientation in batch.
    """
    try:
        results = {
            "success": [],
            "failed": [],
            "total": len(request.image_paths)
        }

        for path in request.image_paths:
            try:
                # Validate file exists
                if not os.path.exists(path):
                    results["failed"].append({
                        "path": path,
                        "error": "File not found"
                    })
                    continue

                # Open image
                img = Image.open(path)
                original_size = img.size

                # Rotate image (negative angle for clockwise rotation)
                # expand=True ensures the entire rotated image is visible
                rotated = img.rotate(-request.angle, expand=True, resample=Image.BICUBIC)

                # Save rotated image (overwrite original)
                rotated.save(path, quality=95, optimize=True)

                results["success"].append({
                    "path": path,
                    "operation": "rotate",
                    "angle": request.angle,
                    "original_size": f"{original_size[0]}x{original_size[1]}",
                    "new_size": f"{rotated.size[0]}x{rotated.size[1]}"
                })

                print(f"[IMAGE] Rotated {path} by {request.angle}°")

            except Exception as e:
                results["failed"].append({
                    "path": path,
                    "error": str(e)
                })
                print(f"[ERROR] Failed to rotate {path}: {e}")

        return {
            "ok": True,
            "message": f"Rotated {len(results['success'])} images by {request.angle}° ({len(results['failed'])} failed)",
            "results": results
        }

    except Exception as e:
        print(f"[ERROR] Bulk rotate failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Bulk rotate failed: {str(e)}")


@router.post("/bulk/adjust")
async def bulk_adjust_images(
    request: BulkAdjustRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Adjust brightness, contrast, and saturation for multiple images (Dotb feature)

    Perfect for enhancing product photos in batch.
    All adjustments are applied to all images.

    Values:
    - 1.0 = no change
    - < 1.0 = decrease
    - > 1.0 = increase
    """
    try:
        results = {
            "success": [],
            "failed": [],
            "total": len(request.image_paths)
        }

        for path in request.image_paths:
            try:
                # Validate file exists
                if not os.path.exists(path):
                    results["failed"].append({
                        "path": path,
                        "error": "File not found"
                    })
                    continue

                # Open image
                img = Image.open(path)
                original_mode = img.mode

                # Convert to RGB if necessary (some formats don't support enhancement)
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')

                # Apply brightness adjustment
                if request.brightness != 1.0:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(request.brightness)

                # Apply contrast adjustment
                if request.contrast != 1.0:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(request.contrast)

                # Apply saturation adjustment if specified
                if request.saturation is not None and request.saturation != 1.0:
                    enhancer = ImageEnhance.Color(img)
                    img = enhancer.enhance(request.saturation)

                # Save adjusted image (overwrite original)
                img.save(path, quality=95, optimize=True)

                adjustments = {
                    "brightness": request.brightness,
                    "contrast": request.contrast
                }
                if request.saturation is not None:
                    adjustments["saturation"] = request.saturation

                results["success"].append({
                    "path": path,
                    "operation": "adjust",
                    **adjustments
                })

                print(f"[IMAGE] Adjusted {path}: brightness={request.brightness}, contrast={request.contrast}, saturation={request.saturation}")

            except Exception as e:
                results["failed"].append({
                    "path": path,
                    "error": str(e)
                })
                print(f"[ERROR] Failed to adjust {path}: {e}")

        return {
            "ok": True,
            "message": f"Adjusted {len(results['success'])} images ({len(results['failed'])} failed)",
            "results": results
        }

    except Exception as e:
        print(f"[ERROR] Bulk adjust failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Bulk adjust failed: {str(e)}")


@router.post("/bulk/watermark")
async def bulk_watermark_images(
    request: BulkWatermarkRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Add watermark text to multiple images (Dotb feature)

    Protects your product photos with your brand name or logo.
    Watermark is added to all selected images.

    Positions: top-left, top-right, bottom-left, bottom-right, center
    """
    try:
        results = {
            "success": [],
            "failed": [],
            "total": len(request.image_paths)
        }

        for path in request.image_paths:
            try:
                # Validate file exists
                if not os.path.exists(path):
                    results["failed"].append({
                        "path": path,
                        "error": "File not found"
                    })
                    continue

                # Open image
                img = Image.open(path)

                # Convert to RGBA for transparency support
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # Create a transparent overlay
                overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
                draw = ImageDraw.Draw(overlay)

                # Try to load a font, fallback to default if not available
                try:
                    font = ImageFont.truetype("arial.ttf", request.font_size)
                except:
                    try:
                        # Try common Windows font path
                        font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", request.font_size)
                    except:
                        # Fallback to default font
                        font = ImageFont.load_default()

                # Get text bounding box to calculate position
                bbox = draw.textbbox((0, 0), request.text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Calculate position based on request
                margin = 20
                if request.position == "top-left":
                    position = (margin, margin)
                elif request.position == "top-right":
                    position = (img.width - text_width - margin, margin)
                elif request.position == "bottom-left":
                    position = (margin, img.height - text_height - margin)
                elif request.position == "bottom-right":
                    position = (img.width - text_width - margin, img.height - text_height - margin)
                elif request.position == "center":
                    position = ((img.width - text_width) // 2, (img.height - text_height) // 2)
                else:
                    position = (img.width - text_width - margin, img.height - text_height - margin)

                # Calculate opacity (0-255 from 0.0-1.0)
                opacity = int(request.opacity * 255)

                # Draw text with shadow for better visibility
                shadow_offset = 2
                draw.text((position[0] + shadow_offset, position[1] + shadow_offset),
                         request.text, font=font, fill=(0, 0, 0, opacity // 2))
                draw.text(position, request.text, font=font, fill=(255, 255, 255, opacity))

                # Composite overlay onto image
                watermarked = Image.alpha_composite(img, overlay)

                # Convert back to RGB for JPEG compatibility
                if path.lower().endswith(('.jpg', '.jpeg')):
                    watermarked = watermarked.convert('RGB')

                # Save watermarked image (overwrite original)
                watermarked.save(path, quality=95, optimize=True)

                results["success"].append({
                    "path": path,
                    "operation": "watermark",
                    "text": request.text,
                    "position": request.position,
                    "opacity": request.opacity
                })

                print(f"[IMAGE] Added watermark to {path}: '{request.text}' at {request.position}")

            except Exception as e:
                results["failed"].append({
                    "path": path,
                    "error": str(e)
                })
                print(f"[ERROR] Failed to add watermark to {path}: {e}")
                traceback.print_exc()

        return {
            "ok": True,
            "message": f"Added watermark to {len(results['success'])} images ({len(results['failed'])} failed)",
            "results": results
        }

    except Exception as e:
        print(f"[ERROR] Bulk watermark failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Bulk watermark failed: {str(e)}")


@router.post("/bulk/remove-background")
async def bulk_remove_background(
    request: BulkRemoveBackgroundRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Remove background from multiple images (Dotb feature)

    Creates clean product photos with transparent or white backgrounds.
    Uses AI-powered background removal if rembg is installed.

    Modes:
    - auto: AI detects and removes background (requires rembg)
    - white: Replace background with white
    - transparent: Make background transparent (PNG)
    """
    try:
        # Check if rembg is available
        try:
            from rembg import remove as rembg_remove
            rembg_available = True
        except ImportError:
            rembg_available = False
            print("[WARNING] rembg not installed. Install with: pip install rembg")
            if request.mode == "auto":
                raise HTTPException(
                    status_code=400,
                    detail="Background removal with 'auto' mode requires rembg library. Install with: pip install rembg"
                )

        results = {
            "success": [],
            "failed": [],
            "total": len(request.image_paths)
        }

        for path in request.image_paths:
            try:
                # Validate file exists
                if not os.path.exists(path):
                    results["failed"].append({
                        "path": path,
                        "error": "File not found"
                    })
                    continue

                # Open image
                img = Image.open(path)
                original_format = img.format

                if request.mode == "auto" and rembg_available:
                    # AI-powered background removal with rembg
                    with open(path, 'rb') as input_file:
                        input_data = input_file.read()

                    output_data = rembg_remove(input_data)

                    # Save as PNG to preserve transparency
                    output_path = path
                    if not path.lower().endswith('.png'):
                        output_path = path.rsplit('.', 1)[0] + '.png'

                    with open(output_path, 'wb') as output_file:
                        output_file.write(output_data)

                    results["success"].append({
                        "path": output_path,
                        "operation": "remove_background",
                        "mode": request.mode,
                        "method": "rembg_ai"
                    })

                elif request.mode == "white":
                    # Replace with white background
                    if img.mode == 'RGBA':
                        # Create white background
                        white_bg = Image.new('RGB', img.size, (255, 255, 255))
                        white_bg.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                        img = white_bg
                    else:
                        # Convert to RGB if not already
                        img = img.convert('RGB')

                    img.save(path, quality=95, optimize=True)

                    results["success"].append({
                        "path": path,
                        "operation": "remove_background",
                        "mode": request.mode,
                        "method": "white_replacement"
                    })

                elif request.mode == "transparent":
                    # Make background transparent (simple threshold-based method)
                    # Note: This is a simple implementation. For better results, use rembg with mode='auto'

                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')

                    # Get pixel data
                    pixels = img.load()
                    width, height = img.size

                    # Simple threshold: make white/light pixels transparent
                    # This works best for products on white backgrounds
                    threshold = 240
                    for y in range(height):
                        for x in range(width):
                            r, g, b, a = pixels[x, y]
                            # If pixel is close to white, make it transparent
                            if r > threshold and g > threshold and b > threshold:
                                pixels[x, y] = (r, g, b, 0)

                    # Save as PNG
                    output_path = path
                    if not path.lower().endswith('.png'):
                        output_path = path.rsplit('.', 1)[0] + '.png'

                    img.save(output_path, 'PNG', quality=95, optimize=True)

                    results["success"].append({
                        "path": output_path,
                        "operation": "remove_background",
                        "mode": request.mode,
                        "method": "threshold_transparency",
                        "note": "For better results, use mode='auto' with rembg installed"
                    })

                else:
                    results["failed"].append({
                        "path": path,
                        "error": f"Invalid mode: {request.mode}"
                    })
                    continue

                print(f"[IMAGE] Removed background from {path} using mode={request.mode}")

            except Exception as e:
                results["failed"].append({
                    "path": path,
                    "error": str(e)
                })
                print(f"[ERROR] Failed to remove background from {path}: {e}")
                traceback.print_exc()

        return {
            "ok": True,
            "message": f"Processed {len(results['success'])} images ({len(results['failed'])} failed)",
            "results": results,
            "rembg_available": rembg_available,
            "note": "For AI-powered background removal, install rembg: pip install rembg" if not rembg_available else None
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Bulk background removal failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Bulk background removal failed: {str(e)}")


@router.get("/presets")
async def get_editing_presets(current_user: User = Depends(get_current_user)):
    """
    Get predefined image editing presets for quick batch edits

    Returns common adjustment presets for different scenarios
    """
    presets = [
        {
            "id": "brighten",
            "name": "Brighten Photos",
            "description": "Make photos brighter and more appealing",
            "brightness": 1.2,
            "contrast": 1.1,
            "saturation": 1.05
        },
        {
            "id": "enhance",
            "name": "Enhance Colors",
            "description": "Boost colors and contrast",
            "brightness": 1.0,
            "contrast": 1.3,
            "saturation": 1.2
        },
        {
            "id": "soften",
            "name": "Soften & Warm",
            "description": "Create soft, warm-toned images",
            "brightness": 1.1,
            "contrast": 0.9,
            "saturation": 1.1
        },
        {
            "id": "vintage",
            "name": "Vintage Look",
            "description": "Add vintage effect",
            "brightness": 0.95,
            "contrast": 1.1,
            "saturation": 0.8
        },
        {
            "id": "professional",
            "name": "Professional",
            "description": "Clean, professional product photos",
            "brightness": 1.15,
            "contrast": 1.15,
            "saturation": 1.0
        }
    ]

    return {
        "presets": presets,
        "total": len(presets)
    }
