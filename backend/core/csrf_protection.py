"""
CSRF Protection for VintedBot API

Protects against Cross-Site Request Forgery attacks.

Usage:
    from backend.core.csrf_protection import generate_csrf_token, verify_csrf_token

    # In login endpoint
    token = generate_csrf_token(user_id)

    # In protected endpoints
    verify_csrf_token(request.headers.get("X-CSRF-Token"), user_id)
"""
import hmac
import hashlib
import time
import os
from typing import Optional

CSRF_SECRET = os.getenv("SECRET_KEY", "change-me-in-production")
CSRF_EXPIRY = 3600  # 1 hour


def generate_csrf_token(user_id: str) -> str:
    """
    Generate CSRF token for user

    Args:
        user_id: User identifier

    Returns:
        CSRF token (base64 encoded)
    """
    timestamp = str(int(time.time()))
    message = f"{user_id}:{timestamp}"

    signature = hmac.new(
        CSRF_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{user_id}:{timestamp}:{signature}"


def verify_csrf_token(token: Optional[str], user_id: str) -> bool:
    """
    Verify CSRF token

    Args:
        token: CSRF token from request header
        user_id: Expected user ID

    Returns:
        True if valid, False otherwise
    """
    if not token:
        return False

    try:
        parts = token.split(":")
        if len(parts) != 3:
            return False

        token_user_id, timestamp, signature = parts

        # Check user ID matches
        if token_user_id != user_id:
            return False

        # Check expiry
        token_time = int(timestamp)
        if time.time() - token_time > CSRF_EXPIRY:
            return False

        # Verify signature
        message = f"{token_user_id}:{timestamp}"
        expected_signature = hmac.new(
            CSRF_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    except (ValueError, IndexError):
        return False
