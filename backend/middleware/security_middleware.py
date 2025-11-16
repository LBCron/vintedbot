"""
GLOBAL SECURITY MIDDLEWARE
Protects against common attacks and enforces security policies
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import re
from backend.core.redis_client import cache
from backend.utils.logger import logger


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Global security middleware that protects against:
    - SQL injection
    - XSS attacks
    - Path traversal
    - Excessive requests
    - Malicious user agents
    """

    # Malicious patterns to detect
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(';?\s*drop\b)",
        r"(\bor\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+)",
        r"(\band\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+)",
        r"(--\s*$)",
        r"(/\*.*\*/)",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
        r"\.\.\\",
    ]

    XSS_PATTERNS = [
        r"<script[\s\S]*?>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"<iframe",
    ]

    # Malicious user agents
    BLOCKED_USER_AGENTS = [
        "sqlmap",
        "nikto",
        "nmap",
        "masscan",
        "metasploit",
        "burpsuite",
    ]

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request through security checks"""

        # 1. Global rate limiting
        try:
            await self._check_global_rate_limit(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail}
            )

        # 2. Validate user agent
        try:
            self._validate_user_agent(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail}
            )

        # 3. Check for attack patterns
        try:
            self._check_attack_patterns(request)
        except HTTPException as e:
            logger.warning(
                f"⚠️ Attack detected from {request.client.host}: {e.detail}"
            )
            return JSONResponse(
                status_code=e.status_code,
                content={"error": "Malicious request detected"}
            )

        # 4. Validate request size
        try:
            await self._validate_request_size(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail}
            )

        # Process request
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Process-Time"] = str(process_time)

        return response

    async def _check_global_rate_limit(self, request: Request) -> None:
        """
        Global rate limit: max 1000 requests per minute per IP

        Raises:
            HTTPException(429) if limit exceeded
        """
        if not request.client:
            return

        ip = request.client.host
        key = f"rate_limit:global:{ip}"

        # Get current count
        count = await cache.get(key, default=0)

        if count >= 1000:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down."
            )

        # Increment counter
        await cache.set(key, count + 1, ttl=60)

    def _validate_user_agent(self, request: Request) -> None:
        """
        Validate user agent is not malicious

        Raises:
            HTTPException(403) if malicious user agent detected
        """
        user_agent = request.headers.get("User-Agent", "").lower()

        # Block empty user agents
        if not user_agent:
            raise HTTPException(
                status_code=403,
                detail="Missing User-Agent header"
            )

        # Block known malicious user agents
        for blocked_agent in self.BLOCKED_USER_AGENTS:
            if blocked_agent in user_agent:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied"
                )

    def _check_attack_patterns(self, request: Request) -> None:
        """
        Check for common attack patterns in URL and query params

        Raises:
            HTTPException(400) if attack pattern detected
        """
        # Get full URL with query params
        url = str(request.url)
        query_params = str(request.url.query)

        # Check for SQL injection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request"
                )

        # Check for path traversal
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid path"
                )

        # Check for XSS
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, query_params, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid input"
                )

    async def _validate_request_size(self, request: Request) -> None:
        """
        Validate request size is not excessive

        Raises:
            HTTPException(413) if request too large
        """
        content_length = request.headers.get("Content-Length")

        if content_length:
            size_mb = int(content_length) / (1024 * 1024)

            # Max 100MB per request
            if size_mb > 100:
                raise HTTPException(
                    status_code=413,
                    detail="Request too large (max 100MB)"
                )
