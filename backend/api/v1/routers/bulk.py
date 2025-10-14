"""
Bulk photo upload and AI-powered draft generation endpoints
Handles mass photo uploads, automatic analysis, and draft creation
"""
import os
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from backend.core.ai_analyzer import (
    analyze_clothing_photos,
    batch_analyze_photos,
    smart_group_photos
)
from backend.schemas.bulk import (
    BulkUploadResponse,
    BulkJobStatus,
    DraftItem,
    DraftUpdateRequest,
    DraftListResponse
)
from backend.settings import settings

router = APIRouter(prefix="/bulk", tags=["bulk"])

# In-memory storage for jobs (TODO: move to Redis/DB for production)
bulk_jobs: Dict[str, Dict] = {}
drafts_storage: Dict[str, DraftItem] = {}


def save_uploaded_photos(files: List[UploadFile], job_id: str) -> List[str]:
    """Save uploaded photos and return file paths"""
    temp_dir = Path("backend/data/temp_photos") / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths = []
    
    for i, file in enumerate(files):
        # Generate unique filename
        ext = Path(file.filename).suffix or ".jpg"
        filename = f"photo_{i:03d}{ext}"
        filepath = temp_dir / filename
        
        # Save file
        content = file.file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        saved_paths.append(str(filepath))
        print(f"💾 Saved: {filepath}")
    
    return saved_paths


async def process_bulk_job(job_id: str, photo_paths: List[str], photos_per_item: int):
    """
    Background task: Process bulk photos and create drafts
    """
    try:
        print(f"\n🚀 Starting bulk job {job_id}")
        bulk_jobs[job_id]["status"] = "processing"
        bulk_jobs[job_id]["started_at"] = datetime.utcnow()
        
        # Group photos into items
        photo_groups = smart_group_photos(photo_paths, max_per_group=photos_per_item)
        bulk_jobs[job_id]["total_items"] = len(photo_groups)
        
        # Analyze each group (run in thread pool to avoid blocking event loop)
        analysis_results = []
        for i, group in enumerate(photo_groups):
            print(f"\n📸 Analyzing item {i+1}/{len(photo_groups)}...")
            
            try:
                # Run synchronous OpenAI call in thread pool to avoid blocking event loop
                result = await asyncio.to_thread(analyze_clothing_photos, group)
                result['group_index'] = i
                result['photos'] = group
                analysis_results.append(result)
                
                bulk_jobs[job_id]["completed_items"] += 1
                bulk_jobs[job_id]["progress_percent"] = (i + 1) / len(photo_groups) * 100
                
            except Exception as e:
                print(f"❌ Analysis failed for item {i+1}: {e}")
                bulk_jobs[job_id]["failed_items"] += 1
                bulk_jobs[job_id]["errors"].append(f"Item {i+1}: {str(e)}")
        
        # Create drafts from analysis results
        for result in analysis_results:
            draft_id = str(uuid.uuid4())
            
            # Convert local paths to URLs
            photo_urls = []
            for path in result.get('photos', []):
                # Extract relative path from job_id onwards
                rel_path = str(Path(path).relative_to("backend/data/temp_photos"))
                photo_urls.append(f"/temp_photos/{rel_path}")
            
            draft = DraftItem(
                id=draft_id,
                title=result.get('title', 'Vêtement'),
                description=result.get('description', ''),
                price=result.get('price', 20),
                category=result.get('category', 'autre'),
                condition=result.get('condition', 'Bon état'),
                color=result.get('color', 'Non spécifié'),
                brand=result.get('brand', 'Non spécifié'),
                size=result.get('size', 'Non spécifié'),
                photos=photo_urls,
                status="ready",
                confidence=result.get('confidence', 0.0),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                analysis_result=result
            )
            
            drafts_storage[draft_id] = draft
            bulk_jobs[job_id]["drafts"].append(draft_id)
            
            print(f"✅ Draft created: {draft.title} ({draft.price}€)")
        
        # Mark job as completed
        bulk_jobs[job_id]["status"] = "completed"
        bulk_jobs[job_id]["completed_at"] = datetime.utcnow()
        bulk_jobs[job_id]["progress_percent"] = 100.0
        
        print(f"✅ Bulk job {job_id} completed: {len(analysis_results)} drafts created")
        
    except Exception as e:
        print(f"❌ Bulk job {job_id} failed: {e}")
        bulk_jobs[job_id]["status"] = "failed"
        bulk_jobs[job_id]["errors"].append(f"Job failed: {str(e)}")


@router.post("/photos/analyze", response_model=BulkUploadResponse)
async def bulk_upload_photos(
    files: List[UploadFile] = File(...),
    photos_per_item: int = Query(default=4, ge=1, le=10)
):
    """
    Upload multiple photos and analyze them to create drafts
    
    - Accepts 1-500 photos
    - Automatically groups photos into items (default: 4 photos per item)
    - Analyzes each group with AI to generate title, description, price
    - Creates ready-to-publish drafts
    
    Returns job_id to track progress
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 500:
            raise HTTPException(status_code=400, detail="Maximum 500 photos allowed")
        
        # Validate file types
        for file in files:
            if not file.content_type or not file.content_type.startswith('image/'):
                filename_str = file.filename or "unknown"
                raise HTTPException(
                    status_code=415,
                    detail=f"Only image files allowed: {filename_str}"
                )
        
        # Create job
        job_id = str(uuid.uuid4())[:8]
        
        # Save photos
        photo_paths = save_uploaded_photos(files, job_id)
        
        # Initialize job status
        estimated_items = max(1, len(photo_paths) // photos_per_item)
        
        bulk_jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "total_photos": len(photo_paths),
            "processed_photos": len(photo_paths),
            "total_items": estimated_items,
            "completed_items": 0,
            "failed_items": 0,
            "drafts": [],
            "errors": [],
            "started_at": None,
            "completed_at": None,
            "progress_percent": 0.0
        }
        
        # Start background processing with asyncio
        asyncio.create_task(process_bulk_job(job_id, photo_paths, photos_per_item))
        
        print(f"✅ Bulk job {job_id} created: {len(photo_paths)} photos -> ~{estimated_items} items")
        
        return BulkUploadResponse(
            ok=True,
            job_id=job_id,
            total_photos=len(photo_paths),
            estimated_items=estimated_items,
            status="queued",
            message=f"Processing {len(photo_paths)} photos..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Bulk upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk upload failed: {str(e)}")


@router.get("/jobs/{job_id}", response_model=BulkJobStatus)
async def get_bulk_job_status(job_id: str):
    """
    Get status of a bulk analysis job
    
    Returns:
    - Progress percentage
    - List of completed drafts
    - Errors if any
    """
    try:
        if job_id not in bulk_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job_data = bulk_jobs[job_id]
        
        # Get draft objects
        draft_ids = job_data.get("drafts", [])
        drafts = [drafts_storage[did] for did in draft_ids if did in drafts_storage]
        
        return BulkJobStatus(
            job_id=job_data["job_id"],
            status=job_data["status"],
            total_photos=job_data["total_photos"],
            processed_photos=job_data["processed_photos"],
            total_items=job_data["total_items"],
            completed_items=job_data["completed_items"],
            failed_items=job_data["failed_items"],
            drafts=drafts,
            errors=job_data.get("errors", []),
            started_at=job_data.get("started_at"),
            completed_at=job_data.get("completed_at"),
            progress_percent=job_data.get("progress_percent", 0.0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get job status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/drafts", response_model=DraftListResponse)
async def list_drafts(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    List all drafts with optional filtering
    
    Query params:
    - status: Filter by status (draft, ready, published, failed)
    - page: Page number
    - page_size: Items per page
    """
    try:
        # Get all drafts
        all_drafts = list(drafts_storage.values())
        
        # Filter by status
        if status:
            all_drafts = [d for d in all_drafts if d.status == status]
        
        # Sort by created_at desc
        all_drafts.sort(key=lambda x: x.created_at, reverse=True)
        
        # Paginate
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_drafts = all_drafts[start_idx:end_idx]
        
        return DraftListResponse(
            drafts=paginated_drafts,
            total=len(all_drafts),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        print(f"❌ List drafts error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list drafts: {str(e)}")


@router.get("/drafts/{draft_id}", response_model=DraftItem)
async def get_draft(draft_id: str):
    """Get a specific draft by ID"""
    try:
        if draft_id not in drafts_storage:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        return drafts_storage[draft_id]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Get draft error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get draft: {str(e)}")


@router.patch("/drafts/{draft_id}", response_model=DraftItem)
async def update_draft(draft_id: str, updates: DraftUpdateRequest):
    """
    Update a draft (edit title, price, description, etc.)
    """
    try:
        if draft_id not in drafts_storage:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        draft = drafts_storage[draft_id]
        
        # Apply updates
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(draft, key):
                setattr(draft, key, value)
        
        draft.updated_at = datetime.utcnow()
        drafts_storage[draft_id] = draft
        
        print(f"✅ Draft updated: {draft_id}")
        
        return draft
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update draft error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update draft: {str(e)}")


@router.delete("/drafts/{draft_id}")
async def delete_draft(draft_id: str):
    """Delete a draft"""
    try:
        if draft_id not in drafts_storage:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        del drafts_storage[draft_id]
        
        print(f"✅ Draft deleted: {draft_id}")
        
        return {"ok": True, "message": "Draft deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete draft error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete draft: {str(e)}")


@router.post("/drafts/{draft_id}/publish")
async def publish_draft(draft_id: str):
    """
    Publish a draft to Vinted
    
    This creates a Vinted listing from the draft using the 2-phase workflow:
    1. Prepare listing (Phase A)
    2. Publish listing (Phase B)
    """
    try:
        if draft_id not in drafts_storage:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        draft = drafts_storage[draft_id]
        
        # TODO: Integrate with /vinted/listings/prepare and /vinted/listings/publish
        # For now, just mark as published
        
        draft.status = "published"
        draft.updated_at = datetime.utcnow()
        drafts_storage[draft_id] = draft
        
        print(f"✅ Draft published: {draft_id}")
        
        return {
            "ok": True,
            "draft_id": draft_id,
            "status": "published",
            "message": "Draft marked as published (Vinted integration pending)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Publish draft error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish draft: {str(e)}")
