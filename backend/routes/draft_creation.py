"""
Enhanced Draft Creation API Routes

AI-powered draft creation with:
- GPT-4o Vision Analysis
- Brand Detection (OCR)
- Content Generation (3 styles)
- Smart Pricing
- Complete orchestration
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from pydantic import BaseModel, Field
import os
import uuid
from pathlib import Path

from backend.services.draft_orchestrator_service import DraftOrchestratorService
from backend.core.auth import get_current_user  # ✅ FIXED: Moved from backend.security.auth
from backend.core.rate_limiter import limiter, AI_RATE_LIMIT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/drafts", tags=["draft-creation"])


class DraftCreateRequest(BaseModel):
    photo_urls: List[str] = Field(..., min_length=1, max_length=10)
    style: str = Field("casual_friendly", pattern="^(casual_friendly|professional|trendy)$")
    language: str = Field("fr", pattern="^(fr|en)$")
    user_preferences: Optional[dict] = None


class PhotoAnalysisRequest(BaseModel):
    photo_urls: List[str] = Field(..., min_length=1, max_length=20)


@router.post("/create-from-photos")
@limiter.limit(AI_RATE_LIMIT)
async def create_draft_from_photos(
    http_request: Request,
    request: DraftCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create complete AI-powered draft from photos

    Pipeline:
    1. Vision analysis (GPT-4o)
    2. Brand detection (OCR)
    3. Content generation (title, description, hashtags)
    4. Smart pricing

    Returns complete draft ready for Vinted
    """
    try:
        orchestrator = DraftOrchestratorService()

        # Create draft
        draft = await orchestrator.create_draft_from_photos(
            photo_paths=request.photo_urls,
            style=request.style,
            language=request.language,
            user_preferences=request.user_preferences
        )

        # Add user context
        draft["user_id"] = current_user["id"]
        draft["status"] = "draft"

        logger.info(f"Draft created for user {current_user['id']}: {draft['title']}")

        return {
            "success": True,
            "draft": draft,
            "message": f"Draft créé avec succès : {draft['title']}"
        }

    except Exception as e:
        logger.error(f"Draft creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Échec de création du draft: {str(e)}"
        )


@router.post("/analyze-photos")
@limiter.limit(AI_RATE_LIMIT)
async def analyze_photos_for_grouping(
    http_request: Request,
    request: PhotoAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze photos to detect items and suggest grouping

    Useful before bulk upload to determine:
    - How many items are in photos
    - How to group photos into drafts
    - Which photos belong together
    """
    try:
        orchestrator = DraftOrchestratorService()

        analysis = await orchestrator.analyze_multiple_photos(
            photo_paths=request.photo_urls
        )

        return {
            "success": True,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Photo analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analyse des photos échouée: {str(e)}"
        )


@router.post("/upload-and-create")
@limiter.limit(AI_RATE_LIMIT)
async def upload_and_create_draft(
    http_request: Request,
    files: List[UploadFile] = File(...),
    style: str = Form("casual_friendly"),
    language: str = Form("fr"),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload photos and create draft in one step

    Accepts multiple photo uploads, saves them, then creates draft
    """
    try:
        if len(files) > 10:
            raise HTTPException(400, "Maximum 10 photos per draft")

        # Save uploaded files
        upload_dir = Path(f"/tmp/vintedbot_uploads/{current_user['id']}")
        upload_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for file in files:
            # Generate unique filename
            ext = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{ext}"
            file_path = upload_dir / unique_filename

            # Save file
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            saved_paths.append(str(file_path))

        logger.info(f"Saved {len(saved_paths)} photos for user {current_user['id']}")

        # Create draft
        orchestrator = DraftOrchestratorService()
        draft = await orchestrator.create_draft_from_photos(
            photo_paths=saved_paths,
            style=style,
            language=language
        )

        draft["user_id"] = current_user["id"]
        draft["photo_paths"] = saved_paths

        return {
            "success": True,
            "draft": draft,
            "uploaded_count": len(saved_paths)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload and create failed: {e}", exc_info=True)
        raise HTTPException(500, detail=str(e))


@router.get("/generation-stats")
async def get_generation_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get AI generation statistics for user

    Returns:
    - Total drafts created with AI
    - Success rate
    - Average generation time
    - Most used styles
    """
    # TODO: Implement database tracking
    return {
        "ai_drafts_created": 0,
        "success_rate": 0.95,
        "avg_generation_time_seconds": 12,
        "most_used_style": "casual_friendly",
        "languages_used": {"fr": 80, "en": 20}
    }
