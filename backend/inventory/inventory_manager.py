"""
Advanced Inventory Management System
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import json


class MovementType(str, Enum):
    """Inventory movement types"""
    ADD = "add"  # New item added to inventory
    REMOVE = "remove"  # Item removed (sold, donated, etc.)
    ADJUST = "adjust"  # Quantity adjustment (found, lost, damaged)
    TRANSFER = "transfer"  # Moved between platforms
    RETURN = "return"  # Customer return


class StockStatus(str, Enum):
    """Stock status"""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"  # Below reorder threshold
    OUT_OF_STOCK = "out_of_stock"
    RESERVED = "reserved"  # Reserved for sale
    SOLD = "sold"


class Platform(str, Enum):
    """Supported platforms"""
    VINTED = "vinted"
    LEBONCOIN = "leboncoin"
    DEPOP = "depop"
    EBAY = "ebay"
    VESTIAIRE = "vestiaire"
    WAREHOUSE = "warehouse"  # Physical storage


@dataclass
class InventoryItem:
    """A single inventory item"""
    id: str
    user_id: str
    sku: str  # Stock Keeping Unit
    name: str
    category: str
    brand: Optional[str]
    size: Optional[str]
    color: Optional[str]
    condition: str
    cost_price: float  # What you paid for it
    quantity: int
    status: StockStatus
    location: str  # Physical location (shelf, box, etc.)
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class PlatformListing:
    """A listing on a platform"""
    id: str
    inventory_id: str
    platform: Platform
    platform_listing_id: str  # ID on the platform
    listing_price: float
    quantity_listed: int
    status: str  # draft, active, sold, removed
    published_at: Optional[datetime]
    sold_at: Optional[datetime]


@dataclass
class InventoryMovement:
    """Record of inventory movement"""
    id: str
    inventory_id: str
    user_id: str
    movement_type: MovementType
    quantity: int
    from_location: Optional[str]
    to_location: Optional[str]
    from_platform: Optional[Platform]
    to_platform: Optional[Platform]
    notes: Optional[str]
    created_at: datetime


@dataclass
class InventoryStats:
    """Inventory statistics"""
    total_items: int
    total_value: float  # Cost price
    potential_revenue: float  # Listed prices
    items_in_stock: int
    items_listed: int
    items_sold: int
    low_stock_count: int
    platforms_active: List[str]
    avg_turnover_days: float


@dataclass
class SKUReport:
    """Detailed report for a SKU"""
    sku: str
    quantity: int
    cost_price: float
    total_cost: float
    platforms: List[Dict]  # Where it's listed
    movements: List[InventoryMovement]
    performance: Dict  # Views, likes, sales


class InventoryManager:
    """
    Advanced Inventory Management System

    Features:
    - SKU-based tracking
    - Multi-quantity support
    - Physical location tracking
    - Multi-platform listing sync
    - Inventory movements history
    - Stock alerts (low stock, out of stock)
    - Bulk operations
    - Cost tracking and profit calculation
    """

    def __init__(self, db_path: str = "/data/vintedbot.db"):
        self.db_path = db_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _generate_sku(
        self,
        category: str,
        brand: str,
        user_id: str
    ) -> str:
        """
        Generate unique SKU

        Format: CATEGORY-BRAND-TIMESTAMP
        Example: VET-ZARA-1699564123
        """
        category_code = category[:3].upper()
        brand_code = (brand[:4].upper() if brand else "UNKN")
        timestamp = int(datetime.utcnow().timestamp())

        return f"{category_code}-{brand_code}-{timestamp}"

    async def create_item(
        self,
        user_id: str,
        name: str,
        category: str,
        cost_price: float,
        quantity: int = 1,
        brand: Optional[str] = None,
        size: Optional[str] = None,
        color: Optional[str] = None,
        condition: str = "Bon état",
        location: str = "default",
        notes: Optional[str] = None,
        sku: Optional[str] = None
    ) -> InventoryItem:
        """
        Create a new inventory item

        Auto-generates SKU if not provided
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Generate SKU if not provided
        if not sku:
            sku = self._generate_sku(category, brand or "unknown", user_id)

        item_id = f"inv_{datetime.utcnow().timestamp()}"
        now = datetime.utcnow().isoformat()

        # Determine initial status
        status = StockStatus.IN_STOCK if quantity > 0 else StockStatus.OUT_OF_STOCK

        cursor.execute("""
            INSERT INTO inventory_items (
                id, user_id, sku, name, category, brand, size, color,
                condition, cost_price, quantity, status, location,
                notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id, user_id, sku, name, category, brand, size, color,
            condition, cost_price, quantity, status.value, location,
            notes, now, now
        ))

        # Record initial movement
        if quantity > 0:
            await self._record_movement(
                inventory_id=item_id,
                user_id=user_id,
                movement_type=MovementType.ADD,
                quantity=quantity,
                to_location=location,
                notes="Initial inventory",
                cursor=cursor
            )

        conn.commit()
        conn.close()

        return InventoryItem(
            id=item_id,
            user_id=user_id,
            sku=sku,
            name=name,
            category=category,
            brand=brand,
            size=size,
            color=color,
            condition=condition,
            cost_price=cost_price,
            quantity=quantity,
            status=status,
            location=location,
            notes=notes,
            created_at=datetime.fromisoformat(now),
            updated_at=datetime.fromisoformat(now)
        )

    async def get_item(
        self,
        item_id: str,
        user_id: str
    ) -> Optional[InventoryItem]:
        """Get inventory item by ID"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM inventory_items
            WHERE id = ? AND user_id = ?
        """, (item_id, user_id))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return InventoryItem(
            id=row['id'],
            user_id=row['user_id'],
            sku=row['sku'],
            name=row['name'],
            category=row['category'],
            brand=row['brand'],
            size=row['size'],
            color=row['color'],
            condition=row['condition'],
            cost_price=row['cost_price'],
            quantity=row['quantity'],
            status=StockStatus(row['status']),
            location=row['location'],
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    async def update_quantity(
        self,
        item_id: str,
        user_id: str,
        quantity_change: int,
        movement_type: MovementType,
        notes: Optional[str] = None
    ) -> InventoryItem:
        """
        Update item quantity

        quantity_change can be positive (add) or negative (remove)
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get current item
        cursor.execute("""
            SELECT * FROM inventory_items
            WHERE id = ? AND user_id = ?
        """, (item_id, user_id))

        item = cursor.fetchone()
        if not item:
            conn.close()
            raise ValueError(f"Item {item_id} not found")

        # Calculate new quantity
        new_quantity = item['quantity'] + quantity_change

        if new_quantity < 0:
            conn.close()
            raise ValueError(f"Cannot reduce quantity below 0 (current: {item['quantity']}, change: {quantity_change})")

        # Determine new status
        if new_quantity == 0:
            new_status = StockStatus.OUT_OF_STOCK
        elif new_quantity <= 2:  # Low stock threshold
            new_status = StockStatus.LOW_STOCK
        else:
            new_status = StockStatus.IN_STOCK

        # Update quantity
        cursor.execute("""
            UPDATE inventory_items
            SET quantity = ?, status = ?, updated_at = ?
            WHERE id = ?
        """, (new_quantity, new_status.value, datetime.utcnow().isoformat(), item_id))

        # Record movement
        await self._record_movement(
            inventory_id=item_id,
            user_id=user_id,
            movement_type=movement_type,
            quantity=abs(quantity_change),
            notes=notes,
            cursor=cursor
        )

        conn.commit()
        conn.close()

        # Return updated item
        return await self.get_item(item_id, user_id)

    async def _record_movement(
        self,
        inventory_id: str,
        user_id: str,
        movement_type: MovementType,
        quantity: int,
        from_location: Optional[str] = None,
        to_location: Optional[str] = None,
        from_platform: Optional[Platform] = None,
        to_platform: Optional[Platform] = None,
        notes: Optional[str] = None,
        cursor: Optional[sqlite3.Cursor] = None
    ):
        """Record an inventory movement"""
        should_close = cursor is None

        if cursor is None:
            conn = self._get_db_connection()
            cursor = conn.cursor()

        movement_id = f"mov_{datetime.utcnow().timestamp()}"

        cursor.execute("""
            INSERT INTO inventory_movements (
                id, inventory_id, user_id, movement_type, quantity,
                from_location, to_location, from_platform, to_platform,
                notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            movement_id, inventory_id, user_id, movement_type.value, quantity,
            from_location, to_location,
            from_platform.value if from_platform else None,
            to_platform.value if to_platform else None,
            notes, datetime.utcnow().isoformat()
        ))

        if should_close:
            conn.commit()
            conn.close()

    async def create_platform_listing(
        self,
        inventory_id: str,
        user_id: str,
        platform: Platform,
        platform_listing_id: str,
        listing_price: float,
        quantity_listed: int
    ) -> PlatformListing:
        """
        Create a listing on a platform

        This reserves inventory quantity for the platform
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Verify inventory exists and has enough quantity
        item = await self.get_item(inventory_id, user_id)
        if not item:
            conn.close()
            raise ValueError(f"Inventory item {inventory_id} not found")

        if item.quantity < quantity_listed:
            conn.close()
            raise ValueError(f"Insufficient quantity (have: {item.quantity}, need: {quantity_listed})")

        listing_id = f"pl_{datetime.utcnow().timestamp()}"
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO platform_listings (
                id, inventory_id, platform, platform_listing_id,
                listing_price, quantity_listed, status,
                published_at, sold_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, NULL)
        """, (
            listing_id, inventory_id, platform.value, platform_listing_id,
            listing_price, quantity_listed, now
        ))

        # Record movement
        await self._record_movement(
            inventory_id=inventory_id,
            user_id=user_id,
            movement_type=MovementType.TRANSFER,
            quantity=quantity_listed,
            from_location=item.location,
            to_platform=platform,
            notes=f"Listed on {platform.value}",
            cursor=cursor
        )

        conn.commit()
        conn.close()

        return PlatformListing(
            id=listing_id,
            inventory_id=inventory_id,
            platform=platform,
            platform_listing_id=platform_listing_id,
            listing_price=listing_price,
            quantity_listed=quantity_listed,
            status='active',
            published_at=datetime.fromisoformat(now),
            sold_at=None
        )

    async def mark_listing_sold(
        self,
        listing_id: str,
        user_id: str
    ) -> Dict:
        """
        Mark a platform listing as sold

        This reduces inventory quantity
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get listing
        cursor.execute("""
            SELECT * FROM platform_listings
            WHERE id = ?
        """, (listing_id,))

        listing = cursor.fetchone()
        if not listing:
            conn.close()
            raise ValueError(f"Listing {listing_id} not found")

        # Update listing status
        cursor.execute("""
            UPDATE platform_listings
            SET status = 'sold', sold_at = ?
            WHERE id = ?
        """, (datetime.utcnow().isoformat(), listing_id))

        # Reduce inventory quantity
        cursor.execute("""
            SELECT quantity FROM inventory_items
            WHERE id = ?
        """, (listing['inventory_id'],))

        item = cursor.fetchone()
        new_quantity = item['quantity'] - listing['quantity_listed']

        cursor.execute("""
            UPDATE inventory_items
            SET quantity = ?, status = ?, updated_at = ?
            WHERE id = ?
        """, (
            new_quantity,
            StockStatus.OUT_OF_STOCK.value if new_quantity == 0 else StockStatus.IN_STOCK.value,
            datetime.utcnow().isoformat(),
            listing['inventory_id']
        ))

        # Record movement
        await self._record_movement(
            inventory_id=listing['inventory_id'],
            user_id=user_id,
            movement_type=MovementType.REMOVE,
            quantity=listing['quantity_listed'],
            from_platform=Platform(listing['platform']),
            notes=f"Sold on {listing['platform']}",
            cursor=cursor
        )

        conn.commit()
        conn.close()

        return {
            'ok': True,
            'listing_id': listing_id,
            'quantity_sold': listing['quantity_listed'],
            'remaining_quantity': new_quantity
        }

    async def get_inventory_stats(
        self,
        user_id: str
    ) -> InventoryStats:
        """Get inventory statistics"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Total items and value
        cursor.execute("""
            SELECT
                COUNT(*) as total_items,
                SUM(quantity) as total_quantity,
                SUM(cost_price * quantity) as total_value,
                SUM(CASE WHEN status = 'in_stock' THEN 1 ELSE 0 END) as in_stock,
                SUM(CASE WHEN status = 'low_stock' THEN 1 ELSE 0 END) as low_stock,
                SUM(CASE WHEN status = 'sold' THEN 1 ELSE 0 END) as sold
            FROM inventory_items
            WHERE user_id = ?
        """, (user_id,))

        stats = cursor.fetchone()

        # Potential revenue (from listings)
        cursor.execute("""
            SELECT SUM(listing_price * quantity_listed) as potential
            FROM platform_listings pl
            JOIN inventory_items ii ON pl.inventory_id = ii.id
            WHERE ii.user_id = ?
            AND pl.status = 'active'
        """, (user_id,))

        revenue_data = cursor.fetchone()
        potential_revenue = revenue_data['potential'] or 0

        # Active platforms
        cursor.execute("""
            SELECT DISTINCT platform
            FROM platform_listings pl
            JOIN inventory_items ii ON pl.inventory_id = ii.id
            WHERE ii.user_id = ?
            AND pl.status = 'active'
        """, (user_id,))

        platforms = [row['platform'] for row in cursor.fetchall()]

        # Average turnover (time from add to sold)
        cursor.execute("""
            SELECT AVG(julianday(sold_at) - julianday(published_at)) as avg_days
            FROM platform_listings pl
            JOIN inventory_items ii ON pl.inventory_id = ii.id
            WHERE ii.user_id = ?
            AND pl.status = 'sold'
            AND pl.sold_at IS NOT NULL
        """, (user_id,))

        turnover_data = cursor.fetchone()
        avg_turnover = turnover_data['avg_days'] or 0

        # Items listed
        cursor.execute("""
            SELECT COUNT(DISTINCT inventory_id) as listed
            FROM platform_listings pl
            JOIN inventory_items ii ON pl.inventory_id = ii.id
            WHERE ii.user_id = ?
            AND pl.status = 'active'
        """, (user_id,))

        listed_data = cursor.fetchone()
        items_listed = listed_data['listed'] or 0

        conn.close()

        return InventoryStats(
            total_items=stats['total_items'] or 0,
            total_value=stats['total_value'] or 0,
            potential_revenue=potential_revenue,
            items_in_stock=stats['in_stock'] or 0,
            items_listed=items_listed,
            items_sold=stats['sold'] or 0,
            low_stock_count=stats['low_stock'] or 0,
            platforms_active=platforms,
            avg_turnover_days=avg_turnover
        )

    async def search_inventory(
        self,
        user_id: str,
        sku: Optional[str] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        status: Optional[StockStatus] = None,
        location: Optional[str] = None,
        limit: int = 50
    ) -> List[InventoryItem]:
        """Search inventory with filters"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM inventory_items WHERE user_id = ?"
        params = [user_id]

        if sku:
            query += " AND sku LIKE ?"
            params.append(f"%{sku}%")

        if category:
            query += " AND category = ?"
            params.append(category)

        if brand:
            query += " AND brand LIKE ?"
            params.append(f"%{brand}%")

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if location:
            query += " AND location = ?"
            params.append(location)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        items = []
        for row in cursor.fetchall():
            items.append(InventoryItem(
                id=row['id'],
                user_id=row['user_id'],
                sku=row['sku'],
                name=row['name'],
                category=row['category'],
                brand=row['brand'],
                size=row['size'],
                color=row['color'],
                condition=row['condition'],
                cost_price=row['cost_price'],
                quantity=row['quantity'],
                status=StockStatus(row['status']),
                location=row['location'],
                notes=row['notes'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            ))

        conn.close()
        return items

    async def get_sku_report(
        self,
        sku: str,
        user_id: str
    ) -> Optional[SKUReport]:
        """Get detailed report for a SKU"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get item
        cursor.execute("""
            SELECT * FROM inventory_items
            WHERE sku = ? AND user_id = ?
        """, (sku, user_id))

        item = cursor.fetchone()
        if not item:
            conn.close()
            return None

        # Get platform listings
        cursor.execute("""
            SELECT * FROM platform_listings
            WHERE inventory_id = ?
            ORDER BY published_at DESC
        """, (item['id'],))

        platforms = []
        for row in cursor.fetchall():
            platforms.append({
                'platform': row['platform'],
                'price': row['listing_price'],
                'quantity': row['quantity_listed'],
                'status': row['status'],
                'published_at': row['published_at'],
                'sold_at': row['sold_at']
            })

        # Get movements
        cursor.execute("""
            SELECT * FROM inventory_movements
            WHERE inventory_id = ?
            ORDER BY created_at DESC
            LIMIT 20
        """, (item['id'],))

        movements = []
        for row in cursor.fetchall():
            movements.append(InventoryMovement(
                id=row['id'],
                inventory_id=row['inventory_id'],
                user_id=row['user_id'],
                movement_type=MovementType(row['movement_type']),
                quantity=row['quantity'],
                from_location=row['from_location'],
                to_location=row['to_location'],
                from_platform=Platform(row['from_platform']) if row['from_platform'] else None,
                to_platform=Platform(row['to_platform']) if row['to_platform'] else None,
                notes=row['notes'],
                created_at=datetime.fromisoformat(row['created_at'])
            ))

        conn.close()

        total_cost = item['cost_price'] * item['quantity']

        return SKUReport(
            sku=sku,
            quantity=item['quantity'],
            cost_price=item['cost_price'],
            total_cost=total_cost,
            platforms=platforms,
            movements=movements,
            performance={
                'views': 0,  # Would come from listings table
                'likes': 0,
                'sales': len([p for p in platforms if p['status'] == 'sold'])
            }
        )

    async def bulk_update_location(
        self,
        user_id: str,
        item_ids: List[str],
        new_location: str
    ) -> int:
        """Bulk update location for multiple items"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        updated_count = 0

        for item_id in item_ids:
            cursor.execute("""
                UPDATE inventory_items
                SET location = ?, updated_at = ?
                WHERE id = ? AND user_id = ?
            """, (new_location, datetime.utcnow().isoformat(), item_id, user_id))

            if cursor.rowcount > 0:
                updated_count += 1

        conn.commit()
        conn.close()

        return updated_count
