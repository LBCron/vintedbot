"""
Quota Enforcement Middleware
Checks and enforces usage limits before critical operations
"""
from fastapi import HTTPException, status
from typing import Literal
from backend.core.storage import get_storage
from backend.core.auth import User

QuotaType = Literal["drafts", "publications", "ai_analyses"]


class QuotaExceededError(HTTPException):
    """Raised when user has exceeded their quota"""
    def __init__(self, quota_type: str, limit: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "quota_exceeded",
                "quota_type": quota_type,
                "limit": limit,
                "message": f"You have reached your {quota_type} quota limit ({limit}). Please upgrade your plan."
            }
        )


async def check_and_consume_quota(
    user: User,
    quota_type: QuotaType,
    amount: int = 1
) -> None:
    """
    Check if user has quota available and consume it atomically
    
    Args:
        user: Current authenticated user
        quota_type: Type of quota to check (drafts, publications, ai_analyses)
        amount: Amount to consume (default: 1)
        
    Raises:
        QuotaExceededError: If user has exceeded their quota
        HTTPException(403): If user account is suspended
    """
    storage = get_storage()
    
    # Check user status
    user_data = storage.get_user_by_id(user.id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if user_data["status"] == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been suspended due to quota violations. Please contact support."
        )
    
    if user_data["status"] == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been cancelled. Please reactivate your subscription."
        )
    
    # Get current quotas
    quotas = storage.get_user_quotas(user.id)
    if not quotas:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota information"
        )
    
    # Check if user has enough quota for the requested amount
    quota_mappings = {
        "drafts": ("drafts_created", "drafts_limit"),
        "publications": ("publications_month", "publications_limit"),
        "ai_analyses": ("ai_analyses_month", "ai_analyses_limit")
    }
    used_field, limit_field = quota_mappings[quota_type]
    current_usage = quotas[used_field]
    limit = quotas[limit_field]
    
    # CRITICAL: Check that current_usage + amount <= limit
    if current_usage + amount > limit:
        raise QuotaExceededError(quota_type, limit)
    
    # Consume quota (only if check passed)
    quota_field_mapping = {
        "drafts": "drafts_created",
        "publications": "publications_month",
        "ai_analyses": "ai_analyses_month"
    }
    storage.increment_quota_usage(user.id, quota_field_mapping[quota_type], amount)


async def check_storage_quota(user: User, size_mb: float) -> None:
    """
    Check if user has storage quota available
    
    Args:
        user: Current authenticated user
        size_mb: Size in MB to check
        
    Raises:
        QuotaExceededError: If user has exceeded their storage quota
    """
    storage = get_storage()
    quotas = storage.get_user_quotas(user.id)
    
    if not quotas:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quota information"
        )
    
    if quotas["photos_storage_mb"] + size_mb > quotas["photos_storage_limit_mb"]:
        raise QuotaExceededError("photos_storage", quotas["photos_storage_limit_mb"])
    
    # Consume storage quota
    storage.increment_quota_usage(user.id, "photos_storage_mb", int(size_mb))
