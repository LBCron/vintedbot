from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import List, Optional
from sqlmodel import select
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.settings import settings
from backend.core.media import (
    sniff_mime,
    is_allowed_mime,
    process_image,
    sha256_of,
    store_local,
)
from backend.db import get_db_session
from backend.models import Media, Draft, DraftPhoto
from backend.api.v1.schemas import DraftOut, DraftPhotoOut, MediaOut

router = APIRouter(tags=["ingest"])
limiter = Limiter(key_func=get_remote_address)


@router.options("/ingest/upload")
async def ingest_upload_options():
    """OPTIONS endpoint for CORS preflight"""
    return {"methods": ["POST", "OPTIONS"]}


@router.post("/ingest/upload", response_model=DraftOut, status_code=201)
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def ingest_upload(
    request: Request,
    files: List[UploadFile] = File(..., description="Multiple image files (field name: 'files')"),
    title: str = Form("", description="Optional initial title for the draft"),
):
    """
    Upload multiple images and create a draft listing.
    
    Features:
    - Accepts 1-20 image files
    - Auto-corrects orientation from EXIF
    - Resizes to max 1600px
    - Compresses to JPEG (quality 80)
    - Strips GPS/EXIF data
    - Idempotent storage by content hash
    
    Returns: Draft listing with processed photos
    """
    if not files or len(files) == 0:
        raise HTTPException(400, "No files provided")
    
    if len(files) > settings.MAX_UPLOADS_PER_REQUEST:
        raise HTTPException(
            413,
            f"Too many files ({len(files)} > {settings.MAX_UPLOADS_PER_REQUEST})"
        )

    # Process each image
    processed = []
    for f in files:
        raw = await f.read()
        
        # Validate size (raise 413 for oversized files)
        mb = len(raw) / (1024 * 1024)
        if mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                413,
                f"File too large: {mb:.1f} MB exceeds limit of {settings.MAX_FILE_SIZE_MB} MB"
            )
        
        # Validate MIME type
        mime = sniff_mime(raw)
        if not is_allowed_mime(mime):
            raise HTTPException(415, f"Unsupported MIME type: {mime}")
        
        # Process image (orientation, resize, EXIF removal)
        jpeg_bytes, w, h, out_mime = process_image(raw)
        
        # Calculate hash for idempotency
        sha = sha256_of(jpeg_bytes)
        
        # Store locally
        url = store_local(jpeg_bytes, sha)
        
        processed.append({
            "sha": sha,
            "url": url,
            "width": w,
            "height": h,
            "mime": out_mime,
            "size_bytes": len(jpeg_bytes),
            "filename": f"{sha}.jpg"
        })

    # Save to database
    with get_db_session() as session:
        # Create draft
        draft = Draft(
            title=title or "",
            description="",
            status="draft"
        )
        session.add(draft)
        session.flush()
        
        # Create media records and link to draft
        media_records = []
        for idx, p in enumerate(processed):
            # Check if media already exists
            result = session.exec(
                select(Media).where(Media.sha256 == p["sha"])
            )
            existing_media = result.first()
            
            if existing_media:
                media = existing_media
            else:
                media = Media(
                    sha256=p["sha"],
                    filename=p["filename"],
                    mime=p["mime"],
                    width=p["width"],
                    height=p["height"],
                    size_bytes=p["size_bytes"],
                    storage="local",
                    url=p["url"]
                )
                session.add(media)
                session.flush()
            
            # Link to draft
            draft_photo = DraftPhoto(
                draft_id=draft.id,
                media_id=media.id,
                order_index=idx
            )
            session.add(draft_photo)
            
            # Store media data for response (before session closes)
            media_records.append({
                "id": media.id,
                "url": media.url,
                "width": media.width,
                "height": media.height,
                "mime": media.mime,
                "order_index": idx
            })
        
        session.commit()
        session.refresh(draft)
    
    # Build response DTO
    photos_out = [
        DraftPhotoOut(
            media=MediaOut(
                id=m["id"],
                url=m["url"],
                width=m["width"],
                height=m["height"],
                mime=m["mime"]
            ),
            order_index=m["order_index"]
        )
        for m in media_records
    ]
    
    return DraftOut(
        id=draft.id,
        title=draft.title,
        description=draft.description,
        status=draft.status,
        price_suggested=None,
        photos=photos_out
    )
