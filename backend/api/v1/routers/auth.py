"""
Authentication router for VintedBot SaaS
Handles user registration, login, and profile management
"""

from fastapi import APIRouter, HTTPException, Depends, Header, status
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

router = APIRouter(prefix="/auth")
security = HTTPBearer()


# ========== Helper Functions ==========

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Middleware dependency to extract current user from JWT token
    
    Usage in endpoints:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            user_id = current_user["id"]
            ...
    """
    token = credentials.credentials
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
async def register(user_data: UserRegister):
    """
    Register a new user account
    
    - Creates user with 'free' plan by default
    - Sets up default quotas automatically
    - Returns JWT access token
    
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
    
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login with email and password
    
    - Verifies credentials
    - Returns JWT access token
    - Token expires in 7 days
    
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
