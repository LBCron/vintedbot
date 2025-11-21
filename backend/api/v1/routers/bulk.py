"""
Bulk photo upload and AI-powered draft generation endpoints
Handles mass photo uploads, automatic analysis, and draft creation
"""
import os
import uuid
import asyncio
import json
import zipfile
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query, Form, Depends, Request, Body
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image
import io

from backend.core.ai_analyzer import (
    analyze_clothing_photos,
    batch_analyze_photos,
    smart_group_photos,
    smart_analyze_and_group_photos
)
from backend.core.storage import get_store
from backend.core.auth import get_current_user, User
from backend.middleware.quota_checker import check_and_consume_quota, check_storage_quota
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
from backend.core.storage import get_store

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


def resolve_photo_path(photo_path: str) -> str:
    """
    RÉSOLUTION ROBUSTE DES CHEMINS PHOTOS (pour backend filesystem access)

    Gère tous les formats possibles :
    - "/temp_photos/xxx/photo_000.jpg" -> "{DATA_DIR}/temp_photos/xxx/photo_000.jpg"
    - "backend/data/temp_photos/xxx/photo_000.jpg" -> "{DATA_DIR}/temp_photos/xxx/photo_000.jpg"
    - "temp_photos/xxx/photo_000.jpg" -> "{DATA_DIR}/temp_photos/xxx/photo_000.jpg"

    Returns:
        Chemin absolu valide qui existe sur le système de fichiers
    """
    import os
    from backend.settings import settings as resolve_settings

    # 1. Si le chemin existe déjà tel quel, retourner
    if os.path.exists(photo_path):
        return photo_path

    # 2. Essayer avec le DATA_DIR
    if not photo_path.startswith(resolve_settings.DATA_DIR):
        # Supprimer "backend/data/" ou "/" au début si présent
        clean_path = photo_path.replace("backend/data/", "").lstrip("/")
        prefixed_path = f"{resolve_settings.DATA_DIR}/{clean_path}"
        if os.path.exists(prefixed_path):
            return prefixed_path

    # 3. Essayer en ajoutant DATA_DIR/temp_photos
    if "temp_photos" not in photo_path:
        basename = os.path.basename(photo_path)
        # Chercher le job_id dans le chemin (format: {job_id}/photo_xxx.jpg)
        parts = photo_path.split("/")
        if len(parts) >= 2:
            job_id = parts[-2]
            test_path = f"{resolve_settings.DATA_DIR}/temp_photos/{job_id}/{basename}"
            if os.path.exists(test_path):
                return test_path

    # 4. Retourner le chemin original (même s'il n'existe pas)
    return photo_path


def normalize_photo_url_for_frontend(photo_path: str) -> str:
    """
    Normalize photo path to frontend-compatible URL (API response layer only)
    
    Converts filesystem paths to HTTP URLs:
    - "backend/data/temp_photos/xxx/photo_000.jpg" -> "/temp_photos/xxx/photo_000.jpg"
    - "temp_photos/xxx/photo_000.jpg" -> "/temp_photos/xxx/photo_000.jpg"
    - "/temp_photos/xxx/photo_000.jpg" -> "/temp_photos/xxx/photo_000.jpg" (unchanged)
    """
    if not photo_path:
        return photo_path
    
    # Remove "backend/data/" prefix if present
    if photo_path.startswith("backend/data/temp_photos/"):
        photo_path = photo_path.replace("backend/data/temp_photos/", "temp_photos/", 1)
    
    # Ensure leading slash for HTTP URLs
    if photo_path.startswith("temp_photos/") and not photo_path.startswith("/"):
        photo_path = "/" + photo_path
    
    return photo_path


def normalize_draft_for_frontend(draft: Dict) -> Dict:
    """
    Normalize all photo URLs in a draft dict for frontend consumption
    Keeps internal data intact, only normalizes for API response
    """
    draft = draft.copy()  # Don't mutate original
    
    # Normalize photos in item_json
    if draft.get("item_json") and "photos" in draft["item_json"]:
        item_json = draft["item_json"].copy()
        item_json["photos"] = [normalize_photo_url_for_frontend(p) for p in item_json.get("photos", [])]
        draft["item_json"] = item_json
    
    # Normalize photos in listing_json
    if draft.get("listing_json") and "photos" in draft["listing_json"]:
        listing_json = draft["listing_json"].copy()
        listing_json["photos"] = [normalize_photo_url_for_frontend(p) for p in listing_json.get("photos", [])]
        draft["listing_json"] = listing_json
    
    return draft


def save_uploaded_photos(files: List[UploadFile], job_id: str) -> List[str]:
    """Save uploaded photos and return file paths (converts HEIC to JPEG)"""
    from backend.settings import settings as bulk_settings

    # [OK] CRITICAL: Register HEIC support for PIL in this function context
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
        print("[HEIC] Registered HEIC support for PIL")
    except Exception as e:
        print(f"[HEIC] Warning: Failed to register HEIC support: {e}")

    temp_dir = Path(f"{bulk_settings.DATA_DIR}/temp_photos") / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []

    for i, file in enumerate(files):
        # Read file content
        content = file.file.read()

        # Check if file is HEIC/HEIF
        original_ext = Path(file.filename or "photo.jpg").suffix.lower()
        is_heic = original_ext in ['.heic', '.heif']

        if is_heic:
            # Convert HEIC to JPEG
            try:
                from PIL import Image
                import io

                # [OK] FIX: Save HEIC to disk first, then open it (pillow-heif needs file path)
                temp_heic = temp_dir / f"temp_{i:03d}.heic"
                with open(temp_heic, "wb") as f:
                    f.write(content)

                # Open HEIC image from file path
                img = Image.open(temp_heic)

                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Save as JPEG
                filename = f"photo_{i:03d}.jpg"
                filepath = temp_dir / filename
                img.save(filepath, 'JPEG', quality=90)

                # Delete temp HEIC file
                temp_heic.unlink()

                print(f"[HEIC] Converted HEIC -> JPEG: {filename}")
            except Exception as e:
                print(f"[ERROR] Failed to convert HEIC {file.filename}: {e}")
                # Fallback: save as original
                filename = f"photo_{i:03d}{original_ext}"
                filepath = temp_dir / filename
                with open(filepath, "wb") as f:
                    f.write(content)
        else:
            # Save as-is (JPEG, PNG, etc.)
            ext = original_ext or ".jpg"
            filename = f"photo_{i:03d}{ext}"
            filepath = temp_dir / filename
            with open(filepath, "wb") as f:
                f.write(content)
            print(f"[SAVE] Saved: {filename}")
        
        saved_paths.append(str(filepath))
    
    return saved_paths


async def process_bulk_job(
    job_id: str, 
    photo_paths: List[str], 
    photos_per_item: int,
    use_smart_grouping: bool = False,
    style: str = "classique",
    update_db: bool = True,  # Update photo_plans in DB for real-time progress
    user_id: Optional[str] = None  # User ID for duplicate detection
):
    """
    Background task: Process bulk photos and create drafts
    """
    try:
        print(f"\n[START] Starting bulk job {job_id} (smart_grouping={use_smart_grouping}, style={style})")
        bulk_jobs[job_id]["status"] = "processing"
        bulk_jobs[job_id]["started_at"] = datetime.utcnow()
        
        # CHECKPOINT 0%: Job started
        bulk_jobs[job_id]["progress_percent"] = 0.0
        if update_db and get_photo_plan(job_id):
            get_store().update_photo_plan(job_id, status="processing", progress_percent=0.0)
        
        analysis_results = []
        
        # CHECKPOINT 25%: Initial setup and grouping complete
        print(f"[STEP_1] Step 1/4: Grouping photos...")
        bulk_jobs[job_id]["progress_percent"] = 25.0
        if update_db and get_photo_plan(job_id):
            get_store().update_photo_plan(job_id, progress_percent=25.0)
        
        if use_smart_grouping:
            # INTELLIGENT GROUPING: Let AI analyze all photos and group them
            print(f"[AI] Using intelligent grouping for {len(photo_paths)} photos...")
            
            try:
                # Run smart grouping in thread pool (single API call for all photos)
                analysis_results = await asyncio.to_thread(
                    smart_analyze_and_group_photos, 
                    photo_paths, 
                    style
                )
                
                bulk_jobs[job_id]["total_items"] = len(analysis_results)
                bulk_jobs[job_id]["completed_items"] = len(analysis_results)
                
                # CHECKPOINT 50%: AI analysis complete
                print(f"[DONE] Step 2/4: AI analysis complete ({len(analysis_results)} items detected)")
                bulk_jobs[job_id]["progress_percent"] = 50.0
                if update_db and get_photo_plan(job_id):
                    get_store().update_photo_plan(job_id, progress_percent=50.0)
                
            except Exception as e:
                print(f"[ERROR] Smart grouping failed: {e}, falling back to simple grouping")
                # Fallback to simple grouping
                use_smart_grouping = False
        
        if not use_smart_grouping:
            # SIMPLE GROUPING: Group by sequence (every N photos = 1 item)
            photo_groups = smart_group_photos(photo_paths, max_per_group=photos_per_item)
            bulk_jobs[job_id]["total_items"] = len(photo_groups)
            
            # Analyze each group (run in thread pool to avoid blocking event loop)
            for i, group in enumerate(photo_groups):
                print(f"\n[ANALYZING] Analyzing item {i+1}/{len(photo_groups)}...")
                
                try:
                    # Run synchronous OpenAI call in thread pool to avoid blocking event loop
                    result = await asyncio.to_thread(analyze_clothing_photos, group)
                    result['group_index'] = i
                    result['photos'] = group
                    analysis_results.append(result)
                    
                    bulk_jobs[job_id]["completed_items"] += 1
                    # Map analysis progress from 25% -> 50%
                    progress = 25.0 + ((i + 1) / len(photo_groups) * 25.0)
                    bulk_jobs[job_id]["progress_percent"] = progress
                    
                    # Update DB progress every ~5 items or on last item
                    if update_db and (i % max(1, len(photo_groups) // 5) == 0 or i == len(photo_groups) - 1):
                        if get_photo_plan(job_id):
                            get_store().update_photo_plan(job_id, progress_percent=progress)
                            print(f"[PROGRESS] Progress: {int(progress)}% ({i+1}/{len(photo_groups)} items analyzed)")
                    
                except Exception as e:
                    print(f"[ERROR] Analysis failed for item {i+1}: {e}")
                    bulk_jobs[job_id]["failed_items"] += 1
                    bulk_jobs[job_id]["errors"].append(f"Item {i+1}: {str(e)}")
        
        # CHECKPOINT 50%: Analysis complete, starting draft creation
        print(f"[STEP_3] Step 3/4: Creating drafts from {len(analysis_results)} analysis results...")
        bulk_jobs[job_id]["progress_percent"] = 50.0
        if update_db and get_photo_plan(job_id):
            get_store().update_photo_plan(job_id, progress_percent=50.0)
        
        # Create drafts from analysis results
        for idx, result in enumerate(analysis_results):
            draft_id = str(uuid.uuid4())
            
            # Convert local paths to URLs
            photo_urls = []
            for path in result.get('photos', []):
                # Extract relative path from DATA_DIR/temp_photos onwards
                try:
                    temp_photos_base = f"{settings.DATA_DIR}/temp_photos"
                    rel_path = str(Path(path).relative_to(temp_photos_base))
                    photo_urls.append(f"/temp_photos/{rel_path}")
                except ValueError:
                    # Fallback if relative_to fails
                    photo_urls.append(f"/temp_photos/{Path(path).name}")
            
            draft = DraftItem(
                id=draft_id,
                title=result.get('title', 'Vêtement'),
                description=result.get('description', ''),
                price=result.get('price', 20),
                category=result.get('category', 'autre'),
                condition=result.get('condition', 'Bon état'),
                color=result.get('color', 'Non spécifié'),
                brand=result.get('brand', 'Non spécifié'),
                size=result.get('size', 'Taille non visible'),  # Use new default
                photos=photo_urls,
                status="ready",
                confidence=result.get('confidence', 0.8),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                analysis_result=result
            )
            
            # Save draft to in-memory storage
            drafts_storage[draft_id] = draft
            bulk_jobs[job_id]["drafts"].append(draft_id)
            
            # Save draft to SQLite for persistence
            try:
                # Store additional fields in item_json
                item_json = {
                    "condition": draft.condition,
                    "photos": photo_urls,
                    "confidence": draft.confidence,
                    "category": draft.category,
                    "analysis_result": result
                }
                
                get_store().save_draft(
                    draft_id=draft_id,
                    title=draft.title,
                    description=draft.description,
                    price=draft.price,
                    category=draft.category,
                    color=draft.color,
                    brand=draft.brand,
                    size=draft.size,
                    item_json=item_json,
                    status="ready",
                    user_id=user_id  # CRITICAL: Pass user_id for duplicate detection
                )
                print(f"[DRAFT] Created draft (SQLite + memory): {draft.title} ({draft.price}€)")
            except Exception as e:
                print(f"[WARNING] Failed to save draft to SQLite: {e} (continuing with in-memory only)")
            
            # Map draft creation progress from 50% -> 100%
            progress = 50.0 + ((idx + 1) / len(analysis_results) * 50.0)
            bulk_jobs[job_id]["progress_percent"] = progress
            
            # Update DB progress every ~5 drafts or on last draft
            if update_db and (idx % max(1, len(analysis_results) // 10) == 0 or idx == len(analysis_results) - 1):
                if get_photo_plan(job_id):
                    get_store().update_photo_plan(job_id, progress_percent=progress)
                    print(f"[PROGRESS] Progress: {int(progress)}% ({idx+1}/{len(analysis_results)} drafts created)")
        
        bulk_jobs[job_id]["status"] = "completed"
        bulk_jobs[job_id]["completed_at"] = datetime.utcnow()
        bulk_jobs[job_id]["progress_percent"] = 100.0
        
        # Update DB status to "completed"
        if update_db and get_photo_plan(job_id):
            draft_ids = bulk_jobs[job_id].get("drafts", [])
            get_store().update_photo_plan(
                job_id, 
                detected_items=len(analysis_results),
                draft_ids=draft_ids,
                status="completed",
                progress_percent=100.0
            )
        
        print(f"\n[DONE] Bulk job {job_id} completed: {len(analysis_results)} drafts created")
        
    except Exception as e:
        print(f"[ERROR] Bulk job {job_id} failed: {e}")
        bulk_jobs[job_id]["status"] = "failed"
        bulk_jobs[job_id]["errors"].append(str(e))
        
        # CRITICAL: Update DB status to "failed" so clients see the true outcome
        if update_db and get_photo_plan(job_id):
            try:
                get_store().update_photo_plan(
                    job_id,
                    status="failed",
                    progress_percent=bulk_jobs[job_id].get("progress_percent", 0.0)
                )
                print(f"[DB] Updated DB status to 'failed' for job {job_id}")
            except Exception as db_error:
                print(f"[WARNING] Failed to update DB status: {db_error}")


@router.post("/upload", response_model=BulkUploadResponse)
async def bulk_upload_photos(
    files: List[UploadFile] = File(...),
    auto_group: bool = Query(default=True),
    photos_per_item: int = Query(default=6, ge=1, le=10),
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple photos for bulk analysis
    
    **Requires:** Authentication + AI quota + storage quota
    
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
        
        # Check quotas
        await check_and_consume_quota(current_user, "ai_analyses", amount=1)
        total_size_mb = sum([f.size for f in files if f.size]) / (1024 * 1024)
        await check_storage_quota(current_user, total_size_mb)
        
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
        
        # Initialize job status (in-memory)
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
        
        # CRITICAL: Save photo_plan to DB so progress tracking works
        save_photo_plan(
            plan_id=job_id,
            photo_paths=photo_paths,
            photo_count=len(photo_paths),
            auto_grouping=auto_group,
            estimated_items=estimated_items
        )
        
        # Start background processing
        asyncio.create_task(
            process_bulk_job(
                job_id, 
                photo_paths, 
                photos_per_item, 
                use_smart_grouping=False,
                style="classique",
                user_id=str(current_user.id)  # CRITICAL: Pass user_id for duplicate detection
            )
        )
        
        print(f"[JOB] Bulk job {job_id} created: {len(photo_paths)} photos, {estimated_items} estimated items")
        
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
        print(f"[ERROR] Bulk upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/analyze", response_model=BulkUploadResponse)
async def bulk_analyze_smart(
    files: List[UploadFile] = File(...),
    style: str = Query(default="classique", description="Description style: minimal, streetwear, or classique"),
    current_user: User = Depends(get_current_user)
):
    """
    SMART BULK ANALYSIS with AI-powered grouping
    
    **Requires:** Authentication + AI quota + storage quota
    
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
        
        # Check quotas
        await check_and_consume_quota(current_user, "ai_analyses", amount=1)
        total_size_mb = sum([f.size for f in files if f.size]) / (1024 * 1024)
        await check_storage_quota(current_user, total_size_mb)
        
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
        
        # Initialize job status (in-memory)
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
        
        # CRITICAL: Save photo_plan to DB so progress tracking works
        save_photo_plan(
            plan_id=job_id,
            photo_paths=photo_paths,
            photo_count=len(photo_paths),
            auto_grouping=True,  # Smart analysis always uses auto-grouping
            estimated_items=0  # Unknown until AI analyzes
        )
        
        # Start background processing with SMART GROUPING
        asyncio.create_task(
            process_bulk_job(
                job_id, 
                photo_paths, 
                photos_per_item=4,  # Ignored when smart_grouping=True
                use_smart_grouping=True,  # ALWAYS use smart grouping
                style=style,
                user_id=str(current_user.id)  # CRITICAL: Pass user_id for duplicate detection
            )
        )
        
        print(f"[AI] Smart bulk job {job_id} created: {len(photo_paths)} photos -> AI grouping, style={style}")
        
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
        print(f"[ERROR] Smart bulk analyze error: {e}")
        raise HTTPException(status_code=500, detail=f"Smart analysis failed: {str(e)}")


async def process_single_item_job(job_id: str, photo_paths: List[str], style: str = "classique"):
    """
    Process all photos as a SINGLE item - no clustering
    Perfect for users uploading multiple photos of one item
    """
    try:
        print(f"[JOB] Processing single item job {job_id}: {len(photo_paths)} photos")
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
        
        print(f"[DONE] Single item job {job_id} completed: {draft.title} ({draft.price}€)")
        
    except Exception as e:
        print(f"[ERROR] Single item job {job_id} failed: {e}")
        bulk_jobs[job_id]["status"] = "failed"
        bulk_jobs[job_id]["errors"].append(str(e))
        bulk_jobs[job_id]["failed_items"] = 1


@router.post("/ingest", response_model=BulkUploadResponse)
async def bulk_ingest_photos(
    files: List[UploadFile] = File(...),
    grouping_mode: str = Query(default="auto", description="Grouping mode: 'auto', 'single_item', or 'multi_item'"),
    style: str = Query(default="classique", description="Description style: minimal, streetwear, or classique"),
    current_user: User = Depends(get_current_user)
):
    """
    SAFE BULK INGEST - Zero failed drafts
    
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
    
    **Requires:** Authentication + AI analyses quota
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        photo_count = len(files)
        
        # Check AI quota (1 analysis for any number of photos)
        await check_and_consume_quota(current_user, "ai_analyses", amount=1)
        
        # Check storage quota (estimate 2MB per photo)
        total_size_mb = sum([f.size for f in files if f.size]) / (1024 * 1024)
        await check_storage_quota(current_user, total_size_mb)
        
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
                    style=style,
                    user_id=str(current_user.id)  # CRITICAL: Pass user_id for duplicate detection
                )
            )
            mode_desc = f"AI intelligent grouping"
        
        print(f"[JOB] Ingest job {job_id} created: {photo_count} photos -> {mode_desc}, style={style}")
        
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
        print(f"[ERROR] Bulk ingest error: {e}")
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
        # First check database for photo_plans (for /bulk/photos/analyze jobs)
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
            
            # Return REAL status from database (processing, completed, failed)
            status = photo_plan.get("status", "processing")
            progress = photo_plan.get("progress_percent", 0.0)
            
            # Calculate processed photos based on progress
            total_photos = photo_plan["photo_count"]
            processed_photos = int(total_photos * (progress / 100.0)) if status == "processing" else total_photos
            
            return BulkJobStatus(
                job_id=job_id,
                status=status,  # REAL status from DB
                total_photos=total_photos,
                processed_photos=processed_photos,
                total_items=detected_items,
                completed_items=detected_items if status == "completed" else 0,
                failed_items=0,
                drafts=draft_objects,
                errors=[],
                started_at=photo_plan.get("started_at", photo_plan["created_at"]),
                completed_at=photo_plan.get("completed_at"),
                progress_percent=progress  # REAL progress from DB
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
        print(f"[ERROR] Get job status error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get("/drafts", response_model=DraftListResponse)
async def list_drafts(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """
    List all drafts with optional filtering (reads from SQLite + in-memory fallback)
    
    **Requires:** Authentication (returns only user's own drafts)
    """
    try:
        # Get drafts from SQLite storage first (FILTERED BY USER)
        db_drafts_raw = get_store().get_drafts(status=status, limit=1000, user_id=str(current_user.id))
        
        # Convert SQLite rows to DraftItem objects
        db_drafts = []
        for row in db_drafts_raw:
            if row["item_json"]:
                # Deserialize JSON string to dict
                import json
                item_data = json.loads(row["item_json"]) if isinstance(row["item_json"], str) else row["item_json"]
                # Normalize photo URLs for frontend
                normalized_photos = [normalize_photo_url_for_frontend(p) for p in item_data.get("photos", [])]
                draft = DraftItem(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    price=row["price"],
                    brand=row["brand"],
                    size=row["size"],
                    color=row["color"],
                    category=row["category"],
                    photos=normalized_photos,
                    status=row["status"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    analysis_result=item_data,
                    flags=PublishFlags(**json.loads(row["flags_json"]) if isinstance(row["flags_json"], str) else row["flags_json"]) if row["flags_json"] else PublishFlags(),
                    missing_fields=[]
                )
                db_drafts.append(draft)
        
        # Merge with in-memory drafts (for backward compatibility)
        all_drafts = db_drafts + list(drafts_storage.values())
        
        # Remove duplicates (prefer SQLite version)
        seen_ids = set()
        unique_drafts = []
        for d in all_drafts:
            if d.id not in seen_ids:
                seen_ids.add(d.id)
                unique_drafts.append(d)
        
        # Filter by status if provided (for in-memory fallback)
        if status:
            unique_drafts = [d for d in unique_drafts if d.status == status]
        
        # Sort by created_at desc
        unique_drafts.sort(key=lambda x: x.created_at, reverse=True)
        
        # Pagination
        total = len(unique_drafts)
        start = (page - 1) * page_size
        end = start + page_size
        page_drafts = unique_drafts[start:end]
        
        return DraftListResponse(
            drafts=page_drafts,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        print(f"[ERROR] List drafts error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list drafts: {str(e)}")


@router.get("/drafts/{draft_id}", response_model=DraftItem)
async def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific draft by ID

    **Requires:** Authentication (user ownership validation)
    """
    try:
        # Get draft from SQLite
        draft_data = get_store().get_draft(draft_id)

        if not draft_data:
            raise HTTPException(status_code=404, detail="Draft not found")

        # Verify user ownership
        if draft_data.get("user_id") and draft_data["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Ce brouillon ne vous appartient pas")

        # First try in-memory (fastest)
        if draft_id in drafts_storage:
            return drafts_storage[draft_id]

        # Convert SQLite data to DraftItem
        item_json = draft_data.get("item_json", {})
        photos = item_json.get("photos", [])
        normalized_photos = [normalize_photo_url_for_frontend(p) for p in photos]

        draft = DraftItem(
            id=draft_data["id"],
            title=draft_data["title"],
            description=draft_data["description"],
            price=draft_data["price"],
            brand=draft_data.get("brand", "Non spécifié"),
            size=draft_data.get("size", "Non spécifié"),
            color=draft_data.get("color", "Non spécifié"),
            category=draft_data.get("category", "autre"),
            photos=normalized_photos,
            status=draft_data["status"],
            condition=item_json.get("condition", "Bon état"),
            confidence=item_json.get("confidence", 0.8),
            created_at=datetime.fromisoformat(draft_data["created_at"]),
            updated_at=datetime.fromisoformat(draft_data["updated_at"]),
            sku=draft_data.get("sku"),
            location=draft_data.get("location"),
            stock_quantity=draft_data.get("stock_quantity", 1),
            analysis_result=item_json.get("analysis_result", {}),
            flags=PublishFlags(**draft_data["flags_json"]) if draft_data.get("flags_json") else PublishFlags(),
            missing_fields=[]
        )

        return draft

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Get draft error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get draft: {str(e)}")


@router.patch("/drafts/{draft_id}", response_model=DraftItem)
async def update_draft(
    draft_id: str,
    updates: DraftUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update a draft (edit title, price, description, etc.)

    **Requires:** Authentication (user ownership validation)
    """
    try:
        # Get draft from database first
        draft_data = get_store().get_draft(draft_id)
        if not draft_data:
            raise HTTPException(status_code=404, detail="Draft not found")

        # Verify user ownership
        if draft_data.get("user_id") and draft_data["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Ce brouillon ne vous appartient pas")

        # Check in-memory storage
        if draft_id in drafts_storage:
            draft = drafts_storage[draft_id]
        else:
            # Reconstruct from database
            item_json = draft_data.get("item_json", {})
            photos = item_json.get("photos", [])
            normalized_photos = [normalize_photo_url_for_frontend(p) for p in photos]

            draft = DraftItem(
                id=draft_data["id"],
                title=draft_data["title"],
                description=draft_data["description"],
                price=draft_data["price"],
                brand=draft_data.get("brand", "Non spécifié"),
                size=draft_data.get("size", "Non spécifié"),
                color=draft_data.get("color", "Non spécifié"),
                category=draft_data.get("category", "autre"),
                photos=normalized_photos,
                status=draft_data["status"],
                condition=item_json.get("condition", "Bon état"),
                confidence=item_json.get("confidence", 0.8),
                created_at=datetime.fromisoformat(draft_data["created_at"]),
                updated_at=datetime.fromisoformat(draft_data["updated_at"]),
                sku=draft_data.get("sku"),
                location=draft_data.get("location"),
                stock_quantity=draft_data.get("stock_quantity", 1),
                analysis_result=item_json.get("analysis_result", {}),
                flags=PublishFlags(**draft_data["flags_json"]) if draft_data.get("flags_json") else PublishFlags(),
                missing_fields=[]
            )

        # Apply updates
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(draft, key):
                setattr(draft, key, value)

        draft.updated_at = datetime.utcnow()

        # Persist to database
        get_store().update_draft(
            draft_id=draft_id,
            title=draft.title,
            description=draft.description,
            price=draft.price,
            brand=draft.brand,
            size=draft.size,
            color=draft.color,
            category=draft.category,
            status=draft.status,
            sku=draft.sku,
            location=draft.location,
            stock_quantity=draft.stock_quantity
        )

        # Update in-memory
        drafts_storage[draft_id] = draft

        print(f"[UPDATE] Draft updated: {draft_id}")

        return draft

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Update draft error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update draft: {str(e)}")


@router.patch("/drafts/{draft_id}/photos/reorder")
async def reorder_draft_photos(
    draft_id: str,
    photos: List[str] = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
):
    """
    Reorder photos in a draft

    **Requires:** Authentication (user ownership validation)

    **Body:** {"photos": ["url1", "url2", ...]} - List of photo URLs in the new desired order

    **Returns:** Updated draft with reordered photos
    """
    try:
        # Get draft from SQLite for ownership check
        draft_data = get_store().get_draft(draft_id)

        if not draft_data:
            raise HTTPException(status_code=404, detail="Draft not found")

        # CRITICAL: Verify user ownership
        if draft_data.get("user_id") and draft_data["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Ce brouillon ne vous appartient pas")

        # Validate that all photos in the request belong to this draft
        current_photos = draft_data.get("item_json", {}).get("photos", [])
        current_photos_normalized = [normalize_photo_url_for_frontend(p) for p in current_photos]

        # Check if all provided photos exist in the current draft
        for photo in photos:
            if photo not in current_photos_normalized:
                raise HTTPException(
                    status_code=400,
                    detail=f"Photo not found in draft: {photo}"
                )

        # Update photos order in database
        get_store().update_draft_photos(draft_id, photos)

        # Also update in-memory if present
        if draft_id in drafts_storage:
            draft = drafts_storage[draft_id]
            draft.photos = photos
            draft.updated_at = datetime.utcnow()
            drafts_storage[draft_id] = draft

        print(f"[REORDER] Photos reordered for draft {draft_id}: {len(photos)} photos")

        return {
            "ok": True,
            "draft_id": draft_id,
            "photos": photos,
            "message": "Photos reordered successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Reorder photos error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reorder photos: {str(e)}")


@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a draft (from BOTH SQLite and memory)

    **Requires:** Authentication (user ownership validation)
    """
    try:
        # Get draft from SQLite for ownership check
        draft_data = get_store().get_draft(draft_id)
        
        if not draft_data:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # CRITICAL: Verify user ownership
        if draft_data.get("user_id") and draft_data["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Ce brouillon ne vous appartient pas")
        
        # Delete from SQLite (permanent deletion!)
        get_store().delete_draft(draft_id)
        
        # Also delete from memory if present
        if draft_id in drafts_storage:
            del drafts_storage[draft_id]
        
        print(f"[DELETE] Draft deleted (SQLite + memory): {draft_id}")
        
        return {"ok": True, "message": "Draft deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Delete draft error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete draft: {str(e)}")


@router.post("/drafts/{draft_id}/photos")
async def add_photos_to_draft(
    draft_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    AJOUTER DES PHOTOS À UN BROUILLON EXISTANT
    
    Permet d'ajouter des photos supplémentaires à un brouillon déjà créé.
    Utile pour compléter un article avec plus de détails visuels.
    
    **Requires:** Authentication (user ownership validation)
    
    **Returns:** {ok, added, total}
    """
    try:
        # Get draft from SQLite (with user ownership check)
        draft_data = get_store().get_draft(draft_id)
        
        if not draft_data:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # CRITICAL: Verify user ownership
        if draft_data.get("user_id") and draft_data["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Ce brouillon ne vous appartient pas")
        
        # Validate images
        invalid_files = []
        for file in files:
            if not validate_image_file(file):
                invalid_files.append(file.filename or "unknown")
        
        if invalid_files:
            raise HTTPException(
                status_code=415,
                detail=f"Invalid formats (expected JPG/PNG/WEBP/HEIC): {', '.join(invalid_files[:5])}"
            )
        
        # Get current photos from draft
        item_json = draft_data.get("item_json", {})
        current_photos = item_json.get("photos", [])
        
        # Upload new photos (use draft_id as job_id for consistency)
        new_photo_paths = save_uploaded_photos(files, draft_id)
        
        # Update draft with new photos
        updated_photos = current_photos + new_photo_paths
        item_json["photos"] = updated_photos
        
        # Save updated draft to database
        get_store().update_draft_photos(draft_id, updated_photos)
        
        print(f"[ADDED] Added {len(new_photo_paths)} photos to draft {draft_id} (total: {len(updated_photos)})")
        
        return {
            "ok": True,
            "added": len(new_photo_paths),
            "total": len(updated_photos),
            "photos": updated_photos
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Add photos error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add photos: {str(e)}")


@router.post("/drafts/{draft_id}/publish")
async def publish_draft(
    draft_id: str,
    dry_run: bool = Query(default=False, description="If true, simulate without real publication"),
    publish_mode: str = Query(default="auto", description="'auto' = publish directly, 'draft' = save as Vinted draft"),
    current_user: User = Depends(get_current_user)
):
    """
    REAL VINTED PUBLICATION (2-Phase Workflow)

    **Requires:** Authentication (user ownership validation) + publications quota
    
    **Workflow:**
    1. Phase A: Prepare listing on Vinted (upload photos, fill form)
    2. Phase B: Click "Publish" button and get listing URL
    
    **Returns:** {ok, draft_id, status, listing_url, vinted_id}
    
    **dry_run=true**: Simulate without real publication (for testing)
    **dry_run=false**: REAL publication to Vinted (default)
    """
    try:
        # Get draft from SQLite (with user ownership check)
        draft_data = get_store().get_draft(draft_id)
        
        if not draft_data:
            print(f"[WARNING] [PUBLISH] Draft {draft_id} not found in database")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "draft_not_found",
                    "message": "Ce brouillon n'existe plus. Il a peut-être été supprimé ou a expiré.",
                    "draft_id": draft_id
                }
            )
        
        # CRITICAL: Verify user ownership
        if draft_data.get("user_id") and draft_data["user_id"] != str(current_user.id):
            print(f"[WARNING] [PUBLISH] User {current_user.id} trying to publish draft owned by {draft_data['user_id']}")
            raise HTTPException(
                status_code=403,
                detail="Ce brouillon ne vous appartient pas"
            )
        
        # Check publications quota (only if not dry_run)
        if not dry_run:
            await check_and_consume_quota(current_user, "publications", amount=1)
        
        print(f"{'[DRY-RUN]' if dry_run else '[PUBLISH]'} User {current_user.id} publishing draft {draft_id}")
        
        # Extract draft fields
        item_json = draft_data.get("item_json", {})
        photos_raw = item_json.get("photos", [])
        
        # FIX CRITIQUE: Résoudre les chemins photos de manière robuste
        photos = []
        for photo_path in photos_raw:
            resolved = resolve_photo_path(photo_path)
            if os.path.exists(resolved):
                photos.append(resolved)
                print(f"[PHOTO] Photo résolved: {photo_path} -> {resolved}")
            else:
                print(f"[WARNING] Photo introuvable après résolution: {photo_path} (tried {resolved})")
        
        if not photos:
            print(f"[ERROR] [PUBLISH] Aucune photo valide trouvée pour draft {draft_id}")
            return {
                "ok": False,
                "draft_id": draft_id,
                "status": "prepare_failed",
                "reason": f"Photos introuvables. Chemins bruts: {photos_raw[:3]}",
                "dry_run": dry_run
            }
        
        # Parse price_suggestion from analysis_result
        analysis_result = item_json.get("analysis_result", {})
        price_min = analysis_result.get("price_min", draft_data["price"] * 0.8)
        price_max = analysis_result.get("price_max", draft_data["price"] * 1.2)
        
        from backend.schemas.vinted import PriceSuggestion, PublishFlags
        price_suggestion = PriceSuggestion(
            min=int(price_min),
            target=draft_data["price"],
            max=int(price_max)
        )
        
        # Extract hashtags from description (anywhere in last line)
        description = draft_data["description"]
        hashtags = []
        if description:
            lines = description.strip().split('\n')
            last_line = lines[-1].strip()
            
            # Extract all words starting with # from last line
            hashtags = [tag.strip() for tag in last_line.split() if tag.startswith('#')]
            
            # If hashtags found, remove them from description
            if hashtags:
                # Remove hashtags from last line
                words = last_line.split()
                cleaned_words = [w for w in words if not w.startswith('#')]
                cleaned_last_line = ' '.join(cleaned_words).strip()
                
                # Rebuild description without hashtags
                if cleaned_last_line:
                    lines[-1] = cleaned_last_line
                    description = '\n'.join(lines).strip()
                else:
                    # Last line was only hashtags, remove it completely
                    description = '\n'.join(lines[:-1]).strip()
        
        # Build publish readiness flags
        has_all_photos = len(photos) > 0
        hashtags_valid = 3 <= len(hashtags) <= 5
        flags = PublishFlags(
            publish_ready=has_all_photos and hashtags_valid,
            ai_validated=True,
            photos_validated=has_all_photos
        )
        
        # PHASE A: Prepare listing on Vinted
        print(f"[PHASE_A] Phase A: Preparing listing '{draft_data['title'][:50]}...'")
        
        # Build request payload
        request_payload = {
            "title": draft_data["title"],
            "price": draft_data["price"],
            "description": description,
            "brand": draft_data.get("brand"),
            "size": draft_data.get("size"),
            "condition": item_json.get("condition", "Bon état"),
            "color": draft_data.get("color"),
            "category_hint": draft_data.get("category"),
            "photos": photos,
            "hashtags": hashtags,
            "price_suggestion": {
                "min": price_suggestion.min,
                "target": price_suggestion.target,
                "max": price_suggestion.max
            },
            "flags": {
                "publish_ready": flags.publish_ready,
                "ai_validated": flags.ai_validated,
                "photos_validated": flags.photos_validated
            },
            "publish_mode": publish_mode,
            "dry_run": dry_run
        }
        
        # Get auth token for internal requests
        import httpx
        from backend.core.auth import create_access_token
        from backend.settings import settings
        access_token = create_access_token({
            "user_id": current_user.id,
            "email": current_user.email
        })

        # MODE DRAFT: Create draft on Vinted (single-phase, no publish)
        if publish_mode == "draft":
            print(f"[DRAFT] Creating Vinted draft (no publish)...")

            async with httpx.AsyncClient(timeout=60.0) as client:
                draft_response_raw = await client.post(
                    f"http://localhost:{settings.PORT}/vinted/listings/draft",
                    json=request_payload,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if draft_response_raw.status_code != 200:
                    error_detail = draft_response_raw.json().get("detail", "Unknown error")
                    print(f"[ERROR] Draft creation failed: {error_detail}")
                    return {
                        "ok": False,
                        "draft_id": draft_id,
                        "status": "draft_failed",
                        "reason": error_detail,
                        "dry_run": dry_run
                    }
                
                draft_response = draft_response_raw.json()
            
            if not draft_response.get("ok"):
                reason = draft_response.get("reason", "Unknown error")
                print(f"[ERROR] Draft creation failed: {reason}")
                return {
                    "ok": False,
                    "draft_id": draft_id,
                    "status": "draft_failed",
                    "reason": reason,
                    "dry_run": dry_run
                }
            
            vinted_draft_url = draft_response.get("vinted_draft_url")
            vinted_draft_id = draft_response.get("vinted_draft_id")
            print(f"[SUCCESS] Vinted draft created: {vinted_draft_url}")
            
            # Update draft in DB with Vinted draft info
            if not dry_run:
                get_store().update_draft_vinted_info(draft_id, vinted_draft_url, vinted_draft_id, publish_mode)
            
            return {
                "ok": True,
                "draft_id": draft_id,
                "status": "draft_created",
                "vinted_draft_url": vinted_draft_url,
                "vinted_draft_id": vinted_draft_id,
                "publish_mode": "draft",
                "dry_run": dry_run,
                "message": f"Brouillon créé sur Vinted ! Validez-le manuellement : {vinted_draft_url}" if not dry_run else "Simulation réussie (dry_run=true)"
            }
        
        # MODE AUTO: Prepare + Publish (2-phase workflow)
        print(f"[PHASE_A] Phase A: Preparing listing '{draft_data['title'][:50]}...'")

        async with httpx.AsyncClient(timeout=60.0) as client:
            prepare_response_raw = await client.post(
                f"http://localhost:{settings.PORT}/vinted/listings/prepare",
                json=request_payload,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if prepare_response_raw.status_code != 200:
                error_detail = prepare_response_raw.json().get("detail", "Unknown error")
                print(f"[ERROR] Phase A failed: {error_detail}")
                return {
                    "ok": False,
                    "draft_id": draft_id,
                    "status": "prepare_failed",
                    "reason": error_detail,
                    "dry_run": dry_run
                }
            
            prepare_response = prepare_response_raw.json()
        
        if not prepare_response.get("ok"):
            reason = prepare_response.get("reason", "Unknown error")
            print(f"[ERROR] Phase A failed: {reason}")
            return {
                "ok": False,
                "draft_id": draft_id,
                "status": "prepare_failed",
                "reason": reason,
                "dry_run": dry_run
            }
        
        confirm_token = prepare_response.get("confirm_token")
        print(f"[SUCCESS] Phase A complete: confirm_token={confirm_token[:20] if confirm_token else 'N/A'}...")
        
        # PHASE B: Publish listing
        print(f"[PHASE_B] Phase B: Publishing to Vinted...")
        
        # Generate idempotency key
        import hashlib
        idempotency_key = hashlib.sha256(f"{draft_id}:{confirm_token}".encode()).hexdigest()
        
        # Build publish request payload
        publish_payload = {
            "confirm_token": confirm_token,
            "dry_run": dry_run
        }
        
        # Call publish endpoint via internal HTTP request
        async with httpx.AsyncClient(timeout=60.0) as client:  # 60s timeout for Playwright
            publish_response_raw = await client.post(
                f"http://localhost:{settings.PORT}/vinted/listings/publish",
                json=publish_payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Idempotency-Key": idempotency_key
                }
            )
            
            if publish_response_raw.status_code == 409:
                print(f"[WARNING] Duplicate publish attempt blocked (idempotency key already used)")
                raise HTTPException(
                    status_code=409,
                    detail="Cette annonce a déjà été publiée (clé d'idempotence utilisée)"
                )
            
            if publish_response_raw.status_code != 200:
                error_detail = publish_response_raw.json().get("detail", "Unknown error")
                print(f"[ERROR] Phase B failed: {error_detail}")
                return {
                    "ok": False,
                    "draft_id": draft_id,
                    "status": "publish_failed",
                    "reason": error_detail,
                    "dry_run": dry_run
                }
            
            publish_response = publish_response_raw.json()
        
        if not publish_response.get("ok"):
            reason = publish_response.get("reason", "Unknown error")
            print(f"[ERROR] Phase B failed: {reason}")
            return {
                "ok": False,
                "draft_id": draft_id,
                "status": "publish_failed",
                "reason": reason,
                "dry_run": dry_run
            }
        
        listing_url = publish_response.get("listing_url")
        vinted_id = publish_response.get("listing_id")
        print(f"[SUCCESS] Phase B complete: {listing_url}")
        
        # Update draft status in SQLite
        if not dry_run:
            get_store().update_draft_status(draft_id, "published")
            # TODO: Save vinted_id and listing_url to database
        
        # Also update in-memory if exists
        if draft_id in drafts_storage:
            draft = drafts_storage[draft_id]
            draft.status = "published"
            draft.updated_at = datetime.utcnow()
            drafts_storage[draft_id] = draft
        
        print(f"[SUCCESS] {'[DRY-RUN]' if dry_run else ''} Draft published: {draft_id} -> {listing_url}")
        
        return {
            "ok": True,
            "draft_id": draft_id,
            "status": "published",
            "listing_url": listing_url,
            "vinted_id": vinted_id,
            "dry_run": dry_run,
            "message": "Annonce publiée sur Vinted avec succès !" if not dry_run else "Simulation réussie (dry_run=true)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Publish draft error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to publish draft: {str(e)}")


@router.post("/drafts/{draft_id}/publish-direct")
async def publish_draft_direct(
    draft_id: str,
    publish_mode: str = Query(default="auto", description="'auto' = publish directly, 'draft' = save as Vinted draft"),
    current_user: User = Depends(get_current_user)
):
    """
    SPRINT 1 FEATURE: Optimized 1-Click Direct Publish to Vinted

    This is the simplified, faster endpoint for direct publication using the new
    publish_item_complete() workflow with advanced anti-detection.

    **Differences from /publish:**
    - Uses new publish_item_complete() method for full automation
    - Single-phase workflow (no separate prepare/publish steps)
    - Optimized for speed and simplicity
    - Enhanced anti-detection measures
    - Human-like typing and delays

    **Requires:** Authentication (user ownership validation) + publications quota

    **Returns:** {ok, draft_id, status, listing_url, vinted_id, vinted_draft_url}

    **publish_mode:**
    - 'auto': Direct publish to Vinted (default)
    - 'draft': Save as Vinted draft for manual review
    """
    try:
        from backend.core.vinted_client import VintedClient
        from backend.core.session import get_vinted_session

        # Get draft from SQLite (with user ownership check)
        draft_data = get_store().get_draft(draft_id)

        if not draft_data:
            print(f"[WARNING] [PUBLISH-DIRECT] Draft {draft_id} not found")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "draft_not_found",
                    "message": "Ce brouillon n'existe plus",
                    "draft_id": draft_id
                }
            )

        # CRITICAL: Verify user ownership
        if draft_data.get("user_id") and draft_data["user_id"] != str(current_user.id):
            print(f"[WARNING] [PUBLISH-DIRECT] User {current_user.id} denied access to draft {draft_id}")
            raise HTTPException(
                status_code=403,
                detail="Ce brouillon ne vous appartient pas"
            )

        # Check publications quota
        await check_and_consume_quota(current_user, "publications", amount=1)

        print(f"[PUBLISH-DIRECT] User {current_user.id} publishing draft {draft_id} (mode: {publish_mode})")

        # Extract draft fields
        item_json = draft_data.get("item_json", {})
        photos_raw = item_json.get("photos", [])

        # Resolve photo paths
        photos = []
        for photo_path in photos_raw:
            resolved = resolve_photo_path(photo_path)
            if os.path.exists(resolved):
                photos.append(resolved)
                print(f"[PHOTO] Resolved: {photo_path} -> {resolved}")
            else:
                print(f"[WARNING] Photo not found: {photo_path}")

        if not photos:
            print(f"[ERROR] No valid photos for draft {draft_id}")
            return {
                "ok": False,
                "draft_id": draft_id,
                "status": "failed",
                "reason": "Aucune photo valide trouvée"
            }

        print(f"[INFO] Found {len(photos)} valid photos")

        # Get Vinted session
        session = get_vinted_session(current_user.id)
        if not session:
            print(f"[ERROR] No Vinted session for user {current_user.id}")
            raise HTTPException(
                status_code=400,
                detail="Session Vinted non configurée. Veuillez ajouter vos cookies Vinted."
            )

        # Extract all listing data
        title = draft_data["title"]
        price = draft_data["price"]
        description = draft_data["description"]
        brand = draft_data.get("brand")
        size = draft_data.get("size")
        condition = item_json.get("condition", "Bon état")
        color = draft_data.get("color")
        category = draft_data.get("category")

        print(f"[INFO] Publishing: {title[:50]}... ({len(photos)} photos, {price}€)")

        # Initialize VintedClient with anti-detection
        async with VintedClient(headless=True) as client:
            await client.init()

            # Create context with session
            await client.create_context(session)

            # Create page
            page = await client.new_page()

            # Execute 1-click publish workflow
            print("[INFO] Starting 1-click publish workflow...")
            success, error_message, result_data = await client.publish_item_complete(
                page=page,
                title=title,
                price=price,
                description=description,
                photos=photos,
                brand=brand,
                size=size,
                condition=condition,
                color=color,
                category_hint=category,
                publish_mode=publish_mode
            )

            if not success:
                print(f"[ERROR] Publish workflow failed: {error_message}")
                return {
                    "ok": False,
                    "draft_id": draft_id,
                    "status": "failed",
                    "reason": error_message
                }

            # Update draft status in database
            if publish_mode == "draft":
                # Update with Vinted draft info
                vinted_draft_url = result_data.get("vinted_draft_url")
                vinted_draft_id = result_data.get("vinted_draft_id")
                get_store().update_draft_vinted_info(draft_id, vinted_draft_url, vinted_draft_id, publish_mode)

                print(f"[SUCCESS] Vinted draft created: {vinted_draft_url}")

                return {
                    "ok": True,
                    "draft_id": draft_id,
                    "status": "draft_created",
                    "vinted_draft_url": vinted_draft_url,
                    "vinted_draft_id": vinted_draft_id,
                    "publish_mode": "draft",
                    "message": f"Brouillon créé sur Vinted ! Validez-le manuellement : {vinted_draft_url}"
                }
            else:
                # Update with published listing info
                listing_url = result_data.get("listing_url")
                listing_id = result_data.get("listing_id")
                get_store().update_draft_status(draft_id, "published")

                print(f"[SUCCESS] Published to Vinted: {listing_url}")

                return {
                    "ok": True,
                    "draft_id": draft_id,
                    "status": "published",
                    "listing_url": listing_url,
                    "vinted_id": listing_id,
                    "publish_mode": "auto",
                    "message": "Annonce publiée sur Vinted avec succès ! 🎉"
                }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Direct publish error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la publication: {str(e)}")


@router.post("/photos/analyze")
async def analyze_bulk_photos(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    ANALYZE PHOTOS WITH REAL AI (Frontend-compatible endpoint)

    Uploads photos and launches REAL AI analysis in background.
    This endpoint is called by the Lovable frontend.

    **Requires:** Authentication + AI analyses quota

    **Returns:** {job_id, status, total_photos, estimated_items, plan_id}
    **Status:** "processing" (use GET /bulk/jobs/{job_id} to poll progress)
    """
    import traceback
    import sys

    print("=" * 80)
    print(f"[ENDPOINT] analyze_bulk_photos REACHED")
    print(f"User ID: {current_user.id if current_user else 'NONE'}")
    print(f"Email: {current_user.email if current_user else 'NONE'}")
    print("=" * 80)
    sys.stdout.flush()

    try:
        # Parse multipart form data manually to handle any field names
        form = await request.form()
        
        # Extract files (could be "files", "file", "photos", or any other field name)
        files = []
        auto_grouping = True  # default
        
        for field_name, field_value in form.items():
            if hasattr(field_value, 'file'):  # It's an uploaded file
                files.append(field_value)
            elif field_name == "auto_grouping":
                auto_grouping = str(field_value).lower() == "true"
        
        print(f"[REQUEST] Received analyze request: files={len(files)}, auto_grouping={auto_grouping}, user={current_user.id}")
        
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
        
        # Check AI quota before processing
        await check_and_consume_quota(current_user, "ai_analyses", amount=1)

        # Check storage quota
        total_size_mb = sum([f.size or 0 for f in files]) / (1024 * 1024)
        await check_storage_quota(current_user, total_size_mb)
        
        # Save photos temporarily and create job ID
        job_id = str(uuid.uuid4())[:8]
        photo_paths = save_uploaded_photos(files, job_id)
        
        # Smart estimation: ~5-6 photos per item on average
        estimated_items = max(1, photo_count // 5)
        
        # Initialize job status in memory
        bulk_jobs[job_id] = {
            "job_id": job_id,
            "status": "processing",
            "total_photos": photo_count,
            "processed_photos": 0,
            "total_items": estimated_items,
            "completed_items": 0,
            "failed_items": 0,
            "drafts": [],
            "errors": [],
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "progress_percent": 0.0
        }
        
        # ALWAYS use GPT-4 Vision for grouping (never trust aspect ratio)
        # Previous logic grouped by aspect ratio which mixed jogging/hoodie photos
        use_smart_grouping = True  # Force AI Vision grouping regardless of photo count
        
        # Launch AI analysis in background
        asyncio.create_task(
            process_bulk_job(
                job_id=job_id,
                photo_paths=photo_paths,
                photos_per_item=7,  # Default 7 photos per item
                use_smart_grouping=use_smart_grouping,
                style="classique",
                user_id=str(current_user.id)  # CRITICAL: Pass user_id for duplicate detection
            )
        )
        
        # Save initial plan to database for persistence
        save_photo_plan(
            plan_id=job_id,
            photo_paths=photo_paths,
            photo_count=photo_count,
            auto_grouping=auto_grouping,
            estimated_items=estimated_items
        )
        
        print(f"[JOB] Launched AI analysis job {job_id}: {photo_count} photos, estimated {estimated_items} items")
        
        return {
            "job_id": job_id,
            "plan_id": job_id,
            "status": "processing",  # Changed from "completed" to "processing"
            "total_photos": photo_count,
            "estimated_items": estimated_items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print("=" * 80)
        print(f"[ERROR] ANALYZE PHOTOS ERROR: {type(e).__name__}: {e}")
        print("=" * 80)
        import traceback
        import sys
        error_details = traceback.format_exc()
        print(error_details)
        sys.stdout.flush()

        # Also write to a dedicated error log file
        try:
            with open("backend/data/analyze_error.log", "a", encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Timestamp: {datetime.utcnow().isoformat()}\n")
                f.write(f"User: {current_user.id if current_user else 'NONE'}\n")
                f.write(f"Error: {type(e).__name__}: {e}\n")
                f.write(f"Traceback:\n{error_details}\n")
                f.write(f"{'='*80}\n")
        except:
            pass

        raise HTTPException(status_code=500, detail=f"Failed to analyze photos: {str(e)}")


@router.post("/plan", response_model=GroupingPlan)
async def create_grouping_plan(
    files: List[UploadFile] = File(...),
    auto_grouping: bool = Query(default=True, description="Enable auto single-item detection"),
    style: str = Query(default="classique", description="Description style"),
    current_user: User = Depends(get_current_user)
):
    """
    CREATE GROUPING PLAN (Anti-Saucisson)
    
    Analyzes photos and creates an intelligent grouping plan WITHOUT generating drafts yet.
    
    **Auto-grouping rules:**
    - If auto_grouping=true OR photos ≤ SINGLE_ITEM_DEFAULT_MAX_PHOTOS (80) -> Single item mode
    - Detects labels (care labels, brand tags, size labels) via AI Vision
    - Clusters ≤2 photos or label-only -> auto-attach to largest cluster
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
            print(f"[AI] Running AI Vision grouping for {photo_count} photos...")
            
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
        
        print(f"[PLAN] Created grouping plan {plan_id}: {photo_count} photos -> {estimated_items} items ({grouping_reason})")
        
        return plan
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Create plan error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create plan: {str(e)}")


@router.post("/generate", response_model=GenerateResponse)
async def generate_drafts_from_plan(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    [QUALITY] GENERATE DRAFTS WITH STRICT VALIDATION (Zero Failed Drafts)
    
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
    
    **Requires:** Authentication + drafts quota
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
        
        # Check drafts quota before creating (estimate based on grouped items)
        estimated_drafts = len(grouped_items)
        await check_and_consume_quota(current_user, "drafts", amount=estimated_drafts)
        
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
                
                # If validation fails for this item -> Skip it
                if validation_errors:
                    error_msg = f"Item {item_index} ({title[:30]}...): {'; '.join(validation_errors)}"
                    errors.append(error_msg)
                    skipped_items.append(item)
                    print(f"[WARNING] Skipped item {item_index}: {error_msg}")
                    continue
                
                # All validations passed -> Create draft for this item
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
                
                # Save draft to SQLite storage (may return merged draft with different ID!)
                saved_draft = get_store().save_draft(
                    draft_id=draft_id,
                    title=title,
                    description=description,
                    price=float(item.get("price", 0)),
                    brand=item.get("brand"),
                    size=item.get("size"),
                    color=item.get("color"),
                    category=item.get("category"),
                    item_json=item,
                    listing_json=None,
                    flags_json={
                        "publish_ready": True,
                        "ai_validated": True,
                        "photos_validated": True
                    },
                    user_id=str(current_user.id),  # CRITICAL: Pass user_id for duplicate detection
                    status="ready"
                )
                
                # CRITICAL: Use the REAL ID returned (may differ if merged!)
                real_draft_id = saved_draft.get("id", draft_id)
                
                # Update draft object with real ID
                draft.id = real_draft_id
                
                # Also keep in-memory for backward compatibility (with REAL ID!)
                drafts_storage[real_draft_id] = draft
                created_drafts.append(draft)
                
                print(f"[OK] Draft {item_index}/{len(grouped_items)}: {draft.title} ({len(item.get('photos', []))} photos, {hashtag_count} hashtags)")
                
            except Exception as e:
                error_msg = f"Item {item_index} error: {str(e)}"
                errors.append(error_msg)
                print(f"[ERROR] {error_msg}")
        
        # Return response with all created drafts
        success_count = len(created_drafts)
        skip_count = len(skipped_items)
        detected_count = len(grouped_items)
        
        # Update photo plan with REAL results (if plan_id exists)
        if plan_id:
            draft_ids_list = [d.id for d in created_drafts]
            update_photo_plan_results(plan_id, detected_count, draft_ids_list)
            print(f"[UPDATE] Updated plan {plan_id}: {detected_count} detected items, {success_count} valid drafts")
        
        if success_count == 0:
            return GenerateResponse(
                ok=False,
                generated_count=0,
                skipped_count=skip_count,
                drafts=[],
                errors=errors,
                message=f"[ERROR] No valid drafts created. {skip_count} items skipped. Errors: {'; '.join(errors[:3])}"
            )
        
        return GenerateResponse(
            ok=True,
            generated_count=success_count,
            skipped_count=skip_count,
            drafts=created_drafts,
            errors=errors,
            message=f"[OK] Created {success_count} draft(s) from {detected_count} detected items ({skip_count} skipped)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Generate drafts error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")



# ==================== EXPORT/IMPORT ENDPOINTS ====================

@router.get("/export/drafts")
async def export_drafts(
    status: Optional[str] = Query(None, description="Filter by status: ready, pending, all")
):
    """
    Export drafts as ZIP archive (SQLite-based, zero cost)
    
    Returns:
    - drafts.json: Minimal draft data (title, price, brand, size, etc.)
    - readme.txt: Instructions for reimporting
    
    **Status filters:**
    - ready: Only drafts ready to publish
    - pending: Drafts needing review
    - all: Everything
    """
    try:
        # Get drafts from SQLite
        if status == "all":
            drafts_raw = get_store().get_drafts(status=None, limit=10000)
        else:
            drafts_raw = get_store().get_drafts(status=status or "ready", limit=10000)
        
        # Convert to minimal format (exclude heavy fields like photos)
        drafts_export = []
        for draft in drafts_raw:
            drafts_export.append({
                "id": draft["id"],
                "title": draft["title"],
                "description": draft["description"],
                "price": draft["price"],
                "brand": draft["brand"],
                "size": draft["size"],
                "color": draft["color"],
                "category": draft["category"],
                "status": draft["status"],
                "created_at": draft["created_at"]
            })
        
        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add drafts.json
            drafts_json = json.dumps(drafts_export, indent=2, ensure_ascii=False)
            zip_file.writestr("drafts.json", drafts_json)
            
            # Add readme.txt
            readme = f"""VintedBot Drafts Export
========================

Exported on: {datetime.utcnow().isoformat()}
Total drafts: {len(drafts_export)}
Status filter: {status or 'ready'}

HOW TO IMPORT:
1. POST this ZIP to /import/drafts
2. Or extract drafts.json and POST the JSON directly

Note: Photos are NOT included (reference only).
This is a metadata-only backup for quick restoration.
"""
            zip_file.writestr("readme.txt", readme)
        
        zip_buffer.seek(0)
        
        filename = f"vintedbot_drafts_{status or 'ready'}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.getvalue()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"[ERROR] Export error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/import/drafts")
async def import_drafts(
    file: UploadFile = File(..., description="ZIP archive or JSON file with drafts"),
    current_user: User = Depends(get_current_user)
):
    """
    Import drafts from ZIP or JSON (SQLite-based, zero cost)
    
    Accepts:
    - ZIP archive (from /export/drafts)
    - JSON file with draft array
    
    Creates new drafts WITHOUT changing existing ones.
    """
    try:
        content = await file.read()
        filename = file.filename or ""
        
        drafts_data = []
        
        # Parse ZIP or JSON
        if filename.endswith(".zip"):
            # Extract JSON from ZIP
            with zipfile.ZipFile(io.BytesIO(content)) as zip_file:
                if "drafts.json" not in zip_file.namelist():
                    raise HTTPException(status_code=400, detail="ZIP must contain drafts.json")
                
                json_content = zip_file.read("drafts.json").decode("utf-8")
                drafts_data = json.loads(json_content)
        
        elif filename.endswith(".json"):
            # Direct JSON import
            drafts_data = json.loads(content.decode("utf-8"))
        
        else:
            raise HTTPException(status_code=400, detail="File must be .zip or .json")
        
        # Import drafts
        imported_count = 0
        skipped_count = 0
        
        for draft in drafts_data:
            try:
                # Generate new ID to avoid conflicts
                draft_id = str(uuid.uuid4())
                
                # Create draft in SQLite
                get_store().save_draft(
                    draft_id=draft_id,
                    title=draft["title"],
                    description=draft.get("description", ""),
                    price=float(draft["price"]),
                    brand=draft.get("brand"),
                    size=draft.get("size"),
                    color=draft.get("color"),
                    category=draft.get("category"),
                    status="pending",  # Force pending for review
                    user_id=str(current_user.id)  # CRITICAL: Pass user_id for duplicate detection
                )
                
                imported_count += 1
                
            except Exception as e:
                print(f"[WARN] Skipped draft {draft.get('id')}: {e}")
                skipped_count += 1
        
        return JSONResponse({
            "ok": True,
            "imported": imported_count,
            "skipped": skipped_count,
            "message": f"[OK] Imported {imported_count} drafts ({skipped_count} skipped)"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Import error: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# ==================== AI ANALYTICS ENDPOINTS ====================

@router.get("/analytics/ai-performance")
async def get_ai_performance_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    Get AI performance analytics

    Returns:
        - Cache hit rate (cost savings)
        - Quality validation metrics
        - Confidence score distribution
        - Fallback usage rate
    """
    try:
        from backend.services.redis_cache import get_cache_stats, get_quality_metrics

        cache_stats = get_cache_stats()
        quality_metrics = get_quality_metrics()

        # Calculate cost savings estimate
        cache_hit_rate = cache_stats.get("hit_rate", 0)
        total_analyses = quality_metrics.get("total", 0)

        # Assuming $0.05 per analysis average (6 photos * ~3 tiles each * $0.01275/tile)
        COST_PER_ANALYSIS = 0.05
        estimated_cost_saved = (cache_stats.get("hits", 0) * COST_PER_ANALYSIS)
        estimated_total_cost = (total_analyses * COST_PER_ANALYSIS)
        actual_cost = estimated_total_cost - estimated_cost_saved

        return {
            "cache": {
                "hits": cache_stats.get("hits", 0),
                "misses": cache_stats.get("misses", 0),
                "saves": cache_stats.get("saves", 0),
                "hit_rate": cache_hit_rate,
                "cost_saved": round(estimated_cost_saved, 2),
                "actual_cost": round(actual_cost, 2),
                "total_cost_without_cache": round(estimated_total_cost, 2)
            },
            "quality": {
                "total_analyses": total_analyses,
                "passed": quality_metrics.get("passed", 0),
                "failed": quality_metrics.get("failed", 0),
                "pass_rate": quality_metrics.get("pass_rate", 0),
                "confidence_distribution": {
                    "high": quality_metrics.get("confidence_high", 0),
                    "medium": quality_metrics.get("confidence_medium", 0),
                    "low": quality_metrics.get("confidence_low", 0)
                },
                "fallback_used": quality_metrics.get("fallback_used", 0),
                "fallback_rate": round(
                    (quality_metrics.get("fallback_used", 0) / total_analyses * 100) if total_analyses > 0 else 0,
                    2
                )
            }
        }

    except ImportError:
        # Redis not available
        return {
            "cache": {
                "hits": 0,
                "misses": 0,
                "saves": 0,
                "hit_rate": 0,
                "cost_saved": 0,
                "actual_cost": 0,
                "total_cost_without_cache": 0,
                "note": "Redis cache not available"
            },
            "quality": {
                "total_analyses": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0,
                "confidence_distribution": {
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "fallback_used": 0,
                "fallback_rate": 0,
                "note": "Metrics tracking not available"
            }
        }
    except Exception as e:
        print(f"[ERROR] Analytics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@router.post("/analytics/cache/clear")
async def clear_ai_cache(
    pattern: str = Query("ai_analysis:*", description="Redis key pattern to clear"),
    current_user: User = Depends(get_current_user)
):
    """
    Clear AI analysis cache (admin tool for testing/debugging)

    Use cases:
    - Clear all cache: pattern="ai_analysis:*"
    - Clear specific cache: pattern="ai_analysis:abc123..."
    """
    try:
        from backend.services.redis_cache import clear_cache

        deleted_count = clear_cache(pattern)

        return {
            "ok": True,
            "deleted": deleted_count,
            "message": f"Cleared {deleted_count} cached entries"
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="Redis cache not available")
    except Exception as e:
        print(f"[ERROR] Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.post("/analytics/image/estimate-cost")
async def estimate_image_processing_cost(
    files: List[UploadFile] = File(..., description="Images to estimate cost for"),
    current_user: User = Depends(get_current_user)
):
    """
    Estimate OpenAI Vision API cost for image processing
    Shows cost before/after optimization

    Useful for:
    - Cost planning before bulk upload
    - Understanding optimization savings
    """
    try:
        from backend.services.image_optimizer import estimate_api_cost

        # Save uploaded files temporarily
        temp_paths = []
        for file in files:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            temp_paths.append(temp_file.name)

        # Estimate costs
        cost_estimate = estimate_api_cost(temp_paths)

        # Cleanup temp files
        for path in temp_paths:
            try:
                os.unlink(path)
            except:
                pass

        return {
            "ok": True,
            "images_count": cost_estimate["images_count"],
            "cost_before_optimization": f"${cost_estimate['cost_before']}",
            "cost_after_optimization": f"${cost_estimate['cost_after']}",
            "savings": f"${cost_estimate['savings']}",
            "savings_percent": f"{cost_estimate['savings_percent']}%",
            "recommendation": "[OK] Image optimization saves ~75% API costs" if cost_estimate['savings_percent'] > 50 else "[INFO] Minimal savings expected"
        }

    except ImportError:
        raise HTTPException(status_code=503, detail="Image optimizer not available")
    except Exception as e:
        print(f"[ERROR] Cost estimation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to estimate cost: {str(e)}")

