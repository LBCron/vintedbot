"""
SECURITY PATCHES - CRITICAL VULNERABILITIES FIX
Apply all critical security fixes identified in audit

Usage:
    python backend/security/apply_patches.py
"""

from backend.core.redis_client import cache, get_redis
from fastapi import HTTPException, Request
from typing import Optional, Dict
import secrets
import httpx
from datetime import timedelta
import re


# ============================================
# PATCH #1: OAuth State Management (Redis)
# ============================================

class OAuthStateManager:
    """Secure OAuth state management with Redis"""

    @staticmethod
    async def generate_state(user_id: Optional[str] = None) -> str:
        """Generate cryptographically secure OAuth state"""
        state = secrets.token_urlsafe(32)

        # Store in Redis with 10-minute TTL
        await cache.set(
            f"oauth:state:{state}",
            user_id or "anonymous",
            ttl=600  # 10 minutes
        )

        return state

    @staticmethod
    async def verify_state(state: str) -> Optional[str]:
        """Verify OAuth state and delete (single-use)"""
        key = f"oauth:state:{state}"

        # Get user_id
        user_id = await cache.get(key)

        if user_id:
            # Delete state (single-use)
            await cache.delete(key)
            return user_id

        return None


# ============================================
# PATCH #2: Login Rate Limiting
# ============================================

class LoginRateLimiter:
    """Rate limiting for login attempts"""

    @staticmethod
    async def check_attempts(email: str) -> None:
        """Check failed login attempts and block if too many"""
        key = f"login_attempts:{email.lower()}"
        attempts = await cache.get(key, default=0)

        if attempts >= 5:
            raise HTTPException(
                status_code=429,
                detail="Too many failed login attempts. Try again in 15 minutes."
            )

    @staticmethod
    async def record_failure(email: str) -> None:
        """Record a failed login attempt"""
        key = f"login_attempts:{email.lower()}"
        attempts = await cache.get(key, default=0)

        await cache.set(key, attempts + 1, ttl=900)  # 15 minutes

    @staticmethod
    async def clear_attempts(email: str) -> None:
        """Clear attempts on successful login"""
        await cache.delete(f"login_attempts:{email.lower()}")


# ============================================
# PATCH #3: Password Strength Validator
# ============================================

class PasswordValidator:
    """Validate password strength"""

    # Common passwords to block
    COMMON_PASSWORDS = {
        "password", "12345678", "qwerty", "admin123", "letmein",
        "welcome", "monkey", "dragon", "master", "password123"
    }

    @staticmethod
    def validate(password: str) -> Dict[str, any]:
        """
        Validate password strength

        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []

        # Length check (minimum 12)
        if len(password) < 12:
            errors.append("Password must be at least 12 characters long")

        # Uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        # Lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        # Digit
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        # Special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/]', password):
            errors.append("Password must contain at least one special character")

        # Common password check
        if password.lower() in PasswordValidator.COMMON_PASSWORDS:
            errors.append("This password is too common. Please choose a more unique password")

        # Sequential characters
        if re.search(r'(012|123|234|345|456|567|678|789|abc|bcd|cde)', password.lower()):
            errors.append("Password should not contain obvious sequences")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }


# ============================================
# PATCH #4: Path Traversal Prevention
# ============================================

from pathlib import Path
import os

class SecurePathValidator:
    """Validate file paths to prevent path traversal"""

    # Allowed base directories
    UPLOAD_DIR = Path("/home/user/vintedbot/backend/data/uploads").resolve()
    TEMP_DIR = Path("/home/user/vintedbot/backend/data/temp_uploads").resolve()

    @staticmethod
    def validate_path(
        path: str,
        user_id: Optional[int] = None,
        allowed_dir: Optional[Path] = None
    ) -> Path:
        """
        Validate and sanitize file path

        Raises:
            HTTPException if path is invalid or outside allowed directory

        Returns:
            Validated absolute Path object
        """
        try:
            # Convert to absolute path
            abs_path = Path(path).resolve()

            # Determine allowed directory
            if allowed_dir is None:
                allowed_dir = SecurePathValidator.UPLOAD_DIR

            # Check if path is within allowed directory
            try:
                abs_path.relative_to(allowed_dir)
            except ValueError:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: Path outside allowed directory"
                )

            # Check if file exists
            if not abs_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="File not found"
                )

            # Check if it's a regular file (not directory or symlink)
            if not abs_path.is_file():
                raise HTTPException(
                    status_code=400,
                    detail="Path must be a regular file"
                )

            return abs_path

        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file path: {str(e)}"
            )


# ============================================
# PATCH #5: Secure Impersonation
# ============================================

from datetime import datetime
import json

class SecureImpersonation:
    """Secure admin impersonation with audit logging"""

    @staticmethod
    async def create_session(admin_id: int, target_user_id: int) -> str:
        """Create short-lived impersonation session"""
        session_id = secrets.token_urlsafe(32)

        session_data = {
            "admin_id": admin_id,
            "target_user_id": target_user_id,
            "started_at": datetime.utcnow().isoformat(),
            "actions": []
        }

        # Store session in Redis (1 hour TTL)
        await cache.set(
            f"impersonation:{session_id}",
            session_data,
            ttl=3600  # 1 hour
        )

        return session_id

    @staticmethod
    async def verify_session(session_id: str) -> Optional[Dict]:
        """Verify impersonation session is still valid"""
        session_data = await cache.get(f"impersonation:{session_id}")
        return session_data

    @staticmethod
    async def revoke_session(session_id: str) -> bool:
        """Revoke an active impersonation session"""
        return await cache.delete(f"impersonation:{session_id}")

    @staticmethod
    async def log_action(session_id: str, action: str, details: Dict) -> None:
        """Log action performed during impersonation"""
        session_data = await cache.get(f"impersonation:{session_id}")

        if session_data:
            if "actions" not in session_data:
                session_data["actions"] = []

            session_data["actions"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "action": action,
                "details": details
            })

            # Update session with logged action
            await cache.set(
                f"impersonation:{session_id}",
                session_data,
                ttl=3600
            )


# ============================================
# PATCH #6: HTTP Timeout Configuration
# ============================================

class SecureHTTPClient:
    """HTTP client with proper timeouts"""

    # Default timeouts
    DEFAULT_TIMEOUT = httpx.Timeout(
        connect=5.0,   # 5s to establish connection
        read=30.0,     # 30s to read response
        write=5.0,     # 5s to send request
        pool=5.0       # 5s to get connection from pool
    )

    @staticmethod
    def get_client(timeout: Optional[httpx.Timeout] = None) -> httpx.AsyncClient:
        """Get configured HTTP client with timeouts"""
        return httpx.AsyncClient(
            timeout=timeout or SecureHTTPClient.DEFAULT_TIMEOUT,
            follow_redirects=True,
            max_redirects=3
        )


# ============================================
# PATCH #7: Atomic Quota Management
# ============================================

class AtomicQuotaManager:
    """Thread-safe quota management with Redis"""

    @staticmethod
    async def check_and_consume(
        user_id: int,
        quota_type: str,
        amount: int = 1
    ) -> None:
        """
        Atomically check and consume quota

        Raises:
            HTTPException if quota exceeded
        """
        quota_key = f"quota:{user_id}:{quota_type}"
        limit_key = f"quota_limit:{user_id}:{quota_type}"

        # Get Redis client
        redis = await get_redis()
        if not redis:
            # Fallback if Redis unavailable
            return

        # Lua script for atomic check-and-increment
        lua_script = """
        local quota_key = KEYS[1]
        local limit_key = KEYS[2]
        local amount = tonumber(ARGV[1])

        local current = tonumber(redis.call('GET', quota_key) or 0)
        local limit = tonumber(redis.call('GET', limit_key) or 100)

        if current + amount <= limit then
            redis.call('INCRBY', quota_key, amount)
            return 1
        else
            return 0
        end
        """

        result = await redis.eval(
            lua_script,
            2,  # Number of keys
            quota_key,
            limit_key,
            amount
        )

        if result == 0:
            raise HTTPException(
                status_code=429,
                detail=f"Quota exceeded for {quota_type}"
            )


# ============================================
# PATCH #8: Secure Error Handler
# ============================================

from backend.utils.logger import logger
import traceback
import uuid

class SecureErrorHandler:
    """Sanitize error messages for production"""

    @staticmethod
    def handle_error(error: Exception, request: Request) -> Dict:
        """
        Handle error securely

        - Log full error details server-side
        - Return sanitized error to client
        """
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())

        # Log full error details server-side
        logger.error(
            f"[{request_id}] Error in {request.method} {request.url.path}",
            exc_info=error
        )

        # Return sanitized error to client
        if isinstance(error, HTTPException):
            # HTTPException already has safe message
            return {
                "error": error.detail,
                "status_code": error.status_code,
                "request_id": request_id
            }
        else:
            # Generic error message
            return {
                "error": "An unexpected error occurred. Please contact support with this request ID.",
                "request_id": request_id,
                "status_code": 500
            }


# ============================================
# PATCH #9: Concurrent Upload Limiter
# ============================================

class ConcurrentUploadLimiter:
    """Prevent too many concurrent uploads per user"""

    MAX_CONCURRENT = 50

    @staticmethod
    async def acquire(user_id: int) -> None:
        """Acquire upload slot"""
        key = f"concurrent_uploads:{user_id}"
        count = await cache.get(key, default=0)

        if count >= ConcurrentUploadLimiter.MAX_CONCURRENT:
            raise HTTPException(
                status_code=429,
                detail="Too many concurrent uploads. Please wait for existing uploads to complete."
            )

        await cache.set(key, count + 1, ttl=300)  # 5 minutes

    @staticmethod
    async def release(user_id: int) -> None:
        """Release upload slot"""
        key = f"concurrent_uploads:{user_id}"
        count = await cache.get(key, default=0)

        if count > 0:
            await cache.set(key, count - 1, ttl=300)


# ============================================
# PATCH #10: Message Length Validator
# ============================================

from pydantic import validator

class MessageLengthValidator:
    """Validate message lengths for AI requests"""

    MAX_MESSAGE_LENGTH = 2000
    MIN_MESSAGE_LENGTH = 10

    @staticmethod
    def validate(message: str) -> str:
        """
        Validate message length

        Raises:
            ValueError if invalid
        """
        if len(message) < MessageLengthValidator.MIN_MESSAGE_LENGTH:
            raise ValueError(f"Message must be at least {MessageLengthValidator.MIN_MESSAGE_LENGTH} characters")

        if len(message) > MessageLengthValidator.MAX_MESSAGE_LENGTH:
            raise ValueError(f"Message must not exceed {MessageLengthValidator.MAX_MESSAGE_LENGTH} characters")

        return message.strip()


# ============================================
# Export all patches
# ============================================

__all__ = [
    'OAuthStateManager',
    'LoginRateLimiter',
    'PasswordValidator',
    'SecurePathValidator',
    'SecureImpersonation',
    'SecureHTTPClient',
    'AtomicQuotaManager',
    'SecureErrorHandler',
    'ConcurrentUploadLimiter',
    'MessageLengthValidator',
]
