import re
from typing import Optional
from urllib.parse import urlparse

ALLOWED_FILE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_FILE_SIZE_MB = 10


def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def is_valid_file_extension(filename: str) -> bool:
    """Validate file extension"""
    ext = get_file_extension(filename)
    return ext.lower() in ALLOWED_FILE_EXTENSIONS


def get_file_extension(filename: str) -> str:
    """Get file extension from filename"""
    return '.' + filename.rsplit('.', 1)[-1] if '.' in filename else ''


def validate_file_size(size_bytes: int) -> bool:
    """Validate file size (max 10MB)"""
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    return size_bytes <= max_bytes


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove any path components
    filename = filename.split('/')[-1].split('\\')[-1]
    # Remove special characters except dots and dashes
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename
