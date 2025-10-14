"""
Vinted automation API endpoints
Handles session management, photo uploads, and listing creation/publication
"""
import asyncio
import secrets
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from fastapi import APIRouter, HTTPException, UploadFile, File, Header, Depends
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from backend.settings import settings
from backend.core.session import SessionVault, VintedSession
from backend.core.vinted_client import VintedClient, CaptchaDetected
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


@router.post("/auth/session", response_model=SessionResponse)
async def save_session(request: SessionRequest):
    """
    Save Vinted authentication session (cookie + user-agent)
    
    Security: Cookie is encrypted with Fernet before storage
    """
    try:
        print(f"📥 Received session request: cookie length={len(request.cookie)}, UA={request.user_agent[:50]}...")
        # Create session object
        session = VintedSession(
            cookie=request.cookie,
            user_agent=request.user_agent,
            expires_at=request.expires_at or datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow()
        )
        
        # Extract username if possible (optional parsing)
        username = None
        # Could parse from cookie if format is known
        
        # Save encrypted session
        persisted = vault.save_session(session)
        
        print(f"✅ Session saved (encrypted): user={username or 'unknown'}")
        
        return SessionResponse(
            ok=True,
            persisted=persisted,
            username=username
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


@router.post("/photos/upload", response_model=PhotoUploadResponse)
@limiter.limit("10/minute")
async def upload_photo(
    file: UploadFile = File(...),
    request: Optional[str] = None
):
    """
    Upload photo for Vinted listing
    
    Rate limited to 10/minute
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=415, detail="Only image files are allowed")
        
        # Generate temp_id
        temp_id = f"photo_{secrets.token_urlsafe(16)}"
        
        # Save file temporarily
        import os
        temp_dir = "backend/data/temp_photos"
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = f"{temp_dir}/{temp_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"✅ Photo uploaded: {file.filename} -> {temp_id}")
        
        # Return photo metadata
        return PhotoUploadResponse(
            ok=True,
            photo={
                "temp_id": temp_id,
                "url": f"/temp_photos/{temp_id}_{file.filename}",
                "filename": file.filename
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/listings/prepare", response_model=ListingPrepareResponse)
async def prepare_listing(request: ListingPrepareRequest):
    """
    Prepare a Vinted listing (Phase A - Draft)
    
    - Opens /items/new
    - Uploads photos
    - Fills form fields
    - Stops before publish
    - Returns confirm_token for phase B
    
    Default: dry_run=true (simulation only)
    """
    try:
        # Check authentication
        session = vault.load_session()
        if not session:
            raise HTTPException(status_code=401, detail="Not authenticated. Call /auth/session first.")
        
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
                for photo_ref in request.photos:
                    # Resolve photo path (could be temp_id or path)
                    photo_path = f"backend/data/temp_photos/{photo_ref}"
                    if not await client.upload_photo(page, photo_path):
                        print(f"⚠️ Photo upload failed: {photo_ref}")
            
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
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """
    Publish a prepared listing (Phase B - Publish)
    
    - Verifies confirm_token (TTL check)
    - Clicks "Publier" button
    - Detects captcha/challenges
    - Returns listing_id and URL on success
    
    Default: dry_run=true (safe mode)
    Rate limited: 5/minute
    """
    try:
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
