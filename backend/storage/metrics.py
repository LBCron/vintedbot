"""
Storage Metrics & Cost Tracking
Calcule les coûts et l'usage du stockage multi-tier
"""
from typing import Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from .storage_manager import StorageTier


class StorageMetrics:
    """
    Tracking coûts et usage storage

    Calcule:
    - Nombre de photos par tier
    - Taille totale par tier
    - Coût mensuel estimé
    - Économies réalisées
    """

    # Prix au GB/mois
    PRICING = {
        'temp': 0.00,      # Fly.io Volumes (gratuit)
        'hot': 0.015,      # Cloudflare R2
        'cold': 0.006      # Backblaze B2
    }

    async def get_storage_stats(self) -> Dict[str, Any]:
        """
        Retourne statistiques storage

        Returns:
            {
                "temp_count": 150,
                "temp_size_gb": 0.5,
                "hot_count": 5000,
                "hot_size_gb": 50,
                "cold_count": 2000,
                "cold_size_gb": 20,
                "total_count": 7150,
                "total_size_gb": 70.5,
                "monthly_cost_estimate": 0.87,
                "savings_vs_all_hot": 14.63
            }
        """
        from backend.core.storage import get_store

        stats = {
            'temp_count': 0,
            'temp_size_gb': 0.0,
            'hot_count': 0,
            'hot_size_gb': 0.0,
            'cold_count': 0,
            'cold_size_gb': 0.0,
            'total_count': 0,
            'total_size_gb': 0.0
        }

        store = get_store()
        with store.get_connection() as conn:
            cursor = conn.cursor()

            # Stats par tier
            for tier in ['temp', 'hot', 'cold']:
                cursor.execute("""
                    SELECT
                        COUNT(*) as count,
                        SUM(compressed_size_bytes) as total_bytes
                    FROM photo_metadata
                    WHERE tier = ?
                """, (tier,))

                row = cursor.fetchone()

                if row and row['count']:
                    count = row['count']
                    total_bytes = row['total_bytes'] or 0
                    total_gb = total_bytes / (1024 ** 3)  # Bytes to GB

                    stats[f'{tier}_count'] = count
                    stats[f'{tier}_size_gb'] = round(total_gb, 3)

            # Totaux
            stats['total_count'] = (
                stats['temp_count'] +
                stats['hot_count'] +
                stats['cold_count']
            )

            stats['total_size_gb'] = round(
                stats['temp_size_gb'] +
                stats['hot_size_gb'] +
                stats['cold_size_gb'],
                3
            )

        # Coûts
        stats['monthly_cost_estimate'] = await self.estimate_monthly_cost(stats)

        # Économies vs all-HOT
        all_hot_cost = stats['total_size_gb'] * self.PRICING['hot']
        stats['savings_vs_all_hot'] = round(all_hot_cost - stats['monthly_cost_estimate'], 2)

        return stats

    async def estimate_monthly_cost(self, stats: Dict[str, Any] = None) -> float:
        """
        Estime coût mensuel

        Calcul:
        - TEMP (Fly.io): gratuit
        - HOT (R2): size_gb × $0.015
        - COLD (B2): size_gb × $0.006

        Args:
            stats: Stats pré-calculées (optionnel)

        Returns:
            Coût mensuel en USD
        """
        if not stats:
            stats = await self.get_storage_stats()

        hot_cost = stats['hot_size_gb'] * self.PRICING['hot']
        cold_cost = stats['cold_size_gb'] * self.PRICING['cold']

        total = hot_cost + cold_cost

        return round(total, 2)

    async def get_cost_breakdown(self) -> Dict[str, Any]:
        """
        Détail des coûts par tier

        Returns:
            {
                "temp": {"cost": 0.00, "percentage": 0},
                "hot": {"cost": 0.75, "percentage": 86},
                "cold": {"cost": 0.12, "percentage": 14},
                "total": 0.87
            }
        """
        stats = await self.get_storage_stats()

        hot_cost = stats['hot_size_gb'] * self.PRICING['hot']
        cold_cost = stats['cold_size_gb'] * self.PRICING['cold']
        total_cost = hot_cost + cold_cost

        breakdown = {
            'temp': {
                'cost': 0.00,
                'size_gb': stats['temp_size_gb'],
                'percentage': 0
            },
            'hot': {
                'cost': round(hot_cost, 2),
                'size_gb': stats['hot_size_gb'],
                'percentage': round((hot_cost / total_cost * 100) if total_cost > 0 else 0, 1)
            },
            'cold': {
                'cost': round(cold_cost, 2),
                'size_gb': stats['cold_size_gb'],
                'percentage': round((cold_cost / total_cost * 100) if total_cost > 0 else 0, 1)
            },
            'total': round(total_cost, 2)
        }

        return breakdown

    async def get_lifecycle_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Métriques du lifecycle sur X jours

        Returns:
            {
                "photos_uploaded": 1000,
                "photos_promoted": 200,
                "photos_archived": 50,
                "photos_deleted": 750,
                "avg_temp_duration_hours": 36,
                "avg_hot_duration_days": 45
            }
        """
        from backend.core.storage import get_store

        threshold = datetime.utcnow() - timedelta(days=days)

        metrics = {
            'photos_uploaded': 0,
            'photos_promoted': 0,  # TEMP -> HOT
            'photos_archived': 0,  # HOT -> COLD
            'photos_deleted': 0
        }

        store = get_store()
        with store.get_connection() as conn:
            cursor = conn.cursor()

            # Photos uploadées
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM photo_metadata
                WHERE upload_date > ?
            """, (threshold.isoformat(),))
            row = cursor.fetchone()
            metrics['photos_uploaded'] = row['count'] if row else 0

            # Photos en HOT (promues)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM photo_metadata
                WHERE tier = 'hot' AND upload_date > ?
            """, (threshold.isoformat(),))
            row = cursor.fetchone()
            metrics['photos_promoted'] = row['count'] if row else 0

            # Photos en COLD (archivées)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM photo_metadata
                WHERE tier = 'cold' AND upload_date > ?
            """, (threshold.isoformat(),))
            row = cursor.fetchone()
            metrics['photos_archived'] = row['count'] if row else 0

            # TODO: Photos supprimées (nécessite table de log)
            metrics['photos_deleted'] = 0

        return metrics

    async def get_user_storage_usage(self, user_id: str) -> Dict[str, Any]:
        """
        Usage storage pour un utilisateur

        Args:
            user_id: ID utilisateur

        Returns:
            {
                "total_photos": 50,
                "total_size_gb": 2.5,
                "by_tier": {...}
            }
        """
        from backend.core.storage import get_store

        usage = {
            'total_photos': 0,
            'total_size_gb': 0.0,
            'by_tier': {}
        }

        store = get_store()
        with store.get_connection() as conn:
            cursor = conn.cursor()

            # Stats par tier
            for tier in ['temp', 'hot', 'cold']:
                cursor.execute("""
                    SELECT
                        COUNT(*) as count,
                        SUM(compressed_size_bytes) as total_bytes
                    FROM photo_metadata
                    WHERE user_id = ? AND tier = ?
                """, (user_id, tier))

                row = cursor.fetchone()

                if row and row['count']:
                    count = row['count']
                    total_bytes = row['total_bytes'] or 0
                    total_gb = total_bytes / (1024 ** 3)

                    usage['by_tier'][tier] = {
                        'count': count,
                        'size_gb': round(total_gb, 3)
                    }

                    usage['total_photos'] += count
                    usage['total_size_gb'] += total_gb

            usage['total_size_gb'] = round(usage['total_size_gb'], 3)

        return usage

    async def get_optimization_recommendations(self) -> list[str]:
        """
        Recommandations d'optimisation

        Returns:
            Liste de recommandations
        """
        recommendations = []

        stats = await self.get_storage_stats()

        # Trop de photos en TEMP
        if stats['temp_count'] > 1000:
            recommendations.append(
                f"[WARN] {stats['temp_count']} photos en TEMP storage. "
                "Vérifiez que le lifecycle job fonctionne correctement."
            )

        # Trop de photos en HOT
        if stats['hot_size_gb'] > 100:
            recommendations.append(
                f"💡 {stats['hot_size_gb']} GB en HOT storage (${stats['hot_size_gb'] * self.PRICING['hot']:.2f}/mois). "
                "Considérez réduire la période avant archivage COLD (actuellement 90 jours)."
            )

        # Peu de photos en COLD
        if stats['cold_count'] < stats['hot_count'] * 0.1 and stats['hot_count'] > 100:
            recommendations.append(
                "💡 Peu de photos archivées en COLD. "
                "Le lifecycle pourrait être plus agressif pour économiser."
            )

        # Coût élevé
        monthly_cost = stats['monthly_cost_estimate']
        if monthly_cost > 50:
            recommendations.append(
                f"💸 Coût mensuel élevé: ${monthly_cost:.2f}. "
                "Considérez supprimer les photos publiées plus rapidement (actuellement 7 jours)."
            )

        if not recommendations:
            recommendations.append("[OK] Stockage bien optimisé !")

        return recommendations
