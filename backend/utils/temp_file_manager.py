"""
SECURITY FIX Bug #17: Automatic temp file cleanup manager

Ensures temporary files are properly cleaned up to prevent disk space issues.
Provides context managers and automatic cleanup on application exit.
"""
import os
import atexit
import tempfile
import threading
from pathlib import Path
from typing import Optional, Set
from loguru import logger


class TempFileManager:
    """
    Manages temporary files with automatic cleanup

    Features:
    - Tracks all created temp files
    - Automatic cleanup on application exit
    - Thread-safe operations
    - Manual cleanup methods
    """

    def __init__(self):
        self._temp_files: Set[str] = set()
        self._lock = threading.Lock()
        # Register cleanup on exit
        atexit.register(self.cleanup_all)

    def create_temp_file(self, suffix: str = "", prefix: str = "tmp", dir: Optional[str] = None) -> str:
        """
        Create a temporary file that will be automatically cleaned up

        Args:
            suffix: File suffix (e.g., ".jpg")
            prefix: File prefix
            dir: Directory for temp file (None = system temp dir)

        Returns:
            Path to temporary file
        """
        temp = tempfile.NamedTemporaryFile(
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            delete=False
        )
        temp_path = temp.name
        temp.close()

        with self._lock:
            self._temp_files.add(temp_path)

        logger.debug(f"Created temp file: {temp_path}")
        return temp_path

    def register_temp_file(self, path: str):
        """
        Register an existing file for cleanup

        Useful when temp files are created manually
        """
        with self._lock:
            self._temp_files.add(path)
        logger.debug(f"Registered temp file for cleanup: {path}")

    def cleanup_file(self, path: str) -> bool:
        """
        Manually cleanup a specific temp file

        Returns:
            True if file was deleted, False otherwise
        """
        try:
            if os.path.exists(path):
                os.unlink(path)
                logger.debug(f"Cleaned up temp file: {path}")

            with self._lock:
                self._temp_files.discard(path)

            return True
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {path}: {e}")
            return False

    def cleanup_all(self):
        """
        Cleanup all tracked temporary files

        Called automatically on application exit
        """
        with self._lock:
            files_to_cleanup = list(self._temp_files)

        cleaned = 0
        failed = 0

        for temp_path in files_to_cleanup:
            if self.cleanup_file(temp_path):
                cleaned += 1
            else:
                failed += 1

        if cleaned > 0:
            logger.info(f"✅ Cleaned up {cleaned} temporary file(s)")
        if failed > 0:
            logger.warning(f"⚠️ Failed to cleanup {failed} temporary file(s)")

    def get_temp_count(self) -> int:
        """Get count of tracked temp files"""
        with self._lock:
            return len(self._temp_files)


# Global singleton instance
temp_file_manager = TempFileManager()


class TempFile:
    """
    Context manager for temporary files with automatic cleanup

    Usage:
        with TempFile(suffix=".jpg") as temp_path:
            # Use temp_path
            image.save(temp_path)
        # File is automatically deleted when context exits
    """

    def __init__(self, suffix: str = "", prefix: str = "tmp", dir: Optional[str] = None):
        self.suffix = suffix
        self.prefix = prefix
        self.dir = dir
        self.path: Optional[str] = None

    def __enter__(self) -> str:
        """Create temp file on context entry"""
        self.path = temp_file_manager.create_temp_file(
            suffix=self.suffix,
            prefix=self.prefix,
            dir=self.dir
        )
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup temp file on context exit"""
        if self.path:
            temp_file_manager.cleanup_file(self.path)


def cleanup_old_temp_files(directory: str, max_age_hours: int = 24):
    """
    Cleanup old temporary files in a directory

    Args:
        directory: Directory to clean
        max_age_hours: Max age of files to keep (default: 24 hours)
    """
    import time

    try:
        dir_path = Path(directory)
        if not dir_path.exists():
            return

        now = time.time()
        max_age_seconds = max_age_hours * 3600
        cleaned = 0

        for file_path in dir_path.glob("tmp*"):
            if not file_path.is_file():
                continue

            file_age = now - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    cleaned += 1
                except Exception as e:
                    logger.warning(f"Failed to cleanup old temp file {file_path}: {e}")

        if cleaned > 0:
            logger.info(f"✅ Cleaned up {cleaned} old temporary file(s) from {directory}")

    except Exception as e:
        logger.error(f"Error cleaning up old temp files: {e}")
