from fastapi import APIRouter, UploadFile, File
from typing import List, Optional
import uuid
import os
from backend.models.schemas import PhotoIngestRequest, Draft, Item, ItemStatus
from backend.services.ai import ai_service
from backend.services.duplicates import duplicate_detector
from backend.models.db import db

router = APIRouter(prefix="/ingest", tags=["Ingest"])


@router.post("/photos", response_model=Draft)
async def ingest_photos(
    request: Optional[PhotoIngestRequest] = None,
    files: Optional[List[UploadFile]] = File(None)
):
    image_urls = []
    
    if request and request.urls:
        image_urls.extend(request.urls)
    
    if files:
        os.makedirs("backend/data/uploads", exist_ok=True)
        for file in files:
            file_path = f"backend/data/uploads/{uuid.uuid4()}_{file.filename}"
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            image_urls.append(file_path)
    
    draft = ai_service.generate_listing(image_urls)
    
    existing_items = db.get_all()
    is_duplicate, _ = duplicate_detector.check_duplicates(
        draft.title, 
        draft.image_urls, 
        existing_items
    )
    draft.possible_duplicate = is_duplicate
    
    print(f"🧠 New AI draft created: {draft.title} ({draft.price_suggestion.target}€ target)")
    
    return draft


@router.post("/save-draft", response_model=Item)
async def save_draft(draft: Draft):
    image_hash = None
    if draft.image_urls:
        image_hash = duplicate_detector.compute_image_hash(draft.image_urls[0])
    
    item = Item(
        id=str(uuid.uuid4()),
        title=draft.title,
        description=draft.description,
        brand=draft.brand,
        category=draft.category_guess,
        size=draft.size_guess,
        condition=draft.condition,
        price=draft.price_suggestion.target,
        price_suggestion=draft.price_suggestion,
        keywords=draft.keywords,
        image_urls=draft.image_urls,
        image_hash=image_hash,
        status=ItemStatus.DRAFT,
        possible_duplicate=draft.possible_duplicate,
        estimated_sale_score=draft.estimated_sale_score
    )
    
    saved_item = db.create(item)
    return saved_item
