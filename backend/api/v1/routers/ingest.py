from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from sqlmodel import select
from backend.settings import settings
from backend.core.media import (
    sniff_mime,
    check_size_limit,
    is_allowed_mime,
    process_image,
    sha256_of,
    store_local,
)
from backend.db import get_session
from backend.models import Media, Draft, DraftPhoto
from backend.api.v1.schemas import DraftOut, DraftPhotoOut, MediaOut

router = APIRouter(tags=["ingest"])


@router.post("/ingest/upload", response_model=DraftOut, status_code=201)
async def ingest_upload(
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
    if not files:
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
        
        # Validate size
        check_size_limit(raw)
        
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
    async with get_session() as session:
        # Create draft
        draft = Draft(
            title=title or "",
            description="",
            status="draft"
        )
        session.add(draft)
        await session.flush()
        
        # Create media records and link to draft
        media_records = []
        for idx, p in enumerate(processed):
            # Check if media already exists
            result = await session.execute(
                select(Media).where(Media.sha256 == p["sha"])
            )
            existing_media = result.scalar_one_or_none()
            
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
                await session.flush()
            
            # Link to draft
            draft_photo = DraftPhoto(
                draft_id=draft.id,
                media_id=media.id,
                order_index=idx
            )
            session.add(draft_photo)
            media_records.append((media, idx))
        
        await session.commit()
    
    # Build response DTO
    photos_out = [
        DraftPhotoOut(
            media=MediaOut(
                id=media.id,
                url=media.url,
                width=media.width,
                height=media.height,
                mime=media.mime
            ),
            order_index=order_idx
        )
        for media, order_idx in media_records
    ]
    
    return DraftOut(
        id=draft.id,
        title=draft.title,
        description=draft.description,
        status=draft.status,
        price_suggested=None,
        photos=photos_out
    )
