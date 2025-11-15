"""API routes for AI image enhancement"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from pydantic import BaseModel, Field, field_validator
from typing import List
from backend.services.image_enhancer_service import ImageEnhancerService
from backend.security.auth import get_current_user
from backend.core.rate_limiter import limiter, AI_RATE_LIMIT, IMAGE_RATE_LIMIT, BATCH_RATE_LIMIT
import logging
import os
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/images", tags=["image-enhancement"])


class BatchEnhanceRequest(BaseModel):
    image_paths: List[str] = Field(..., min_length=1, max_length=20, description="Max 20 images per batch")
    auto_apply: bool = False

    @field_validator('image_paths')
    @classmethod
    def validate_image_paths(cls, v):
        if not v:
            raise ValueError('image_paths cannot be empty')
        if len(v) > 20:
            raise ValueError('Cannot enhance more than 20 images at once')
        # Validate each path
        for path in v:
            if not path or len(path) > 500:
                raise ValueError('Invalid image path')
            # Basic path traversal protection
            if '..' in path or path.startswith('/etc') or path.startswith('/root'):
                raise ValueError('Invalid image path')
        return v


@router.post("/analyze")
@limiter.limit(AI_RATE_LIMIT)
async def analyze_image(
    http_request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Analyze image quality with AI"""
    # Save uploaded file temporarily
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"

    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        service = ImageEnhancerService()
        analysis = await service.analyze_image_quality(temp_path)

        return analysis

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/enhance")
@limiter.limit(IMAGE_RATE_LIMIT)
async def enhance_image(
    http_request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Enhance image automatically"""
    # Save uploaded file
    temp_path = f"/tmp/{uuid.uuid4()}_{file.filename}"

    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        service = ImageEnhancerService()

        # Smart enhance
        enhanced_path = service.smart_enhance(temp_path)

        # Return enhanced image path
        return {
            "success": True,
            "original_path": temp_path,
            "enhanced_path": enhanced_path
        }

    except Exception as e:
        logger.error(f"Failed to enhance image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-enhance")
@limiter.limit(BATCH_RATE_LIMIT)
async def batch_enhance_images(
    http_request: Request,
    request: BatchEnhanceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Batch enhance multiple images"""
    service = ImageEnhancerService()
    results = await service.batch_enhance(
        request.image_paths,
        request.auto_apply
    )

    return {
        "results": results,
        "total": len(results),
        "successful": len([r for r in results if r.get("success")])
    }
