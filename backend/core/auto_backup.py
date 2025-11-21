"""
Automatic Backup System
Sauvegarde automatique de la base de données, configurations, et données critiques
"""
import shutil
import gzip
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
from loguru import logger
import tarfile


class BackupManager:
    """Manage automatic backups"""

    def __init__(
        self,
        backup_dir: str = "backend/data/backups",
        retention_days: int = 30
    ):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

        # Files and directories to backup
        self.backup_targets = [
            "backend/data/db.sqlite",
            "backend/data/vbs.db",
            "backend/monitoring/snapshots",
            ".env",
            "backend/data/uploads",
        ]

    def create_backup(self, backup_name: Optional[str] = None) -> Optional[Path]:
        """
        Create complete backup

        Args:
            backup_name: Custom backup name (optional)

        Returns:
            Path to backup file
        """
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        backup_file = self.backup_dir / f"{backup_name}.tar.gz"

        try:
            logger.info(f"[PACKAGE] Creating backup: {backup_name}")

            with tarfile.open(backup_file, "w:gz") as tar:
                for target in self.backup_targets:
                    target_path = Path(target)
                    if target_path.exists():
                        tar.add(target_path, arcname=target_path.name)
                        logger.info(f"  [OK] Added: {target}")
                    else:
                        logger.warning(f"  [WARN] Skipped (not found): {target}")

            # Add metadata
            metadata = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "files": [t for t in self.backup_targets if Path(t).exists()],
                "size_bytes": backup_file.stat().st_size
            }

            metadata_file = self.backup_dir / f"{backup_name}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"[OK] Backup created: {backup_file} ({metadata['size_bytes'] / 1024 / 1024:.2f} MB)")
            return backup_file

        except Exception as e:
            logger.error(f"[ERROR] Backup failed: {e}")
            return None

    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore from backup

        Args:
            backup_name: Name of backup to restore

        Returns:
            True if restored successfully
        """
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"

        if not backup_file.exists():
            logger.error(f"[ERROR] Backup not found: {backup_name}")
            return False

        try:
            logger.info(f"[PACKAGE] Restoring backup: {backup_name}")

            # Create restore point first
            self.create_backup(backup_name=f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

            # Extract backup
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path=".")

            logger.info(f"[OK] Backup restored: {backup_name}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Restore failed: {e}")
            return False

    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []

        for backup_file in sorted(self.backup_dir.glob("*.tar.gz"), reverse=True):
            metadata_file = backup_file.with_suffix('.json')

            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    backups.append(metadata)
                except:
                    # Fallback if no metadata
                    backups.append({
                        "backup_name": backup_file.stem,
                        "created_at": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                        "size_bytes": backup_file.stat().st_size
                    })

        return backups

    def cleanup_old_backups(self):
        """Delete backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted = 0

        for backup_file in self.backup_dir.glob("*.tar.gz"):
            metadata_file = backup_file.with_suffix('.json')

            # Get creation date
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    created_at = datetime.fromisoformat(metadata['created_at'])
                except:
                    created_at = datetime.fromtimestamp(backup_file.stat().st_mtime)
            else:
                created_at = datetime.fromtimestamp(backup_file.stat().st_mtime)

            # Delete if too old
            if created_at < cutoff_date:
                try:
                    backup_file.unlink()
                    if metadata_file.exists():
                        metadata_file.unlink()
                    deleted += 1
                    logger.info(f"🗑️ Deleted old backup: {backup_file.name}")
                except Exception as e:
                    logger.error(f"[ERROR] Failed to delete {backup_file.name}: {e}")

        if deleted > 0:
            logger.info(f"[OK] Cleaned up {deleted} old backups")
        else:
            logger.info("[OK] No old backups to clean up")

    def get_backup_stats(self) -> Dict:
        """Get backup statistics"""
        backups = self.list_backups()

        total_size = sum(b.get('size_bytes', 0) for b in backups)
        oldest = min((b['created_at'] for b in backups), default=None) if backups else None
        newest = max((b['created_at'] for b in backups), default=None) if backups else None

        return {
            "total_backups": len(backups),
            "total_size_mb": total_size / 1024 / 1024,
            "oldest_backup": oldest,
            "newest_backup": newest,
            "retention_days": self.retention_days
        }


class AutoBackupScheduler:
    """Schedule automatic backups"""

    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.is_running = False
        self.task = None

    async def start(self, interval_hours: int = 24):
        """
        Start automatic backup scheduler

        Args:
            interval_hours: Backup interval in hours
        """
        self.is_running = True
        logger.info(f"[PROCESS] Auto-backup scheduler started (every {interval_hours}h)")

        while self.is_running:
            try:
                # Create backup
                backup_file = self.backup_manager.create_backup()

                if backup_file:
                    logger.info("[OK] Scheduled backup completed")
                else:
                    logger.error("[ERROR] Scheduled backup failed")

                # Cleanup old backups
                self.backup_manager.cleanup_old_backups()

                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)

            except Exception as e:
                logger.error(f"[ERROR] Auto-backup error: {e}")
                await asyncio.sleep(3600)  # Wait 1h before retry

    def stop(self):
        """Stop scheduler"""
        self.is_running = False
        if self.task:
            self.task.cancel()
        logger.info("🛑 Auto-backup scheduler stopped")


# Integration with existing job scheduler
def schedule_daily_backup():
    """Schedule daily backups using APScheduler"""
    from backend.jobs import scheduler

    backup_manager = BackupManager()

    def backup_job():
        logger.info("⏰ Running scheduled backup...")
        backup_file = backup_manager.create_backup()
        if backup_file:
            logger.info("[OK] Scheduled backup completed")
            backup_manager.cleanup_old_backups()

    # Schedule daily at 3 AM
    scheduler.add_job(
        backup_job,
        'cron',
        hour=3,
        minute=0,
        id='daily_backup',
        replace_existing=True
    )

    logger.info("[OK] Daily backup scheduled at 3:00 AM")


if __name__ == "__main__":
    # Test backup system
    manager = BackupManager()

    print("[PACKAGE] Creating test backup...")
    backup_file = manager.create_backup()

    if backup_file:
        print(f"[OK] Backup created: {backup_file}")

        print("\n[INFO] Available backups:")
        for backup in manager.list_backups():
            print(f"  - {backup['backup_name']} ({backup.get('size_bytes', 0) / 1024:.1f} KB)")

        print("\n📊 Backup stats:")
        stats = manager.get_backup_stats()
        print(f"  Total: {stats['total_backups']} backups")
        print(f"  Size: {stats['total_size_mb']:.2f} MB")
        print(f"  Retention: {stats['retention_days']} days")

        # Cleanup test
        print("\n🗑️ Testing cleanup...")
        manager.cleanup_old_backups()
    else:
        print("[ERROR] Backup failed")
