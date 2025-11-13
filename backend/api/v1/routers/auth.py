"""
Authentication router for VintedBot SaaS
Handles user registration, login, and profile management
"""

from fastapi import APIRouter, HTTPException, Depends, Header, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
from typing import Optional
import httpx
import os
import secrets
from urllib.parse import urlencode

router = APIRouter(prefix="/auth")
security = HTTPBearer(auto_error=False)  # Don't auto-error if no Bearer token (we use cookies too)

# Cookie configuration
COOKIE_NAME = "auth_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days in seconds
COOKIE_SECURE = os.getenv("ENV", "development") == "production"  # True in production
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "lax"  # Allow cross-site for OAuth callbacks

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback")

# Temporary storage for OAuth states (in production use Redis)
oauth_states = {}


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
async def register(user_data: UserRegister, response: Response):
    """
    Register a new user account

    - Creates user with 'free' plan by default
    - Sets up default quotas automatically
    - Sets HTTP-only cookie with JWT token
    - Also returns token in body for backwards compatibility

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

    # Validate password strength (basic check)
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters"
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
async def login(credentials: UserLogin, response: Response):
    """
    Login with email and password

    - Verifies credentials
    - Sets HTTP-only cookie with JWT token
    - Token expires in 7 days
    - Also returns token in body for backwards compatibility

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

    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = True  # Store state temporarily

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

    # Verify state (CSRF protection)
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    del oauth_states[state]  # Remove used state

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
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
