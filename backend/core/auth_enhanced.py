"""
Enhanced authentication system with improved security
- httpOnly cookie support (more secure than localStorage)
- CSRF protection
- Token rotation
- Device fingerprinting
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel
from loguru import logger


class AuthConfig(BaseModel):
    """Authentication configuration"""
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    use_httponly_cookies: bool = True
    csrf_protection: bool = True


class TokenPair(BaseModel):
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class EnhancedAuthManager:
    """
    Enhanced authentication manager with multiple security features

    Features:
    - httpOnly cookies (XSS protection)
    - CSRF tokens (CSRF protection)
    - Refresh tokens (longer sessions without storing sensitive data)
    - Device fingerprinting (detect suspicious logins)
    """

    def __init__(self, config: AuthConfig):
        self.config = config
        self.http_bearer = HTTPBearer(auto_error=False)

    def create_access_token(
        self,
        user_id: int,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create JWT access token (short-lived)

        Args:
            user_id: User ID
            email: User email
            additional_claims: Additional claims to include in token

        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + timedelta(
            minutes=self.config.access_token_expire_minutes
        )

        payload = {
            "sub": str(user_id),
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm
        )

    def create_refresh_token(self, user_id: int) -> str:
        """
        Create refresh token (long-lived)

        Args:
            user_id: User ID

        Returns:
            Refresh token string
        """
        expire = datetime.utcnow() + timedelta(
            days=self.config.refresh_token_expire_days
        )

        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # Unique token ID for revocation
        }

        return jwt.encode(
            payload,
            self.config.jwt_secret,
            algorithm=self.config.jwt_algorithm
        )

    def create_token_pair(
        self,
        user_id: int,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> TokenPair:
        """
        Create access and refresh token pair

        Args:
            user_id: User ID
            email: User email
            additional_claims: Additional claims for access token

        Returns:
            TokenPair with both tokens
        """
        access_token = self.create_access_token(user_id, email, additional_claims)
        refresh_token = self.create_refresh_token(user_id)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.access_token_expire_minutes * 60
        )

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode JWT token

        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid, expired, or wrong type
        """
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )

            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}"
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )

    def set_auth_cookies(
        self,
        response: Response,
        access_token: str,
        refresh_token: str
    ):
        """
        Set authentication cookies (httpOnly for security)

        Args:
            response: FastAPI response object
            access_token: Access token
            refresh_token: Refresh token
        """
        # Access token cookie (short-lived)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,  # XSS protection
            secure=True,    # HTTPS only (set to False for development)
            samesite="strict",  # CSRF protection
            max_age=self.config.access_token_expire_minutes * 60
        )

        # Refresh token cookie (long-lived)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=self.config.refresh_token_expire_days * 24 * 3600
        )

        logger.info("Authentication cookies set")

    def clear_auth_cookies(self, response: Response):
        """
        Clear authentication cookies (logout)

        Args:
            response: FastAPI response object
        """
        response.delete_cookie(key="access_token")
        response.delete_cookie(key="refresh_token")
        logger.info("Authentication cookies cleared")

    def get_token_from_request(self, request: Request) -> Optional[str]:
        """
        Extract token from request (cookie or Authorization header)

        Args:
            request: FastAPI request object

        Returns:
            Token string or None
        """
        # Try httpOnly cookie first (more secure)
        if self.config.use_httponly_cookies:
            token = request.cookies.get("access_token")
            if token:
                return token

        # Fallback to Authorization header (for mobile apps, etc.)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.replace("Bearer ", "")

        return None

    def create_csrf_token(self) -> str:
        """
        Create CSRF token

        Returns:
            CSRF token string
        """
        return secrets.token_urlsafe(32)

    def verify_csrf_token(
        self,
        request: Request,
        expected_token: Optional[str] = None
    ) -> bool:
        """
        Verify CSRF token from request

        Args:
            request: FastAPI request object
            expected_token: Expected CSRF token (from session/database)

        Returns:
            True if valid, False otherwise
        """
        if not self.config.csrf_protection:
            return True

        # Get CSRF token from header
        csrf_token = request.headers.get("X-CSRF-Token")

        if not csrf_token or not expected_token:
            return False

        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(csrf_token, expected_token)

    def get_device_fingerprint(self, request: Request) -> str:
        """
        Generate device fingerprint from request

        Args:
            request: FastAPI request object

        Returns:
            Device fingerprint hash
        """
        # Combine multiple request attributes for fingerprint
        fingerprint_data = [
            request.headers.get("user-agent", ""),
            request.headers.get("accept-language", ""),
            request.headers.get("accept-encoding", ""),
            request.client.host if request.client else ""
        ]

        fingerprint_string = "|".join(fingerprint_data)

        # Hash the fingerprint for storage
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()

    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        payload = self.verify_token(refresh_token, token_type="refresh")

        user_id = int(payload["sub"])

        # TODO: Check if refresh token is revoked in database

        # Create new token pair
        # Note: Would need user email, so might need database lookup
        # For now, just create new access token
        # In production, you'd query the database for user details

        raise NotImplementedError(
            "Refresh token requires database integration for user lookup"
        )


# Example usage functions


def create_auth_manager(jwt_secret: str) -> EnhancedAuthManager:
    """Create enhanced auth manager with default config"""
    config = AuthConfig(jwt_secret=jwt_secret)
    return EnhancedAuthManager(config)


# Dependency for FastAPI routes
async def get_current_user_enhanced(
    request: Request,
    auth_manager: EnhancedAuthManager
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user

    Args:
        request: FastAPI request
        auth_manager: EnhancedAuthManager instance

    Returns:
        User data from token

    Raises:
        HTTPException: If not authenticated
    """
    token = auth_manager.get_token_from_request(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    payload = auth_manager.verify_token(token)

    return {
        "user_id": int(payload["sub"]),
        "email": payload["email"]
    }
