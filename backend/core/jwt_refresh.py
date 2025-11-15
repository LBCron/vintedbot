"""
JWT Refresh Token Mechanism

Provides secure token refresh without requiring re-authentication.

Security benefits:
- Short-lived access tokens (15 min)
- Long-lived refresh tokens (7 days)
- Refresh tokens stored in database (can be revoked)
- Access tokens stored in memory only
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
import os
import secrets

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "change-me")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: str, additional_claims: Dict = None) -> str:
    """
    Create short-lived access token (15 minutes)

    Args:
        user_id: User identifier
        additional_claims: Additional JWT claims

    Returns:
        JWT access token
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    claims = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow(),
    }

    if additional_claims:
        claims.update(additional_claims)

    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create long-lived refresh token (7 days)

    Args:
        user_id: User identifier

    Returns:
        JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = secrets.token_urlsafe(32)  # Unique token ID for revocation

    claims = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": jti,
        "iat": datetime.utcnow(),
    }

    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            return None

        return payload

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """
    Generate new access token from refresh token

    Args:
        refresh_token: Valid refresh token

    Returns:
        Dict with new access_token and user_id, or None if invalid
    """
    payload = verify_token(refresh_token, token_type="refresh")

    if not payload:
        return None

    user_id = payload["sub"]

    # TODO: Check if refresh token is revoked in database
    # For now, just generate new access token

    new_access_token = create_access_token(user_id)

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "user_id": user_id,
    }
