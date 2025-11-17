import sys
import os
import json
from loguru import logger
import uuid

# Remove default handler
logger.remove()

# SECURITY FIX Bug #62: Structured logging for production
ENV = os.getenv("ENV", "development")
IS_PRODUCTION = ENV == "production"

# JSON serializer for structured logging
def serialize_record(record):
    """
    Serialize log record to JSON format for production

    Structured fields:
    - timestamp: ISO 8601 format
    - level: Log level (INFO, ERROR, etc.)
    - logger: Logger name
    - function: Function name
    - line: Line number
    - message: Log message
    - extra: Any additional context
    """
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "logger": record["name"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
    }

    # Add extra fields if present
    if record["extra"]:
        subset["extra"] = record["extra"]

    # Add exception info if present
    if record["exception"]:
        subset["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback
        }

    return json.dumps(subset)

def patching(record):
    """Format JSON logs with newline"""
    record["extra"]["serialized"] = serialize_record(record)

# Configure logger based on environment
if IS_PRODUCTION:
    # Production: JSON structured logging for parsing by log aggregators
    logger = logger.patch(patching)
    logger.add(
        sys.stdout,
        format="{extra[serialized]}",
        level="INFO",
        colorize=False,  # No colors in production logs
        serialize=False  # We handle serialization manually
    )

    # Production file logs (JSON)
    logger.add(
        "backend/data/app.log",
        rotation="100 MB",  # Larger rotation for production
        retention="30 days",  # Keep logs longer in production
        format="{extra[serialized]}",
        level="INFO",  # INFO level in production
        compression="gz",  # Compress old logs
        serialize=False
    )
else:
    # Development: Human-readable colored logs
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        level="DEBUG",  # DEBUG level in development
        colorize=True
    )

    # Development file logs (human-readable)
    logger.add(
        "backend/data/app.log",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
        level="DEBUG"
    )


def get_request_id() -> str:
    """Generate unique request ID"""
    return str(uuid.uuid4())[:8]


def sanitize_headers(headers: dict) -> dict:
    """
    SECURITY FIX Bug #15: Remove sensitive data from headers before logging

    Filters out:
    - Authorization tokens
    - Cookies
    - API keys
    - Session tokens
    - CSRF tokens
    """
    SENSITIVE_HEADERS = {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "x-session-token",
        "x-csrf-token",
        "api-key",
        "auth-token",
        "session-token",
        "csrf-token",
        "access-token",
        "refresh-token",
    }

    sanitized = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if key_lower in SENSITIVE_HEADERS:
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value

    return sanitized


def log_request(method: str, path: str, status_code: int, duration_ms: float, request_id: str):
    """Log HTTP request with details"""
    logger.info(
        f"[{request_id}] {method} {path} - {status_code} ({duration_ms:.2f}ms)"
    )
