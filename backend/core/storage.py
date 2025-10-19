"""
SQLite Storage Backend - Zero external dependencies, 100% local & persistent
Replaces PostgreSQL with file-based storage (data/vbs.db)
"""
import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path
from contextlib import contextmanager


# Environment configuration
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "sqlite")
TTL_DRAFTS_DAYS = int(os.getenv("TTL_DRAFTS_DAYS", "30"))
TTL_PUBLISH_LOG_DAYS = int(os.getenv("TTL_PUBLISH_LOG_DAYS", "90"))
DB_PATH = os.getenv("SQLITE_DB_PATH", "backend/data/vbs.db")


class SQLiteStore:
    """
    Local persistent storage using SQLite (zero cost, survives restarts)
    
    Features:
    - Drafts management with quality gate tracking
    - Publish log with idempotency protection
    - Listings inventory
    - Photo plans (migrated from PostgreSQL)
    - Automatic TTL-based purge (APScheduler job)
    """
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
    
    @contextmanager
    def get_connection(self):
        """Context manager for SQLite connections with proper cleanup"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_schema(self):
        """Initialize database schema with all tables and indexes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Drafts table (replaces in-memory draft storage)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drafts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL CHECK(price >= 0),
                    brand TEXT,
                    size TEXT,
                    color TEXT,
                    category TEXT,
                    item_json TEXT,  -- Full Item object as JSON
                    listing_json TEXT,  -- Vinted listing preparation data
                    flags_json TEXT,  -- PublishFlags as JSON
                    status TEXT CHECK(status IN ('pending','ready','prepared','published','error','manual')) DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. Listings table (active Vinted listings)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS listings (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    vinted_id TEXT UNIQUE,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    listing_url TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 3. Publish log (idempotency + audit trail)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS publish_log (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    draft_id TEXT,
                    idempotency_key TEXT UNIQUE,
                    confirm_token TEXT NOT NULL,
                    dry_run INTEGER NOT NULL DEFAULT 0,
                    status TEXT DEFAULT 'queued',
                    listing_url TEXT,
                    error_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 4. Photo plans (migrated from PostgreSQL)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS photo_plans (
                    plan_id TEXT PRIMARY KEY,
                    photo_paths TEXT NOT NULL,  -- JSON array
                    photo_count INTEGER NOT NULL,
                    auto_grouping INTEGER DEFAULT 0,
                    estimated_items INTEGER NOT NULL,
                    detected_items INTEGER,
                    draft_ids TEXT DEFAULT '[]',  -- JSON array
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 5. Bulk jobs (legacy ingest jobs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bulk_jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    total_photos INTEGER DEFAULT 0,
                    processed_photos INTEGER DEFAULT 0,
                    total_items INTEGER DEFAULT 0,
                    completed_items INTEGER DEFAULT 0,
                    failed_items INTEGER DEFAULT 0,
                    drafts TEXT DEFAULT '[]',  -- JSON array
                    errors TEXT DEFAULT '[]',  -- JSON array
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_user ON drafts(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_user ON listings(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_publog_idem ON publish_log(idempotency_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_plans_plan_id ON photo_plans(plan_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON bulk_jobs(job_id)")
            
            conn.commit()
    
    # ==================== DRAFTS ====================
    
    def save_draft(
        self,
        draft_id: str,
        title: str,
        description: str,
        price: float,
        brand: Optional[str] = None,
        size: Optional[str] = None,
        color: Optional[str] = None,
        category: Optional[str] = None,
        item_json: Optional[Dict] = None,
        listing_json: Optional[Dict] = None,
        flags_json: Optional[Dict] = None,
        status: str = "pending",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save a new draft after quality gate validation"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drafts (id, user_id, title, description, price, brand, size, color, category, 
                                   item_json, listing_json, flags_json, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                draft_id, user_id, title, description, price, brand, size, color, category,
                json.dumps(item_json) if item_json else None,
                json.dumps(listing_json) if listing_json else None,
                json.dumps(flags_json) if flags_json else None,
                status
            ))
            conn.commit()
            return self.get_draft(draft_id)
    
    def update_draft_status(self, draft_id: str, status: str, listing_json: Optional[Dict] = None):
        """Update draft status (e.g., pending -> ready -> prepared -> published)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if listing_json:
                cursor.execute("""
                    UPDATE drafts 
                    SET status = ?, listing_json = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, json.dumps(listing_json), draft_id))
            else:
                cursor.execute("""
                    UPDATE drafts 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, draft_id))
            conn.commit()
    
    def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        """Get single draft by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
            row = cursor.fetchone()
            return self._row_to_draft(row) if row else None
    
    def get_drafts(
        self, 
        status: Optional[str] = None, 
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get drafts with optional filtering"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM drafts WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [self._row_to_draft(row) for row in cursor.fetchall()]
    
    def _row_to_draft(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to draft dict"""
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "title": row["title"],
            "description": row["description"],
            "price": row["price"],
            "brand": row["brand"],
            "size": row["size"],
            "color": row["color"],
            "category": row["category"],
            "item_json": json.loads(row["item_json"]) if row["item_json"] else None,
            "listing_json": json.loads(row["listing_json"]) if row["listing_json"] else None,
            "flags_json": json.loads(row["flags_json"]) if row["flags_json"] else None,
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    
    # ==================== PUBLISH LOG ====================
    
    def log_publish(
        self,
        log_id: str,
        draft_id: str,
        idempotency_key: str,
        confirm_token: str,
        dry_run: bool = False,
        status: str = "queued",
        listing_url: Optional[str] = None,
        error_json: Optional[Dict] = None,
        user_id: Optional[str] = None
    ):
        """Log publish attempt with idempotency protection"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO publish_log (id, user_id, draft_id, idempotency_key, confirm_token, 
                                        dry_run, status, listing_url, error_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(idempotency_key) DO UPDATE SET
                    status = excluded.status,
                    listing_url = excluded.listing_url,
                    error_json = excluded.error_json
            """, (
                log_id, user_id, draft_id, idempotency_key, confirm_token,
                1 if dry_run else 0, status, listing_url,
                json.dumps(error_json) if error_json else None
            ))
            conn.commit()
    
    def seen_idempotency(self, idempotency_key: str) -> bool:
        """Check if idempotency key was already used (prevents duplicate publishes)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM publish_log WHERE idempotency_key = ?", (idempotency_key,))
            return cursor.fetchone() is not None
    
    # ==================== LISTINGS ====================
    
    def upsert_listing(
        self,
        listing_id: str,
        title: str,
        price: float,
        vinted_id: Optional[str] = None,
        listing_url: Optional[str] = None,
        status: str = "active",
        user_id: Optional[str] = None
    ):
        """Create or update a Vinted listing record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO listings (id, user_id, vinted_id, title, price, listing_url, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    vinted_id = excluded.vinted_id,
                    listing_url = excluded.listing_url,
                    status = excluded.status,
                    updated_at = CURRENT_TIMESTAMP
            """, (listing_id, user_id, vinted_id, title, price, listing_url, status))
            conn.commit()
    
    # ==================== PHOTO PLANS ====================
    
    def save_photo_plan(
        self,
        plan_id: str,
        photo_paths: List[str],
        photo_count: int,
        auto_grouping: bool,
        estimated_items: int
    ):
        """Save photo analysis plan (migrated from PostgreSQL)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO photo_plans (plan_id, photo_paths, photo_count, auto_grouping, estimated_items)
                VALUES (?, ?, ?, ?, ?)
            """, (plan_id, json.dumps(photo_paths), photo_count, 1 if auto_grouping else 0, estimated_items))
            conn.commit()
    
    def update_photo_plan(
        self,
        plan_id: str,
        detected_items: Optional[int] = None,
        draft_ids: Optional[List[str]] = None
    ):
        """Update plan with real detection results and draft IDs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if detected_items is not None:
                updates.append("detected_items = ?")
                params.append(detected_items)
            if draft_ids is not None:
                updates.append("draft_ids = ?")
                params.append(json.dumps(draft_ids))
            
            if updates:
                query = f"UPDATE photo_plans SET {', '.join(updates)} WHERE plan_id = ?"
                params.append(plan_id)
                cursor.execute(query, params)
                conn.commit()
    
    def get_photo_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get photo plan by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM photo_plans WHERE plan_id = ?", (plan_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "plan_id": row["plan_id"],
                "photo_paths": json.loads(row["photo_paths"]),
                "photo_count": row["photo_count"],
                "auto_grouping": bool(row["auto_grouping"]),
                "estimated_items": row["estimated_items"],
                "detected_items": row["detected_items"],
                "draft_ids": json.loads(row["draft_ids"]) if row["draft_ids"] else [],
                "created_at": row["created_at"]
            }
    
    # ==================== BULK JOBS ====================
    
    def save_bulk_job(self, job_id: str, status: str, total_photos: int = 0):
        """Save bulk processing job"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bulk_jobs (job_id, status, total_photos)
                VALUES (?, ?, ?)
            """, (job_id, status, total_photos))
            conn.commit()
    
    def update_bulk_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        drafts: Optional[List[str]] = None,
        errors: Optional[List[str]] = None
    ):
        """Update bulk job progress"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if status:
                updates.append("status = ?")
                params.append(status)
            if drafts is not None:
                updates.append("drafts = ?")
                params.append(json.dumps(drafts))
            if errors is not None:
                updates.append("errors = ?")
                params.append(json.dumps(errors))
            
            if updates:
                query = f"UPDATE bulk_jobs SET {', '.join(updates)} WHERE job_id = ?"
                params.append(job_id)
                cursor.execute(query, params)
                conn.commit()
    
    def get_bulk_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get bulk job by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bulk_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "job_id": row["job_id"],
                "status": row["status"],
                "total_photos": row["total_photos"],
                "processed_photos": row["processed_photos"],
                "total_items": row["total_items"],
                "completed_items": row["completed_items"],
                "failed_items": row["failed_items"],
                "drafts": json.loads(row["drafts"]) if row["drafts"] else [],
                "errors": json.loads(row["errors"]) if row["errors"] else [],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"]
            }
    
    # ==================== TTL & MAINTENANCE ====================
    
    def vacuum_and_prune(self):
        """
        Daily maintenance job (runs at 02:00 via APScheduler):
        1. Delete old published/error drafts (TTL_DRAFTS_DAYS)
        2. Purge old publish logs (TTL_PUBLISH_LOG_DAYS)
        3. VACUUM database to reclaim space
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Calculate cutoff dates
            draft_cutoff = (datetime.utcnow() - timedelta(days=TTL_DRAFTS_DAYS)).isoformat()
            log_cutoff = (datetime.utcnow() - timedelta(days=TTL_PUBLISH_LOG_DAYS)).isoformat()
            
            # 1. Delete old drafts (published or error status only)
            cursor.execute("""
                DELETE FROM drafts 
                WHERE status IN ('published', 'error') 
                AND created_at < ?
            """, (draft_cutoff,))
            deleted_drafts = cursor.rowcount
            
            # 2. Purge old publish logs
            cursor.execute("""
                DELETE FROM publish_log 
                WHERE created_at < ?
            """, (log_cutoff,))
            deleted_logs = cursor.rowcount
            
            conn.commit()
            
            # 3. VACUUM to reclaim space
            cursor.execute("VACUUM")
            
            return {
                "deleted_drafts": deleted_drafts,
                "deleted_logs": deleted_logs,
                "draft_ttl_days": TTL_DRAFTS_DAYS,
                "log_ttl_days": TTL_PUBLISH_LOG_DAYS
            }


# Global instance
_store: Optional[SQLiteStore] = None

def get_store() -> SQLiteStore:
    """Get or create SQLiteStore singleton"""
    global _store
    if _store is None:
        _store = SQLiteStore()
    return _store
