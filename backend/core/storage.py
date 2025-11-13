"""
SQLite Storage Backend - Zero external dependencies, 100% local & persistent
Replaces PostgreSQL with file-based storage (data/vbs.db)
"""
import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from contextlib import contextmanager
import imagehash
from PIL import Image


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
                    vinted_draft_url TEXT,  -- URL to Vinted draft (for draft mode)
                    vinted_draft_id TEXT,  -- Vinted draft ID
                    publish_mode TEXT DEFAULT 'auto' CHECK(publish_mode IN ('auto','draft')),  -- 'auto' = direct publish, 'draft' = save as draft
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Migration: Add draft mode columns to existing tables
            try:
                cursor.execute("ALTER TABLE drafts ADD COLUMN vinted_draft_url TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE drafts ADD COLUMN vinted_draft_id TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE drafts ADD COLUMN publish_mode TEXT DEFAULT 'auto'")
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Stock Management columns (Dotb feature)
            try:
                cursor.execute("ALTER TABLE drafts ADD COLUMN sku TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute("ALTER TABLE drafts ADD COLUMN location TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                cursor.execute("ALTER TABLE drafts ADD COLUMN stock_quantity INTEGER DEFAULT 1")
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Create index for SKU searches
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_sku ON drafts(sku)")
            except sqlite3.OperationalError:
                pass

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
            
            # Migration: Add category column to listings table for analytics
            try:
                cursor.execute("ALTER TABLE listings ADD COLUMN category TEXT")
            except sqlite3.OperationalError:
                pass
            
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
            
            # ========== PREMIUM FEATURES TABLES (Nov 2025) ==========
            
            # 9. Analytics Events (track views, likes, messages for statistics)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT NOT NULL,
                    event_type TEXT NOT NULL CHECK(event_type IN ('view','like','message','sale','bump')),
                    user_id TEXT,
                    source TEXT DEFAULT 'organic',
                    metadata TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
                )
            """)
            
            # 10. Aggregated Metrics (daily/weekly stats for performance)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aggregated_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    listing_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    views INT DEFAULT 0,
                    likes INT DEFAULT 0,
                    messages INT DEFAULT 0,
                    sales INT DEFAULT 0,
                    bumps INT DEFAULT 0,
                    UNIQUE(listing_id, date),
                    FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE
                )
            """)
            
            # 11. Automation Rules (auto-bump, auto-follow, auto-messages config)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS automation_rules (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('bump','follow','unfollow','favorite','message','price_drop')),
                    config TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    last_run TEXT,
                    next_run TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # 12. Automation Jobs (execution log for automation tasks)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS automation_jobs (
                    id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending' CHECK(status IN ('pending','running','completed','failed','paused')),
                    target_id TEXT,
                    result TEXT,
                    error TEXT,
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    FOREIGN KEY (rule_id) REFERENCES automation_rules(id) ON DELETE CASCADE
                )
            """)
            
            # 13. Vinted Accounts (multi-account management)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vinted_accounts (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    nickname TEXT NOT NULL,
                    vinted_username TEXT,
                    vinted_user_id TEXT,
                    encrypted_cookie TEXT NOT NULL,
                    user_agent TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_default INTEGER DEFAULT 0,
                    last_used TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # 14. Message Templates (for auto-messages)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_templates (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    trigger TEXT CHECK(trigger IN ('like','follow','message_received')),
                    template TEXT NOT NULL,
                    delay_minutes INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # 15. Conversations (inbox tracking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    vinted_conversation_id TEXT UNIQUE,
                    other_user_id TEXT,
                    other_username TEXT,
                    listing_id TEXT,
                    last_message TEXT,
                    last_message_at TEXT,
                    unread_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active' CHECK(status IN ('active','archived','spam')),
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # 16. Follow Tracking (for auto-follow/unfollow)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    vinted_user_id TEXT NOT NULL,
                    followed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    unfollowed_at TEXT,
                    follow_back INTEGER DEFAULT 0,
                    source TEXT DEFAULT 'manual',
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # 17. Orders (Dotb feature - order management and tracking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    vinted_order_id TEXT UNIQUE,
                    item_id TEXT,
                    item_title TEXT NOT NULL,
                    price REAL NOT NULL,
                    buyer_id TEXT,
                    buyer_name TEXT,
                    status TEXT DEFAULT 'pending' CHECK(status IN ('pending','paid','shipped','completed','cancelled','disputed')),
                    tracking_number TEXT,
                    shipping_carrier TEXT,
                    payment_method TEXT,
                    shipping_address TEXT,
                    notes TEXT,
                    feedback_sent INTEGER DEFAULT 0,
                    feedback_rating INTEGER,
                    feedback_comment TEXT,
                    vinted_conversation_id TEXT,
                    order_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    paid_at TEXT,
                    shipped_at TEXT,
                    completed_at TEXT,
                    cancelled_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_user ON drafts(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_user ON listings(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_listings_vinted_id ON listings(vinted_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_publog_idem ON publish_log(idempotency_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_plans_plan_id ON photo_plans(plan_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON bulk_jobs(job_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_quotas_user ON user_quotas(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_listing ON analytics_events(listing_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON analytics_events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON analytics_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_listing ON aggregated_metrics(listing_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_date ON aggregated_metrics(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_automation_user ON automation_rules(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_automation_type ON automation_rules(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_rule ON automation_jobs(rule_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON automation_jobs(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_user ON vinted_accounts(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_user ON message_templates(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_follows_user ON follows(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_follows_vinted_user ON follows(vinted_user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_vinted_id ON orders(vinted_order_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)")

            conn.commit()
    
    # ==================== DRAFTS ====================
    
    def deduplicate_photos(self, photos: List[str]) -> List[str]:
        """
        Remove duplicate photos using perceptual hashing (imagehash)
        
        Args:
            photos: List of photo paths
            
        Returns:
            List of unique photo paths (duplicates removed)
        """
        if not photos:
            return []
        
        unique_photos = []
        seen_hashes = set()
        
        for photo_path in photos:
            try:
                # Skip if photo doesn't exist
                if not Path(photo_path).exists():
                    print(f"⚠️ Photo not found: {photo_path}")
                    continue
                
                # Compute perceptual hash
                img = Image.open(photo_path)
                img_hash = str(imagehash.phash(img))
                
                # Check if hash already seen
                if img_hash not in seen_hashes:
                    seen_hashes.add(img_hash)
                    unique_photos.append(photo_path)
                else:
                    print(f"🗑️ Duplicate photo detected: {Path(photo_path).name}")
            
            except Exception as e:
                print(f"⚠️ Error processing photo {photo_path}: {e}")
                # Keep photo anyway (conservative approach)
                unique_photos.append(photo_path)
        
        removed_count = len(photos) - len(unique_photos)
        if removed_count > 0:
            print(f"✅ Removed {removed_count} duplicate photo(s)")
        
        return unique_photos
    
    def find_duplicate_draft(
        self,
        title: str,
        brand: Optional[str] = None,
        size: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find potential duplicate draft using FLEXIBLE matching (not exact)
        Uses rapidfuzz for title similarity (>85% = duplicate)
        Returns existing draft if found, None otherwise
        """
        from rapidfuzz import fuzz
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First pass: get all drafts with same brand + category + user
            # (don't require exact title match)
            query = """
                SELECT * FROM drafts 
                WHERE brand = ? 
                AND category = ?
                AND status IN ('pending', 'ready')
            """
            params = [brand, category]
            
            # Add user filter if provided
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Second pass: check title similarity with rapidfuzz
            for row in rows:
                existing_title = row["title"]
                similarity = fuzz.ratio(title.lower(), existing_title.lower())
                
                # If titles are >85% similar, consider it a duplicate
                if similarity >= 85:
                    print(f"🔍 Duplicate found via similarity: {similarity}% match")
                    print(f"   New: '{title}'")
                    print(f"   Existing: '{existing_title}'")
                    return self._row_to_draft(row)
            
            return None
    
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
        user_id: Optional[str] = None,
        skip_duplicate_check: bool = False,
        sku: Optional[str] = None,
        location: Optional[str] = None,
        stock_quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Save a new draft after quality gate validation
        
        If duplicate detected → MERGE photos (deduplicated) instead of rejecting
        
        Args:
            skip_duplicate_check: If True, skip duplicate detection (default: False)
        
        Returns:
            Saved draft dict (new or merged)
        """
        # Check for duplicates (unless explicitly skipped)
        if not skip_duplicate_check:
            existing = self.find_duplicate_draft(title, brand, size, category, user_id)
            if existing:
                print(f"🔄 Duplicate draft detected: {title}")
                print(f"   Existing ID: {existing['id'][:8]}...")
                
                # Extract existing JSON data (fallback to empty dicts) - CORRECT KEYS!
                existing_item = existing.get("item_json") or {}
                existing_listing = existing.get("listing_json") or {}
                existing_photos = existing_item.get("photos", []) if isinstance(existing_item, dict) else []
                
                # If new item_json is None, use existing data (CRITICAL: don't erase!)
                merged_item_json = item_json if item_json is not None else (existing_item.copy() if existing_item else {})
                merged_listing_json = listing_json if listing_json is not None else (existing_listing.copy() if existing_listing else {})
                
                # Extract new photos
                new_photos = merged_item_json.get("photos", [])
                
                # Combine and deduplicate photos
                all_photos = existing_photos + new_photos
                unique_photos = self.deduplicate_photos(all_photos)
                
                print(f"   Photos: {len(existing_photos)} existing + {len(new_photos)} new = {len(unique_photos)} unique")
                
                # Update BOTH item_json AND listing_json with merged photos
                merged_item_json["photos"] = unique_photos
                merged_listing_json["photos"] = unique_photos
                
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE drafts 
                        SET item_json = ?, listing_json = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        json.dumps(merged_item_json),
                        json.dumps(merged_listing_json),
                        existing["id"]
                    ))
                    conn.commit()
                
                print(f"✅ Draft merged successfully (item_json + listing_json synced)!")
                return self.get_draft(existing["id"]) or existing
        
        # No duplicate → create new draft
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drafts (id, user_id, title, description, price, brand, size, color, category,
                                   item_json, listing_json, flags_json, status, sku, location, stock_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                draft_id, user_id, title, description, price, brand, size, color, category,
                json.dumps(item_json) if item_json else None,
                json.dumps(listing_json) if listing_json else None,
                json.dumps(flags_json) if flags_json else None,
                status, sku, location, stock_quantity
            ))
            conn.commit()
            draft = self.get_draft(draft_id)
            return draft if draft else {}

    def update_draft(
        self,
        draft_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[float] = None,
        brand: Optional[str] = None,
        size: Optional[str] = None,
        color: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        sku: Optional[str] = None,
        location: Optional[str] = None,
        stock_quantity: Optional[int] = None
    ):
        """Update draft fields (including stock management fields)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Build dynamic UPDATE query based on provided fields
            update_fields = []
            values = []

            if title is not None:
                update_fields.append("title = ?")
                values.append(title)
            if description is not None:
                update_fields.append("description = ?")
                values.append(description)
            if price is not None:
                update_fields.append("price = ?")
                values.append(price)
            if brand is not None:
                update_fields.append("brand = ?")
                values.append(brand)
            if size is not None:
                update_fields.append("size = ?")
                values.append(size)
            if color is not None:
                update_fields.append("color = ?")
                values.append(color)
            if category is not None:
                update_fields.append("category = ?")
                values.append(category)
            if status is not None:
                update_fields.append("status = ?")
                values.append(status)
            if sku is not None:
                update_fields.append("sku = ?")
                values.append(sku)
            if location is not None:
                update_fields.append("location = ?")
                values.append(location)
            if stock_quantity is not None:
                update_fields.append("stock_quantity = ?")
                values.append(stock_quantity)

            # Always update timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")

            if not update_fields:
                return  # Nothing to update

            # Add draft_id to values for WHERE clause
            values.append(draft_id)

            query = f"UPDATE drafts SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()

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
    
    def update_draft_photos(self, draft_id: str, photos: List[str]):
        """Update draft photos list"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get current item_json
            cursor.execute("SELECT item_json FROM drafts WHERE id = ?", (draft_id,))
            row = cursor.fetchone()
            if not row:
                return
            
            item_json = json.loads(row["item_json"]) if row["item_json"] else {}
            item_json["photos"] = photos
            
            # Update item_json with new photos
            cursor.execute("""
                UPDATE drafts 
                SET item_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(item_json), draft_id))
            conn.commit()
    
    def update_draft_vinted_info(self, draft_id: str, vinted_draft_url: Optional[str], vinted_draft_id: Optional[str], publish_mode: str = "auto"):
        """Update draft with Vinted draft information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE drafts 
                SET vinted_draft_url = ?, vinted_draft_id = ?, publish_mode = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (vinted_draft_url, vinted_draft_id, publish_mode, draft_id))
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
        # ✅ FIXED: Convert sqlite3.Row to dict to use .get() for optional fields
        row_dict = dict(row)
        return {
            "id": row_dict["id"],
            "user_id": row_dict["user_id"],
            "title": row_dict["title"],
            "description": row_dict["description"],
            "price": row_dict["price"],
            "brand": row_dict["brand"],
            "size": row_dict["size"],
            "color": row_dict["color"],
            "category": row_dict["category"],
            "item_json": json.loads(row_dict["item_json"]) if row_dict["item_json"] else None,
            "listing_json": json.loads(row_dict["listing_json"]) if row_dict["listing_json"] else None,
            "flags_json": json.loads(row_dict["flags_json"]) if row_dict["flags_json"] else None,
            "status": row_dict["status"],
            "sku": row_dict.get("sku"),
            "location": row_dict.get("location"),
            "stock_quantity": row_dict.get("stock_quantity", 1),
            "created_at": row_dict["created_at"],
            "updated_at": row_dict["updated_at"]
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
    
    def get_listing(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """Get a listing by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM listings WHERE id = ?", (listing_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)
    
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
        admin_emails = ["ronan.chenlopes@hotmail.com", "ronanchenlopes@gmail.com"]
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
            # user_id should be int after lastrowid
            if user_id is None:
                raise Exception("Failed to create user: no ID returned")
            user = self.get_user_by_id(user_id)
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

    def get_vinted_session_for_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the default active Vinted account for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Prioritize the default active account
            cursor.execute("""
                SELECT encrypted_cookie, user_agent FROM vinted_accounts
                WHERE user_id = ? AND is_active = 1
                ORDER BY is_default DESC
                LIMIT 1
            """, (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            from backend.utils.crypto import decrypt_blob
            decrypted_cookie = decrypt_blob(row["encrypted_cookie"])

            return {
                "cookie": decrypted_cookie,
                "user_agent": row["user_agent"]
            }

    def add_vinted_account(
        self,
        user_id: str,
        nickname: str,
        cookie: str,
        user_agent: str,
        is_default: bool = False
    ) -> str:
        """Add a new Vinted account for a user"""
        import uuid
        from backend.utils.crypto import encrypt_blob

        account_id = str(uuid.uuid4())
        encrypted_cookie = encrypt_blob(cookie)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if an account with the same nickname already exists for this user
            cursor.execute("""
                SELECT id FROM vinted_accounts
                WHERE user_id = ? AND nickname = ?
            """, (user_id, nickname))

            if cursor.fetchone():
                raise ValueError(f"Un compte avec le nom '{nickname}' existe déjà. Veuillez choisir un autre nom.")

            # If this is set as default, unset other defaults
            if is_default:
                cursor.execute("""
                    UPDATE vinted_accounts
                    SET is_default = 0
                    WHERE user_id = ?
                """, (user_id,))

            # Insert new account
            cursor.execute("""
                INSERT INTO vinted_accounts (
                    id, user_id, nickname, encrypted_cookie, user_agent,
                    is_active, is_default, last_used, created_at
                ) VALUES (?, ?, ?, ?, ?, 1, ?, datetime('now'), datetime('now'))
            """, (account_id, user_id, nickname, encrypted_cookie, user_agent, 1 if is_default else 0))

            conn.commit()

        return account_id

    def get_user_vinted_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all Vinted accounts for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nickname, vinted_username, vinted_user_id,
                       is_active, is_default, last_used, created_at
                FROM vinted_accounts
                WHERE user_id = ?
                ORDER BY is_default DESC, last_used DESC
            """, (user_id,))

            accounts = []
            for row in cursor.fetchall():
                accounts.append({
                    "id": row["id"],
                    "nickname": row["nickname"],
                    "vinted_username": row["vinted_username"],
                    "vinted_user_id": row["vinted_user_id"],
                    "is_active": bool(row["is_active"]),
                    "is_default": bool(row["is_default"]),
                    "last_used": row["last_used"],
                    "created_at": row["created_at"]
                })

            return accounts

    def delete_vinted_account(self, user_id: str, account_id: str) -> bool:
        """Delete a Vinted account for a user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Verify the account belongs to this user
            cursor.execute("""
                SELECT id FROM vinted_accounts
                WHERE id = ? AND user_id = ?
            """, (account_id, user_id))

            if not cursor.fetchone():
                return False

            # Delete the account
            cursor.execute("""
                DELETE FROM vinted_accounts
                WHERE id = ? AND user_id = ?
            """, (account_id, user_id))

            conn.commit()
            return True

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
    
    def delete_draft(self, draft_id: str) -> bool:
        """
        Delete a draft from SQLite database
        
        Returns:
            True if deleted, False if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                print(f"🗑️ Draft {draft_id[:8]}... deleted from SQLite")
            return deleted
    
    # ==================== ANALYTICS ====================
    
    def track_analytics_event(
        self,
        listing_id: str,
        event_type: str,
        user_id: Optional[str] = None,
        source: str = "organic",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track an analytics event (view, like, message, sale, bump)
        
        Args:
            listing_id: Listing ID
            event_type: 'view', 'like', 'message', 'sale', 'bump'
            user_id: Vinted user ID (who performed action)
            source: 'organic', 'search', 'profile', 'bump'
            metadata: Additional metadata as JSON
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO analytics_events 
                (listing_id, event_type, user_id, source, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                listing_id,
                event_type,
                user_id,
                source,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
    
    def aggregate_daily_metrics(self, date: Optional[str] = None):
        """
        Aggregate analytics events into daily metrics
        Run this as a scheduled job daily
        
        Args:
            date: Date to aggregate (YYYY-MM-DD), defaults to yesterday
        """
        if not date:
            date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Aggregate events per listing per day
            cursor.execute("""
                INSERT OR REPLACE INTO aggregated_metrics 
                (listing_id, date, views, likes, messages, sales, bumps)
                SELECT 
                    listing_id,
                    DATE(timestamp) as date,
                    SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) as views,
                    SUM(CASE WHEN event_type = 'like' THEN 1 ELSE 0 END) as likes,
                    SUM(CASE WHEN event_type = 'message' THEN 1 ELSE 0 END) as messages,
                    SUM(CASE WHEN event_type = 'sale' THEN 1 ELSE 0 END) as sales,
                    SUM(CASE WHEN event_type = 'bump' THEN 1 ELSE 0 END) as bumps
                FROM analytics_events
                WHERE DATE(timestamp) = ?
                GROUP BY listing_id, DATE(timestamp)
            """, (date,))
            conn.commit()
    
    def get_dashboard_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get dashboard analytics stats for a user
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            Dictionary with total stats and time-based breakdowns
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        today_start = datetime.utcnow().strftime('%Y-%m-%d')
        week_start = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get user's listings
            cursor.execute("""
                SELECT id FROM listings 
                WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            listing_ids = [row["id"] for row in cursor.fetchall()]
            
            if not listing_ids:
                return {
                    "total_listings": 0,
                    "active_listings": 0,
                    "total_views": 0,
                    "views_today": 0,
                    "views_week": 0,
                    "total_likes": 0,
                    "likes_today": 0,
                    "total_messages": 0,
                    "avg_conversion_rate": 0.0
                }
            
            # Total stats across all time
            placeholders = ','.join('?' * len(listing_ids))
            cursor.execute(f"""
                SELECT 
                    SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) as total_views,
                    SUM(CASE WHEN event_type = 'like' THEN 1 ELSE 0 END) as total_likes,
                    SUM(CASE WHEN event_type = 'message' THEN 1 ELSE 0 END) as total_messages
                FROM analytics_events
                WHERE listing_id IN ({placeholders})
                AND timestamp >= ?
            """, (*listing_ids, cutoff_date))
            totals = cursor.fetchone()
            
            # Today's stats
            cursor.execute(f"""
                SELECT 
                    SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) as views_today,
                    SUM(CASE WHEN event_type = 'like' THEN 1 ELSE 0 END) as likes_today
                FROM analytics_events
                WHERE listing_id IN ({placeholders})
                AND DATE(timestamp) = ?
            """, (*listing_ids, today_start))
            today = cursor.fetchone()
            
            # Week's views
            cursor.execute(f"""
                SELECT COUNT(*) as views_week
                FROM analytics_events
                WHERE listing_id IN ({placeholders})
                AND event_type = 'view'
                AND timestamp >= ?
            """, (*listing_ids, week_start))
            week = cursor.fetchone()
            
            total_views = totals["total_views"] or 0
            total_messages = totals["total_messages"] or 0
            conversion_rate = (total_messages / total_views * 100) if total_views > 0 else 0.0
            
            return {
                "total_listings": len(listing_ids),
                "active_listings": len(listing_ids),
                "total_views": total_views,
                "views_today": today["views_today"] or 0,
                "views_week": week["views_week"] or 0,
                "total_likes": totals["total_likes"] or 0,
                "likes_today": today["likes_today"] or 0,
                "total_messages": total_messages,
                "avg_conversion_rate": round(conversion_rate, 2)
            }
    
    def get_performance_heatmap(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get performance heatmap (best times to post by day/hour)
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            List of heatmap entries with day_of_week, hour, and metrics
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get user's listings
            cursor.execute("""
                SELECT id FROM listings WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            listing_ids = [row["id"] for row in cursor.fetchall()]
            
            if not listing_ids:
                return []
            
            placeholders = ','.join('?' * len(listing_ids))
            
            # Group by day of week and hour
            cursor.execute(f"""
                SELECT 
                    CAST(strftime('%w', timestamp) AS INTEGER) as day_of_week,
                    CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                    SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) as views,
                    SUM(CASE WHEN event_type = 'like' THEN 1 ELSE 0 END) as likes,
                    SUM(CASE WHEN event_type = 'message' THEN 1 ELSE 0 END) as messages
                FROM analytics_events
                WHERE listing_id IN ({placeholders})
                AND timestamp >= ?
                GROUP BY day_of_week, hour
                ORDER BY views DESC, likes DESC
            """, (*listing_ids, cutoff_date))
            
            results = []
            for row in cursor.fetchall():
                views = row["views"] or 0
                messages = row["messages"] or 0
                performance_score = views + (row["likes"] or 0) * 2 + messages * 5
                
                results.append({
                    "day_of_week": row["day_of_week"],
                    "hour": row["hour"],
                    "views": views,
                    "likes": row["likes"] or 0,
                    "messages": messages,
                    "performance_score": float(performance_score)
                })
            
            return results
    
    def get_top_bottom_listings(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Get top and bottom performing listings
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            limit: Number of listings per category
            
        Returns:
            Tuple of (top_listings, bottom_listings)
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get listings with aggregated metrics
            cursor.execute("""
                SELECT 
                    l.id,
                    l.title,
                    l.price,
                    l.category,
                    l.created_at,
                    COALESCE(SUM(CASE WHEN e.event_type = 'view' THEN 1 ELSE 0 END), 0) as views,
                    COALESCE(SUM(CASE WHEN e.event_type = 'like' THEN 1 ELSE 0 END), 0) as likes,
                    COALESCE(SUM(CASE WHEN e.event_type = 'message' THEN 1 ELSE 0 END), 0) as messages,
                    COALESCE(MAX(CASE WHEN e.event_type = 'bump' THEN e.timestamp END), l.created_at) as last_bump
                FROM listings l
                LEFT JOIN analytics_events e ON l.id = e.listing_id AND e.timestamp >= ?
                WHERE l.user_id = ? AND l.status = 'active'
                GROUP BY l.id
            """, (cutoff_date, user_id))
            
            listings = []
            for row in cursor.fetchall():
                views = row["views"]
                likes = row["likes"]
                messages = row["messages"]
                conversion_rate = (messages / views * 100) if views > 0 else 0.0
                performance_score = views + likes * 2 + messages * 5
                
                created_at = datetime.fromisoformat(row["created_at"])
                days_active = (datetime.utcnow() - created_at).days + 1
                
                listings.append({
                    "listing_id": row["id"],
                    "title": row["title"],
                    "price": row["price"],
                    "category": row["category"],
                    "views_total": views,
                    "views_today": 0,
                    "views_week": 0,
                    "likes_total": likes,
                    "likes_today": 0,
                    "messages_total": messages,
                    "conversion_rate": round(conversion_rate, 2),
                    "days_active": days_active,
                    "last_bump": row["last_bump"],
                    "performance_score": float(performance_score)
                })
            
            # Sort by performance score
            listings.sort(key=lambda x: x["performance_score"], reverse=True)
            
            # Top performers (highest scores)
            top_listings = listings[:limit]
            
            # Bottom performers (lowest scores, but only if they have at least 1 day active)
            bottom_listings = [l for l in listings if l["days_active"] >= 1]
            bottom_listings.sort(key=lambda x: x["performance_score"])
            bottom_listings = bottom_listings[:limit]
            
            return top_listings, bottom_listings
    
    def get_category_performance(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get performance metrics by category
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            List of category performance stats
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    l.category,
                    COUNT(DISTINCT l.id) as listings_count,
                    AVG(l.price) as avg_price,
                    COALESCE(SUM(CASE WHEN e.event_type = 'view' THEN 1 ELSE 0 END), 0) as total_views,
                    COALESCE(SUM(CASE WHEN e.event_type = 'like' THEN 1 ELSE 0 END), 0) as total_likes,
                    COALESCE(SUM(CASE WHEN e.event_type = 'message' THEN 1 ELSE 0 END), 0) as total_messages
                FROM listings l
                LEFT JOIN analytics_events e ON l.id = e.listing_id AND e.timestamp >= ?
                WHERE l.user_id = ? AND l.status = 'active'
                GROUP BY l.category
                HAVING listings_count > 0
                ORDER BY total_views DESC
            """, (cutoff_date, user_id))
            
            results = []
            for row in cursor.fetchall():
                listings_count = row["listings_count"]
                total_views = row["total_views"]
                total_messages = row["total_messages"]
                
                avg_views = total_views / listings_count if listings_count > 0 else 0
                avg_likes = row["total_likes"] / listings_count if listings_count > 0 else 0
                conversion_rate = (total_messages / total_views * 100) if total_views > 0 else 0.0
                
                results.append({
                    "category": row["category"] or "Uncategorized",
                    "listings_count": listings_count,
                    "avg_views": round(avg_views, 1),
                    "avg_likes": round(avg_likes, 1),
                    "avg_price": round(row["avg_price"] or 0, 2),
                    "conversion_rate": round(conversion_rate, 2),
                    "avg_days_to_sell": None
                })
            
            return results
    
    # ==================== AUTOMATION ====================
    
    def save_automation_rule(
        self,
        rule_id: str,
        user_id: str,
        rule_type: str,
        config: Dict[str, Any],
        enabled: bool = True
    ):
        """
        Save automation rule configuration
        
        Args:
            rule_id: Unique rule ID
            user_id: User ID
            rule_type: 'bump', 'follow', 'unfollow', 'message', etc.
            config: Configuration dict
            enabled: Whether rule is enabled
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO automation_rules 
                (id, user_id, type, config, enabled)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rule_id,
                user_id,
                rule_type,
                json.dumps(config),
                1 if enabled else 0
            ))
            conn.commit()
    
    def get_automation_rules(
        self,
        user_id: str,
        rule_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get automation rules for a user
        
        Args:
            user_id: User ID
            rule_type: Optional filter by type
            
        Returns:
            List of automation rules
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if rule_type:
                cursor.execute("""
                    SELECT * FROM automation_rules 
                    WHERE user_id = ? AND type = ?
                    ORDER BY created_at DESC
                """, (user_id, rule_type))
            else:
                cursor.execute("""
                    SELECT * FROM automation_rules 
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "type": row["type"],
                    "config": json.loads(row["config"]) if row["config"] else {},
                    "enabled": bool(row["enabled"]),
                    "last_run": row["last_run"],
                    "next_run": row["next_run"],
                    "created_at": row["created_at"]
                })
            
            return results
    
    def log_automation_job(
        self,
        job_id: str,
        rule_id: str,
        job_type: str,
        status: str = "pending",
        target_id: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """
        Log an automation job execution
        
        Args:
            job_id: Unique job ID
            rule_id: Automation rule ID
            job_type: Type of automation
            status: 'pending', 'running', 'completed', 'failed'
            target_id: Target listing/user ID
            result: Result data
            error: Error message if failed
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO automation_jobs 
                (id, rule_id, type, status, target_id, result, error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                rule_id,
                job_type,
                status,
                target_id,
                json.dumps(result) if result else None,
                error
            ))
            conn.commit()
    
    def update_automation_job(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Update automation job status and result"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE automation_jobs 
                SET status = ?, 
                    result = ?, 
                    error = ?,
                    completed_at = CASE WHEN ? IN ('completed', 'failed') THEN CURRENT_TIMESTAMP ELSE completed_at END
                WHERE id = ?
            """, (
                status,
                json.dumps(result) if result else None,
                error,
                status,
                job_id
            ))
            conn.commit()
    
    def get_automation_summary(self, user_id: str, days: int = 1) -> Dict[str, Any]:
        """
        Get automation summary for a user
        
        Args:
            user_id: User ID
            days: Number of days to look back
            
        Returns:
            Summary statistics
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get rule counts
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_rules,
                    SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as active_rules
                FROM automation_rules
                WHERE user_id = ?
            """, (user_id,))
            rule_counts = cursor.fetchone()
            
            # Get job counts for the period
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs
                FROM automation_jobs j
                JOIN automation_rules r ON j.rule_id = r.id
                WHERE r.user_id = ? AND j.started_at >= ?
            """, (user_id, cutoff_date))
            job_counts = cursor.fetchone()
            
            # Get recent jobs
            cursor.execute("""
                SELECT j.*, r.user_id
                FROM automation_jobs j
                JOIN automation_rules r ON j.rule_id = r.id
                WHERE r.user_id = ?
                ORDER BY j.started_at DESC
                LIMIT 10
            """, (user_id,))
            
            recent_jobs = []
            for row in cursor.fetchall():
                recent_jobs.append({
                    "id": row["id"],
                    "rule_id": row["rule_id"],
                    "type": row["type"],
                    "status": row["status"],
                    "target_id": row["target_id"],
                    "result": json.loads(row["result"]) if row["result"] else None,
                    "error": row["error"],
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"]
                })
            
            return {
                "total_rules": rule_counts["total_rules"] or 0,
                "active_rules": rule_counts["active_rules"] or 0,
                "jobs_today": job_counts["total_jobs"] or 0,
                "jobs_successful": job_counts["successful_jobs"] or 0,
                "jobs_failed": job_counts["failed_jobs"] or 0,
                "recent_jobs": recent_jobs
            }
    
    def is_following(self, user_id: str, vinted_user_id: str) -> bool:
        """Check if user is currently following a Vinted user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM follows
                WHERE user_id = ? AND vinted_user_id = ? AND unfollowed_at IS NULL
            """, (user_id, vinted_user_id))
            row = cursor.fetchone()
            return row["count"] > 0
    
    def track_follow(
        self,
        user_id: str,
        vinted_user_id: str,
        source: str = "automation"
    ):
        """Track a follow action"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO follows 
                (user_id, vinted_user_id, source)
                VALUES (?, ?, ?)
            """, (user_id, vinted_user_id, source))
            conn.commit()
    
    def track_unfollow(self, user_id: str, vinted_user_id: str):
        """Track an unfollow action"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE follows 
                SET unfollowed_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND vinted_user_id = ? AND unfollowed_at IS NULL
            """, (user_id, vinted_user_id))
            conn.commit()
    
    def get_follows_to_unfollow(self, user_id: str, days_since_follow: int = 7) -> List[str]:
        """Get Vinted user IDs that should be unfollowed"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days_since_follow)).isoformat()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT vinted_user_id 
                FROM follows
                WHERE user_id = ? 
                AND unfollowed_at IS NULL
                AND followed_at < ?
                AND follow_back = 0
            """, (user_id, cutoff_date))
            
            return [row["vinted_user_id"] for row in cursor.fetchall()]
    
    def get_automation_rules_to_execute(self) -> List[Dict]:
        """Get enabled automation rules ready to run"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM automation_rules
                WHERE enabled = 1 AND (next_run IS NULL OR next_run <= datetime('now'))
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    def count_automation_jobs_today(self, rule_id: str) -> int:
        """Count jobs executed today for a rule"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM automation_jobs
                WHERE rule_id = ? AND date(started_at) = date('now')
            """, (rule_id,))
            return cursor.fetchone()[0]
    
    def update_automation_rule_schedule(self, rule_id: str, last_run: datetime, next_run: datetime):
        """Update rule schedule after execution"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE automation_rules
                SET last_run = ?, next_run = ?
                WHERE id = ?
            """, (last_run.isoformat(), next_run.isoformat(), rule_id))
            conn.commit()
    
    def get_last_bump_time(self, listing_id: str) -> Optional[datetime]:
        """Get last bump timestamp for a listing"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(timestamp) FROM analytics_events
                WHERE listing_id = ? AND event_type = 'bump'
            """, (listing_id,))
            result = cursor.fetchone()[0]
            return datetime.fromisoformat(result) if result else None
    
    def get_user_listings(self, user_id: str, status: str = 'active') -> List[Dict]:
        """Get user's listings by status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM listings WHERE user_id = ? AND status = ?
            """, (user_id, status))
            return [dict(row) for row in cursor.fetchall()]
    
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

    # ==================== ORDERS (Dotb feature) ====================

    def save_order(
        self,
        order_id: str,
        user_id: str,
        item_title: str,
        price: float,
        vinted_order_id: Optional[str] = None,
        item_id: Optional[str] = None,
        buyer_id: Optional[str] = None,
        buyer_name: Optional[str] = None,
        status: str = "pending",
        tracking_number: Optional[str] = None,
        shipping_carrier: Optional[str] = None,
        payment_method: Optional[str] = None,
        shipping_address: Optional[str] = None,
        notes: Optional[str] = None,
        vinted_conversation_id: Optional[str] = None,
        order_date: Optional[str] = None,
        paid_at: Optional[str] = None,
        shipped_at: Optional[str] = None
    ) -> str:
        """
        Save order to database (Dotb feature)

        Args:
            order_id: Unique order identifier
            user_id: User ID
            item_title: Item title
            price: Order price
            vinted_order_id: Vinted order ID (optional)
            ... other optional fields

        Returns:
            order_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO orders (
                    id, user_id, vinted_order_id, item_id, item_title, price,
                    buyer_id, buyer_name, status, tracking_number, shipping_carrier,
                    payment_method, shipping_address, notes, vinted_conversation_id,
                    order_date, paid_at, shipped_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                order_id, user_id, vinted_order_id, item_id, item_title, price,
                buyer_id, buyer_name, status, tracking_number, shipping_carrier,
                payment_method, shipping_address, notes, vinted_conversation_id,
                order_date or datetime.now().isoformat(), paid_at, shipped_at
            ))
            conn.commit()
            return order_id

    def get_user_orders(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get orders for a user (Dotb feature)

        Args:
            user_id: User ID
            status: Filter by status (optional)
            limit: Maximum number of orders to return
            offset: Offset for pagination

        Returns:
            List of order dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if status:
                cursor.execute("""
                    SELECT * FROM orders
                    WHERE user_id = ? AND status = ?
                    ORDER BY order_date DESC
                    LIMIT ? OFFSET ?
                """, (user_id, status, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM orders
                    WHERE user_id = ?
                    ORDER BY order_date DESC
                    LIMIT ? OFFSET ?
                """, (user_id, limit, offset))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID (Dotb feature)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_order_status(
        self,
        order_id: str,
        status: str,
        tracking_number: Optional[str] = None,
        shipped_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        cancelled_at: Optional[str] = None
    ):
        """
        Update order status (Dotb feature)

        Args:
            order_id: Order ID
            status: New status
            tracking_number: Tracking number (optional)
            shipped_at: Shipping timestamp (optional)
            completed_at: Completion timestamp (optional)
            cancelled_at: Cancellation timestamp (optional)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            values = [status]

            if tracking_number:
                update_fields.append("tracking_number = ?")
                values.append(tracking_number)

            if shipped_at:
                update_fields.append("shipped_at = ?")
                values.append(shipped_at)

            if completed_at:
                update_fields.append("completed_at = ?")
                values.append(completed_at)

            if cancelled_at:
                update_fields.append("cancelled_at = ?")
                values.append(cancelled_at)

            values.append(order_id)

            query = f"UPDATE orders SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()

    def update_order_feedback(
        self,
        order_id: str,
        rating: int,
        comment: str
    ):
        """
        Update order feedback (Dotb feature)

        Args:
            order_id: Order ID
            rating: Feedback rating (1-5)
            comment: Feedback comment
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE orders
                SET feedback_sent = 1,
                    feedback_rating = ?,
                    feedback_comment = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (rating, comment, order_id))
            conn.commit()

    def get_orders_count_by_status(self, user_id: str) -> Dict[str, int]:
        """
        Get order counts by status (Dotb feature)

        Args:
            user_id: User ID

        Returns:
            Dictionary with status counts
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM orders
                WHERE user_id = ?
                GROUP BY status
            """, (user_id,))

            rows = cursor.fetchall()
            counts = {}
            for row in rows:
                counts[row['status']] = row['count']

            return counts

    def get_total_revenue(self, user_id: str, status: str = "completed") -> float:
        """
        Get total revenue from orders (Dotb feature)

        Args:
            user_id: User ID
            status: Order status to count (default: completed)

        Returns:
            Total revenue
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(price), 0) as total
                FROM orders
                WHERE user_id = ? AND status = ?
            """, (user_id, status))

            row = cursor.fetchone()
            return float(row['total']) if row else 0.0

    def delete_order(self, order_id: str):
        """Delete order (Dotb feature)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
            conn.commit()

    # ============================================================================
    # SPRINT 1 FEATURE 1B: SYNC SUPPORT METHODS
    # ============================================================================

    def get_published_listings(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all published listings for a user

        Returns:
            List of published listing dicts with draft_id, vinted_id, and updated_at
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id as draft_id,
                    title,
                    description,
                    price,
                    category,
                    brand,
                    size,
                    color,
                    item_json,
                    updated_at,
                    created_at
                FROM drafts
                WHERE user_id = ?
                  AND status = 'published'
                  AND item_json LIKE '%vinted_id%'
            """, (str(user_id),))

            rows = cursor.fetchall()
            listings = []

            for row in rows:
                # Parse item_json to get vinted_id
                item_json = json.loads(row['item_json']) if row['item_json'] else {}
                vinted_id = item_json.get('vinted_id')

                if vinted_id:
                    listings.append({
                        'draft_id': row['draft_id'],
                        'vinted_id': vinted_id,
                        'title': row['title'],
                        'description': row['description'],
                        'price': row['price'],
                        'category': row['category'],
                        'brand': row['brand'],
                        'size': row['size'],
                        'color': row['color'],
                        'condition': item_json.get('condition', 'Bon état'),
                        'updated_at': datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                        'created_at': datetime.fromisoformat(row['created_at']) if row['created_at'] else None
                    })

            return listings

    def get_modified_listings(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all modified listings that need to be synced to Vinted

        A listing is considered modified if:
        - It's published (has vinted_id)
        - It was updated after last sync (needs_sync flag or recent updated_at)

        Returns:
            List of modified listing dicts
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id as draft_id,
                    title,
                    description,
                    price,
                    category,
                    brand,
                    size,
                    color,
                    item_json,
                    updated_at,
                    created_at
                FROM drafts
                WHERE user_id = ?
                  AND status = 'published'
                  AND item_json LIKE '%vinted_id%'
                  AND item_json LIKE '%needs_sync":true%'
            """, (str(user_id),))

            rows = cursor.fetchall()
            listings = []

            for row in rows:
                # Parse item_json to get vinted_id
                item_json = json.loads(row['item_json']) if row['item_json'] else {}
                vinted_id = item_json.get('vinted_id')
                needs_sync = item_json.get('needs_sync', False)

                if vinted_id and needs_sync:
                    listings.append({
                        'draft_id': row['draft_id'],
                        'vinted_id': vinted_id,
                        'title': row['title'],
                        'description': row['description'],
                        'price': row['price'],
                        'category': row['category'],
                        'brand': row['brand'],
                        'size': row['size'],
                        'color': row['color'],
                        'condition': item_json.get('condition', 'Bon état'),
                        'updated_at': datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
                    })

            return listings

    def mark_listing_synced(self, draft_id: str):
        """
        Mark a listing as synced (clear needs_sync flag)

        Args:
            draft_id: Draft ID to mark as synced
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get current item_json
            cursor.execute("SELECT item_json FROM drafts WHERE id = ?", (draft_id,))
            row = cursor.fetchone()

            if row:
                item_json = json.loads(row['item_json']) if row['item_json'] else {}
                item_json['needs_sync'] = False
                item_json['last_synced_at'] = datetime.utcnow().isoformat()

                # Update with modified item_json
                cursor.execute("""
                    UPDATE drafts
                    SET item_json = ?
                    WHERE id = ?
                """, (json.dumps(item_json), draft_id))

                conn.commit()

    def update_draft_vinted_info(
        self,
        draft_id: str,
        vinted_draft_url: Optional[str],
        vinted_draft_id: Optional[str],
        publish_mode: str
    ):
        """
        Update draft with Vinted draft information

        Args:
            draft_id: Draft ID
            vinted_draft_url: Vinted draft URL
            vinted_draft_id: Vinted draft ID
            publish_mode: 'auto' or 'draft'
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get current item_json
            cursor.execute("SELECT item_json FROM drafts WHERE id = ?", (draft_id,))
            row = cursor.fetchone()

            if row:
                item_json = json.loads(row['item_json']) if row['item_json'] else {}
                item_json['vinted_draft_url'] = vinted_draft_url
                item_json['vinted_draft_id'] = vinted_draft_id
                item_json['publish_mode'] = publish_mode
                item_json['last_synced_at'] = datetime.utcnow().isoformat()

                # Update with modified item_json
                cursor.execute("""
                    UPDATE drafts
                    SET item_json = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (json.dumps(item_json), datetime.utcnow().isoformat(), draft_id))

                conn.commit()


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
