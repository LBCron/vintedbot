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
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query, Form
from fastapi.responses import JSONResponse
from PIL import Image
import io

from backend.core.ai_analyzer import (
    analyze_clothing_photos,
    batch_analyze_photos,
    smart_group_photos,
    smart_analyze_and_group_photos
)
from backend.schemas.bulk import (
    BulkUploadResponse,
    BulkJobStatus,
    DraftItem,
    DraftUpdateRequest,
    DraftListResponse,
    GroupingPlan,
    PhotoCluster,
    GenerateRequest,
    GenerateResponse,
    ValidationError
)
from backend.schemas.vinted import PublishFlags
from backend.settings import settings
from backend.database import save_photo_plan, get_photo_plan, delete_photo_plan, update_photo_plan_results

router = APIRouter(prefix="/bulk", tags=["bulk"])

# In-memory storage for jobs (TODO: move to Redis/DB for production)
bulk_jobs: Dict[str, Dict] = {}
drafts_storage: Dict[str, DraftItem] = {}
grouping_plans: Dict[str, GroupingPlan] = {}  # Storage for grouping plans
photo_analysis_cache: Dict[str, Dict] = {}  # Temporary storage for analyzed photos

# Validation flexible des formats d'images
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.heic', '.heif'}
ALLOWED_MIMES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp', 'image/heic', 'image/heif'}


def validate_image_file(file: UploadFile) -> bool:
    """
    Validation flexible des images - accepte par extension, MIME type, ou vérification PIL
    """
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    mime = (file.content_type or "").lower()
    
    # Méthode 1: Vérifier l'extension
    if ext in ALLOWED_EXTENSIONS:
        return True
    
    # Méthode 2: Vérifier le MIME type
    if mime in ALLOWED_MIMES:
        return True
    
    # Méthode 3: Essayer de vérifier avec PIL (dernier recours)
    try:
        file.file.seek(0)
        img = Image.open(file.file)
        img.verify()
        file.file.seek(0)  # Reset pour la lecture suivante
        return True
    except Exception:
        pass
    
    return False


def save_uploaded_photos(files: List[UploadFile], job_id: str) -> List[str]:
    """Save uploaded photos and return file paths"""
    temp_dir = Path("backend/data/temp_photos") / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths = []
    
    for i, file in enumerate(files):
        # Generate unique filename
        ext = Path(file.filename or "photo.jpg").suffix or ".jpg"
        filename = f"photo_{i:03d}{ext}"
        filepath = temp_dir / filename
        
        # Save file
        content = file.file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        saved_paths.append(str(filepath))
        print(f"💾 Saved: {filepath}")
    
    return saved_paths


async def process_bulk_job(
    job_id: str, 
    photo_paths: List[str], 
    photos_per_item: int,
    use_smart_grouping: bool = False,
    style: str = "classique"
):
    """
    Background task: Process bulk photos and create drafts
    """
    try:
        print(f"\n🚀 Starting bulk job {job_id} (smart_grouping={use_smart_grouping}, style={style})")
        bulk_jobs[job_id]["status"] = "processing"
        bulk_jobs[job_id]["started_at"] = datetime.utcnow()
        
        analysis_results = []
        
        if use_smart_grouping:
            # INTELLIGENT GROUPING: Let AI analyze all photos and group them
            print(f"🧠 Using intelligent grouping for {len(photo_paths)} photos...")
            
            try:
                # Run smart grouping in thread pool (single API call for all photos)
                analysis_results = await asyncio.to_thread(
                    smart_analyze_and_group_photos, 
                    photo_paths, 
                    style
                )
                
                bulk_jobs[job_id]["total_items"] = len(analysis_results)
                bulk_jobs[job_id]["completed_items"] = len(analysis_results)
                bulk_jobs[job_id]["progress_percent"] = 100.0
                
            except Exception as e:
                print(f"❌ Smart grouping failed: {e}, falling back to simple grouping")
                # Fallback to simple grouping
                use_smart_grouping = False
        
        if not use_smart_grouping:
            # SIMPLE GROUPING: Group by sequence (every N photos = 1 item)
            photo_groups = smart_group_photos(photo_paths, max_per_group=photos_per_item)
            bulk_jobs[job_id]["total_items"] = len(photo_groups)
            
            # Analyze each group (run in thread pool to avoid blocking event loop)
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
                confidence=result.get('confidence', 0.8),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                analysis_result=result
            )
            
            drafts_storage[draft_id] = draft
            bulk_jobs[job_id]["drafts"].append(draft_id)
            
            print(f"✅ Created draft: {draft.title} ({draft.price}€)")
        
        bulk_jobs[job_id]["status"] = "completed"
        bulk_jobs[job_id]["completed_at"] = datetime.utcnow()
        bulk_jobs[job_id]["progress_percent"] = 100.0
        
        print(f"\n✅ Bulk job {job_id} completed: {len(analysis_results)} drafts created")
        
    except Exception as e:
        print(f"❌ Bulk job {job_id} failed: {e}")
        bulk_jobs[job_id]["status"] = "failed"
        bulk_jobs[job_id]["errors"].append(str(e))


@router.post("/upload", response_model=BulkUploadResponse)
async def bulk_upload_photos(
    files: List[UploadFile] = File(...),
    auto_group: bool = Query(default=True),
    photos_per_item: int = Query(default=6, ge=1, le=10)
):
    """
    Upload multiple photos for bulk analysis
    
    **Simple workflow:**
    1. Upload photos
    2. Photos are automatically grouped (N photos per item)
    3. AI analyzes each group
    4. Drafts are created
    
    Returns a job_id to track progress
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 photos per upload")
        
        # Validate all files are images
        invalid_files = []
        for file in files:
            if not validate_image_file(file):
                invalid_files.append(file.filename or "unknown")
        
        if invalid_files:
            raise HTTPException(
                status_code=415,
                detail=f"Invalid formats (expected JPG/PNG/WEBP/HEIC/GIF/BMP): {', '.join(invalid_files[:5])}"
            )
        
        # Create job ID
        job_id = str(uuid.uuid4())[:8]
        
        # Save photos
        photo_paths = save_uploaded_photos(files, job_id)
        
        # Calculate estimated items
        estimated_items = len(photo_paths) // photos_per_item if auto_group else len(photo_paths)
        
        # Initialize job status
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
        
        # Start background processing
        asyncio.create_task(
            process_bulk_job(
                job_id, 
                photo_paths, 
                photos_per_item, 
                use_smart_grouping=False,
                style="classique"
            )
        )
        
        print(f"📦 Bulk job {job_id} created: {len(photo_paths)} photos, {estimated_items} estimated items")
        
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
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/analyze", response_model=BulkUploadResponse)
async def bulk_analyze_smart(
    files: List[UploadFile] = File(...),
    style: str = Query(default="classique", description="Description style: minimal, streetwear, or classique")
):
    """
    🧠 SMART BULK ANALYSIS with AI-powered grouping
    
    Uses OpenAI Vision to intelligently group photos into items.
    Perfect for mixed batches where you don't know how many items there are.
    
    **How it works:**
    1. Upload all photos
    2. AI analyzes ALL photos together
    3. AI groups photos by visual similarity
    4. Creates one draft per detected item
    
    **Example use case:**
    - Upload 20 photos of 5 different items
    - AI detects and groups them automatically
    - Returns 5 drafts (one per item)
    
    Returns a job_id to track progress
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        if len(files) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 photos for smart analysis")
        
        # Validate all files are images
        invalid_files = []
        for file in files:
            if not validate_image_file(file):
                invalid_files.append(file.filename or "unknown")
        
        if invalid_files:
            raise HTTPException(
                status_code=415,
                detail=f"Invalid formats (expected JPG/PNG/WEBP/HEIC/GIF/BMP): {', '.join(invalid_files[:5])}"
            )
        
        # Create job ID
        job_id = str(uuid.uuid4())[:8]
        
        # Save photos
        photo_paths = save_uploaded_photos(files, job_id)
        
        # Initialize job status
        bulk_jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "total_photos": len(photo_paths),
            "processed_photos": len(photo_paths),
            "total_items": 0,  # Unknown until AI analyzes
            "completed_items": 0,
            "failed_items": 0,
            "drafts": [],
            "errors": [],
            "started_at": None,
            "completed_at": None,
            "progress_percent": 0.0
        }
        
        # Start background processing with SMART GROUPING
        asyncio.create_task(
            process_bulk_job(
                job_id, 
                photo_paths, 
                photos_per_item=4,  # Ignored when smart_grouping=True
                use_smart_grouping=True,  # ✅ ALWAYS use smart grouping
                style=style
            )
        )
        
        print(f"🧠 Smart bulk job {job_id} created: {len(photo_paths)} photos -> AI grouping, style={style}")
        
        return BulkUploadResponse(
            ok=True,
            job_id=job_id,
            total_photos=len(photo_paths),
            estimated_items=0,  # Unknown until AI analyzes
            status="queued",
            message=f"AI analyzing {len(photo_paths)} photos to detect items..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Smart bulk analyze error: {e}")
        raise HTTPException(status_code=500, detail=f"Smart analysis failed: {str(e)}")


async def process_single_item_job(job_id: str, photo_paths: List[str], style: str = "classique"):
    """
    Process all photos as a SINGLE item - no clustering
    Perfect for users uploading multiple photos of one item
    """
    try:
        print(f"📦 Processing single item job {job_id}: {len(photo_paths)} photos")
        bulk_jobs[job_id]["status"] = "processing"
        bulk_jobs[job_id]["started_at"] = datetime.utcnow()
        
        # Analyze all photos as ONE item
        analysis_result = await asyncio.to_thread(
            analyze_clothing_photos,
            photo_paths
        )
        
        # Create single draft with ALL photos
        draft_id = str(uuid.uuid4())
        draft = DraftItem(
            id=draft_id,
            title=analysis_result.get("title", "Article sans titre"),
            description=analysis_result.get("description", ""),
            price=float(analysis_result.get("price", 0)),
            category=analysis_result.get("category", "autre"),
            condition=analysis_result.get("condition", "Bon état"),
            color=analysis_result.get("color", "Non spécifié"),
            brand=analysis_result.get("brand", "Non spécifié"),
            size=analysis_result.get("size", "Non spécifié"),
            photos=[path.replace("backend/data/", "/") for path in photo_paths],
            status="ready",
            confidence=analysis_result.get("confidence", 0.85),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            analysis_result=analysis_result
        )
        
        drafts_storage[draft_id] = draft
        bulk_jobs[job_id]["drafts"].append(draft_id)
        bulk_jobs[job_id]["total_items"] = 1
        bulk_jobs[job_id]["completed_items"] = 1
        bulk_jobs[job_id]["status"] = "completed"
        bulk_jobs[job_id]["completed_at"] = datetime.utcnow()
        bulk_jobs[job_id]["progress_percent"] = 100.0
        
        print(f"✅ Single item job {job_id} completed: {draft.title} ({draft.price}€)")
        
    except Exception as e:
        print(f"❌ Single item job {job_id} failed: {e}")
        bulk_jobs[job_id]["status"] = "failed"
        bulk_jobs[job_id]["errors"].append(str(e))
        bulk_jobs[job_id]["failed_items"] = 1


@router.post("/ingest", response_model=BulkUploadResponse)
async def bulk_ingest_photos(
    files: List[UploadFile] = File(...),
    grouping_mode: str = Query(default="auto", description="Grouping mode: 'auto', 'single_item', or 'multi_item'"),
    style: str = Query(default="classique", description="Description style: minimal, streetwear, or classique")
):
    """
    📦 SAFE BULK INGEST - Zero failed drafts
    
    Intelligently processes photos with automatic single-item detection.
    
    **Automatic single-item mode triggers:**
    - Photos ≤ SINGLE_ITEM_DEFAULT_MAX_PHOTOS (default: 80)
    - grouping_mode="single_item" explicitly set
    
    **Grouping modes:**
    - `auto` (default): Smart detection based on photo count
    - `single_item`: Force all photos into one article
    - `multi_item`: Use AI intelligent grouping
    
    **How it works:**
    1. Detects if photos should be grouped as single item
    2. If single_item: Creates ONE draft with all photos
    3. If multi_item: Uses AI Vision to intelligently group photos
    
    **Returns:** job_id to track progress
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        photo_count = len(files)
        
        # Determine if single_item mode
        force_single_item = (
            grouping_mode == "single_item" or 
            (grouping_mode == "auto" and photo_count <= settings.SINGLE_ITEM_DEFAULT_MAX_PHOTOS)
        )
        
        # Validation
        max_limit = 50 if not force_single_item else 20
        if photo_count > max_limit:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {max_limit} photos for {'single item' if force_single_item else 'multi-item grouping'}"
            )
        
        invalid_files = []
        for file in files:
            if not validate_image_file(file):
                invalid_files.append(file.filename or "unknown")
        
        if invalid_files:
            raise HTTPException(
                status_code=415,
                detail=f"Invalid formats (expected JPG/PNG/WEBP/HEIC/GIF/BMP): {', '.join(invalid_files[:5])}"
            )
        
        # Create job
        job_id = str(uuid.uuid4())[:8]
        
        # Save photos
        photo_paths = save_uploaded_photos(files, job_id)
        
        # Initialize job status
        estimated_items = 1 if force_single_item else 0
        
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
            "progress_percent": 0.0,
            "grouping_mode": "single_item" if force_single_item else "multi_item"
        }
        
        # Start background processing
        if force_single_item:
            # Single item mode: analyze all photos as ONE item
            asyncio.create_task(
                process_single_item_job(job_id, photo_paths, style)
            )
            mode_desc = f"single item ({photo_count} photos)"
        else:
            # Multi-item mode: use smart AI grouping
            asyncio.create_task(
                process_bulk_job(
                    job_id,
                    photo_paths,
                    photos_per_item=4,
                    use_smart_grouping=True,
                    style=style
                )
            )
            mode_desc = f"AI intelligent grouping"
        
        print(f"📦 Ingest job {job_id} created: {photo_count} photos -> {mode_desc}, style={style}")
        
        return BulkUploadResponse(
            ok=True,
            job_id=job_id,
            total_photos=len(photo_paths),
            estimated_items=estimated_items,
            status="queued",
            message=f"Processing {photo_count} photos as {mode_desc}..."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Bulk ingest error: {e}")
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")


@router.get("/jobs/{job_id}", response_model=BulkJobStatus)
async def get_bulk_job_status(job_id: str):
    """
    Get status of a bulk analysis job
    
    Returns:
    - Progress percentage
    - List of completed drafts
    - Errors if any
    
    **Note:** Also checks photo_analysis_cache for jobs created by /bulk/photos/analyze
    """
    try:
        # First check PostgreSQL database (for /bulk/photos/analyze jobs)
        photo_plan = get_photo_plan(job_id)
        if photo_plan:
            # Use REAL detected count if available, otherwise fallback to estimation
            detected_items = photo_plan.get("detected_items") or photo_plan["estimated_items"]
            draft_ids = photo_plan.get("draft_ids", [])
            
            # Retrieve actual draft objects if available
            draft_objects = []
            for did in draft_ids:
                if did in drafts_storage:
                    draft_objects.append(drafts_storage[did])
            
            # Photo analysis is complete, drafts may or may not be generated yet
            return BulkJobStatus(
                job_id=job_id,
                status="completed",
                total_photos=photo_plan["photo_count"],
                processed_photos=photo_plan["photo_count"],
                total_items=detected_items,  # Use REAL count, not estimation!
                completed_items=detected_items,
                failed_items=0,
                drafts=draft_objects,
                errors=[],
                started_at=photo_plan["created_at"],
                completed_at=photo_plan["created_at"],
                progress_percent=100.0
            )
        
        # Then check bulk_jobs (for /bulk/ingest jobs)
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
    """
    try:
        # Get all drafts
        all_drafts = list(drafts_storage.values())
        
        # Filter by status if provided
        if status:
            all_drafts = [d for d in all_drafts if d.status == status]
        
        # Sort by created_at desc
        all_drafts.sort(key=lambda x: x.created_at, reverse=True)
        
        # Pagination
        total = len(all_drafts)
        start = (page - 1) * page_size
        end = start + page_size
        page_drafts = all_drafts[start:end]
        
        return DraftListResponse(
            drafts=page_drafts,
            total=total,
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


@router.post("/photos/analyze")
async def analyze_bulk_photos(
    files: List[UploadFile] = File(...),
    auto_grouping: bool = Form(default=True)
):
    """
    📸 ANALYZE PHOTOS (Frontend-compatible endpoint)
    
    Analyzes uploaded photos and returns grouping info.
    This endpoint is called by the Lovable frontend.
    
    **Returns:** {job_id, status, total_photos, estimated_items, plan_id}
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        photo_count = len(files)
        
        # Validate files
        invalid_files = []
        for file in files:
            if not validate_image_file(file):
                invalid_files.append(file.filename or "unknown")
        
        if invalid_files:
            raise HTTPException(
                status_code=415,
                detail=f"Invalid formats: {', '.join(invalid_files[:5])}"
            )
        
        # Save photos temporarily and create plan
        plan_id = str(uuid.uuid4())[:8]
        photo_paths = save_uploaded_photos(files, plan_id)
        
        # Determine single-item mode:
        # - If auto_grouping=False → Force single-item (all photos = 1 article)
        # - If auto_grouping=True AND ≤80 photos → Single-item by default
        # - If auto_grouping=True AND >80 photos → Multi-item (GPT-4 Vision analysis)
        force_single_item = (
            not auto_grouping or photo_count <= settings.SINGLE_ITEM_DEFAULT_MAX_PHOTOS
        )
        
        # Smart estimation: ~5-6 photos per item on average (better UX for frontend)
        # This is just an initial estimate - GPT-4 Vision will detect the real count
        estimated_items = max(1, photo_count // 5)
        
        # Save plan to PostgreSQL database for persistence
        save_photo_plan(
            plan_id=plan_id,
            photo_paths=photo_paths,
            photo_count=photo_count,
            auto_grouping=auto_grouping,
            estimated_items=estimated_items
        )
        
        print(f"📸 Analyzed {photo_count} photos → plan_id: {plan_id}, estimated: {estimated_items} items (saved to DB)")
        
        return {
            "job_id": plan_id,
            "plan_id": plan_id,
            "status": "completed",
            "total_photos": photo_count,
            "estimated_items": estimated_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Analyze photos error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze photos: {str(e)}")


@router.post("/plan", response_model=GroupingPlan)
async def create_grouping_plan(
    files: List[UploadFile] = File(...),
    auto_grouping: bool = Query(default=True, description="Enable auto single-item detection"),
    style: str = Query(default="classique", description="Description style")
):
    """
    🎯 CREATE GROUPING PLAN (Anti-Saucisson)
    
    Analyzes photos and creates an intelligent grouping plan WITHOUT generating drafts yet.
    
    **Auto-grouping rules:**
    - If auto_grouping=true OR photos ≤ SINGLE_ITEM_DEFAULT_MAX_PHOTOS (80) → Single item mode
    - Detects labels (care labels, brand tags, size labels) via AI Vision
    - Clusters ≤2 photos or label-only → auto-attach to largest cluster
    - NEVER creates label-only articles
    
    **Returns:** A grouping plan with cluster details and merge recommendations
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        photo_count = len(files)
        
        # Validate files
        invalid_files = []
        for file in files:
            if not validate_image_file(file):
                invalid_files.append(file.filename or "unknown")
        
        if invalid_files:
            raise HTTPException(
                status_code=415,
                detail=f"Invalid formats: {', '.join(invalid_files[:5])}"
            )
        
        # Save photos temporarily
        plan_id = str(uuid.uuid4())[:8]
        photo_paths = save_uploaded_photos(files, plan_id)
        
        # Determine single-item mode (auto_grouping OR ≤80 photos)
        force_single_item = (
            auto_grouping or photo_count <= settings.SINGLE_ITEM_DEFAULT_MAX_PHOTOS
        )
        
        clusters = []
        grouping_reason = ""
        
        if force_single_item:
            # SINGLE ITEM MODE: All photos in one cluster
            clusters.append(PhotoCluster(
                cluster_id="main",
                photo_paths=photo_paths,
                photo_count=photo_count,
                cluster_type="main_item",
                confidence=0.95,
                label_detected=None,
                merge_target=None
            ))
            grouping_reason = f"Auto single-item (≤{settings.SINGLE_ITEM_DEFAULT_MAX_PHOTOS} photos)"
            estimated_items = 1
            
        else:
            # MULTI-ITEM MODE: AI Vision detection with label attachment
            print(f"🧠 Running AI Vision grouping for {photo_count} photos...")
            
            # Use existing smart_analyze_and_group_photos to get AI grouping
            grouped_results = await asyncio.to_thread(
                smart_analyze_and_group_photos,
                photo_paths,
                style
            )
            
            # Convert AI results to PhotoClusters
            for idx, result in enumerate(grouped_results):
                result_photos = result.get('photos', [])
                
                # Determine cluster type based on photo count and confidence
                cluster_type = "main_item"
                label_detected = None
                merge_target = None
                
                # Check if this might be a label cluster (≤2 photos)
                if len(result_photos) <= 2:
                    cluster_type = "detail"  # Could be label or detail
                    # If this is a small cluster, mark it to merge with main
                    if len(grouped_results) > 1:
                        merge_target = "0"  # Merge to first (largest) cluster
                
                clusters.append(PhotoCluster(
                    cluster_id=str(idx),
                    photo_paths=result_photos,
                    photo_count=len(result_photos),
                    cluster_type=cluster_type,
                    confidence=result.get('confidence', 0.8),
                    label_detected=label_detected,
                    merge_target=merge_target
                ))
            
            grouping_reason = f"AI Vision grouping ({len(grouped_results)} items detected)"
            estimated_items = len(grouped_results)
        
        # Create and store plan
        plan = GroupingPlan(
            plan_id=plan_id,
            total_photos=photo_count,
            clusters=clusters,
            estimated_items=estimated_items,
            single_item_mode=force_single_item,
            grouping_reason=grouping_reason,
            created_at=datetime.utcnow()
        )
        
        grouping_plans[plan_id] = plan
        
        print(f"📋 Created grouping plan {plan_id}: {photo_count} photos → {estimated_items} items ({grouping_reason})")
        
        return plan
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Create plan error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create plan: {str(e)}")


@router.post("/generate", response_model=GenerateResponse)
async def generate_drafts_from_plan(request: GenerateRequest):
    """
    ✨ GENERATE DRAFTS WITH STRICT VALIDATION (Zero Failed Drafts)
    
    Creates drafts from a grouping plan or photos with STRICT validation.
    
    **Validation rules (MUST ALL PASS):**
    - publish_ready === true
    - missing_fields.length === 0
    - title ≤ 70 characters
    - 3 ≤ hashtags ≤ 5
    
    **If validation fails:**
    - Returns clear error message
    - NO draft created (zero failed drafts)
    
    **Usage:**
    - Option 1: Use plan_id from /bulk/plan
    - Option 2: Provide photo_paths directly
    """
    try:
        photo_paths = []
        plan_id = request.plan_id
        
        # Get photo paths from plan or request
        if plan_id:
            # First check PostgreSQL database (for /bulk/photos/analyze plans)
            photo_plan = get_photo_plan(plan_id)
            if photo_plan:
                photo_paths = photo_plan["photo_paths"]
            # Then check grouping_plans (for /bulk/plan plans)
            elif plan_id in grouping_plans:
                plan = grouping_plans[plan_id]
                # Collect all photos from main clusters (skip label-only)
                for cluster in plan.clusters:
                    if cluster.cluster_type != "label" or cluster.merge_target:
                        photo_paths.extend(cluster.photo_paths)
            else:
                raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
                    
        elif request.photo_paths:
            photo_paths = request.photo_paths
        else:
            raise HTTPException(status_code=400, detail="Either plan_id or photo_paths required")
        
        if not photo_paths:
            raise HTTPException(status_code=400, detail="No photos to process")
        
        # Use smart grouping to detect MULTIPLE distinct items
        style = request.style or "classique"
        grouped_items = await asyncio.to_thread(
            smart_analyze_and_group_photos,
            photo_paths,
            style
        )
        
        # Process EACH detected item individually
        created_drafts = []
        skipped_items = []
        errors = []
        
        for item_index, item in enumerate(grouped_items, 1):
            try:
                # STRICT VALIDATION for each item
                validation_errors = []
                
                # Check title length
                title = item.get("title", "")
                if len(title) > 70:
                    validation_errors.append(f"title too long ({len(title)} chars)")
                
                # Check hashtags
                description = item.get("description", "")
                hashtags = [word for word in description.split() if word.startswith('#')]
                hashtag_count = len(hashtags)
                
                if hashtag_count < 3 or hashtag_count > 5:
                    validation_errors.append(f"invalid hashtag count ({hashtag_count})")
                
                # Check required fields
                required_fields = ['title', 'description', 'price', 'category', 'brand', 'size']
                missing_fields = [f for f in required_fields if not item.get(f)]
                
                if missing_fields:
                    validation_errors.append(f"missing: {', '.join(missing_fields)}")
                
                # If validation fails for this item → Skip it
                if validation_errors:
                    error_msg = f"Item {item_index} ({title[:30]}...): {'; '.join(validation_errors)}"
                    errors.append(error_msg)
                    skipped_items.append(item)
                    print(f"⚠️ Skipped item {item_index}: {error_msg}")
                    continue
                
                # All validations passed → Create draft for this item
                draft_id = str(uuid.uuid4())
                draft = DraftItem(
                    id=draft_id,
                    title=title,
                    description=description,
                    price=float(item.get("price", 0)),
                    category=item.get("category", "autre"),
                    condition=item.get("condition", "Bon état"),
                    color=item.get("color", "Non spécifié"),
                    brand=item.get("brand", "Non spécifié"),
                    size=item.get("size", "Non spécifié"),
                    photos=[path.replace("backend/data/", "/") for path in item.get("photos", [])],
                    status="ready",
                    confidence=item.get("confidence", 0.85),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    analysis_result=item,
                    flags=PublishFlags(
                        publish_ready=True,
                        ai_validated=True,
                        photos_validated=True
                    ),
                    missing_fields=[]
                )
                
                drafts_storage[draft_id] = draft
                created_drafts.append(draft)
                
                print(f"✅ Draft {item_index}/{len(grouped_items)}: {draft.title} ({len(item.get('photos', []))} photos, {hashtag_count} hashtags)")
                
            except Exception as e:
                error_msg = f"Item {item_index} error: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
        
        # Return response with all created drafts
        success_count = len(created_drafts)
        skip_count = len(skipped_items)
        detected_count = len(grouped_items)
        
        # Update photo plan with REAL results (if plan_id exists)
        if plan_id:
            draft_ids_list = [d.id for d in created_drafts]
            update_photo_plan_results(plan_id, detected_count, draft_ids_list)
            print(f"📊 Updated plan {plan_id}: {detected_count} detected items, {success_count} valid drafts")
        
        if success_count == 0:
            return GenerateResponse(
                ok=False,
                generated_count=0,
                skipped_count=skip_count,
                drafts=[],
                errors=errors,
                message=f"❌ No valid drafts created. {skip_count} items skipped. Errors: {'; '.join(errors[:3])}"
            )
        
        return GenerateResponse(
            ok=True,
            generated_count=success_count,
            skipped_count=skip_count,
            drafts=created_drafts,
            errors=errors,
            message=f"✅ Created {success_count} draft(s) from {detected_count} detected items ({skip_count} skipped)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Generate drafts error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
