"""API routes for AI image enhancement"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
from backend.services.image_enhancer_service import ImageEnhancerService
from backend.security.auth import get_current_user
import logging
import os
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/images", tags=["image-enhancement"])


class BatchEnhanceRequest(BaseModel):
    image_paths: List[str]
    auto_apply: bool = False


@router.post("/analyze")
async def analyze_image(
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
async def enhance_image(
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
async def batch_enhance_images(
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
