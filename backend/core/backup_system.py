"""
Automated Backup System for PostgreSQL
Includes rotation, compression, and S3 upload
"""
import os
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import asyncio
from backend.utils.logger import logger
from backend.core.s3_storage import storage

# Backup configuration
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backend/data/backups"))
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
BACKUP_TO_S3 = os.getenv("BACKUP_TO_S3", "false").lower() == "true"


class BackupSystem:
    """
    Automated backup system with:
    - PostgreSQL dumps
    - Compression (gzip)
    - Rotation (keep N days)
    - S3 upload (optional)
    - Health monitoring
    """

    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def create_backup(self) -> Optional[str]:
        """
        Create PostgreSQL backup

        Returns:
            Path to backup file or None if failed
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"vintedbots_backup_{timestamp}.sql"
        backup_path = self.backup_dir / backup_filename

        try:
            # Get database connection details
            database_url = os.getenv("DATABASE_URL")

            if not database_url:
                logger.error("DATABASE_URL not configured")
                return None

            # Parse PostgreSQL URL
            # Format: postgresql://user:pass@host:port/dbname
            if database_url.startswith("sqlite"):
                return await self._backup_sqlite()

            # Extract connection details
            import re
            pattern = r"postgresql(?:\+\w+)?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)"
            match = re.match(pattern, database_url)

            if not match:
                logger.error("Invalid DATABASE_URL format")
                return None

            user, password, host, port, dbname = match.groups()

            # Create pg_dump command
            dump_command = f"pg_dump -h {host} -p {port} -U {user} -d {dbname} -F p -f {backup_path}"

            # Set password via environment
            env = os.environ.copy()
            env["PGPASSWORD"] = password

            # Execute dump
            process = await asyncio.create_subprocess_shell(
                dump_command,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"pg_dump failed: {stderr.decode()}")
                return None

            logger.info(f"✅ PostgreSQL backup created: {backup_path}")

            # Compress backup
            compressed_path = await self._compress_backup(backup_path)

            # Upload to S3 if enabled
            if BACKUP_TO_S3 and compressed_path:
                await self._upload_to_s3(compressed_path)

            # Clean up uncompressed file
            if backup_path.exists():
                backup_path.unlink()

            return str(compressed_path) if compressed_path else str(backup_path)

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None

    async def _backup_sqlite(self) -> Optional[str]:
        """Backup SQLite database"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"vintedbots_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename

        try:
            # Get SQLite database path
            db_path = os.getenv("SQLITE_DB_PATH", "backend/data/vbs.db")

            if not Path(db_path).exists():
                logger.error(f"SQLite database not found: {db_path}")
                return None

            # Copy database file
            shutil.copy2(db_path, backup_path)

            logger.info(f"✅ SQLite backup created: {backup_path}")

            # Compress backup
            compressed_path = await self._compress_backup(backup_path)

            # Upload to S3 if enabled
            if BACKUP_TO_S3 and compressed_path:
                await self._upload_to_s3(compressed_path)

            # Clean up uncompressed file
            if backup_path.exists():
                backup_path.unlink()

            return str(compressed_path) if compressed_path else str(backup_path)

        except Exception as e:
            logger.error(f"SQLite backup failed: {e}")
            return None

    async def _compress_backup(self, backup_path: Path) -> Optional[Path]:
        """Compress backup with gzip"""
        try:
            compressed_path = backup_path.with_suffix(backup_path.suffix + ".gz")

            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            original_size = backup_path.stat().st_size
            compressed_size = compressed_path.stat().st_size
            ratio = (1 - compressed_size / original_size) * 100

            logger.info(
                f"✅ Backup compressed: {original_size / 1024 / 1024:.1f}MB → "
                f"{compressed_size / 1024 / 1024:.1f}MB ({ratio:.1f}% reduction)"
            )

            return compressed_path

        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return None

    async def _upload_to_s3(self, backup_path: Path) -> bool:
        """Upload backup to S3"""
        try:
            object_name = f"backups/{backup_path.name}"
            url = await storage.upload_file(str(backup_path), object_name)

            if url:
                logger.info(f"✅ Backup uploaded to S3: {url}")
                return True
            else:
                logger.error("S3 upload failed")
                return False

        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return False

    async def cleanup_old_backups(self):
        """Delete backups older than retention period"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=BACKUP_RETENTION_DAYS)

            deleted_count = 0
            total_size_freed = 0

            for backup_file in self.backup_dir.glob("vintedbots_backup_*"):
                # Get file modification time
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

                if mtime < cutoff_date:
                    size = backup_file.stat().st_size
                    backup_file.unlink()
                    deleted_count += 1
                    total_size_freed += size

            if deleted_count > 0:
                logger.info(
                    f"🗑️ Cleaned up {deleted_count} old backups "
                    f"({total_size_freed / 1024 / 1024:.1f}MB freed)"
                )

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

    async def list_backups(self) -> list:
        """List all available backups"""
        backups = []

        for backup_file in sorted(self.backup_dir.glob("vintedbots_backup_*"), reverse=True):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return backups

    async def restore_backup(self, backup_filename: str) -> bool:
        """
        Restore database from backup

        WARNING: This will overwrite the current database!
        """
        try:
            backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                logger.error(f"Backup not found: {backup_filename}")
                return False

            # Decompress if needed
            if backup_path.suffix == ".gz":
                temp_path = backup_path.with_suffix("")
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                backup_path = temp_path

            # Get database connection details
            database_url = os.getenv("DATABASE_URL")

            if database_url.startswith("sqlite"):
                # Restore SQLite
                db_path = os.getenv("SQLITE_DB_PATH", "backend/data/vbs.db")
                shutil.copy2(backup_path, db_path)
                logger.info(f"✅ SQLite restored from: {backup_filename}")
                return True

            # Parse PostgreSQL URL
            import re
            pattern = r"postgresql(?:\+\w+)?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)"
            match = re.match(pattern, database_url)

            if not match:
                logger.error("Invalid DATABASE_URL format")
                return False

            user, password, host, port, dbname = match.groups()

            # Drop and recreate database
            # WARNING: This deletes all data!
            restore_command = f"psql -h {host} -p {port} -U {user} -d {dbname} -f {backup_path}"

            env = os.environ.copy()
            env["PGPASSWORD"] = password

            process = await asyncio.create_subprocess_shell(
                restore_command,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Restore failed: {stderr.decode()}")
                return False

            logger.info(f"✅ PostgreSQL restored from: {backup_filename}")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False


# Global backup system instance
backup_system = BackupSystem()
