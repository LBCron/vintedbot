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
                    status TEXT DEFAULT 'processing',  -- processing, completed, failed
                    progress_percent REAL DEFAULT 0.0,
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
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
            
            # 6. Users table (SaaS multi-user support)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    name TEXT,
                    plan TEXT DEFAULT 'free' CHECK(plan IN ('free','starter','pro','scale')),
                    status TEXT DEFAULT 'active' CHECK(status IN ('active','suspended','cancelled','trial')),
                    is_admin INTEGER DEFAULT 0,
                    trial_end_date TEXT,
                    stripe_customer_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add is_admin column to existing tables (migration)
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # 7. Subscriptions table (Stripe billing)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    stripe_subscription_id TEXT UNIQUE,
                    plan TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_period_start TEXT,
                    current_period_end TEXT,
                    cancel_at_period_end INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # 8. User quotas table (dynamic quota management)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_quotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    drafts_created INTEGER DEFAULT 0,
                    drafts_limit INTEGER DEFAULT 50,
                    publications_month INTEGER DEFAULT 0,
                    publications_limit INTEGER DEFAULT 10,
                    ai_analyses_month INTEGER DEFAULT 0,
                    ai_analyses_limit INTEGER DEFAULT 20,
                    photos_storage_mb INTEGER DEFAULT 0,
                    photos_storage_limit_mb INTEGER DEFAULT 500,
                    reset_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_user ON drafts(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_user ON listings(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_publog_idem ON publish_log(idempotency_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_plans_plan_id ON photo_plans(plan_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON bulk_jobs(job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotas_user ON user_quotas(user_id)")
            
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
            draft = self.get_draft(draft_id)
            return draft if draft else {}
    
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
    
    def reserve_publish_key(
        self,
        log_id: str,
        idempotency_key: str,
        confirm_token: str,
        user_id: Optional[str] = None
    ):
        """
        ATOMICALLY reserve an idempotency key before publish (raises sqlite3.IntegrityError on duplicate).
        This MUST be called BEFORE the external Vinted API call to prevent race conditions.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # NO ON CONFLICT - this will raise IntegrityError if key exists
            cursor.execute("""
                INSERT INTO publish_log (id, user_id, draft_id, idempotency_key, confirm_token, 
                                        dry_run, status, listing_url, error_json)
                VALUES (?, ?, NULL, ?, ?, 0, 'pending', NULL, NULL)
            """, (log_id, user_id, idempotency_key, confirm_token))
            conn.commit()
    
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
        """Update publish log after external publish (upserts if not exists)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO publish_log (id, user_id, draft_id, idempotency_key, confirm_token, 
                                        dry_run, status, listing_url, error_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(idempotency_key) DO UPDATE SET
                    draft_id = excluded.draft_id,
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
        draft_ids: Optional[List[str]] = None,
        status: Optional[str] = None,
        progress_percent: Optional[float] = None
    ):
        """Update plan with real detection results, draft IDs, and progress"""
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
            if status is not None:
                updates.append("status = ?")
                params.append(status)
                if status == "completed":
                    updates.append("completed_at = CURRENT_TIMESTAMP")
            if progress_percent is not None:
                updates.append("progress_percent = ?")
                params.append(progress_percent)
            
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
            
            # ✅ FIXED: Convert sqlite3.Row to dict to use .get()
            row_dict = dict(row)
            
            return {
                "plan_id": row_dict["plan_id"],
                "photo_paths": json.loads(row_dict["photo_paths"]),
                "photo_count": row_dict["photo_count"],
                "auto_grouping": bool(row_dict["auto_grouping"]),
                "estimated_items": row_dict["estimated_items"],
                "detected_items": row_dict["detected_items"],
                "draft_ids": json.loads(row_dict["draft_ids"]) if row_dict["draft_ids"] else [],
                "status": row_dict.get("status", "processing"),
                "progress_percent": row_dict.get("progress_percent", 0.0),
                "started_at": row_dict.get("started_at"),
                "completed_at": row_dict.get("completed_at"),
                "created_at": row_dict["created_at"]
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
    
    # ==================== USERS & AUTH ====================
    
    def create_user(
        self,
        email: str,
        hashed_password: str,
        name: Optional[str] = None,
        plan: str = "free"
    ) -> Dict[str, Any]:
        """Create a new user account"""
        # 🔓 Auto-mark admin emails (owner bypass quotas)
        admin_emails = ["ronan.chenlopes@hotmail.com"]
        is_admin = 1 if email.lower() in admin_emails else 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (email, hashed_password, name, plan, status, is_admin)
                VALUES (?, ?, ?, ?, 'active', ?)
            """, (email, hashed_password, name, plan, is_admin))
            user_id = cursor.lastrowid
            
            # Create default quotas for new user
            cursor.execute("""
                INSERT INTO user_quotas (
                    user_id, 
                    drafts_limit, 
                    publications_limit, 
                    ai_analyses_limit,
                    photos_storage_limit_mb,
                    reset_date
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                50 if plan == "free" else (200 if plan == "starter" else (1000 if plan == "pro" else 999999)),
                10 if plan == "free" else (50 if plan == "starter" else (200 if plan == "pro" else 999999)),
                20 if plan == "free" else (100 if plan == "starter" else (500 if plan == "pro" else 999999)),
                500 if plan == "free" else (2000 if plan == "starter" else (10000 if plan == "pro" else 99999)),
                (datetime.utcnow() + timedelta(days=30)).isoformat()
            ))
            
            conn.commit()
            # user_id is guaranteed to be int after lastrowid
            user = self.get_user_by_id(int(user_id))
            if not user:
                raise Exception("Failed to create user")
            return user
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email (for login)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "id": row["id"],
                "email": row["email"],
                "hashed_password": row["hashed_password"],
                "name": row["name"],
                "plan": row["plan"],
                "status": row["status"],
                "is_admin": bool(row["is_admin"]) if "is_admin" in row.keys() else False,
                "trial_end_date": row["trial_end_date"],
                "stripe_customer_id": row["stripe_customer_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "id": row["id"],
                "email": row["email"],
                "hashed_password": row["hashed_password"],
                "name": row["name"],
                "plan": row["plan"],
                "status": row["status"],
                "is_admin": bool(row["is_admin"]) if "is_admin" in row.keys() else False,
                "trial_end_date": row["trial_end_date"],
                "stripe_customer_id": row["stripe_customer_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    def get_user_quotas(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user quotas and current usage"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_quotas WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "user_id": row["user_id"],
                "drafts_created": row["drafts_created"],
                "drafts_limit": row["drafts_limit"],
                "publications_month": row["publications_month"],
                "publications_limit": row["publications_limit"],
                "ai_analyses_month": row["ai_analyses_month"],
                "ai_analyses_limit": row["ai_analyses_limit"],
                "photos_storage_mb": row["photos_storage_mb"],
                "photos_storage_limit_mb": row["photos_storage_limit_mb"],
                "reset_date": row["reset_date"]
            }
    
    def increment_quota_usage(
        self,
        user_id: int,
        quota_type: str,
        amount: int = 1
    ):
        """Increment quota usage (drafts_created, publications_month, ai_analyses_month)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            valid_types = ["drafts_created", "publications_month", "ai_analyses_month", "photos_storage_mb"]
            if quota_type not in valid_types:
                raise ValueError(f"Invalid quota_type: {quota_type}")
            
            cursor.execute(f"""
                UPDATE user_quotas 
                SET {quota_type} = {quota_type} + ?
                WHERE user_id = ?
            """, (amount, user_id))
            conn.commit()
    
    def check_quota_available(self, user_id: int, quota_type: str) -> bool:
        """Check if user has quota available for action"""
        quotas = self.get_user_quotas(user_id)
        if not quotas:
            return False
        
        quota_mappings = {
            "drafts": ("drafts_created", "drafts_limit"),
            "publications": ("publications_month", "publications_limit"),
            "ai_analyses": ("ai_analyses_month", "ai_analyses_limit")
        }
        
        if quota_type not in quota_mappings:
            return True
        
        used_field, limit_field = quota_mappings[quota_type]
        return quotas[used_field] < quotas[limit_field]
    
    # ==================== STRIPE INTEGRATION ====================
    
    def update_user_stripe_customer(self, user_id: int, customer_id: str):
        """Update user's Stripe customer ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET stripe_customer_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (customer_id, user_id))
            conn.commit()
    
    def update_user_subscription(
        self,
        user_id: int,
        plan: str,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None
    ):
        """Update user's subscription plan and Stripe IDs"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Update user plan
            if stripe_customer_id:
                cursor.execute("""
                    UPDATE users 
                    SET plan = ?, stripe_customer_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (plan, stripe_customer_id, user_id))
            else:
                cursor.execute("""
                    UPDATE users 
                    SET plan = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (plan, user_id))
            
            # Update or create subscription record
            if stripe_subscription_id:
                # Active subscription
                cursor.execute("""
                    INSERT OR REPLACE INTO subscriptions 
                    (user_id, stripe_subscription_id, plan, status, updated_at)
                    VALUES (?, ?, ?, 'active', CURRENT_TIMESTAMP)
                """, (user_id, stripe_subscription_id, plan))
            else:
                # Cancellation - mark existing subscriptions as cancelled
                cursor.execute("""
                    UPDATE subscriptions 
                    SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND status = 'active'
                """, (user_id,))
            
            conn.commit()
    
    def get_user_by_stripe_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Stripe customer ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM users WHERE stripe_customer_id = ?
            """, (customer_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "id": row["id"],
                "email": row["email"],
                "name": row["name"],
                "plan": row["plan"],
                "status": row["status"],
                "stripe_customer_id": row["stripe_customer_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }
    
    def update_user_quotas(self, user_id: int, quotas: Dict[str, int]):
        """Update user quota limits (when plan changes)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_quotas 
                SET 
                    drafts_limit = ?,
                    publications_limit = ?,
                    ai_analyses_limit = ?,
                    photos_storage_limit_mb = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (
                quotas.get("drafts", 50),
                quotas.get("publications_month", 10),
                quotas.get("ai_analyses_month", 20),
                quotas.get("photos_storage_mb", 500),
                user_id
            ))
            conn.commit()
    
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

# Alias for backward compatibility
get_storage = get_store
