"""
Automatic Cookie Management & Rotation
Gère les cookies Vinted, détecte l'expiration, et permet la rotation
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger
import base64
from cryptography.fernet import Fernet
import os


class CookieManager:
    """Manage Vinted cookies with encryption and rotation"""

    def __init__(self, db_path: str = "backend/data/cookies.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self._init_database()

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for cookies"""
        key_file = Path("backend/data/.cookie_key")
        key_file.parent.mkdir(parents=True, exist_ok=True)

        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Secure the key file (Unix only)
            try:
                os.chmod(key_file, 0o600)
            except:
                pass
            return key

    def _init_database(self):
        """Initialize cookie database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                cookie_encrypted BLOB NOT NULL,
                user_agent TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                last_checked TIMESTAMP,
                expires_at TIMESTAMP,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cookie_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie_id INTEGER NOT NULL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (cookie_id) REFERENCES cookies(id)
            )
        """)

        conn.commit()
        conn.close()

    def add_cookie(
        self,
        name: str,
        cookie: str,
        user_agent: str,
        expires_days: int = 30,
        notes: Optional[str] = None
    ) -> bool:
        """
        Add new cookie to rotation

        Args:
            name: Friendly name for the cookie
            cookie: Cookie string
            user_agent: User agent to use with this cookie
            expires_days: Days until cookie expires
            notes: Optional notes

        Returns:
            True if added successfully
        """
        try:
            # Encrypt cookie
            cookie_encrypted = self.cipher.encrypt(cookie.encode())

            expires_at = datetime.now() + timedelta(days=expires_days)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO cookies
                (name, cookie_encrypted, user_agent, expires_at, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (name, cookie_encrypted, user_agent, expires_at.isoformat(), notes))

            conn.commit()
            conn.close()

            logger.info(f"[OK] Cookie added: {name}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Failed to add cookie: {e}")
            return False

    def get_cookie(self, name: str) -> Optional[Dict]:
        """
        Get cookie by name

        Args:
            name: Cookie name

        Returns:
            Cookie dict or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM cookies WHERE name = ? AND status = 'active'
            """, (name,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            # Decrypt cookie
            cookie_decrypted = self.cipher.decrypt(row['cookie_encrypted']).decode()

            return {
                'id': row['id'],
                'name': row['name'],
                'cookie': cookie_decrypted,
                'user_agent': row['user_agent'],
                'status': row['status'],
                'expires_at': row['expires_at']
            }

        except Exception as e:
            logger.error(f"[ERROR] Failed to get cookie: {e}")
            return None

    def get_next_cookie(self) -> Optional[Dict]:
        """
        Get next active cookie in rotation

        Returns:
            Cookie dict or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get least recently used active cookie that hasn't expired
            cursor.execute("""
                SELECT * FROM cookies
                WHERE status = 'active'
                AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY last_used ASC NULLS FIRST
                LIMIT 1
            """, (datetime.now().isoformat(),))

            row = cursor.fetchone()
            conn.close()

            if not row:
                logger.warning("[WARN] No active cookies available")
                return None

            # Decrypt cookie
            cookie_decrypted = self.cipher.decrypt(row['cookie_encrypted']).decode()

            # Update last_used
            self._update_last_used(row['id'])

            return {
                'id': row['id'],
                'name': row['name'],
                'cookie': cookie_decrypted,
                'user_agent': row['user_agent'],
                'status': row['status'],
                'expires_at': row['expires_at']
            }

        except Exception as e:
            logger.error(f"[ERROR] Failed to get next cookie: {e}")
            return None

    def _update_last_used(self, cookie_id: int):
        """Update last_used timestamp"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE cookies SET last_used = ? WHERE id = ?
            """, (datetime.now().isoformat(), cookie_id))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"[ERROR] Failed to update last_used: {e}")

    def mark_cookie_failed(self, cookie_id: int, error_message: str = None):
        """
        Mark cookie as failed

        Args:
            cookie_id: Cookie ID
            error_message: Optional error message
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Mark cookie as failed
            cursor.execute("""
                UPDATE cookies SET status = 'failed' WHERE id = ?
            """, (cookie_id,))

            # Log usage
            cursor.execute("""
                INSERT INTO cookie_usage (cookie_id, success, error_message)
                VALUES (?, ?, ?)
            """, (cookie_id, False, error_message))

            conn.commit()
            conn.close()

            logger.warning(f"[WARN] Cookie marked as failed: ID {cookie_id}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to mark cookie as failed: {e}")

    def list_cookies(self, include_expired: bool = False) -> List[Dict]:
        """
        List all cookies

        Args:
            include_expired: Include expired cookies

        Returns:
            List of cookie dicts (without decrypted cookie values)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if include_expired:
                cursor.execute("SELECT id, name, status, created_at, last_used, expires_at FROM cookies")
            else:
                cursor.execute("""
                    SELECT id, name, status, created_at, last_used, expires_at
                    FROM cookies
                    WHERE expires_at IS NULL OR expires_at > ?
                """, (datetime.now().isoformat(),))

            rows = cursor.fetchall()
            conn.close()

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"[ERROR] Failed to list cookies: {e}")
            return []

    def cleanup_expired_cookies(self):
        """Remove expired cookies"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE cookies SET status = 'expired'
                WHERE expires_at <= ? AND status = 'active'
            """, (datetime.now().isoformat(),))

            expired_count = cursor.rowcount
            conn.commit()
            conn.close()

            if expired_count > 0:
                logger.info(f"🗑️ Marked {expired_count} cookies as expired")

        except Exception as e:
            logger.error(f"[ERROR] Failed to cleanup cookies: {e}")

    def get_stats(self) -> Dict:
        """Get cookie statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Count by status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM cookies
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())

            # Total usage
            cursor.execute("SELECT COUNT(*) FROM cookie_usage")
            total_usage = cursor.fetchone()[0]

            # Success rate
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                FROM cookie_usage
            """)
            success_rate = cursor.fetchone()[0] or 0

            conn.close()

            return {
                'status_counts': status_counts,
                'total_usage': total_usage,
                'success_rate': success_rate
            }

        except Exception as e:
            logger.error(f"[ERROR] Failed to get stats: {e}")
            return {}


if __name__ == "__main__":
    # Test cookie manager
    manager = CookieManager()

    # Add test cookie
    manager.add_cookie(
        name="test_account_1",
        cookie="_vinted_fr_session=test123; _ga=GA1.2.123456789",
        user_agent="Mozilla/5.0...",
        expires_days=30,
        notes="Test account"
    )

    # List cookies
    print("\n[INFO] Available cookies:")
    for cookie in manager.list_cookies():
        print(f"  - {cookie['name']} (Status: {cookie['status']})")

    # Get next cookie
    print("\n[PROCESS] Getting next cookie:")
    next_cookie = manager.get_next_cookie()
    if next_cookie:
        print(f"  Selected: {next_cookie['name']}")

    # Stats
    print("\n📊 Cookie stats:")
    stats = manager.get_stats()
    print(f"  Status counts: {stats.get('status_counts', {})}")
    print(f"  Total usage: {stats.get('total_usage', 0)}")
    print(f"  Success rate: {stats.get('success_rate', 0):.1f}%")
