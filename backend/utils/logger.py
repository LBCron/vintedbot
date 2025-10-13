import sys
from loguru import logger
import uuid

# Remove default handler
logger.remove()

# Add custom handler with structured format
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    level="INFO",
    colorize=True
)

# Add file handler
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


def log_request(method: str, path: str, status_code: int, duration_ms: float, request_id: str):
    """Log HTTP request with details"""
    logger.info(
        f"[{request_id}] {method} {path} - {status_code} ({duration_ms:.2f}ms)"
    )
