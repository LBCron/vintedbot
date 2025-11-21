"""
S3/MinIO Storage Service for Photo Management
Production-ready with automatic fallback to local storage
"""
import os
import uuid
from typing import Optional, BinaryIO
from pathlib import Path
from datetime import datetime, timedelta
import aioboto3
from botocore.exceptions import ClientError
from backend.utils.logger import logger

# S3 Configuration
S3_ENDPOINT = os.getenv("S3_ENDPOINT")  # e.g., http://minio:9000 or https://s3.amazonaws.com
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_BUCKET = os.getenv("S3_BUCKET", "vintedbots-photos")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL")  # Optional: CDN URL

# Local fallback
LOCAL_STORAGE_PATH = Path(os.getenv("LOCAL_STORAGE_PATH", "backend/data/photos"))
LOCAL_STORAGE_PATH.mkdir(parents=True, exist_ok=True)

# Storage mode
STORAGE_MODE = "s3" if S3_ENDPOINT and S3_ACCESS_KEY and S3_SECRET_KEY else "local"


class S3StorageService:
    """
    S3-compatible storage service with automatic local fallback

    Supports:
    - AWS S3
    - MinIO (self-hosted S3-compatible)
    - DigitalOcean Spaces
    - Backblaze B2
    - Any S3-compatible service
    """

    def __init__(self):
        self.mode = STORAGE_MODE
        self.bucket = S3_BUCKET
        self.session = None

        if self.mode == "s3":
            logger.info(f"[PACKAGE] S3 Storage: endpoint={S3_ENDPOINT}, bucket={S3_BUCKET}")
        else:
            logger.info(f"💾 Local Storage: path={LOCAL_STORAGE_PATH}")

    def _get_session(self):
        """Get aioboto3 session (lazy initialization)"""
        if self.session is None and self.mode == "s3":
            self.session = aioboto3.Session(
                aws_access_key_id=S3_ACCESS_KEY,
                aws_secret_access_key=S3_SECRET_KEY,
                region_name=S3_REGION
            )
        return self.session

    async def _ensure_bucket_exists(self, client):
        """Ensure S3 bucket exists, create if not"""
        try:
            await client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                # Bucket doesn't exist, create it
                try:
                    await client.create_bucket(Bucket=self.bucket)
                    logger.info(f"[OK] Created S3 bucket: {self.bucket}")
                except ClientError as create_error:
                    logger.error(f"[ERROR] Failed to create bucket: {create_error}")
                    raise
            else:
                raise

    async def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to S3 or local storage

        Args:
            file_path: Local file path to upload
            object_name: S3 object name (defaults to unique UUID)
            content_type: MIME type (auto-detected if not provided)

        Returns:
            Public URL or local path to uploaded file
        """
        if object_name is None:
            # Generate unique object name
            ext = Path(file_path).suffix
            object_name = f"{uuid.uuid4()}{ext}"

        # Auto-detect content type
        if content_type is None:
            ext = Path(file_path).suffix.lower()
            content_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.heic': 'image/heic',
            }
            content_type = content_types.get(ext, 'application/octet-stream')

        try:
            if self.mode == "s3":
                return await self._upload_to_s3(file_path, object_name, content_type)
            else:
                return await self._upload_to_local(file_path, object_name)

        except Exception as e:
            logger.error(f"[ERROR] Upload failed: {e}")
            # Fallback to local storage
            if self.mode == "s3":
                logger.warning("[WARN] Falling back to local storage")
                return await self._upload_to_local(file_path, object_name)
            raise

    async def _upload_to_s3(self, file_path: str, object_name: str, content_type: str) -> str:
        """Upload file to S3"""
        session = self._get_session()

        async with session.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            region_name=S3_REGION
        ) as s3_client:
            # Ensure bucket exists
            await self._ensure_bucket_exists(s3_client)

            # Upload file
            with open(file_path, 'rb') as f:
                await s3_client.upload_fileobj(
                    f,
                    self.bucket,
                    object_name,
                    ExtraArgs={
                        'ContentType': content_type,
                        'ACL': 'public-read'  # Make publicly accessible
                    }
                )

            # Generate public URL
            if S3_PUBLIC_URL:
                url = f"{S3_PUBLIC_URL}/{object_name}"
            else:
                url = f"{S3_ENDPOINT}/{self.bucket}/{object_name}"

            logger.info(f"[OK] Uploaded to S3: {object_name}")
            return url

    async def _upload_to_local(self, file_path: str, object_name: str) -> str:
        """Upload file to local storage"""
        dest_path = LOCAL_STORAGE_PATH / object_name

        # Create subdirectories if object_name contains slashes
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        import shutil
        shutil.copy2(file_path, dest_path)

        # Return relative URL
        url = f"/photos/{object_name}"
        logger.info(f"[OK] Saved locally: {object_name}")
        return url

    async def upload_bytes(
        self,
        file_data: bytes,
        object_name: Optional[str] = None,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload bytes directly to storage

        Args:
            file_data: File content as bytes
            object_name: S3 object name (defaults to unique UUID)
            content_type: MIME type

        Returns:
            Public URL or local path
        """
        if object_name is None:
            object_name = f"{uuid.uuid4()}.bin"

        try:
            if self.mode == "s3":
                return await self._upload_bytes_to_s3(file_data, object_name, content_type)
            else:
                return await self._upload_bytes_to_local(file_data, object_name)

        except Exception as e:
            logger.error(f"[ERROR] Upload bytes failed: {e}")
            if self.mode == "s3":
                logger.warning("[WARN] Falling back to local storage")
                return await self._upload_bytes_to_local(file_data, object_name)
            raise

    async def _upload_bytes_to_s3(self, file_data: bytes, object_name: str, content_type: str) -> str:
        """Upload bytes to S3"""
        session = self._get_session()

        async with session.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            region_name=S3_REGION
        ) as s3_client:
            await self._ensure_bucket_exists(s3_client)

            await s3_client.put_object(
                Bucket=self.bucket,
                Key=object_name,
                Body=file_data,
                ContentType=content_type,
                ACL='public-read'
            )

            if S3_PUBLIC_URL:
                url = f"{S3_PUBLIC_URL}/{object_name}"
            else:
                url = f"{S3_ENDPOINT}/{self.bucket}/{object_name}"

            return url

    async def _upload_bytes_to_local(self, file_data: bytes, object_name: str) -> str:
        """Upload bytes to local storage"""
        dest_path = LOCAL_STORAGE_PATH / object_name
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        with open(dest_path, 'wb') as f:
            f.write(file_data)

        return f"/photos/{object_name}"

    async def delete_file(self, object_name: str) -> bool:
        """
        Delete file from storage

        Args:
            object_name: Object name to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.mode == "s3":
                return await self._delete_from_s3(object_name)
            else:
                return await self._delete_from_local(object_name)

        except Exception as e:
            logger.error(f"[ERROR] Delete failed for {object_name}: {e}")
            return False

    async def _delete_from_s3(self, object_name: str) -> bool:
        """Delete file from S3"""
        session = self._get_session()

        async with session.client(
            's3',
            endpoint_url=S3_ENDPOINT,
            region_name=S3_REGION
        ) as s3_client:
            await s3_client.delete_object(Bucket=self.bucket, Key=object_name)
            logger.info(f"🗑️ Deleted from S3: {object_name}")
            return True

    async def _delete_from_local(self, object_name: str) -> bool:
        """Delete file from local storage"""
        file_path = LOCAL_STORAGE_PATH / object_name
        if file_path.exists():
            file_path.unlink()
            logger.info(f"🗑️ Deleted locally: {object_name}")
            return True
        return False

    async def generate_presigned_url(
        self,
        object_name: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary access (S3 only)

        Args:
            object_name: Object name
            expiration: URL expiration in seconds (default: 1 hour)

        Returns:
            Presigned URL or None if local storage
        """
        if self.mode != "s3":
            return f"/photos/{object_name}"  # Local files are always accessible

        try:
            session = self._get_session()

            async with session.client(
                's3',
                endpoint_url=S3_ENDPOINT,
                region_name=S3_REGION
            ) as s3_client:
                url = await s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': object_name},
                    ExpiresIn=expiration
                )
                return url

        except Exception as e:
            logger.error(f"[ERROR] Failed to generate presigned URL: {e}")
            return None


# Global storage instance
storage = S3StorageService()


# Health check
async def check_storage_health() -> dict:
    """Check storage service health"""
    try:
        if storage.mode == "s3":
            session = storage._get_session()

            async with session.client(
                's3',
                endpoint_url=S3_ENDPOINT,
                region_name=S3_REGION
            ) as s3_client:
                # Try to list buckets
                await s3_client.list_buckets()

                return {
                    "status": "healthy",
                    "mode": "s3",
                    "endpoint": S3_ENDPOINT,
                    "bucket": S3_BUCKET
                }
        else:
            # Check local storage
            if LOCAL_STORAGE_PATH.exists():
                return {
                    "status": "healthy",
                    "mode": "local",
                    "path": str(LOCAL_STORAGE_PATH)
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Local storage path does not exist"
                }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
