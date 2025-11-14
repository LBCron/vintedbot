"""
TIER 3: Backblaze B2 (COLD Storage)
Stockage archive pour photos rarement accédées (> 90 jours)
"""
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from b2sdk.v2.exception import NonExistentBucket, FileNotPresent
import os
from loguru import logger


class BackblazeB2Storage:
    """
    Backblaze B2
    COLD storage pour archives

    Coût: $0.006/GB/mois (60% moins cher que R2)
    Egress: $0.01/GB (après 3x storage gratuit)

    Utilisé pour:
    - Photos > 90 jours sans accès
    - Archives long terme
    - Backup
    """

    def __init__(self):
        """
        Initialize Backblaze B2 client

        Env vars required:
        - B2_APPLICATION_KEY_ID
        - B2_APPLICATION_KEY
        - B2_BUCKET_NAME
        """
        key_id = os.getenv('B2_APPLICATION_KEY_ID')
        app_key = os.getenv('B2_APPLICATION_KEY')

        if not all([key_id, app_key]):
            logger.warning("⚠️ B2 credentials not configured, B2 storage will not work")
            self.b2_api = None
            self.bucket = None
            return

        try:
            info = InMemoryAccountInfo()
            self.b2_api = B2Api(info)

            self.b2_api.authorize_account(
                'production',
                key_id,
                app_key
            )

            bucket_name = os.getenv('B2_BUCKET_NAME', 'vintedbot-archive')
            self.bucket = self.b2_api.get_bucket_by_name(bucket_name)

            logger.info(f"✅ BackblazeB2Storage initialized (bucket: {bucket_name})")

        except Exception as e:
            logger.error(f"❌ Failed to initialize B2: {e}")
            self.b2_api = None
            self.bucket = None

    async def upload(self, photo_id: str, data: bytes):
        """
        Upload photo to B2

        Args:
            photo_id: Unique photo identifier
            data: Binary photo data
        """
        if not self.bucket:
            raise RuntimeError("B2 bucket not initialized")

        file_name = f"cold/{photo_id}.jpg"

        try:
            self.bucket.upload_bytes(
                data,
                file_name,
                content_type='image/jpeg',
                file_infos={
                    'photo_id': photo_id,
                    'tier': 'cold'
                }
            )

            logger.debug(f"❄️ Uploaded to B2: {file_name} ({len(data)} bytes)")

        except Exception as e:
            logger.error(f"❌ B2 upload failed: {e}")
            raise

    async def download(self, photo_id: str) -> bytes:
        """
        Download photo from B2

        Args:
            photo_id: Unique photo identifier

        Returns:
            Binary photo data
        """
        if not self.bucket:
            raise RuntimeError("B2 bucket not initialized")

        file_name = f"cold/{photo_id}.jpg"

        try:
            downloaded_file = self.bucket.download_file_by_name(file_name)

            # Read file content
            import io
            buffer = io.BytesIO()
            downloaded_file.save(buffer)
            data = buffer.getvalue()

            logger.debug(f"❄️ Downloaded from B2: {file_name} ({len(data)} bytes)")

            return data

        except FileNotPresent:
            raise FileNotFoundError(f"Photo {photo_id} not found in B2")
        except Exception as e:
            logger.error(f"❌ B2 download failed: {e}")
            raise

    async def delete(self, photo_id: str):
        """
        Delete photo from B2

        Args:
            photo_id: Unique photo identifier
        """
        if not self.bucket:
            raise RuntimeError("B2 bucket not initialized")

        file_name = f"cold/{photo_id}.jpg"

        try:
            # Get file info first
            file_version = self.bucket.get_file_info_by_name(file_name)

            # Delete file version
            self.b2_api.delete_file_version(
                file_version.id_,
                file_name
            )

            logger.debug(f"🗑️ Deleted from B2: {file_name}")

        except FileNotPresent:
            logger.warning(f"Photo {photo_id} not found in B2 for deletion")
        except Exception as e:
            logger.error(f"❌ B2 delete failed: {e}")
            raise

    async def get_url(self, photo_id: str) -> str:
        """
        Get download URL for photo

        Note: B2 URLs require authorization, so we generate a download URL
        that includes temporary auth

        Args:
            photo_id: Unique photo identifier

        Returns:
            Download URL
        """
        if not self.bucket:
            raise RuntimeError("B2 bucket not initialized")

        file_name = f"cold/{photo_id}.jpg"

        try:
            # Get download URL (includes auth)
            download_url = self.bucket.get_download_url(file_name)

            return download_url

        except Exception as e:
            logger.error(f"❌ Failed to get B2 URL: {e}")
            raise

    async def exists(self, photo_id: str) -> bool:
        """
        Check if photo exists in B2

        Args:
            photo_id: Unique photo identifier

        Returns:
            True if exists, False otherwise
        """
        if not self.bucket:
            return False

        file_name = f"cold/{photo_id}.jpg"

        try:
            self.bucket.get_file_info_by_name(file_name)
            return True
        except FileNotPresent:
            return False
        except Exception:
            return False

    async def get_size(self, photo_id: str) -> int:
        """
        Get size of photo in bytes

        Args:
            photo_id: Unique photo identifier

        Returns:
            Size in bytes
        """
        if not self.bucket:
            return 0

        file_name = f"cold/{photo_id}.jpg"

        try:
            file_info = self.bucket.get_file_info_by_name(file_name)
            return file_info.size
        except FileNotPresent:
            return 0
        except Exception:
            return 0
