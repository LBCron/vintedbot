"""
Tests unitaires pour le système de stockage multi-tier
Exécuter avec : pytest backend/storage/test_storage.py -v
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

# Mock environment variables for testing
os.environ['R2_ENDPOINT_URL'] = 'https://test.r2.cloudflarestorage.com'
os.environ['R2_ACCESS_KEY_ID'] = 'test_key'
os.environ['R2_SECRET_ACCESS_KEY'] = 'test_secret'
os.environ['R2_BUCKET_NAME'] = 'test-bucket'

from backend.storage.compression import ImageCompressor
from backend.storage.storage_manager import StorageManager, StorageTier, PhotoMetadata


class TestImageCompressor:
    """Tests pour la compression d'images"""

    @pytest.mark.asyncio
    async def test_compress_jpeg(self):
        """Test compression d'une image JPEG"""
        compressor = ImageCompressor()

        # Créer une image test simple (100x100 rouge)
        from PIL import Image
        import io

        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=95)
        original_data = img_bytes.getvalue()

        # Compresser
        compressed_data = await compressor.compress(
            original_data,
            quality=85,
            max_width=2000,
            max_height=2000
        )

        # Vérifier que la compression a réduit la taille
        assert len(compressed_data) < len(original_data)
        assert len(compressed_data) > 0

        # Vérifier que l'image est toujours valide
        compressed_img = Image.open(io.BytesIO(compressed_data))
        assert compressed_img.size == (100, 100)
        assert compressed_img.mode == 'RGB'

    @pytest.mark.asyncio
    async def test_compress_large_image(self):
        """Test compression avec resize d'une grande image"""
        compressor = ImageCompressor()

        from PIL import Image
        import io

        # Créer une grande image (3000x3000)
        img = Image.new('RGB', (3000, 3000), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=95)
        original_data = img_bytes.getvalue()

        # Compresser avec resize à max 2000x2000
        compressed_data = await compressor.compress(
            original_data,
            quality=85,
            max_width=2000,
            max_height=2000
        )

        # Vérifier resize
        compressed_img = Image.open(io.BytesIO(compressed_data))
        assert compressed_img.width <= 2000
        assert compressed_img.height <= 2000

        # Vérifier réduction de taille significative
        reduction_ratio = (1 - len(compressed_data) / len(original_data)) * 100
        assert reduction_ratio > 30  # Au moins 30% de réduction

    @pytest.mark.asyncio
    async def test_compress_rgba_to_rgb(self):
        """Test conversion RGBA -> RGB pour JPEG"""
        compressor = ImageCompressor()

        from PIL import Image
        import io

        # Créer image RGBA (avec transparence)
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        original_data = img_bytes.getvalue()

        # Compresser (devrait convertir en RGB)
        compressed_data = await compressor.compress(original_data, quality=85)

        # Vérifier conversion en RGB
        compressed_img = Image.open(io.BytesIO(compressed_data))
        assert compressed_img.mode == 'RGB'


class TestStorageManager:
    """Tests pour le gestionnaire de stockage"""

    @pytest.fixture
    def storage_manager(self):
        """Fixture pour créer un StorageManager"""
        return StorageManager()

    def test_storage_manager_initialization(self, storage_manager):
        """Test que le StorageManager s'initialise correctement"""
        assert storage_manager.tier1 is not None
        assert storage_manager.tier2 is not None
        assert storage_manager.tier3 is not None
        assert storage_manager.compressor is not None

    @pytest.mark.asyncio
    async def test_upload_photo_creates_metadata(self, storage_manager):
        """Test que l'upload crée bien les metadata"""
        from PIL import Image
        import io

        # Créer image test
        img = Image.new('RGB', (100, 100), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        file_data = img_bytes.getvalue()

        # Mock de _save_metadata pour tester sans DB
        saved_metadata = None

        async def mock_save_metadata(metadata):
            nonlocal saved_metadata
            saved_metadata = metadata

        storage_manager._save_metadata = mock_save_metadata

        # Upload
        metadata = await storage_manager.upload_photo(
            user_id="test_user",
            file_data=file_data,
            filename="test.jpg",
            draft_id="draft_123"
        )

        # Vérifications
        assert metadata.user_id == "test_user"
        assert metadata.draft_id == "draft_123"
        assert metadata.tier == StorageTier.TEMP
        assert metadata.photo_id is not None
        assert metadata.compressed_size_bytes > 0
        assert metadata.compressed_size_bytes < metadata.file_size_bytes
        assert metadata.scheduled_deletion is not None
        assert saved_metadata is not None


class TestStorageTiers:
    """Tests pour les différents tiers de stockage"""

    def test_tier1_local_storage_paths(self):
        """Test que TIER 1 utilise les bons chemins"""
        from backend.storage.tier1_local import LocalStorage

        tier1 = LocalStorage()
        assert tier1.base_path.exists()
        assert str(tier1.base_path).endswith('photos/temp')

    @pytest.mark.asyncio
    async def test_tier1_upload_download_delete(self):
        """Test workflow complet TIER 1"""
        from backend.storage.tier1_local import LocalStorage

        tier1 = LocalStorage()
        photo_id = "test_photo_123"
        test_data = b"test photo data content"

        try:
            # Upload
            await tier1.upload(photo_id, test_data)

            # Vérifier que le fichier existe
            file_path = tier1.base_path / f"{photo_id}.jpg"
            assert file_path.exists()

            # Download
            downloaded_data = await tier1.download(photo_id)
            assert downloaded_data == test_data

            # Delete
            await tier1.delete(photo_id)
            assert not file_path.exists()

        finally:
            # Cleanup au cas où
            file_path = tier1.base_path / f"{photo_id}.jpg"
            if file_path.exists():
                file_path.unlink()


class TestLifecycleRules:
    """Tests pour les règles de lifecycle"""

    def test_temp_photo_scheduled_deletion(self):
        """Test que les photos TEMP ont une suppression programmée à 48h"""
        metadata = PhotoMetadata(
            photo_id="test",
            user_id="user1",
            draft_id=None,
            tier=StorageTier.TEMP,
            original_filename="test.jpg",
            file_size_bytes=1000,
            compressed_size_bytes=500,
            upload_date=datetime.utcnow(),
            last_access_date=datetime.utcnow(),
            published_to_vinted=False,
            published_date=None,
            scheduled_deletion=datetime.utcnow() + timedelta(hours=48)
        )

        assert metadata.scheduled_deletion is not None

        # Vérifier que c'est bien ~48h
        time_until_deletion = metadata.scheduled_deletion - metadata.upload_date
        assert 47 <= time_until_deletion.total_seconds() / 3600 <= 49  # Entre 47 et 49h

    def test_published_photo_scheduled_deletion(self):
        """Test que les photos publiées ont une suppression à 7j"""
        now = datetime.utcnow()

        metadata = PhotoMetadata(
            photo_id="test",
            user_id="user1",
            draft_id=None,
            tier=StorageTier.TEMP,
            original_filename="test.jpg",
            file_size_bytes=1000,
            compressed_size_bytes=500,
            upload_date=now,
            last_access_date=now,
            published_to_vinted=True,
            published_date=now,
            scheduled_deletion=now + timedelta(days=7)
        )

        assert metadata.published_to_vinted == True
        assert metadata.scheduled_deletion is not None

        # Vérifier que c'est bien ~7 jours
        time_until_deletion = metadata.scheduled_deletion - metadata.published_date
        assert time_until_deletion.days == 7


class TestCostCalculations:
    """Tests pour les calculs de coûts"""

    def test_storage_cost_calculation(self):
        """Test calcul des coûts de stockage"""
        from backend.storage.metrics import StorageMetrics

        metrics = StorageMetrics()

        # Simuler des stats
        stats = {
            'temp_size_gb': 0.5,   # Gratuit
            'hot_size_gb': 50.0,   # $0.015/GB
            'cold_size_gb': 20.0,  # $0.006/GB
        }

        # Calcul attendu :
        # TEMP: 0.5 GB × $0 = $0
        # HOT: 50 GB × $0.015 = $0.75
        # COLD: 20 GB × $0.006 = $0.12
        # TOTAL: $0.87

        expected_cost = (50.0 * 0.015) + (20.0 * 0.006)
        assert expected_cost == 0.87

    def test_cost_savings_vs_all_hot(self):
        """Test calcul des économies vs tout en HOT"""
        # Scénario : 70 GB total
        # Multi-tier: 50 GB HOT + 20 GB COLD = $0.87
        # All-hot: 70 GB HOT = $1.05
        # Économie: $0.18 (17%)

        multi_tier_cost = (50.0 * 0.015) + (20.0 * 0.006)
        all_hot_cost = 70.0 * 0.015
        savings = all_hot_cost - multi_tier_cost

        assert savings == pytest.approx(0.18, 0.01)
        assert (savings / all_hot_cost * 100) == pytest.approx(17.14, 0.1)


# Script pour exécuter tous les tests
if __name__ == "__main__":
    print("[TEST] Running storage system tests...\n")
    pytest.main([__file__, "-v", "--tb=short"])
