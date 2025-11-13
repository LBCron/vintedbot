"""
Backup and disaster recovery system for VintedBot
Automated database and file backups with rotation
"""
import shutil
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
import sqlite3


class BackupManager:
    """Manage database and file backups"""

    def __init__(
        self,
        backup_dir: str = "backend/data/backups",
        db_path: str = "backend/data/vbs.db",
        max_backups: int = 7  # Keep last 7 backups
    ):
        self.backup_dir = Path(backup_dir)
        self.db_path = Path(db_path)
        self.max_backups = max_backups

        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_database_backup(self, compress: bool = True) -> Dict[str, Any]:
        """
        Create a backup of the SQLite database

        Args:
            compress: Whether to compress the backup with gzip

        Returns:
            Backup metadata (path, size, timestamp)
        """
        try:
            if not self.db_path.exists():
                return {
                    'success': False,
                    'error': 'Database file not found'
                }

            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"vbs_backup_{timestamp}.db"

            if compress:
                backup_filename += ".gz"

            backup_path = self.backup_dir / backup_filename

            # Create backup
            logger.info(f"Creating database backup: {backup_filename}")

            if compress:
                # Compressed backup
                with open(self.db_path, 'rb') as f_in:
                    with gzip.open(backup_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # Direct copy
                shutil.copy2(self.db_path, backup_path)

            backup_size_mb = backup_path.stat().st_size / (1024 * 1024)

            logger.info(f"✅ Database backup created: {backup_size_mb:.2f} MB")

            # Cleanup old backups
            self._cleanup_old_backups()

            return {
                'success': True,
                'backup_path': str(backup_path),
                'size_mb': backup_size_mb,
                'compressed': compress,
                'timestamp': timestamp
            }

        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def restore_database_backup(self, backup_path: str) -> Dict[str, Any]:
        """
        Restore database from a backup

        Args:
            backup_path: Path to backup file

        Returns:
            Restore result
        """
        try:
            backup_file = Path(backup_path)

            if not backup_file.exists():
                return {
                    'success': False,
                    'error': 'Backup file not found'
                }

            # Create backup of current database before restoring
            current_backup = self.create_database_backup(compress=True)

            if not current_backup['success']:
                return {
                    'success': False,
                    'error': 'Failed to backup current database before restore'
                }

            logger.info(f"Restoring database from: {backup_path}")

            # Restore from backup
            if backup_path.endswith('.gz'):
                # Decompress and restore
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(self.db_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                # Direct copy
                shutil.copy2(backup_file, self.db_path)

            # Verify restored database
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                conn.close()
            except Exception as e:
                logger.error(f"Restored database verification failed: {e}")
                # Try to restore the backup we just made
                shutil.copy2(current_backup['backup_path'], self.db_path)
                return {
                    'success': False,
                    'error': f'Restored database is corrupted. Rolled back. Error: {e}'
                }

            logger.info("✅ Database restored successfully")

            return {
                'success': True,
                'restored_from': backup_path,
                'backup_before_restore': current_backup['backup_path']
            }

        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _cleanup_old_backups(self):
        """Remove old backups, keeping only the most recent max_backups"""
        try:
            # Get all backup files sorted by modification time
            backup_files = sorted(
                self.backup_dir.glob("vbs_backup_*.db*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            # Remove old backups
            for old_backup in backup_files[self.max_backups:]:
                old_backup.unlink()
                logger.info(f"Deleted old backup: {old_backup.name}")

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups

        Returns:
            List of backup metadata
        """
        try:
            backups = []

            for backup_file in sorted(
                self.backup_dir.glob("vbs_backup_*.db*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            ):
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size_mb': stat.st_size / (1024 * 1024),
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'age_hours': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
                })

            return backups

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    def get_backup_info(self) -> Dict[str, Any]:
        """Get backup system information"""
        backups = self.list_backups()
        total_size_mb = sum(b['size_mb'] for b in backups)

        return {
            'backup_dir': str(self.backup_dir),
            'total_backups': len(backups),
            'total_size_mb': total_size_mb,
            'max_backups': self.max_backups,
            'latest_backup': backups[0] if backups else None,
            'backups': backups
        }


class DataExporter:
    """Export data for migration or analysis"""

    def __init__(self, db_path: str = "backend/data/vbs.db"):
        self.db_path = Path(db_path)

    def export_to_json(self, output_path: str, tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export database to JSON format

        Args:
            output_path: Path for JSON export
            tables: List of tables to export (None = all tables)

        Returns:
            Export result
        """
        try:
            if not self.db_path.exists():
                return {
                    'success': False,
                    'error': 'Database not found'
                }

            logger.info(f"Exporting database to JSON: {output_path}")

            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column name access

            cursor = conn.cursor()

            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            all_tables = [row[0] for row in cursor.fetchall()]

            # Filter tables if specified
            tables_to_export = tables if tables else all_tables

            export_data = {}

            for table in tables_to_export:
                if table not in all_tables:
                    logger.warning(f"Table '{table}' not found, skipping")
                    continue

                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()

                # Convert rows to dictionaries
                export_data[table] = [dict(row) for row in rows]

                logger.info(f"  Exported {len(rows)} rows from '{table}'")

            conn.close()

            # Write to JSON file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)

            size_mb = output_file.stat().st_size / (1024 * 1024)

            logger.info(f"✅ Export completed: {size_mb:.2f} MB")

            return {
                'success': True,
                'output_path': str(output_file),
                'size_mb': size_mb,
                'tables_exported': list(export_data.keys()),
                'total_records': sum(len(rows) for rows in export_data.values())
            }

        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def export_to_sql(self, output_path: str) -> Dict[str, Any]:
        """
        Export database to SQL dump

        Args:
            output_path: Path for SQL dump

        Returns:
            Export result
        """
        try:
            if not self.db_path.exists():
                return {
                    'success': False,
                    'error': 'Database not found'
                }

            logger.info(f"Exporting database to SQL: {output_path}")

            conn = sqlite3.connect(str(self.db_path))
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                for line in conn.iterdump():
                    f.write(f"{line}\n")

            conn.close()

            size_mb = output_file.stat().st_size / (1024 * 1024)

            logger.info(f"✅ SQL export completed: {size_mb:.2f} MB")

            return {
                'success': True,
                'output_path': str(output_file),
                'size_mb': size_mb
            }

        except Exception as e:
            logger.error(f"Failed to export to SQL: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global backup manager instance
backup_manager = BackupManager()
data_exporter = DataExporter()


def create_backup(compress: bool = True) -> Dict[str, Any]:
    """Create database backup"""
    return backup_manager.create_database_backup(compress=compress)


def restore_backup(backup_path: str) -> Dict[str, Any]:
    """Restore database from backup"""
    return backup_manager.restore_database_backup(backup_path)


def list_backups() -> List[Dict[str, Any]]:
    """List all available backups"""
    return backup_manager.list_backups()


def get_backup_info() -> Dict[str, Any]:
    """Get backup system information"""
    return backup_manager.get_backup_info()


def export_to_json(output_path: str, tables: Optional[List[str]] = None) -> Dict[str, Any]:
    """Export database to JSON"""
    return data_exporter.export_to_json(output_path, tables)


def export_to_sql(output_path: str) -> Dict[str, Any]:
    """Export database to SQL dump"""
    return data_exporter.export_to_sql(output_path)
