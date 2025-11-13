"""
Storage Manager - Orchestrateur principal du système multi-tier

Gère le cycle de vie complet des photos :
1. Upload → TIER 1 (temp, 48h)
2. Si publié Vinted → suppression après 7j
3. Si non publié → TIER 2 (hot, R2)
4. Après 90j sans accès → TIER 3 (cold, B2)
5. Après 365j → suppression définitive
"""
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, List
from dataclasses import dataclass, asdict
import uuid
from loguru import logger


class StorageTier(Enum):
    """Tiers de stockage"""
    TEMP = "temp"    # Fly.io Volumes (24-48h)
    HOT = "hot"      # Cloudflare R2 (< 90 days)
    COLD = "cold"    # Backblaze B2 (> 90 days)


@dataclass
class PhotoMetadata:
    """Métadonnées d'une photo stockée"""
    photo_id: str
    user_id: str
    draft_id: Optional[str]
    tier: StorageTier
    original_filename: str
    size_bytes: int
    compressed_size_bytes: int
    upload_date: datetime
    last_accessed: datetime
    published_to_vinted: bool
    published_date: Optional[datetime]
    scheduled_deletion: Optional[datetime]

    def to_dict(self):
        """Convert to dict for JSON serialization"""
        data = asdict(self)
        data['tier'] = self.tier.value
        data['upload_date'] = self.upload_date.isoformat() if self.upload_date else None
        data['last_accessed'] = self.last_accessed.isoformat() if self.last_accessed else None
        data['published_date'] = self.published_date.isoformat() if self.published_date else None
        data['scheduled_deletion'] = self.scheduled_deletion.isoformat() if self.scheduled_deletion else None
        return data


class StorageManager:
    """
    Gestionnaire central de stockage multi-tier

    Architecture :
    - TIER 1 (TEMP) : Fly.io Volumes - gratuit, 24-48h
    - TIER 2 (HOT)  : Cloudflare R2 - $0.015/GB/mois, accès fréquent
    - TIER 3 (COLD) : Backblaze B2 - $0.006/GB/mois, archive

    Workflow :
    1. Upload → TEMP
    2. Analyse IA → génération draft
    3. Si publié → garder 7j puis supprimer
    4. Si non publié → promouvoir HOT
    5. Après 90j sans accès → archiver COLD
    6. Après 365j → supprimer définitivement
    """

    def __init__(self):
        from .tier1_local import LocalStorage
        from .tier2_r2 import CloudflareR2Storage
        from .tier3_b2 import BackblazeB2Storage
        from .compression import ImageCompressor

        self.tier1 = LocalStorage()
        self.tier2 = CloudflareR2Storage()
        self.tier3 = BackblazeB2Storage()
        self.compressor = ImageCompressor()

        logger.info("✅ StorageManager initialized with 3 tiers")

    async def upload_photo(
        self,
        user_id: str,
        file_data: bytes,
        filename: str,
        draft_id: Optional[str] = None
    ) -> PhotoMetadata:
        """
        Upload photo dans TIER 1 (temporaire)

        Workflow :
        1. Compression image (50% size reduction)
        2. Upload vers Fly.io Volumes
        3. Création metadata
        4. Schedule suppression automatique (48h)

        Args:
            user_id: ID utilisateur
            file_data: Données binaires de l'image
            filename: Nom du fichier original
            draft_id: ID du draft associé (optionnel)

        Returns:
            PhotoMetadata avec toutes les infos
        """
        photo_id = str(uuid.uuid4())

        logger.info(f"📤 Uploading photo {photo_id} for user {user_id}")

        # 1. Compression
        logger.debug(f"Compressing image (original: {len(file_data)} bytes)")
        compressed_data = await self.compressor.compress(
            file_data,
            quality=85,
            max_width=2000,
            max_height=2000
        )

        compression_ratio = (1 - len(compressed_data) / len(file_data)) * 100
        logger.info(f"✅ Compressed: {len(compressed_data)} bytes ({compression_ratio:.1f}% reduction)")

        # 2. Upload TIER 1
        await self.tier1.upload(photo_id, compressed_data)
        logger.info(f"✅ Uploaded to TIER 1 (temp)")

        # 3. Metadata
        metadata = PhotoMetadata(
            photo_id=photo_id,
            user_id=user_id,
            draft_id=draft_id,
            tier=StorageTier.TEMP,
            original_filename=filename,
            size_bytes=len(file_data),
            compressed_size_bytes=len(compressed_data),
            upload_date=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            published_to_vinted=False,
            published_date=None,
            scheduled_deletion=datetime.utcnow() + timedelta(hours=48)
        )

        # 4. Sauvegarder metadata en DB
        await self._save_metadata(metadata)

        logger.info(f"✅ Photo {photo_id} uploaded successfully (scheduled deletion: 48h)")

        return metadata

    async def mark_published_to_vinted(self, photo_id: str):
        """
        Marque photo comme publiée sur Vinted
        → Schedule suppression dans 7 jours

        Logique : Une fois publiée sur Vinted, la photo est déjà hébergée
        par Vinted, donc on peut la supprimer de notre stockage après 7j
        (période de support client)
        """
        metadata = await self._get_metadata(photo_id)

        if not metadata:
            logger.warning(f"Photo {photo_id} not found")
            return

        metadata.published_to_vinted = True
        metadata.published_date = datetime.utcnow()
        metadata.scheduled_deletion = datetime.utcnow() + timedelta(days=7)

        await self._save_metadata(metadata)

        logger.info(f"✅ Photo {photo_id} marked as published (will be deleted in 7 days)")

    async def promote_to_hot_storage(self, photo_id: str):
        """
        Déplace photo de TIER 1 → TIER 2 (Cloudflare R2)

        Appelé quand :
        - Draft reste non publié après 24-48h
        - User veut garder la photo long terme

        Args:
            photo_id: ID de la photo à promouvoir
        """
        metadata = await self._get_metadata(photo_id)

        if not metadata:
            logger.warning(f"Photo {photo_id} not found")
            return

        if metadata.tier != StorageTier.TEMP:
            logger.info(f"Photo {photo_id} already in {metadata.tier.value}, skipping")
            return

        logger.info(f"⬆️ Promoting photo {photo_id} from TEMP to HOT storage")

        # 1. Télécharger depuis TIER 1
        photo_data = await self.tier1.download(photo_id)

        # 2. Upload vers TIER 2 (R2)
        await self.tier2.upload(photo_id, photo_data)

        # 3. Supprimer de TIER 1
        await self.tier1.delete(photo_id)

        # 4. Update metadata
        metadata.tier = StorageTier.HOT
        metadata.scheduled_deletion = None  # Plus de suppression auto
        await self._save_metadata(metadata)

        logger.info(f"✅ Photo {photo_id} promoted to HOT storage (R2)")

    async def archive_to_cold_storage(self, photo_id: str):
        """
        Déplace photo de TIER 2 → TIER 3 (Backblaze B2)

        Appelé automatiquement par lifecycle_manager
        après 90 jours sans accès

        Args:
            photo_id: ID de la photo à archiver
        """
        metadata = await self._get_metadata(photo_id)

        if not metadata:
            logger.warning(f"Photo {photo_id} not found")
            return

        if metadata.tier != StorageTier.HOT:
            logger.info(f"Photo {photo_id} not in HOT tier, skipping")
            return

        logger.info(f"📦 Archiving photo {photo_id} from HOT to COLD storage")

        # 1. Télécharger depuis TIER 2
        photo_data = await self.tier2.download(photo_id)

        # 2. Upload vers TIER 3 (B2)
        await self.tier3.upload(photo_id, photo_data)

        # 3. Supprimer de TIER 2
        await self.tier2.delete(photo_id)

        # 4. Update metadata
        metadata.tier = StorageTier.COLD
        await self._save_metadata(metadata)

        logger.info(f"✅ Photo {photo_id} archived to COLD storage (B2)")

    async def get_photo_url(self, photo_id: str) -> str:
        """
        Retourne URL publique de la photo
        Via CDN pour performance optimale

        Args:
            photo_id: ID de la photo

        Returns:
            URL publique de la photo
        """
        metadata = await self._get_metadata(photo_id)

        if not metadata:
            raise ValueError(f"Photo {photo_id} not found")

        # Update last_accessed
        metadata.last_accessed = datetime.utcnow()
        await self._save_metadata(metadata)

        # Return CDN URL selon tier
        if metadata.tier == StorageTier.TEMP:
            return await self.tier1.get_url(photo_id)
        elif metadata.tier == StorageTier.HOT:
            return await self.tier2.get_cdn_url(photo_id)
        else:  # COLD
            return await self.tier3.get_url(photo_id)

    async def get_photo_data(self, photo_id: str) -> bytes:
        """
        Télécharge les données brutes de la photo

        Args:
            photo_id: ID de la photo

        Returns:
            Données binaires de la photo
        """
        metadata = await self._get_metadata(photo_id)

        if not metadata:
            raise ValueError(f"Photo {photo_id} not found")

        # Update last_accessed
        metadata.last_accessed = datetime.utcnow()
        await self._save_metadata(metadata)

        # Download selon tier
        if metadata.tier == StorageTier.TEMP:
            return await self.tier1.download(photo_id)
        elif metadata.tier == StorageTier.HOT:
            return await self.tier2.download(photo_id)
        else:  # COLD
            return await self.tier3.download(photo_id)

    async def delete_photo(self, photo_id: str):
        """
        Suppression définitive d'une photo

        Args:
            photo_id: ID de la photo à supprimer
        """
        metadata = await self._get_metadata(photo_id)

        if not metadata:
            logger.warning(f"Photo {photo_id} not found for deletion")
            return

        logger.info(f"🗑️ Deleting photo {photo_id} from {metadata.tier.value} storage")

        # Supprimer du tier approprié
        if metadata.tier == StorageTier.TEMP:
            await self.tier1.delete(photo_id)
        elif metadata.tier == StorageTier.HOT:
            await self.tier2.delete(photo_id)
        else:  # COLD
            await self.tier3.delete(photo_id)

        # Supprimer metadata
        await self._delete_metadata(photo_id)

        logger.info(f"✅ Photo {photo_id} deleted")

    async def get_photos_by_draft(self, draft_id: str) -> List[PhotoMetadata]:
        """
        Récupère toutes les photos d'un draft

        Args:
            draft_id: ID du draft

        Returns:
            Liste des métadonnées photos
        """
        # TODO: Implémenter avec SQLite query
        # SELECT * FROM photo_metadata WHERE draft_id = ?
        logger.warning("get_photos_by_draft not yet implemented")
        return []

    async def _save_metadata(self, metadata: PhotoMetadata):
        """
        Sauvegarde metadata en DB

        Table schema:
        CREATE TABLE photo_metadata (
            photo_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            draft_id TEXT,
            tier TEXT NOT NULL,
            original_filename TEXT,
            size_bytes INTEGER,
            compressed_size_bytes INTEGER,
            upload_date TEXT,
            last_accessed TEXT,
            published_to_vinted INTEGER DEFAULT 0,
            published_date TEXT,
            scheduled_deletion TEXT
        )
        """
        # TODO: Implémenter avec SQLite
        from backend.core.storage import get_store

        store = get_store()
        with store.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO photo_metadata (
                    photo_id, user_id, draft_id, tier, original_filename,
                    size_bytes, compressed_size_bytes, upload_date, last_accessed,
                    published_to_vinted, published_date, scheduled_deletion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.photo_id,
                metadata.user_id,
                metadata.draft_id,
                metadata.tier.value,
                metadata.original_filename,
                metadata.size_bytes,
                metadata.compressed_size_bytes,
                metadata.upload_date.isoformat() if metadata.upload_date else None,
                metadata.last_accessed.isoformat() if metadata.last_accessed else None,
                1 if metadata.published_to_vinted else 0,
                metadata.published_date.isoformat() if metadata.published_date else None,
                metadata.scheduled_deletion.isoformat() if metadata.scheduled_deletion else None
            ))
            conn.commit()

    async def _get_metadata(self, photo_id: str) -> Optional[PhotoMetadata]:
        """Récupère metadata depuis DB"""
        # TODO: Implémenter avec SQLite
        from backend.core.storage import get_store

        store = get_store()
        with store.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM photo_metadata WHERE photo_id = ?
            """, (photo_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return PhotoMetadata(
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

    async def _delete_metadata(self, photo_id: str):
        """Supprime metadata de DB"""
        # TODO: Implémenter avec SQLite
        from backend.core.storage import get_store

        store = get_store()
        with store.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM photo_metadata WHERE photo_id = ?
            """, (photo_id,))
            conn.commit()
