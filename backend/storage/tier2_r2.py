"""
TIER 2: Cloudflare R2 (HOT Storage)
Stockage cloud pour drafts actifs non publiés (< 90 jours)
"""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
from loguru import logger


class CloudflareR2Storage:
    """
    Cloudflare R2 (compatible S3)
    HOT storage pour drafts actifs

    Coût: $0.015/GB/mois
    Bande passante: GRATUITE (0$ egress)

    Utilisé pour:
    - Drafts non publiés
    - Photos accédées fréquemment
    - Storage < 90 jours
    """

    def __init__(self):
        """
        Initialize Cloudflare R2 client

        Env vars required:
        - R2_ENDPOINT_URL
        - R2_ACCESS_KEY_ID
        - R2_SECRET_ACCESS_KEY
        - R2_BUCKET_NAME
        - R2_CDN_DOMAIN (optional, for CDN URLs)
        """
        endpoint_url = os.getenv('R2_ENDPOINT_URL')
        access_key = os.getenv('R2_ACCESS_KEY_ID')
        secret_key = os.getenv('R2_SECRET_ACCESS_KEY')

        if not all([endpoint_url, access_key, secret_key]):
            logger.warning("[WARN] R2 credentials not configured, R2 storage will not work")
            self.client = None
            return

        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )

        self.bucket_name = os.getenv('R2_BUCKET_NAME', 'vintedbot-photos')
        self.cdn_domain = os.getenv('R2_CDN_DOMAIN')  # Ex: photos.vintedbot.app
        self.public_url = os.getenv('R2_PUBLIC_URL')  # Fallback

        logger.info(f"[OK] CloudflareR2Storage initialized (bucket: {self.bucket_name})")

    async def upload(self, photo_id: str, data: bytes):
        """
        Upload photo to R2

        Args:
            photo_id: Unique photo identifier
            data: Binary photo data
        """
        if not self.client:
            raise RuntimeError("R2 client not initialized")

        key = f"hot/{photo_id}.jpg"

        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                ContentType='image/jpeg',
                CacheControl='public, max-age=31536000',  # 1 an cache
                Metadata={
                    'photo_id': photo_id,
                    'tier': 'hot'
                }
            )

            logger.debug(f"☁️ Uploaded to R2: {key} ({len(data)} bytes)")

        except ClientError as e:
            logger.error(f"[ERROR] R2 upload failed: {e}")
            raise

    async def download(self, photo_id: str) -> bytes:
        """
        Download photo from R2

        Args:
            photo_id: Unique photo identifier

        Returns:
            Binary photo data
        """
        if not self.client:
            raise RuntimeError("R2 client not initialized")

        key = f"hot/{photo_id}.jpg"

        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )

            data = response['Body'].read()

            logger.debug(f"☁️ Downloaded from R2: {key} ({len(data)} bytes)")

            return data

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"Photo {photo_id} not found in R2")
            else:
                logger.error(f"[ERROR] R2 download failed: {e}")
                raise

    async def delete(self, photo_id: str):
        """
        Delete photo from R2

        Args:
            photo_id: Unique photo identifier
        """
        if not self.client:
            raise RuntimeError("R2 client not initialized")

        key = f"hot/{photo_id}.jpg"

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )

            logger.debug(f"🗑️ Deleted from R2: {key}")

        except ClientError as e:
            logger.error(f"[ERROR] R2 delete failed: {e}")
            raise

    async def get_cdn_url(self, photo_id: str) -> str:
        """
        Get CDN URL for photo

        Args:
            photo_id: Unique photo identifier

        Returns:
            Public CDN URL
        """
        if self.cdn_domain:
            # Custom CDN domain (recommandé)
            return f"https://{self.cdn_domain}/hot/{photo_id}.jpg"
        elif self.public_url:
            # R2 public URL (fallback)
            return f"{self.public_url}/hot/{photo_id}.jpg"
        else:
            # Generate presigned URL (last resort, expires in 1h)
            return await self.get_presigned_url(photo_id)

    async def get_presigned_url(self, photo_id: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for temporary access

        Args:
            photo_id: Unique photo identifier
            expiration: URL expiration in seconds (default 1h)

        Returns:
            Presigned URL
        """
        if not self.client:
            raise RuntimeError("R2 client not initialized")

        key = f"hot/{photo_id}.jpg"

        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )

            return url

        except ClientError as e:
            logger.error(f"[ERROR] Failed to generate presigned URL: {e}")
            raise

    async def exists(self, photo_id: str) -> bool:
        """
        Check if photo exists in R2

        Args:
            photo_id: Unique photo identifier

        Returns:
            True if exists, False otherwise
        """
        if not self.client:
            return False

        key = f"hot/{photo_id}.jpg"

        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except ClientError:
            return False

    async def get_size(self, photo_id: str) -> int:
        """
        Get size of photo in bytes

        Args:
            photo_id: Unique photo identifier

        Returns:
            Size in bytes
        """
        if not self.client:
            return 0

        key = f"hot/{photo_id}.jpg"

        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['ContentLength']
        except ClientError:
            return 0
