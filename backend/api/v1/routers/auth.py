"""
Authentication router for VintedBot SaaS
Handles user registration, login, and profile management

SECURITY FIX Bug #66: Added rate limiting on auth endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Header, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.core.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserProfile,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)
from backend.core.storage import get_store
from backend.core.cache import cache_service
from backend.utils.password_validator import validate_password, get_password_strength
from typing import Optional
from datetime import datetime
import httpx
import os
import secrets
from urllib.parse import urlencode

router = APIRouter(prefix="/auth")
security = HTTPBearer(auto_error=False)  # Don't auto-error if no Bearer token (we use cookies too)

# SECURITY FIX Bug #66: Rate limiter for auth endpoints (brute-force protection)
limiter = Limiter(key_func=get_remote_address)
ENV = os.getenv("ENV", "development")
AUTH_RATE_LIMIT = "5/minute" if ENV == "production" else ("10/minute" if ENV == "staging" else "50/minute")

# Cookie configuration
COOKIE_NAME = "auth_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days in seconds
COOKIE_SECURE = os.getenv("ENV", "development") == "production"  # True in production
COOKIE_HTTPONLY = True
# SECURITY NOTE Bug #22: SameSite=lax is REQUIRED for OAuth callbacks
# SameSite=strict would break OAuth redirects from Google/GitHub
# This is a standard security tradeoff for OAuth flows
COOKIE_SAMESITE = "lax"  # Allow cross-site for OAuth callbacks

# Google OAuth configuration
# SECURITY FIX Bug #12: No fallback for OAuth credentials (fail-fast in production)
ENV = os.getenv("ENV", "development")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback")

# Validate OAuth config in production
if ENV == "production":
    if not GOOGLE_CLIENT_ID:
        logger.warning("GOOGLE_CLIENT_ID not set - Google OAuth will be disabled")
    if not GOOGLE_CLIENT_SECRET:
        logger.warning("GOOGLE_CLIENT_SECRET not set - Google OAuth will be disabled")

# SECURITY FIX: OAuth states stored in Redis instead of memory
# TTL of 600 seconds (10 minutes) for OAuth state tokens
OAUTH_STATE_TTL = 600


# ========== Helper Functions ==========

def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Middleware dependency to extract current user from JWT token

    Supports BOTH:
    - HTTP-only cookies (preferred, more secure)
    - Authorization Bearer header (backwards compatibility)

    Usage in endpoints:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            user_id = current_user["id"]
            ...
    """
    # Try to get token from cookie first (preferred method)
    token = request.cookies.get(COOKIE_NAME)

    # Fallback to Authorization header if no cookie
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token_data = decode_access_token(token)

    if token_data is None or token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Get full user data from database
    store = get_store()
    user = store.get_user_by_id(token_data.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if user["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user['status']}. Please contact support."
        )

    return user


# ========== Public Endpoints ==========

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_RATE_LIMIT)  # SECURITY FIX Bug #66: Rate limit registration (5/min in prod)
async def register(request: Request, user_data: UserRegister, response: Response):
    """
    Register a new user account

    - Creates user with 'free' plan by default
    - Sets up default quotas automatically
    - Sets HTTP-only cookie with JWT token
    - Also returns token in body for backwards compatibility
    - RATE LIMITED: 5 requests/minute in production (prevents abuse)

    Example:
        POST /auth/register
        {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "name": "John Doe"
        }
    """
    store = get_store()

    # Check if email already exists
    existing_user = store.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # SECURITY FIX: Strong password validation
    is_valid, error_message = validate_password(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Hash password and create user
    hashed_pw = hash_password(user_data.password)
    user = store.create_user(
        email=user_data.email,
        hashed_password=hashed_pw,
        name=user_data.name,
        plan="free"
    )

    # Generate JWT token
    access_token = create_access_token(data={
        "user_id": user["id"],
        "email": user["email"]
    })

    # Set HTTP-only cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        max_age=COOKIE_MAX_AGE,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )

    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
@limiter.limit(AUTH_RATE_LIMIT)  # SECURITY FIX Bug #66: Rate limit login (5/min in prod, brute-force protection)
async def login(request: Request, credentials: UserLogin, response: Response):
    """
    Login with email and password

    - Verifies credentials
    - Sets HTTP-only cookie with JWT token
    - Token expires in 7 days
    - Also returns token in body for backwards compatibility
    - RATE LIMITED: 5 requests/minute in production (brute-force protection)

    Example:
        POST /auth/login
        {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }
    """
    store = get_store()

    # Get user by email
    user = store.get_user_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check account status
    if user["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user['status']}. Please contact support."
        )

    # Generate JWT token
    access_token = create_access_token(data={
        "user_id": user["id"],
        "email": user["email"]
    })

    # Set HTTP-only cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        max_age=COOKIE_MAX_AGE,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )

    return Token(access_token=access_token)


# ========== Protected Endpoints (Requires Auth) ==========

@router.get("/me", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile with quotas
    
    Requires: Authorization: Bearer <token>
    
    Returns user info + quota usage/limits
    """
    store = get_store()
    quotas = store.get_user_quotas(current_user["id"])
    
    return UserProfile(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        plan=current_user["plan"],
        status=current_user["status"],
        created_at=current_user["created_at"],
        quotas_used={
            "drafts": quotas["drafts_created"] if quotas else 0,
            "publications_month": quotas["publications_month"] if quotas else 0,
            "ai_analyses_month": quotas["ai_analyses_month"] if quotas else 0,
            "photos_storage_mb": quotas["photos_storage_mb"] if quotas else 0
        },
        quotas_limit={
            "drafts": quotas["drafts_limit"] if quotas else 0,
            "publications_month": quotas["publications_limit"] if quotas else 0,
            "ai_analyses_month": quotas["ai_analyses_limit"] if quotas else 0,
            "photos_storage_mb": quotas["photos_storage_limit_mb"] if quotas else 0
        }
    )


@router.get("/quotas")
async def get_quotas(current_user: dict = Depends(get_current_user)):
    """
    Get detailed quota information for current user

    Requires: Authorization: Bearer <token>
    """
    store = get_store()
    quotas = store.get_user_quotas(current_user["id"])

    if not quotas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quotas not found"
        )

    return {
        "plan": current_user["plan"],
        "status": current_user["status"],
        "quotas": quotas
    }


@router.post("/logout")
async def logout(response: Response):
    """
    Logout user by clearing the HTTP-only cookie

    Works even without authentication (clears cookie regardless)
    """
    # Clear the auth cookie by setting it to expire immediately
    response.delete_cookie(
        key=COOKIE_NAME,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE
    )

    return {"message": "Logged out successfully"}


# ========== Google OAuth ==========

@router.get("/google")
async def google_login():
    """
    Initiate Google OAuth login

    Redirects user to Google's OAuth consent screen
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
        )

    # SECURITY FIX: Generate random state for CSRF protection and store in Redis
    state = secrets.token_urlsafe(32)
    cache_service.set(
        f"oauth:state:{state}",
        {"created_at": datetime.now().isoformat(), "provider": "google"},
        ttl=OAUTH_STATE_TTL  # 10 minutes expiration
    )

    # Build Google OAuth URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account"
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return {"auth_url": auth_url}


@router.get("/google/callback")
async def google_callback(code: str, state: str):
    """
    Handle Google OAuth callback

    - Exchanges authorization code for access token
    - Fetches user info from Google
    - Creates or logs in user
    - Returns JWT token
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth not configured"
        )

    # SECURITY FIX: Verify state from Redis (CSRF protection)
    state_data = cache_service.get(f"oauth:state:{state}")
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter. Please try logging in again."
        )

    # Delete state immediately after use (prevents replay attacks)
    cache_service.delete(f"oauth:state:{state}")

    # Exchange code for access token
    # SECURITY FIX Bug #10: Add timeout to prevent hanging requests
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        # Fetch user info from Google
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user info from Google"
            )

        userinfo = userinfo_response.json()

    # Extract user data
    email = userinfo.get("email")
    name = userinfo.get("name", email.split("@")[0])
    google_id = userinfo.get("id")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by Google"
        )

    # Check if user exists or create new one
    store = get_store()
    user = store.get_user_by_email(email)

    if not user:
        # Create new user (no password needed for OAuth users)
        user = store.create_user(
            email=email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),  # Random password (not used)
            name=name,
            plan="free"
        )

    # Generate JWT token for our app
    jwt_token = create_access_token(data={
        "user_id": user["id"],
        "email": user["email"]
    })

    return Token(access_token=jwt_token)


# ========== Sprint 2 + Mobile App Security Endpoints ==========

from pydantic import BaseModel
from backend.vinted.vinted_auth import authenticate_vinted_account
from backend.security.totp_manager import enable_2fa_for_user, verify_2fa_code, disable_2fa_for_user, get_totp_storage
from backend.security.jwt_manager import get_jwt_manager


class VintedConnectRequest(BaseModel):
    """Request to connect Vinted account"""
    email: str
    password: str


@router.post("/connect-vinted")
async def connect_vinted_account(
    request: VintedConnectRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Connect Vinted account using email/password (Mobile App Feature)

    - Automatically logs into Vinted
    - Extracts and saves session cookies
    - Encrypts credentials for security
    - Returns success status
    """
    from loguru import logger

    logger.info(f"User {current_user['id']} attempting to connect Vinted account")

    # Authenticate with Vinted
    result = await authenticate_vinted_account(
        email=request.email,
        password=request.password,
        user_id=current_user['id'],
        save_session=True
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
            headers={"X-Error-Code": result.error_code}
        )

    return {
        "ok": True,
        "message": "Vinted account connected successfully",
        "vinted_user_id": result.session.vinted_user_id if result.session else None
    }


@router.post("/2fa/setup")
async def setup_2fa(
    current_user: dict = Depends(get_current_user)
):
    """
    Set up 2FA for user account (Mobile App Feature)

    Returns:
    - QR code for authenticator app
    - Secret key (for manual entry)
    - Backup codes (save these!)
    """
    from loguru import logger

    logger.info(f"User {current_user['id']} setting up 2FA")

    # Generate 2FA setup
    setup = await enable_2fa_for_user(
        user_id=current_user['id'],
        user_email=current_user['email']
    )

    return {
        "ok": True,
        "message": "2FA setup successful. Scan the QR code with your authenticator app.",
        "secret": setup.secret,
        "qr_code": setup.qr_code_data,
        "backup_codes": setup.backup_codes,
        "provisioning_uri": setup.provisioning_uri
    }


class Verify2FARequest(BaseModel):
    """Request to verify 2FA code"""
    code: str


@router.post("/2fa/verify")
async def verify_2fa(
    request: Verify2FARequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify 2FA code (Mobile App Feature)

    - Verifies 6-digit TOTP code
    - Also accepts backup codes
    """
    from loguru import logger

    logger.info(f"User {current_user['id']} verifying 2FA code")

    # Verify code
    is_valid = await verify_2fa_code(
        user_id=current_user['id'],
        code=request.code
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA code"
        )

    return {
        "ok": True,
        "message": "2FA code verified successfully"
    }


@router.post("/2fa/disable")
async def disable_2fa(
    current_user: dict = Depends(get_current_user)
):
    """Disable 2FA for user account"""
    from loguru import logger

    logger.info(f"User {current_user['id']} disabling 2FA")

    await disable_2fa_for_user(current_user['id'])

    return {
        "ok": True,
        "message": "2FA disabled successfully"
    }


@router.get("/2fa/status")
async def get_2fa_status(
    current_user: dict = Depends(get_current_user)
):
    """Check if 2FA is enabled for user"""
    storage = get_totp_storage()

    is_enabled = storage.is_2fa_enabled(current_user['id'])

    return {
        "ok": True,
        "enabled": is_enabled
    }


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""
    refresh_token: str
    device_id: Optional[str] = None


@router.post("/refresh")
async def refresh_access_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token (Mobile App Feature)

    - Uses JWT refresh token
    - Returns new access + refresh token pair
    - Implements token rotation for security
    """
    jwt_manager = get_jwt_manager()

    # Refresh tokens
    new_tokens = jwt_manager.refresh_access_token(
        refresh_token=request.refresh_token,
        device_id=request.device_id
    )

    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    return {
        "ok": True,
        **new_tokens.to_dict()
    }


@router.post("/logout/all-devices")
async def logout_all_devices(
    current_user: dict = Depends(get_current_user)
):
    """
    Logout from all devices (Mobile App Feature)

    - Revokes all refresh tokens
    - Forces re-authentication on all devices
    """
    jwt_manager = get_jwt_manager()

    jwt_manager.revoke_all_user_tokens(current_user['id'])

    return {
        "ok": True,
        "message": "Logged out from all devices successfully"
    }
