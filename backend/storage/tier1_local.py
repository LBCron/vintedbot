"""
TIER 1: Local Storage (Fly.io Volumes)
Stockage temporaire gratuit pour photos en attente (24-48h)
"""
import os
from pathlib import Path
from loguru import logger


class LocalStorage:
    """
    Stockage local sur Fly.io Volumes

    - GRATUIT (inclus dans Fly.io)
    - Rapide (même machine)
    - Temporaire (24-48h)
    - Utilisé pour photos en attente d'analyse IA

    Path: /app/backend/data/photos/temp/
    """

    def __init__(self, base_path: str = "/app/backend/data/photos/temp"):
        """
        Initialize local storage

        Args:
            base_path: Base directory for temp photos
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"[OK] LocalStorage initialized at {self.base_path}")

    async def upload(self, photo_id: str, data: bytes):
        """
        Upload photo to local storage

        Args:
            photo_id: Unique photo identifier
            data: Binary photo data
        """
        file_path = self.base_path / f"{photo_id}.jpg"

        # Write to disk
        file_path.write_bytes(data)

        logger.debug(f"📁 Saved to local: {file_path} ({len(data)} bytes)")

    async def download(self, photo_id: str) -> bytes:
        """
        Download photo from local storage

        Args:
            photo_id: Unique photo identifier

        Returns:
            Binary photo data
        """
        file_path = self.base_path / f"{photo_id}.jpg"

        if not file_path.exists():
            raise FileNotFoundError(f"Photo {photo_id} not found in local storage")

        data = file_path.read_bytes()

        logger.debug(f"📁 Loaded from local: {file_path} ({len(data)} bytes)")

        return data

    async def delete(self, photo_id: str):
        """
        Delete photo from local storage

        Args:
            photo_id: Unique photo identifier
        """
        file_path = self.base_path / f"{photo_id}.jpg"

        if file_path.exists():
            file_path.unlink()
            logger.debug(f"🗑️ Deleted from local: {file_path}")
        else:
            logger.warning(f"Photo {photo_id} not found for deletion")

    async def get_url(self, photo_id: str) -> str:
        """
        Get URL for local photo

        Note: Pour TEMP tier, on retourne un endpoint API qui servira la photo
        car les fichiers locaux ne sont pas accessibles publiquement

        Args:
            photo_id: Unique photo identifier

        Returns:
            API endpoint URL
        """
        # TODO: Retourner URL de l'endpoint FastAPI qui servira la photo
        # Ex: https://vintedbot-backend.fly.dev/api/storage/photos/{photo_id}
        return f"/api/storage/photos/{photo_id}"

    async def exists(self, photo_id: str) -> bool:
        """
        Check if photo exists in local storage

        Args:
            photo_id: Unique photo identifier

        Returns:
            True if exists, False otherwise
        """
        file_path = self.base_path / f"{photo_id}.jpg"
        return file_path.exists()

    async def get_size(self, photo_id: str) -> int:
        """
        Get size of photo in bytes

        Args:
            photo_id: Unique photo identifier

        Returns:
            Size in bytes
        """
        file_path = self.base_path / f"{photo_id}.jpg"

        if not file_path.exists():
            return 0

        return file_path.stat().st_size

    async def list_all(self) -> list[str]:
        """
        List all photo IDs in local storage

        Returns:
            List of photo IDs
        """
        photos = []

        for file in self.base_path.glob("*.jpg"):
            photo_id = file.stem  # Filename without extension
            photos.append(photo_id)

        return photos

    async def get_total_size(self) -> int:
        """
        Get total size of all photos in bytes

        Returns:
            Total size in bytes
        """
        total = 0

        for file in self.base_path.glob("*.jpg"):
            total += file.stat().st_size

        return total
