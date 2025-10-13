import os
import io
import hashlib
from typing import Tuple
import filetype
from PIL import Image, ImageOps
from backend.settings import settings


def _ensure_dirs():
    """Ensure media storage directory exists."""
    if settings.MEDIA_STORAGE == "local":
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)


def sniff_mime(data: bytes) -> str:
    """Detect MIME type using file magic bytes."""
    kind = filetype.guess(data)
    return kind.mime if kind else "application/octet-stream"


def check_size_limit(data: bytes):
    """Check if file size is within allowed limits."""
    mb = len(data) / (1024 * 1024)
    if mb > settings.MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {mb:.1f} MB > {settings.MAX_FILE_SIZE_MB} MB")


def is_allowed_mime(mime: str) -> bool:
    """Check if MIME type is allowed based on prefix matching."""
    return any(mime.startswith(p) for p in settings.ALLOWED_MIME_PREFIXES)


def process_image(data: bytes) -> Tuple[bytes, int, int, str]:
    """
    Process image with the following steps:
    1. Fix orientation based on EXIF data
    2. Convert to RGB
    3. Resize to MAX_DIM_PX if needed
    4. Encode as JPEG with quality settings
    5. Strip EXIF data (including GPS)
    
    Returns: (processed_bytes, width, height, mime_type)
    """
    img = Image.open(io.BytesIO(data))
    
    # Fix orientation using EXIF transpose
    img = ImageOps.exif_transpose(img)
    
    # Convert to RGB (removes alpha channel and ensures JPEG compatibility)
    img = img.convert("RGB")
    
    # Resize if needed
    w, h = img.size
    max_dim = settings.MAX_DIM_PX
    if max(w, h) > max_dim:
        if w >= h:
            nh = int(h * (max_dim / w))
            img = img.resize((max_dim, nh), Image.LANCZOS)
            w, h = max_dim, nh
        else:
            nw = int(w * (max_dim / h))
            img = img.resize((nw, max_dim), Image.LANCZOS)
            w, h = nw, max_dim
    
    # Export as JPEG without EXIF data
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=settings.JPEG_QUALITY, optimize=True)
    
    return out.getvalue(), w, h, "image/jpeg"


def sha256_of(data: bytes) -> str:
    """Calculate SHA256 hash of data."""
    return hashlib.sha256(data).hexdigest()


def store_local(data: bytes, sha: str) -> str:
    """
    Store file locally and return URL.
    Files are stored as <sha256>.jpg for idempotency.
    """
    _ensure_dirs()
    fname = f"{sha}.jpg"
    path = os.path.join(settings.MEDIA_ROOT, fname)
    
    # Only write if file doesn't exist (idempotent)
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(data)
    
    return f"{settings.MEDIA_BASE_URL}/{fname}"


def store_s3(data: bytes, sha: str) -> str:
    """
    Store file in S3-compatible storage (MinIO, Wasabi, AWS S3).
    TODO: Implement S3 storage when needed.
    """
    raise NotImplementedError("S3 storage not yet implemented. Use MEDIA_STORAGE=local")
