"""
Vinted automation API endpoints
Handles session management, photo uploads, and listing creation/publication
"""
import asyncio
import secrets
import io
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Header, Depends, Body
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from PIL import Image
from pillow_heif import register_heif_opener

# Register HEIF/HEIC support in PIL
register_heif_opener()

from backend.settings import settings
from backend.core.session import SessionVault, VintedSession
from backend.core.vinted_client import VintedClient, CaptchaDetected
from backend.core.storage import get_store
from backend.core.auth import get_current_user, User
from backend.middleware.quota_checker import check_and_consume_quota
from backend.schemas.vinted import (
    SessionRequest,
    SessionResponse,
    AuthCheckResponse,
    PhotoUploadResponse,
    ListingPrepareRequest,
    ListingPrepareResponse,
    ListingPublishRequest,
    ListingPublishResponse
)

router = APIRouter(prefix="/vinted", tags=["vinted"])
limiter = Limiter(key_func=get_remote_address)

# Token serializer for confirm_token
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

# Session vault singleton
vault = SessionVault(
    key=settings.SECRET_KEY,
    storage_path=settings.SESSION_STORE_PATH
)


def extract_username_from_cookie(cookie: str) -> Optional[str]:
    """
    Extract username from Vinted cookies
    Looks for common patterns in cookie values
    """
    try:
        # Try to find _vinted_fr_session or similar session cookies
        # These often contain user info
        if "_vinted_" in cookie:
            # Session cookies exist, user is likely authenticated
            # For now, return a placeholder that indicates auth is valid
            # Real parsing would need to decode the session cookie
            return "vinted_user"
        return None
    except:
        return None


@router.post("/auth/session", response_model=SessionResponse)
async def save_session(request: SessionRequest):
    """
    Save Vinted authentication session (cookie + user-agent)
    
    Security: Cookie is encrypted with Fernet before storage
    """
    try:
        print(f"📥 Received session request: cookie_length={len(request.cookie)}, ua_length={len(request.user_agent)}")
        
        # Extract username from cookies (simple detection)
        username = extract_username_from_cookie(request.cookie)
        
        # Create session object
        session = VintedSession(
            cookie=request.cookie,
            user_agent=request.user_agent,
            username=username,
            user_id=username,
            expires_at=request.expires_at or datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow()
        )
        
        # Save encrypted session
        persisted = vault.save_session(session)
        
        print(f"✅ Session saved (encrypted): user={username or 'unknown'}")
        
        # Return EXACT format Lovable expects: {session_id, valid, created_at}
        return SessionResponse(
            session_id=1,  # Static ID for now (could be random or from DB)
            valid=True,
            created_at=datetime.utcnow().isoformat() + "Z",
            note=f"Session saved for user: {username or 'unknown'}"
        )
    except Exception as e:
        print(f"❌ Save session error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save session: {str(e)}")


@router.post("/auth/session/debug")
async def debug_session(payload: Dict[str, Any]):
    """
    Debug endpoint - accepts any JSON to see what Lovable sends
    """
    print(f"🔍 DEBUG - Received payload: {payload}")
    print(f"🔍 DEBUG - Payload keys: {list(payload.keys())}")
    print(f"🔍 DEBUG - Payload types: {[(k, type(v).__name__) for k, v in payload.items()]}")
    
    # Try to save it anyway
    try:
        # Extract cookie and user_agent if they exist
        cookie = payload.get('cookie') or payload.get('cookies') or payload.get('session_cookie')
        user_agent = payload.get('user_agent') or payload.get('userAgent') or payload.get('ua')
        
        if cookie and user_agent:
            session = VintedSession(
                cookie=cookie,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(days=30),
                created_at=datetime.utcnow()
            )
            persisted = vault.save_session(session)
            return {"ok": True, "persisted": persisted, "debug": "Found cookie and user_agent"}
        else:
            return {"ok": False, "error": "Missing cookie or user_agent", "received": payload}
    except Exception as e:
        return {"ok": False, "error": str(e), "received": payload}


@router.post("/auth/validate")
async def validate_session(request: SessionRequest):
    """
    Alternative endpoint that saves AND validates in one go
    Returns comprehensive validation result
    """
    try:
        print(f"📥 VALIDATE - cookie_length={len(request.cookie)}")
        
        # Extract username
        username = extract_username_from_cookie(request.cookie)
        
        # Create and save session
        session = VintedSession(
            cookie=request.cookie,
            user_agent=request.user_agent,
            username=username,
            user_id=username,
            expires_at=request.expires_at or datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow()
        )
        
        persisted = vault.save_session(session)
        
        # Return validation-focused response
        return {
            "valid": True,
            "authenticated": True,
            "saved": persisted,
            "username": username,
            "user_id": username,
            "session": {
                "cookie_length": len(request.cookie),
                "has_vinted_session": "_vinted_" in request.cookie,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None
            }
        }
    except Exception as e:
        print(f"❌ VALIDATE error: {e}")
        return {
            "valid": False,
            "authenticated": False,
            "error": str(e)
        }


@router.get("/auth/check", response_model=AuthCheckResponse)
async def check_auth():
    """
    Check if valid Vinted session exists
    """
    try:
        session = vault.load_session()
        
        if not session:
            return AuthCheckResponse(
                authenticated=False,
                username=None,
                user_id=None
            )
        
        return AuthCheckResponse(
            authenticated=True,
            username=session.username,
            user_id=session.user_id
        )
    except Exception as e:
        print(f"❌ Check auth error: {e}")
        return AuthCheckResponse(
            authenticated=False,
            username=None,
            user_id=None
        )


@router.post("/photos/upload")
@limiter.limit("10/minute")
async def upload_photos(
    files: list[UploadFile] = File(...),
    auto_analyze: bool = True,
    request: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple photos for Vinted listing (mobile-friendly)
    
    **Requires:** Authentication + storage quota (+ AI quota if auto_analyze=true)
    
    Accepts: 1-20 images (JPG, PNG, WEBP, HEIC, HEIF)
    Max size: 15MB per photo
    Rate limited to 10/minute
    
    HEIC/HEIF photos are automatically converted to JPG
    
    NEW: auto_analyze=true triggers AI analysis and draft creation
    
    Returns: 
    - If auto_analyze=false: {"photos": [{"temp_id", "url", "filename"}, ...]}
    - If auto_analyze=true: {"job_id": "...", "photos": [...], "message": "..."}
    """
    try:
        if len(files) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 photos allowed")
        
        # Check AI quota if auto-analysis enabled
        if auto_analyze:
            await check_and_consume_quota(current_user, "ai_analyses", amount=1)
        
        photos = []
        photo_paths = []
        
        # Generate job_id for this upload batch
        job_id = secrets.token_urlsafe(8)
        temp_dir = f"{settings.DATA_DIR}/temp_photos/{job_id}"
        import os
        os.makedirs(temp_dir, exist_ok=True)
        
        for i, file in enumerate(files):
            # Validate file type (accept HEIC/HEIF)
            filename_lower = (file.filename or "").lower()
            is_heic = filename_lower.endswith(('.heic', '.heif'))
            
            if not is_heic and (not file.content_type or not file.content_type.startswith('image/')):
                raise HTTPException(status_code=415, detail=f"Only image files allowed: {file.filename}")
            
            # Read file content
            content = await file.read()
            
            # Check file size (15MB max)
            if len(content) > 15 * 1024 * 1024:
                raise HTTPException(status_code=413, detail=f"File too large (max 15MB): {file.filename}")
            
            # Generate temp_id
            temp_id = f"photo_{i:03d}"
            
            # Convert HEIC/HEIF to JPG
            if is_heic:
                print(f"🔄 Converting HEIC/HEIF to JPG: {file.filename}")
                try:
                    # Open HEIC with PIL (pillow-heif registered)
                    image = Image.open(io.BytesIO(content))
                    
                    # Convert to RGB (remove alpha channel if present)
                    if image.mode in ('RGBA', 'LA', 'P'):
                        image = image.convert('RGB')
                    
                    # Save as JPEG
                    output = io.BytesIO()
                    image.save(output, format='JPEG', quality=85)
                    content = output.getvalue()
                    
                    ext = 'jpg'
                    print(f"✅ Converted HEIC → JPG: {file.filename}")
                except Exception as e:
                    print(f"❌ HEIC conversion failed: {e}")
                    raise HTTPException(status_code=400, detail=f"Failed to convert HEIC: {file.filename}")
            else:
                ext = file.filename.split('.')[-1] if (file.filename and '.' in file.filename) else 'jpg'
            
            filename = f"{temp_id}.{ext}"
            file_path = f"{temp_dir}/{filename}"
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            print(f"✅ Photo uploaded: {file.filename} -> {filename}")
            
            photo_paths.append(file_path)
            photos.append({
                "temp_id": temp_id,
                "url": f"/temp_photos/{job_id}/{filename}",
                "filename": file.filename
            })
        
        # If auto_analyze enabled, trigger AI analysis
        if auto_analyze:
            from backend.api.v1.routers.bulk import process_bulk_job, bulk_jobs
            
            # Initialize job
            bulk_jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "total_photos": len(photo_paths),
                "processed_photos": len(photo_paths),
                "total_items": max(1, len(photo_paths) // 4),
                "completed_items": 0,
                "failed_items": 0,
                "drafts": [],
                "errors": [],
                "started_at": None,
                "completed_at": None,
                "progress_percent": 0.0
            }
            
            # Start analysis in background
            asyncio.create_task(process_bulk_job(job_id, photo_paths, photos_per_item=4))
            
            print(f"🚀 AI analysis started: job_id={job_id}")
            
            return {
                "job_id": job_id,
                "photos": photos,
                "message": f"Analyzing {len(photos)} photos... Check /bulk/jobs/{job_id} for status"
            }
        
        # Return standard format if auto_analyze disabled
        return {"photos": photos}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/listings/prepare", response_model=ListingPrepareResponse)
async def prepare_listing(
    request: ListingPrepareRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Prepare a Vinted listing (Phase A - Draft)
    
    **Requires:** Authentication (user ownership validation)
    
    - Opens /items/new
    - Uploads photos
    - Fills form fields
    - Stops before publish
    - Returns confirm_token for phase B
    
    Default: dry_run=true (simulation only)
    """
    try:
        print(f"\n{'='*60}")
        print(f"🚀 DÉBUT PUBLICATION - PHASE A (PREPARE)")
        print(f"{'='*60}")
        print(f"📋 Title: {request.title[:50]}...")
        print(f"💰 Price: {request.price}€")
        print(f"📸 Photos: {len(request.photos)} fichiers")
        print(f"🏷️  Category: {request.category_hint}")
        print(f"👕 Size: {request.size}")
        print(f"✨ Condition: {request.condition}")
        print(f"🎨 Brand: {request.brand}")
        
        # In dry_run mode, skip session check (simulation only)
        if not request.dry_run and not settings.MOCK_MODE:
            # Check authentication (ONLY for real execution)
            session = vault.load_session()
            if not session:
                print(f"❌ ERREUR: Aucune session Vinted trouvée")
                print(f"   → Va dans Settings pour coller ton cookie Vinted")
                raise HTTPException(status_code=401, detail="Not authenticated. Call /auth/session first.")
            
            print(f"✅ Session Vinted active: user={session.username or 'unknown'}")
        else:
            print(f"🧪 [DRY-RUN MODE] Skipping Vinted session check")
            session = None  # Not needed for dry-run
        
        # 🛡️ PUBLICATION SAFEGUARDS - Validate AI payload
        print(f"\n🔍 VALIDATION DES CHAMPS:")
        if settings.SAFE_DEFAULTS:
            validation_errors = []
            
            # 1. Title length check (≤70 chars for optimal visibility)
            if len(request.title) > 70:
                validation_errors.append(f"Title too long ({len(request.title)} chars, max 70)")
                print(f"   ❌ Titre trop long: {len(request.title)} chars (max 70)")
            else:
                print(f"   ✅ Titre: {len(request.title)} chars")
            
            # 2. Hashtags validation (3-5 required)
            if not request.hashtags or len(request.hashtags) < 3 or len(request.hashtags) > 5:
                hashtag_count = len(request.hashtags) if request.hashtags else 0
                validation_errors.append(f"Invalid hashtags count ({hashtag_count}, need 3-5)")
                print(f"   ❌ Hashtags invalides: {hashtag_count} (besoin 3-5)")
            else:
                print(f"   ✅ Hashtags: {len(request.hashtags)} tags")
            
            # 3. Price suggestion validation (min/target/max required)
            if not request.price_suggestion:
                validation_errors.append("Missing price_suggestion (min/target/max)")
                print(f"   ❌ Prix suggestion manquant")
            elif not all([
                hasattr(request.price_suggestion, 'min'),
                hasattr(request.price_suggestion, 'target'),
                hasattr(request.price_suggestion, 'max')
            ]):
                validation_errors.append("Incomplete price_suggestion (need min/target/max)")
                print(f"   ❌ Prix suggestion incomplet")
            else:
                print(f"   ✅ Prix: {request.price_suggestion.min}€ - {request.price_suggestion.target}€ - {request.price_suggestion.max}€")
            
            # 4. Publish readiness flag
            if not request.flags or not request.flags.publish_ready:
                validation_errors.append("Not ready for publication (flags.publish_ready != true)")
                print(f"   ❌ Pas prêt pour publication (publish_ready=false)")
            else:
                print(f"   ✅ Prêt pour publication")
            
            # If any validation fails, return NOT_READY
            if validation_errors:
                print(f"\n🚫 PUBLICATION BLOQUÉE:")
                for error in validation_errors:
                    print(f"   - {error}")
                return ListingPrepareResponse(
                    ok=False,
                    dry_run=True,
                    reason=f"NOT_READY: {'; '.join(validation_errors)}"
                )
        
        print(f"\n✅ TOUTES LES VALIDATIONS PASSÉES")
        
        # Dry run simulation
        if request.dry_run or settings.MOCK_MODE:
            print(f"🔄 [DRY-RUN] Preparing listing: {request.title}")
            
            # Generate confirm token (TTL: 30 minutes)
            draft_context = {
                "title": request.title,
                "price": request.price,
                "description": request.description,
                "brand": request.brand,
                "size": request.size,
                "condition": request.condition,
                "color": request.color,
                "category_hint": request.category_hint,
                "photos": request.photos,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            confirm_token = serializer.dumps(draft_context)
            
            return ListingPrepareResponse(
                ok=True,
                dry_run=True,
                confirm_token=confirm_token,
                preview_url="https://www.vinted.fr/items/new",
                screenshot_b64=None,  # Not captured in dry-run
                draft_context=draft_context
            )
        
        # Real execution
        print(f"🚀 [REAL] Preparing listing: {request.title}")
        
        # session is guaranteed to exist here (checked above)
        if not session:
            raise HTTPException(status_code=500, detail="Internal error: session not found")
        
        async with VintedClient(headless=settings.PLAYWRIGHT_HEADLESS) as client:
            # Create context with session
            await client.create_context(session)
            page = await client.new_page()
            
            # Navigate to new item page
            await page.goto("https://www.vinted.fr/items/new", wait_until="networkidle")
            
            # Check for challenges
            if await client.detect_challenge(page):
                raise HTTPException(
                    status_code=403,
                    detail="Verification/Captcha detected. Please complete manually."
                )
            
            # Upload photos
            if request.photos:
                from pathlib import Path
                import os
                
                for idx, photo_ref in enumerate(request.photos):
                    # ✅ SMART PATH RESOLUTION - handles all formats
                    # Case 1: Absolute path (starts with /)
                    if photo_ref.startswith('/'):
                        photo_path = f"{settings.DATA_DIR}{photo_ref}"
                    # Case 2: Already has DATA_DIR prefix
                    elif photo_ref.startswith(f'{settings.DATA_DIR}/'):
                        photo_path = photo_ref
                    # Case 3: Relative path with temp_photos
                    elif photo_ref.startswith('temp_photos/'):
                        photo_path = f"{settings.DATA_DIR}/{photo_ref}"
                    # Case 4: Legacy backend/data paths
                    elif photo_ref.startswith('backend/data/'):
                        photo_path = photo_ref.replace('backend/data/', f'{settings.DATA_DIR}/')
                    # Case 5: Just filename (legacy)
                    else:
                        photo_path = f"{settings.DATA_DIR}/temp_photos/{photo_ref}"
                    
                    # Verify file exists before upload
                    if not os.path.exists(photo_path):
                        print(f"❌ Photo [{idx}] NOT FOUND: {photo_ref}")
                        print(f"   Resolved path: {photo_path}")
                        print(f"   File exists: {os.path.exists(photo_path)}")
                        raise HTTPException(
                            status_code=404,
                            detail=f"Photo not found: {photo_ref} (resolved to {photo_path})"
                        )
                    
                    print(f"📸 Uploading photo [{idx+1}/{len(request.photos)}]: {os.path.basename(photo_path)}")
                    upload_success = await client.upload_photo(page, photo_path)
                    
                    if not upload_success:
                        # Check if we were redirected to login/session page
                        current_url = page.url
                        if 'session-refresh' in current_url or 'session/new' in current_url or 'member/login' in current_url:
                            print(f"❌ Session Vinted expirée (redirigé vers {current_url})")
                            raise HTTPException(
                                status_code=401,
                                detail=f"SESSION_EXPIRED: Votre session Vinted a expiré. Veuillez actualiser votre cookie dans Settings. Testez votre session avec le bouton 'Tester ma session'."
                            )
                        
                        print(f"⚠️ Photo upload failed: {photo_ref}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to upload photo: {photo_ref}. Vérifiez votre connexion ou testez votre session Vinted."
                        )
            
            # Fill form
            fill_result = await client.fill_listing_form(
                page=page,
                title=request.title,
                price=request.price,
                description=request.description,
                brand=request.brand,
                size=request.size,
                condition=request.condition,
                color=request.color,
                category_hint=request.category_hint
            )
            
            # Take screenshot
            screenshot_b64 = await client.take_screenshot(page)
            
            # Generate confirm token
            draft_context = {
                "title": request.title,
                "price": request.price,
                "filled_fields": fill_result['filled'],
                "errors": fill_result['errors'],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            confirm_token = serializer.dumps(draft_context)
            
            print(f"✅ Listing prepared: {request.title}")
            
            return ListingPrepareResponse(
                ok=True,
                dry_run=False,
                confirm_token=confirm_token,
                preview_url=page.url,
                screenshot_b64=screenshot_b64,
                draft_context=draft_context
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Prepare error: {e}")
        raise HTTPException(status_code=500, detail=f"Prepare failed: {str(e)}")


@router.post("/listings/publish", response_model=ListingPublishResponse)
@limiter.limit("5/minute")
async def publish_listing(
    request: ListingPublishRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user)
):
    """
    Publish a prepared listing (Phase B - Publish)
    
    - Verifies confirm_token (TTL check)
    - Clicks "Publier" button
    - Detects captcha/challenges
    - Returns listing_id and URL on success
    
    Default: dry_run=true (safe mode)
    Rate limited: 5/minute
    
    **Requires:** Authentication + publications quota
    
    **Required Header:** Idempotency-Key (prevents duplicate publications)
    """
    try:
        # Check publications quota before publishing
        if not request.dry_run:
            await check_and_consume_quota(current_user, "publications", amount=1)
        
        # 🛡️ Idempotency protection - ATOMIC reservation before publish
        # This MUST happen before the external Vinted API call to prevent race conditions
        if not request.dry_run:
            # Try to reserve the idempotency key atomically (UNIQUE constraint)
            # If another concurrent request has the same key, this will raise IntegrityError
            try:
                import uuid as uuid_lib
                log_id = str(uuid_lib.uuid4())
                get_store().reserve_publish_key(
                    log_id=log_id,
                    idempotency_key=idempotency_key,
                    confirm_token=request.confirm_token
                )
            except Exception as e:
                # UNIQUE constraint violation = duplicate request
                if "UNIQUE constraint" in str(e) or "IntegrityError" in str(e):
                    raise HTTPException(
                        status_code=409,
                        detail="Idempotency key already used - duplicate publish attempt blocked"
                    )
                raise  # Other errors bubble up
        
        # Verify token (30 min TTL)
        try:
            draft_context = serializer.loads(request.confirm_token, max_age=1800)
        except SignatureExpired:
            raise HTTPException(status_code=410, detail="Confirm token expired (30 min limit)")
        except BadSignature:
            raise HTTPException(status_code=400, detail="Invalid confirm token")
        
        # Check authentication
        session = vault.load_session()
        if not session:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Dry run simulation
        if request.dry_run or settings.MOCK_MODE:
            print(f"🔄 [DRY-RUN] Publishing: {draft_context.get('title', 'unknown')}")
            
            return ListingPublishResponse(
                ok=True,
                dry_run=True,
                listing_id=None,
                listing_url=None,
                needs_manual=None,
                reason=None
            )
        
        # Real execution
        print(f"🚀 [REAL] Publishing: {draft_context.get('title', 'unknown')}")
        
        async with VintedClient(headless=settings.PLAYWRIGHT_HEADLESS) as client:
            await client.create_context(session)
            page = await client.new_page()
            
            # Navigate to new item page (state should be preserved)
            await page.goto("https://www.vinted.fr/items/new", wait_until="networkidle")
            
            # Detect challenge before publish
            if await client.detect_challenge(page):
                print("⚠️ Challenge/Captcha detected - manual action needed")
                return ListingPublishResponse(
                    ok=True,
                    dry_run=False,
                    listing_id=None,
                    listing_url=None,
                    needs_manual=True,
                    reason="captcha_or_verification"
                )
            
            # Click publish button
            success, error = await client.click_publish(page)
            
            if not success:
                error_lower = (error or "").lower()
                if "captcha" in error_lower or "challenge" in error_lower:
                    return ListingPublishResponse(
                        ok=True,
                        dry_run=False,
                        listing_id=None,
                        listing_url=None,
                        needs_manual=True,
                        reason="captcha_or_verification"
                    )
                raise HTTPException(status_code=500, detail=error or "Unknown error")
            
            # Wait for redirect
            await asyncio.sleep(2)
            
            # Extract listing ID from URL
            listing_id = await client.extract_listing_id(page)
            listing_url = page.url if listing_id else None
            
            print(f"✅ Published: ID={listing_id}, URL={listing_url}")
            
            # Log successful publish to SQLite
            draft_id = draft_context.get("draft_id")
            if draft_id:
                # Log publish result
                import uuid as uuid_lib
                log_id = str(uuid_lib.uuid4())
                get_store().log_publish(
                    log_id=log_id,
                    draft_id=draft_id,
                    idempotency_key=idempotency_key,
                    confirm_token=request.confirm_token,
                    dry_run=False,
                    status="ok",
                    listing_url=listing_url
                )
                
                # Update draft status to published
                get_store().update_draft_status(draft_id, "published")
                
                # Upsert listing record
                if listing_id:
                    get_store().upsert_listing(
                        listing_id=draft_id,  # Use draft_id as listing_id
                        title=draft_context.get("title", ""),
                        price=float(draft_context.get("price", 0)),
                        vinted_id=listing_id,
                        listing_url=listing_url,
                        status="active"
                    )
            
            return ListingPublishResponse(
                ok=True,
                dry_run=False,
                listing_id=listing_id,
                listing_url=listing_url,
                needs_manual=False,
                reason=None
            )
            
    except HTTPException:
        raise
    except CaptchaDetected as e:
        print(f"⚠️ Captcha detected: {e}")
        return ListingPublishResponse(
            ok=True,
            dry_run=False,
            listing_id=None,
            listing_url=None,
            needs_manual=True,
            reason="captcha_or_verification"
        )
    except Exception as e:
        print(f"❌ Publish error: {e}")
        raise HTTPException(status_code=500, detail=f"Publish failed: {str(e)}")


@router.post("/listings/draft", response_model=ListingPrepareResponse)
async def create_draft(
    request: ListingPrepareRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a Vinted draft listing
    
    **Requires:** Authentication (user ownership validation)
    
    - Opens /items/new
    - Uploads photos
    - Fills form fields
    - Clicks "Save as draft" button
    - Returns draft URL and ID
    
    Default: dry_run=true (simulation only)
    
    Returns:
        - ok: true/false
        - vinted_draft_url: URL of the draft (e.g., https://www.vinted.fr/items/drafts/123)
        - vinted_draft_id: ID of the draft
        - dry_run: whether this was a simulation
    """
    try:
        print(f"\n{'='*60}")
        print(f"📝 CRÉATION BROUILLON VINTED")
        print(f"{'='*60}")
        print(f"📋 Title: {request.title[:50]}...")
        print(f"💰 Price: {request.price}€")
        print(f"📸 Photos: {len(request.photos)} fichiers")
        print(f"🏷️  Category: {request.category_hint}")
        print(f"👕 Size: {request.size}")
        print(f"✨ Condition: {request.condition}")
        print(f"🎨 Brand: {request.brand}")
        
        # In dry_run mode, skip session check (simulation only)
        if not request.dry_run and not settings.MOCK_MODE:
            # Check authentication (ONLY for real execution)
            session = vault.load_session()
            if not session:
                print(f"❌ ERREUR: Aucune session Vinted trouvée")
                print(f"   → Va dans Settings pour coller ton cookie Vinted")
                raise HTTPException(status_code=401, detail="Not authenticated. Call /auth/session first.")
            
            print(f"✅ Session Vinted active: user={session.username or 'unknown'}")
        else:
            print(f"🧪 [DRY-RUN MODE] Skipping Vinted session check")
            session = None
        
        # Dry run simulation
        if request.dry_run or settings.MOCK_MODE:
            print(f"🔄 [DRY-RUN] Creating draft: {request.title}")
            
            # Simulate draft creation
            mock_draft_id = "123456789"
            mock_draft_url = f"https://www.vinted.fr/items/drafts/{mock_draft_id}"
            
            return ListingPrepareResponse(
                ok=True,
                dry_run=True,
                vinted_draft_url=mock_draft_url,
                vinted_draft_id=mock_draft_id,
                publish_mode="draft",
                preview_url=mock_draft_url,
                screenshot_b64=None
            )
        
        # Real execution
        print(f"🚀 [REAL] Creating draft: {request.title}")
        
        # session is guaranteed to exist here (checked above)
        if not session:
            raise HTTPException(status_code=500, detail="Internal error: session not found")
        
        async with VintedClient(headless=settings.PLAYWRIGHT_HEADLESS) as client:
            # Create context with session
            await client.create_context(session)
            page = await client.new_page()
            
            # Navigate to new item page
            await page.goto("https://www.vinted.fr/items/new", wait_until="networkidle")
            
            # Check for challenges
            if await client.detect_challenge(page):
                raise HTTPException(
                    status_code=403,
                    detail="Verification/Captcha detected. Please complete manually."
                )
            
            # Upload photos
            if request.photos:
                from pathlib import Path
                import os
                
                for idx, photo_ref in enumerate(request.photos):
                    # Smart path resolution
                    if photo_ref.startswith('/'):
                        photo_path = f"backend/data{photo_ref}"
                    elif photo_ref.startswith('backend/data/'):
                        photo_path = photo_ref
                    elif photo_ref.startswith('temp_photos/'):
                        photo_path = f"backend/data/{photo_ref}"
                    else:
                        photo_path = f"backend/data/temp_photos/{photo_ref}"
                    
                    # Verify file exists
                    if not os.path.exists(photo_path):
                        print(f"❌ Photo [{idx}] NOT FOUND: {photo_ref}")
                        raise HTTPException(
                            status_code=404,
                            detail=f"Photo not found: {photo_ref}"
                        )
                    
                    print(f"📸 Uploading photo [{idx+1}/{len(request.photos)}]: {os.path.basename(photo_path)}")
                    upload_success = await client.upload_photo(page, photo_path)
                    
                    if not upload_success:
                        # Check if redirected to login
                        current_url = page.url
                        if 'session-refresh' in current_url or 'session/new' in current_url or 'member/login' in current_url:
                            print(f"❌ Session Vinted expirée (redirigé vers {current_url})")
                            raise HTTPException(
                                status_code=401,
                                detail=f"SESSION_EXPIRED: Votre session Vinted a expiré."
                            )
                        
                        print(f"⚠️ Photo upload failed: {photo_ref}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to upload photo: {photo_ref}"
                        )
            
            # Fill form
            fill_result = await client.fill_listing_form(
                page=page,
                title=request.title,
                price=request.price,
                description=request.description,
                brand=request.brand,
                size=request.size,
                condition=request.condition,
                color=request.color,
                category_hint=request.category_hint
            )
            
            print(f"✅ Formulaire rempli: {fill_result['filled']}")
            if fill_result['errors']:
                print(f"⚠️ Erreurs: {fill_result['errors']}")
            
            # Click "Save as draft" button
            success, error = await client.click_save_as_draft(page)
            
            if not success:
                error_lower = (error or "").lower()
                if "captcha" in error_lower or "challenge" in error_lower:
                    raise HTTPException(
                        status_code=403,
                        detail="Captcha/Verification detected. Please complete manually."
                    )
                raise HTTPException(
                    status_code=500,
                    detail=error or "Failed to save as draft"
                )
            
            # Wait for navigation
            await asyncio.sleep(2)
            
            # Extract draft ID from URL
            draft_id = await client.extract_draft_id(page)
            draft_url = page.url if draft_id else None
            
            # Take screenshot
            screenshot_b64 = await client.take_screenshot(page)
            
            print(f"✅ Brouillon créé: ID={draft_id}, URL={draft_url}")
            
            return ListingPrepareResponse(
                ok=True,
                dry_run=False,
                vinted_draft_url=draft_url,
                vinted_draft_id=draft_id,
                publish_mode="draft",
                preview_url=draft_url,
                screenshot_b64=screenshot_b64
            )
            
    except HTTPException:
        raise
    except CaptchaDetected as e:
        print(f"⚠️ Captcha detected: {e}")
        raise HTTPException(
            status_code=403,
            detail="Captcha/Verification detected. Please complete manually."
        )
    except Exception as e:
        print(f"❌ Create draft error: {e}")
        raise HTTPException(status_code=500, detail=f"Create draft failed: {str(e)}")


@router.post("/session/test")
async def test_session(current_user: User = Depends(get_current_user)):
    """
    Test if Vinted session cookie is still valid
    
    Returns:
        - valid: Session is active and working
        - expired: Session expired, need to refresh cookie
        - missing: No session found
        - error: Error during test
    """
    try:
        # Get user's session
        session = vault.load_session()
        
        if not session:
            return JSONResponse({
                "ok": False,
                "status": "missing",
                "message": "❌ Aucune session Vinted configurée. Veuillez ajouter votre cookie dans Settings.",
                "action": "add_cookie"
            })
        
        print(f"🔍 Testing Vinted session for user {current_user.id}...")
        
        # Create browser context and test
        async with VintedClient(headless=True) as client:
            await client.create_context(session)
            page = await client.new_page()
            
            # Navigate to a page that requires auth
            await page.goto("https://www.vinted.fr/items/new", wait_until="networkidle", timeout=15000)
            
            # Check current URL
            current_url = page.url
            
            # If redirected to session-refresh or login, session is expired
            if 'session-refresh' in current_url or 'session/new' in current_url or 'member/login' in current_url:
                print(f"❌ Session expired (redirected to {current_url})")
                return JSONResponse({
                    "ok": False,
                    "status": "expired",
                    "message": "❌ Votre session Vinted a expiré. Veuillez actualiser votre cookie.",
                    "action": "refresh_cookie",
                    "detected_url": current_url
                })
            
            # If we're still on /items/new, session is valid
            if '/items/new' in current_url:
                print(f"✅ Session valid!")
                return JSONResponse({
                    "ok": True,
                    "status": "valid",
                    "message": "✅ Votre session Vinted est active et valide !",
                    "action": None
                })
            
            # Unknown state
            print(f"⚠️ Unknown state: {current_url}")
            return JSONResponse({
                "ok": False,
                "status": "unknown",
                "message": f"⚠️ État inconnu. URL actuelle: {current_url}",
                "action": "check_manually",
                "detected_url": current_url
            })
            
    except Exception as e:
        print(f"❌ Session test error: {e}")
        return JSONResponse({
            "ok": False,
            "status": "error",
            "message": f"❌ Erreur lors du test: {str(e)}",
            "action": "retry",
            "error": str(e)
        }, status_code=500)


# ============================================================================
# SPRINT 1 FEATURE 1B: BIDIRECTIONAL SYNC
# ============================================================================

@router.post("/sync/pull")
async def sync_pull_from_vinted(
    listing_ids: Optional[List[str]] = Body(default=None),
    current_user: User = Depends(get_current_user)
):
    """
    Pull changes from Vinted and update local database

    Fetches latest data from Vinted for published listings and detects changes.
    Automatically applies updates based on conflict resolution strategy.

    Args:
        listing_ids: Optional list of specific Vinted listing IDs to sync
                    (None = sync all published listings)

    Returns:
        {
            "ok": bool,
            "status": "success" | "conflict" | "error",
            "pulled_changes": int,
            "conflicts": [SyncChange],
            "errors": [str],
            "synced_at": datetime
        }
    """
    try:
        from backend.core.vinted_sync_service import get_sync_service

        # Get sync service for user
        sync_service = get_sync_service(current_user.id)

        # Pull changes from Vinted
        result = await sync_service.pull_changes(listing_ids=listing_ids)

        return {
            "ok": result.status in ["success", "conflict"],
            "status": result.status.value,
            "pulled_changes": result.pulled_changes,
            "conflicts": [
                {
                    "listing_id": c.listing_id,
                    "field": c.field,
                    "local_value": c.local_value,
                    "vinted_value": c.vinted_value,
                    "conflict": c.conflict
                }
                for c in result.conflicts
            ],
            "errors": result.errors,
            "synced_at": result.synced_at.isoformat() if result.synced_at else None
        }

    except Exception as e:
        logger.error(f"[SYNC-PULL] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync pull failed: {str(e)}")


@router.post("/sync/push")
async def sync_push_to_vinted(
    draft_ids: Optional[List[str]] = Body(default=None),
    current_user: User = Depends(get_current_user)
):
    """
    Push local changes to Vinted

    Uploads local modifications to Vinted for published listings.
    Only pushes listings that have been modified since last sync.

    Args:
        draft_ids: Optional list of specific draft IDs to push
                  (None = push all modified drafts)

    Returns:
        {
            "ok": bool,
            "status": "success" | "error",
            "pushed_changes": int,
            "errors": [str],
            "synced_at": datetime
        }
    """
    try:
        from backend.core.vinted_sync_service import get_sync_service

        # Get sync service for user
        sync_service = get_sync_service(current_user.id)

        # Push changes to Vinted
        result = await sync_service.push_changes(draft_ids=draft_ids)

        return {
            "ok": result.status == "success",
            "status": result.status.value,
            "pushed_changes": result.pushed_changes,
            "errors": result.errors,
            "synced_at": result.synced_at.isoformat() if result.synced_at else None
        }

    except Exception as e:
        logger.error(f"[SYNC-PUSH] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync push failed: {str(e)}")


@router.post("/sync/full")
async def sync_full_bidirectional(
    current_user: User = Depends(get_current_user)
):
    """
    Perform full bidirectional sync (pull + push)

    First pulls changes from Vinted, then pushes local modifications.
    This ensures both systems are in sync.

    Returns:
        {
            "ok": bool,
            "status": "success" | "conflict" | "error",
            "pulled_changes": int,
            "pushed_changes": int,
            "conflicts": [SyncChange],
            "errors": [str],
            "synced_at": datetime
        }
    """
    try:
        from backend.core.vinted_sync_service import get_sync_service

        # Get sync service for user
        sync_service = get_sync_service(current_user.id)

        # Full sync (pull + push)
        result = await sync_service.full_sync()

        return {
            "ok": result.status in ["success", "conflict"],
            "status": result.status.value,
            "pulled_changes": result.pulled_changes,
            "pushed_changes": result.pushed_changes,
            "conflicts": [
                {
                    "listing_id": c.listing_id,
                    "field": c.field,
                    "local_value": c.local_value,
                    "vinted_value": c.vinted_value,
                    "conflict": c.conflict
                }
                for c in result.conflicts
            ],
            "errors": result.errors,
            "synced_at": result.synced_at.isoformat() if result.synced_at else None
        }

    except Exception as e:
        logger.error(f"[SYNC-FULL] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Full sync failed: {str(e)}")


@router.get("/sync/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get current sync status for user

    Returns information about the last sync and current sync state.

    Returns:
        {
            "status": "idle" | "syncing" | "success" | "error" | "conflict",
            "last_sync": datetime | null,
            "poll_interval": int (seconds),
            "conflict_strategy": str
        }
    """
    try:
        from backend.core.vinted_sync_service import get_sync_service

        # Get sync service for user
        sync_service = get_sync_service(current_user.id)

        return {
            "status": sync_service.status.value,
            "last_sync": sync_service.last_sync.isoformat() if sync_service.last_sync else None,
            "poll_interval": sync_service.poll_interval,
            "conflict_strategy": sync_service.conflict_strategy.value
        }

    except Exception as e:
        logger.error(f"[SYNC-STATUS] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")
