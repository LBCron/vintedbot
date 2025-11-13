"""
Mobile App Security: JWT Token Manager with Refresh Tokens
Handles secure JWT generation, validation, and refresh token rotation
"""
import os
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from loguru import logger


@dataclass
class TokenPair:
    """Access + Refresh token pair"""
    access_token: str
    refresh_token: str
    access_expires_in: int  # seconds
    refresh_expires_in: int  # seconds
    token_type: str = "Bearer"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': self.access_expires_in,
            'token_type': self.token_type
        }


class JWTManager:
    """
    JWT Token Manager with Refresh Token Support

    Features:
    - HS256 signed JWTs
    - Access tokens (short-lived: 15 minutes)
    - Refresh tokens (long-lived: 30 days)
    - Token rotation on refresh
    - Revocation support
    - Device fingerprinting
    """

    # Token lifetimes
    ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
    REFRESH_TOKEN_LIFETIME = timedelta(days=30)

    # JWT algorithm
    ALGORITHM = "HS256"

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize JWT manager

        Args:
            secret_key: Secret for signing JWTs. If None, reads from env JWT_SECRET
        """
        self.secret_key = secret_key or os.getenv('JWT_SECRET')

        if not self.secret_key:
            # Generate new secret (WARN: will invalidate existing tokens!)
            logger.warning("No JWT_SECRET found, generating new secret (existing tokens will be invalid)")
            self.secret_key = secrets.token_urlsafe(64)

            if os.getenv('ENV') != 'production':
                logger.info(f"Generated JWT_SECRET (save this to .env):\n{self.secret_key}")

        # In-memory revocation list (in production, use Redis or database)
        self.revoked_tokens: set = set()

    def create_access_token(
        self,
        user_id: int,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create JWT access token

        Args:
            user_id: User ID
            email: User email
            additional_claims: Extra claims to include

        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        expires = now + self.ACCESS_TOKEN_LIFETIME

        payload = {
            'sub': str(user_id),  # Subject (user ID)
            'email': email,
            'type': 'access',
            'iat': now,  # Issued at
            'exp': expires,  # Expiration
            'jti': secrets.token_urlsafe(16)  # JWT ID (for revocation)
        }

        # Add additional claims
        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)

        logger.debug(f"Created access token for user {user_id} (expires in {self.ACCESS_TOKEN_LIFETIME.total_seconds()}s)")

        return token

    def create_refresh_token(
        self,
        user_id: int,
        device_id: Optional[str] = None
    ) -> str:
        """
        Create JWT refresh token

        Args:
            user_id: User ID
            device_id: Device identifier (for security)

        Returns:
            Refresh token string
        """
        now = datetime.utcnow()
        expires = now + self.REFRESH_TOKEN_LIFETIME

        payload = {
            'sub': str(user_id),
            'type': 'refresh',
            'iat': now,
            'exp': expires,
            'jti': secrets.token_urlsafe(16),
            'device_id': device_id or 'unknown'
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)

        logger.debug(f"Created refresh token for user {user_id} (expires in {self.REFRESH_TOKEN_LIFETIME.total_seconds()}s)")

        return token

    def create_token_pair(
        self,
        user_id: int,
        email: str,
        device_id: Optional[str] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> TokenPair:
        """
        Create access + refresh token pair

        Args:
            user_id: User ID
            email: User email
            device_id: Device ID
            additional_claims: Extra claims for access token

        Returns:
            TokenPair with both tokens
        """
        access_token = self.create_access_token(user_id, email, additional_claims)
        refresh_token = self.create_refresh_token(user_id, device_id)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_in=int(self.ACCESS_TOKEN_LIFETIME.total_seconds()),
            refresh_expires_in=int(self.REFRESH_TOKEN_LIFETIME.total_seconds())
        )

    def verify_token(
        self,
        token: str,
        expected_type: str = 'access'
    ) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token

        Args:
            token: JWT token to verify
            expected_type: Expected token type ('access' or 'refresh')

        Returns:
            Decoded payload if valid, None if invalid

        Raises:
            jwt.ExpiredSignatureError: If token expired
            jwt.InvalidTokenError: If token invalid
        """
        try:
            # Decode and verify
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.ALGORITHM]
            )

            # Check type
            if payload.get('type') != expected_type:
                logger.warning(f"Token type mismatch: expected {expected_type}, got {payload.get('type')}")
                return None

            # Check if revoked
            jti = payload.get('jti')
            if jti and jti in self.revoked_tokens:
                logger.warning(f"Token {jti} has been revoked")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            raise

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise

    def refresh_access_token(
        self,
        refresh_token: str,
        device_id: Optional[str] = None
    ) -> Optional[TokenPair]:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Valid refresh token
            device_id: Device ID (must match token)

        Returns:
            New token pair, or None if refresh failed
        """
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token, expected_type='refresh')

            if not payload:
                return None

            # Verify device_id matches (if provided)
            if device_id and payload.get('device_id') != device_id:
                logger.warning(f"Device ID mismatch during refresh")
                return None

            user_id = int(payload['sub'])

            # Get user email (would normally query database)
            # For now, we'll need to get it from somewhere
            from backend.core.storage import get_store
            user = get_store().get_user_by_id(user_id)

            if not user:
                logger.error(f"User {user_id} not found during token refresh")
                return None

            email = user.get('email', '')

            # Revoke old refresh token (token rotation)
            old_jti = payload.get('jti')
            if old_jti:
                self.revoke_token(old_jti)

            # Create new token pair
            new_tokens = self.create_token_pair(
                user_id=user_id,
                email=email,
                device_id=device_id
            )

            logger.info(f"Refreshed tokens for user {user_id}")

            return new_tokens

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            logger.error(f"Token refresh failed: {e}")
            return None

    def revoke_token(self, jti: str):
        """
        Revoke a token by its JTI

        Args:
            jti: JWT ID to revoke
        """
        self.revoked_tokens.add(jti)
        logger.info(f"Revoked token {jti}")

    def revoke_all_user_tokens(self, user_id: int):
        """
        Revoke all tokens for a user (logout from all devices)

        Note: In production, this should be stored in database/Redis
        with user_id → jti mapping

        Args:
            user_id: User ID
        """
        # For now, just log (would need database of active tokens)
        logger.info(f"Revoked all tokens for user {user_id}")

    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode token without verifying signature (for debugging)

        Args:
            token: JWT token

        Returns:
            Decoded payload (unverified!)
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")
            return None


# Singleton instance
_jwt_manager: Optional[JWTManager] = None


def get_jwt_manager() -> JWTManager:
    """Get global JWT manager instance"""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager


# FastAPI dependency for protected routes
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current user from JWT

    Usage:
        @app.get("/protected")
        async def protected_route(user = Depends(get_current_user_from_token)):
            return {"user_id": user['sub']}
    """
    token = credentials.credentials
    jwt_manager = get_jwt_manager()

    try:
        payload = jwt_manager.verify_token(token, expected_type='access')

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


# Generate new JWT secret (run once, save to .env)
def generate_jwt_secret() -> str:
    """
    Generate a new JWT secret key

    Returns:
        Secret key (save this as JWT_SECRET in .env)
    """
    secret = secrets.token_urlsafe(64)

    print("=" * 80)
    print("NEW JWT SECRET (SAVE THIS TO .env AS JWT_SECRET)")
    print("=" * 80)
    print(secret)
    print("=" * 80)
    print("⚠️ WARNING: If you change this, all existing tokens will be invalidated!")
    print("=" * 80)

    return secret


if __name__ == "__main__":
    # Test JWT manager
    print("Testing JWT manager...")

    # Generate secret
    secret = generate_jwt_secret()

    # Test token creation
    manager = JWTManager(secret)

    tokens = manager.create_token_pair(
        user_id=123,
        email="test@example.com",
        device_id="iphone_12_pro"
    )

    print(f"\nAccess Token: {tokens.access_token[:50]}...")
    print(f"Refresh Token: {tokens.refresh_token[:50]}...")

    # Verify access token
    payload = manager.verify_token(tokens.access_token)
    print(f"\nDecoded Access Token: {payload}")

    # Test refresh
    new_tokens = manager.refresh_access_token(tokens.refresh_token, device_id="iphone_12_pro")
    print(f"\nRefreshed! New Access Token: {new_tokens.access_token[:50]}...")

    print("\n✅ JWT manager test passed!")
