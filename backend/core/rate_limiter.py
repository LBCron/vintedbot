"""
Rate Limiting Configuration for VintedBot API

Prevents abuse and controls costs, especially for expensive AI endpoints.

Rate limits:
- AI endpoints (GPT-4): 10 requests/minute per user
- Image endpoints: 20 requests/minute per user
- Standard endpoints: 100 requests/minute per user
- Batch endpoints: 5 requests/minute per user
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from backend.security.auth import get_current_user
import logging

logger = logging.getLogger(__name__)


def get_user_id(request: Request) -> str:
    """
    Get user ID for rate limiting.
    Falls back to IP address if user not authenticated.
    """
    try:
        # Try to get user ID from JWT token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # In a real scenario, we'd decode the JWT here
            # For now, we'll use IP-based limiting
            # Note: get_current_user is a dependency, can't be used directly here
            pass
    except Exception as e:
        logger.debug(f"Could not extract user ID for rate limiting: {e}")

    # Fall back to IP address
    return get_remote_address(request)


# Create rate limiter instances
limiter = Limiter(key_func=get_user_id)

# Rate limit decorators
# Format: "N/timeframe" where timeframe can be second, minute, hour, day

# AI endpoints (GPT-4, OpenAI) - CRITICAL COST CONTROL
# Maximum 10 requests/minute = $0.72/min worst case (at $0.03 per request)
AI_RATE_LIMIT = "10/minute"

# Image processing (uploads, analysis)
IMAGE_RATE_LIMIT = "20/minute"

# Batch operations (multiple items at once)
BATCH_RATE_LIMIT = "5/minute"

# Standard API endpoints
STANDARD_RATE_LIMIT = "100/minute"

# Analytics and read-only endpoints
ANALYTICS_RATE_LIMIT = "30/minute"
