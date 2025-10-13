from fastapi import APIRouter
from backend.settings import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """API v1 health check endpoint"""
    return {
        "status": "ok",
        "api_version": "v1",
        "media_storage": settings.MEDIA_STORAGE,
        "max_uploads": settings.MAX_UPLOADS_PER_REQUEST,
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
        "jpeg_quality": settings.JPEG_QUALITY,
        "max_dim_px": settings.MAX_DIM_PX
    }
