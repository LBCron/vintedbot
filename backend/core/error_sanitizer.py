"""
Error Message Sanitization

Prevents information leakage in production error responses.

Critical for security:
- Hide database connection strings
- Hide file paths
- Hide API keys
- Hide internal stack traces
- Hide dependency versions
"""
import re
import logging
from typing import Any, Dict
import os

logger = logging.getLogger(__name__)


class ErrorSanitizer:
    """Sanitize error messages to prevent information disclosure"""

    # Patterns to remove from error messages
    SENSITIVE_PATTERNS = [
        # Database connection strings
        (r'postgresql://[^\s]+', '[DATABASE_URL]'),
        (r'postgres://[^\s]+', '[DATABASE_URL]'),
        (r'mysql://[^\s]+', '[DATABASE_URL]'),

        # API Keys
        (r'sk-[a-zA-Z0-9]{20,}', '[OPENAI_API_KEY]'),
        (r'sk-ant-[a-zA-Z0-9]{20,}', '[ANTHROPIC_API_KEY]'),
        (r'Bearer [a-zA-Z0-9\-_\.]+', 'Bearer [TOKEN]'),

        # File paths (both Unix and Windows)
        (r'/home/[^\s]+', '[PATH]'),
        (r'/usr/[^\s]+', '[PATH]'),
        (r'/var/[^\s]+', '[PATH]'),
        (r'/opt/[^\s]+', '[PATH]'),
        (r'C:\\[^\s]+', '[PATH]'),
        (r'/backend/[^\s]+\.py', '[FILE]'),

        # Email addresses
        (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]'),

        # IP addresses
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),

        # Passwords in connection strings
        (r':([^:@/]+)@', ':[PASSWORD]@'),
    ]

    @classmethod
    def sanitize(cls, error_message: str, is_production: bool = None) -> str:
        """
        Sanitize error message for safe public display

        Args:
            error_message: Original error message
            is_production: Force production mode (defaults to ENV check)

        Returns:
            Sanitized error message
        """
        if is_production is None:
            is_production = os.getenv("ENV", "development") == "production"

        if not is_production:
            # In development, show full errors for debugging
            return error_message

        # Apply all sanitization patterns
        sanitized = error_message
        for pattern, replacement in cls.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized

    @classmethod
    def sanitize_exception(cls, exception: Exception, is_production: bool = None) -> Dict[str, Any]:
        """
        Convert exception to safe error response

        Args:
            exception: The caught exception
            is_production: Force production mode

        Returns:
            Dictionary with safe error details
        """
        if is_production is None:
            is_production = os.getenv("ENV", "development") == "production"

        error_type = type(exception).__name__
        error_message = str(exception)

        if is_production:
            # Generic message for production
            safe_response = {
                "error": "An error occurred while processing your request",
                "error_type": error_type,
                "error_id": None,  # Could add Sentry error ID here
            }

            # Log full error internally
            logger.error(f"Error: {error_type}: {error_message}", exc_info=True)
        else:
            # Detailed message for development
            safe_response = {
                "error": cls.sanitize(error_message, is_production=False),
                "error_type": error_type,
                "traceback": None,  # Could add traceback in dev if needed
            }

        return safe_response


def get_safe_error_response(
    exception: Exception,
    default_message: str = "An error occurred",
    status_code: int = 500,
) -> Dict[str, Any]:
    """
    Get sanitized error response for API endpoints

    Usage:
        try:
            # ... code ...
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=get_safe_error_response(e)
            )
    """
    is_production = os.getenv("ENV", "development") == "production"

    if is_production:
        return {
            "success": False,
            "error": default_message,
            "error_type": type(exception).__name__,
        }
    else:
        return {
            "success": False,
            "error": ErrorSanitizer.sanitize(str(exception), is_production=False),
            "error_type": type(exception).__name__,
        }
