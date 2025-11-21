"""
Storage Lifecycle Manager
Déplace automatiquement les photos entre tiers selon leur utilisation
Exécuté quotidiennement via cron job
"""
from datetime import datetime, timedelta
from typing import List
from loguru import logger

from .storage_manager import StorageManager, StorageTier, PhotoMetadata


class StorageLifecycleManager:
    """
    Gère le cycle de vie des photos

    Règles:
    1. TEMP > 48h -> Suppression OU promotion HOT
    2. Photos publiées > 7j -> Suppression
    3. TEMP non publié > 48h -> HOT
    4. HOT sans accès 90j -> COLD
    5. COLD > 365j -> Suppression

    Exécuté: Quotidiennement à 3h du matin (cron job)
    """

    def __init__(self, storage_manager: StorageManager):
        """
        Initialize lifecycle manager

        Args:
            storage_manager: StorageManager instance
        """
        self.storage = storage_manager

    async def run_daily_lifecycle(self):
        """
        Job quotidien de lifecycle

        Actions:
        1. Supprimer photos TEMP > 48h
        2. Supprimer photos publiées > 7j
        3. Promouvoir TEMP -> HOT si draft reste
        4. Archiver HOT -> COLD si 90j sans accès
        5. Supprimer COLD > 365j
        """
        logger.info("[PROCESS] Starting storage lifecycle job")

        now = datetime.utcnow()

        # Stats
        stats = {
            'temp_deleted': 0,
            'published_deleted': 0,
            'promoted_to_hot': 0,
            'archived_to_cold': 0,
            'old_deleted': 0
        }

        # 1. Supprimer photos TEMP expirées
        logger.info("[INFO] Step 1: Deleting expired TEMP photos")
        temp_photos = await self._get_photos_by_tier(StorageTier.TEMP)

        for photo in temp_photos:
            if photo.scheduled_deletion and photo.scheduled_deletion < now:
                logger.info(f"🗑️ Deleting expired TEMP photo: {photo.photo_id}")
                await self.storage.delete_photo(photo.photo_id)
                stats['temp_deleted'] += 1

        # 2. Supprimer photos publiées expirées (7j après publication)
        logger.info("[INFO] Step 2: Deleting published photos (7+ days)")
        published_photos = await self._get_published_photos()

        for photo in published_photos:
            if photo.scheduled_deletion and photo.scheduled_deletion < now:
                logger.info(
                    f"🗑️ Deleting published photo: {photo.photo_id} "
                    f"(published {(now - photo.published_date).days} days ago)"
                )
                await self.storage.delete_photo(photo.photo_id)
                stats['published_deleted'] += 1

        # 3. Promouvoir TEMP -> HOT (drafts non publiés)
        logger.info("[INFO] Step 3: Promoting TEMP -> HOT (non-published drafts)")
        temp_old = await self._get_photos_older_than(
            StorageTier.TEMP,
            hours=48
        )

        for photo in temp_old:
            if not photo.published_to_vinted:
                logger.info(
                    f"⬆️ Promoting to HOT storage: {photo.photo_id} "
                    f"(draft_id: {photo.draft_id})"
                )
                await self.storage.promote_to_hot_storage(photo.photo_id)
                stats['promoted_to_hot'] += 1

        # 4. Archiver HOT -> COLD (90j sans accès)
        logger.info("[INFO] Step 4: Archiving HOT -> COLD (90+ days without access)")
        hot_old = await self._get_photos_not_accessed_for(
            StorageTier.HOT,
            days=90
        )

        for photo in hot_old:
            logger.info(
                f"[PACKAGE] Archiving to COLD storage: {photo.photo_id} "
                f"(last accessed {(now - photo.last_accessed).days} days ago)"
            )
            await self.storage.archive_to_cold_storage(photo.photo_id)
            stats['archived_to_cold'] += 1

        # 5. Supprimer COLD > 365j
        logger.info("[INFO] Step 5: Deleting old COLD photos (365+ days)")
        cold_old = await self._get_photos_older_than(
            StorageTier.COLD,
            days=365
        )

        for photo in cold_old:
            logger.info(
                f"🗑️ Deleting old COLD photo: {photo.photo_id} "
                f"(uploaded {(now - photo.upload_date).days} days ago)"
            )
            await self.storage.delete_photo(photo.photo_id)
            stats['old_deleted'] += 1

        # Log summary
        logger.info(
            f"[OK] Storage lifecycle job completed\n"
            f"   - TEMP deleted: {stats['temp_deleted']}\n"
            f"   - Published deleted: {stats['published_deleted']}\n"
            f"   - Promoted to HOT: {stats['promoted_to_hot']}\n"
            f"   - Archived to COLD: {stats['archived_to_cold']}\n"
            f"   - Old photos deleted: {stats['old_deleted']}"
        )

        return stats

    async def _get_photos_by_tier(self, tier: StorageTier) -> List[PhotoMetadata]:
        """
        Récupère toutes les photos d'un tier

        Args:
            tier: Tier de stockage

        Returns:
            Liste de PhotoMetadata
        """
        from backend.core.storage import get_store

        store = get_store()
        with store.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM photo_metadata WHERE tier = ?
            """, (tier.value,))

            rows = cursor.fetchall()

            photos = []
            for row in rows:
                photo = PhotoMetadata(
                    photo_id=row['photo_id'],
                    user_id=row['user_id'],
                    draft_id=row['draft_id'],
                    tier=StorageTier(row['tier']),
                    original_filename=row['original_filename'],
                    size_bytes=row['size_bytes'],
                    compressed_size_bytes=row['compressed_size_bytes'],
                    upload_date=datetime.fromisoformat(row['upload_date']) if row['upload_date'] else None,
                    last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
                    published_to_vinted=bool(row['published_to_vinted']),
                    published_date=datetime.fromisoformat(row['published_date']) if row['published_date'] else None,
                    scheduled_deletion=datetime.fromisoformat(row['scheduled_deletion']) if row['scheduled_deletion'] else None
                )
                photos.append(photo)

            return photos

    async def _get_published_photos(self) -> List[PhotoMetadata]:
        """
        Récupère toutes les photos publiées

        Returns:
            Liste de PhotoMetadata
        """
        from backend.core.storage import get_store

        store = get_store()
        with store.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM photo_metadata
                WHERE published_to_vinted = 1
            """)

            rows = cursor.fetchall()

            photos = []
            for row in rows:
                photo = PhotoMetadata(
                    photo_id=row['photo_id'],
                    user_id=row['user_id'],
                    draft_id=row['draft_id'],
                    tier=StorageTier(row['tier']),
                    original_filename=row['original_filename'],
                    size_bytes=row['size_bytes'],
                    compressed_size_bytes=row['compressed_size_bytes'],
                    upload_date=datetime.fromisoformat(row['upload_date']) if row['upload_date'] else None,
                    last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
                    published_to_vinted=bool(row['published_to_vinted']),
                    published_date=datetime.fromisoformat(row['published_date']) if row['published_date'] else None,
                    scheduled_deletion=datetime.fromisoformat(row['scheduled_deletion']) if row['scheduled_deletion'] else None
                )
                photos.append(photo)

            return photos

    async def _get_photos_older_than(
        self,
        tier: StorageTier,
        hours: int = None,
        days: int = None
    ) -> List[PhotoMetadata]:
        """
        Récupère photos plus vieilles que X

        Args:
            tier: Tier de stockage
            hours: Nombre d'heures (optionnel)
            days: Nombre de jours (optionnel)

        Returns:
            Liste de PhotoMetadata
        """
        if hours:
            threshold = datetime.utcnow() - timedelta(hours=hours)
        elif days:
            threshold = datetime.utcnow() - timedelta(days=days)
        else:
            return []

        from backend.core.storage import get_store

        store = get_store()
        with store.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM photo_metadata
                WHERE tier = ? AND upload_date < ?
            """, (tier.value, threshold.isoformat()))

            rows = cursor.fetchall()

            photos = []
            for row in rows:
                photo = PhotoMetadata(
                    photo_id=row['photo_id'],
                    user_id=row['user_id'],
                    draft_id=row['draft_id'],
                    tier=StorageTier(row['tier']),
                    original_filename=row['original_filename'],
                    size_bytes=row['size_bytes'],
                    compressed_size_bytes=row['compressed_size_bytes'],
                    upload_date=datetime.fromisoformat(row['upload_date']) if row['upload_date'] else None,
                    last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
                    published_to_vinted=bool(row['published_to_vinted']),
                    published_date=datetime.fromisoformat(row['published_date']) if row['published_date'] else None,
                    scheduled_deletion=datetime.fromisoformat(row['scheduled_deletion']) if row['scheduled_deletion'] else None
                )
                photos.append(photo)

            return photos

    async def _get_photos_not_accessed_for(
        self,
        tier: StorageTier,
        days: int
    ) -> List[PhotoMetadata]:
        """
        Récupère photos non accédées depuis X jours

        Args:
            tier: Tier de stockage
            days: Nombre de jours

        Returns:
            Liste de PhotoMetadata
        """
        threshold = datetime.utcnow() - timedelta(days=days)

        from backend.core.storage import get_store

        store = get_store()
        with store.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM photo_metadata
                WHERE tier = ? AND last_accessed < ?
            """, (tier.value, threshold.isoformat()))

            rows = cursor.fetchall()

            photos = []
            for row in rows:
                photo = PhotoMetadata(
                    photo_id=row['photo_id'],
                    user_id=row['user_id'],
                    draft_id=row['draft_id'],
                    tier=StorageTier(row['tier']),
                    original_filename=row['original_filename'],
                    size_bytes=row['size_bytes'],
                    compressed_size_bytes=row['compressed_size_bytes'],
                    upload_date=datetime.fromisoformat(row['upload_date']) if row['upload_date'] else None,
                    last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
                    published_to_vinted=bool(row['published_to_vinted']),
                    published_date=datetime.fromisoformat(row['published_date']) if row['published_date'] else None,
                    scheduled_deletion=datetime.fromisoformat(row['scheduled_deletion']) if row['scheduled_deletion'] else None
                )
                photos.append(photo)

            return photos
