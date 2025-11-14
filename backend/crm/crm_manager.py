"""
CRM Manager - Customer relationship management
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import sqlite3


class CustomerSegment(str, Enum):
    """Customer segments"""
    VIP = "vip"  # High-value customers (3+ purchases)
    LOYAL = "loyal"  # Repeat customers (2 purchases)
    NEW = "new"  # First purchase
    CHURNED = "churned"  # No purchase in 90+ days
    BLACKLIST = "blacklist"  # Problematic customers


class InteractionType(str, Enum):
    """Types of customer interactions"""
    MESSAGE = "message"
    PURCHASE = "purchase"
    OFFER = "offer"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    RETURN = "return"


@dataclass
class Customer:
    """A customer"""
    id: str
    user_id: str  # Seller's user ID
    vinted_id: str  # Customer's Vinted ID
    username: str
    email: Optional[str]
    segment: CustomerSegment
    total_purchases: int
    total_spent: float
    avg_order_value: float
    last_purchase_date: Optional[datetime]
    is_blacklisted: bool
    blacklist_reason: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class CustomerInteraction:
    """Record of customer interaction"""
    id: str
    customer_id: str
    user_id: str
    interaction_type: InteractionType
    summary: str
    details: Optional[str]
    sentiment: Optional[str]  # positive, neutral, negative
    created_at: datetime


@dataclass
class CustomerStats:
    """Customer statistics"""
    total_customers: int
    vip_count: int
    loyal_count: int
    new_count: int
    churned_count: int
    blacklisted_count: int
    avg_lifetime_value: float
    repeat_purchase_rate: float


@dataclass
class Segment:
    """A customer segment"""
    id: str
    user_id: str
    name: str
    description: str
    filters: Dict  # JSON filters
    customer_count: int
    created_at: datetime


class CRMManager:
    """
    CRM (Customer Relationship Management) System

    Features:
    - Customer tracking and profiling
    - Automatic segmentation (VIP, Loyal, New, Churned)
    - Interaction history
    - Blacklist management
    - Custom segments
    - Automated follow-ups
    - Customer lifetime value tracking
    """

    def __init__(self, db_path: str = "/data/vintedbot.db"):
        self.db_path = db_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def create_or_update_customer(
        self,
        user_id: str,
        vinted_id: str,
        username: str,
        email: Optional[str] = None
    ) -> Customer:
        """
        Create or update a customer record

        Automatically called when a purchase is made
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Check if customer exists
        cursor.execute("""
            SELECT * FROM customers
            WHERE vinted_id = ? AND user_id = ?
        """, (vinted_id, user_id))

        existing = cursor.fetchone()

        if existing:
            # Update existing
            cursor.execute("""
                UPDATE customers
                SET username = ?, email = ?, updated_at = ?
                WHERE id = ?
            """, (username, email, datetime.utcnow().isoformat(), existing['id']))

            customer_id = existing['id']
        else:
            # Create new
            customer_id = f"cust_{datetime.utcnow().timestamp()}"
            now = datetime.utcnow().isoformat()

            cursor.execute("""
                INSERT INTO customers (
                    id, user_id, vinted_id, username, email,
                    segment, total_purchases, total_spent, avg_order_value,
                    last_purchase_date, is_blacklisted, blacklist_reason,
                    notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, NULL, 0, NULL, NULL, ?, ?)
            """, (
                customer_id, user_id, vinted_id, username, email,
                CustomerSegment.NEW.value, now, now
            ))

        conn.commit()

        # Get and return customer
        customer = await self.get_customer(customer_id, user_id)
        conn.close()

        return customer

    async def get_customer(
        self,
        customer_id: str,
        user_id: str
    ) -> Optional[Customer]:
        """Get customer by ID"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM customers
            WHERE id = ? AND user_id = ?
        """, (customer_id, user_id))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Customer(
            id=row['id'],
            user_id=row['user_id'],
            vinted_id=row['vinted_id'],
            username=row['username'],
            email=row['email'],
            segment=CustomerSegment(row['segment']),
            total_purchases=row['total_purchases'],
            total_spent=row['total_spent'],
            avg_order_value=row['avg_order_value'],
            last_purchase_date=datetime.fromisoformat(row['last_purchase_date']) if row['last_purchase_date'] else None,
            is_blacklisted=bool(row['is_blacklisted']),
            blacklist_reason=row['blacklist_reason'],
            notes=row['notes'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    async def record_purchase(
        self,
        customer_id: str,
        user_id: str,
        amount: float,
        listing_id: str
    ) -> Customer:
        """
        Record a purchase and update customer stats

        Automatically updates:
        - Total purchases
        - Total spent
        - Average order value
        - Last purchase date
        - Segment (based on purchase count)
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get current customer data
        cursor.execute("""
            SELECT * FROM customers
            WHERE id = ? AND user_id = ?
        """, (customer_id, user_id))

        customer = cursor.fetchone()
        if not customer:
            conn.close()
            raise ValueError(f"Customer {customer_id} not found")

        # Update stats
        new_total_purchases = customer['total_purchases'] + 1
        new_total_spent = customer['total_spent'] + amount
        new_avg_order_value = new_total_spent / new_total_purchases

        # Determine new segment
        if new_total_purchases >= 3:
            new_segment = CustomerSegment.VIP
        elif new_total_purchases >= 2:
            new_segment = CustomerSegment.LOYAL
        else:
            new_segment = CustomerSegment.NEW

        cursor.execute("""
            UPDATE customers
            SET total_purchases = ?,
                total_spent = ?,
                avg_order_value = ?,
                last_purchase_date = ?,
                segment = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            new_total_purchases,
            new_total_spent,
            new_avg_order_value,
            datetime.utcnow().isoformat(),
            new_segment.value,
            datetime.utcnow().isoformat(),
            customer_id
        ))

        # Record interaction
        await self._record_interaction(
            customer_id=customer_id,
            user_id=user_id,
            interaction_type=InteractionType.PURCHASE,
            summary=f"Purchased for {amount}€",
            details=f"Listing ID: {listing_id}",
            sentiment="positive",
            cursor=cursor
        )

        conn.commit()

        # Get and return updated customer
        updated_customer = await self.get_customer(customer_id, user_id)
        conn.close()

        return updated_customer

    async def _record_interaction(
        self,
        customer_id: str,
        user_id: str,
        interaction_type: InteractionType,
        summary: str,
        details: Optional[str] = None,
        sentiment: Optional[str] = None,
        cursor: Optional[sqlite3.Cursor] = None
    ):
        """Record a customer interaction"""
        should_close = cursor is None

        if cursor is None:
            conn = self._get_db_connection()
            cursor = conn.cursor()

        interaction_id = f"int_{datetime.utcnow().timestamp()}"

        cursor.execute("""
            INSERT INTO customer_interactions (
                id, customer_id, user_id, interaction_type,
                summary, details, sentiment, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction_id, customer_id, user_id, interaction_type.value,
            summary, details, sentiment, datetime.utcnow().isoformat()
        ))

        if should_close:
            conn.commit()
            conn.close()

    async def add_to_blacklist(
        self,
        customer_id: str,
        user_id: str,
        reason: str
    ) -> Customer:
        """Add customer to blacklist"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE customers
            SET is_blacklisted = 1,
                blacklist_reason = ?,
                segment = ?,
                updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (
            reason,
            CustomerSegment.BLACKLIST.value,
            datetime.utcnow().isoformat(),
            customer_id,
            user_id
        ))

        # Record interaction
        await self._record_interaction(
            customer_id=customer_id,
            user_id=user_id,
            interaction_type=InteractionType.COMPLAINT,
            summary="Added to blacklist",
            details=reason,
            sentiment="negative",
            cursor=cursor
        )

        conn.commit()

        updated_customer = await self.get_customer(customer_id, user_id)
        conn.close()

        return updated_customer

    async def remove_from_blacklist(
        self,
        customer_id: str,
        user_id: str
    ) -> Customer:
        """Remove customer from blacklist"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get customer to recalculate segment
        customer = await self.get_customer(customer_id, user_id)

        # Recalculate segment based on purchases
        if customer.total_purchases >= 3:
            new_segment = CustomerSegment.VIP
        elif customer.total_purchases >= 2:
            new_segment = CustomerSegment.LOYAL
        else:
            new_segment = CustomerSegment.NEW

        cursor.execute("""
            UPDATE customers
            SET is_blacklisted = 0,
                blacklist_reason = NULL,
                segment = ?,
                updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (
            new_segment.value,
            datetime.utcnow().isoformat(),
            customer_id,
            user_id
        ))

        conn.commit()

        updated_customer = await self.get_customer(customer_id, user_id)
        conn.close()

        return updated_customer

    async def get_customer_interactions(
        self,
        customer_id: str,
        user_id: str,
        limit: int = 20
    ) -> List[CustomerInteraction]:
        """Get interaction history for a customer"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM customer_interactions
            WHERE customer_id = ? AND user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (customer_id, user_id, limit))

        interactions = []
        for row in cursor.fetchall():
            interactions.append(CustomerInteraction(
                id=row['id'],
                customer_id=row['customer_id'],
                user_id=row['user_id'],
                interaction_type=InteractionType(row['interaction_type']),
                summary=row['summary'],
                details=row['details'],
                sentiment=row['sentiment'],
                created_at=datetime.fromisoformat(row['created_at'])
            ))

        conn.close()
        return interactions

    async def get_customers_by_segment(
        self,
        user_id: str,
        segment: CustomerSegment,
        limit: int = 50
    ) -> List[Customer]:
        """Get customers in a specific segment"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM customers
            WHERE user_id = ? AND segment = ?
            ORDER BY total_spent DESC
            LIMIT ?
        """, (user_id, segment.value, limit))

        customers = []
        for row in cursor.fetchall():
            customers.append(Customer(
                id=row['id'],
                user_id=row['user_id'],
                vinted_id=row['vinted_id'],
                username=row['username'],
                email=row['email'],
                segment=CustomerSegment(row['segment']),
                total_purchases=row['total_purchases'],
                total_spent=row['total_spent'],
                avg_order_value=row['avg_order_value'],
                last_purchase_date=datetime.fromisoformat(row['last_purchase_date']) if row['last_purchase_date'] else None,
                is_blacklisted=bool(row['is_blacklisted']),
                blacklist_reason=row['blacklist_reason'],
                notes=row['notes'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            ))

        conn.close()
        return customers

    async def get_crm_stats(
        self,
        user_id: str
    ) -> CustomerStats:
        """Get CRM statistics"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Count by segment
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN segment = 'vip' THEN 1 ELSE 0 END) as vip,
                SUM(CASE WHEN segment = 'loyal' THEN 1 ELSE 0 END) as loyal,
                SUM(CASE WHEN segment = 'new' THEN 1 ELSE 0 END) as new_count,
                SUM(CASE WHEN segment = 'churned' THEN 1 ELSE 0 END) as churned,
                SUM(CASE WHEN is_blacklisted = 1 THEN 1 ELSE 0 END) as blacklisted,
                AVG(total_spent) as avg_ltv,
                SUM(CASE WHEN total_purchases > 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as repeat_rate
            FROM customers
            WHERE user_id = ?
        """, (user_id,))

        stats = cursor.fetchone()
        conn.close()

        return CustomerStats(
            total_customers=stats['total'] or 0,
            vip_count=stats['vip'] or 0,
            loyal_count=stats['loyal'] or 0,
            new_count=stats['new_count'] or 0,
            churned_count=stats['churned'] or 0,
            blacklisted_count=stats['blacklisted'] or 0,
            avg_lifetime_value=stats['avg_ltv'] or 0,
            repeat_purchase_rate=(stats['repeat_rate'] or 0) * 100
        )

    async def identify_churned_customers(
        self,
        user_id: str,
        days_threshold: int = 90
    ) -> int:
        """
        Identify and mark customers as churned

        Returns count of customers marked as churned
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        threshold_date = (datetime.utcnow() - timedelta(days=days_threshold)).isoformat()

        cursor.execute("""
            UPDATE customers
            SET segment = ?, updated_at = ?
            WHERE user_id = ?
            AND segment NOT IN ('blacklist', 'churned')
            AND last_purchase_date < ?
        """, (
            CustomerSegment.CHURNED.value,
            datetime.utcnow().isoformat(),
            user_id,
            threshold_date
        ))

        churned_count = cursor.rowcount

        conn.commit()
        conn.close()

        return churned_count

    async def search_customers(
        self,
        user_id: str,
        query: Optional[str] = None,
        segment: Optional[CustomerSegment] = None,
        min_purchases: Optional[int] = None,
        blacklisted_only: bool = False,
        limit: int = 50
    ) -> List[Customer]:
        """Search customers with filters"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        sql = "SELECT * FROM customers WHERE user_id = ?"
        params = [user_id]

        if query:
            sql += " AND (username LIKE ? OR email LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])

        if segment:
            sql += " AND segment = ?"
            params.append(segment.value)

        if min_purchases:
            sql += " AND total_purchases >= ?"
            params.append(min_purchases)

        if blacklisted_only:
            sql += " AND is_blacklisted = 1"

        sql += " ORDER BY total_spent DESC LIMIT ?"
        params.append(limit)

        cursor.execute(sql, params)

        customers = []
        for row in cursor.fetchall():
            customers.append(Customer(
                id=row['id'],
                user_id=row['user_id'],
                vinted_id=row['vinted_id'],
                username=row['username'],
                email=row['email'],
                segment=CustomerSegment(row['segment']),
                total_purchases=row['total_purchases'],
                total_spent=row['total_spent'],
                avg_order_value=row['avg_order_value'],
                last_purchase_date=datetime.fromisoformat(row['last_purchase_date']) if row['last_purchase_date'] else None,
                is_blacklisted=bool(row['is_blacklisted']),
                blacklist_reason=row['blacklist_reason'],
                notes=row['notes'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            ))

        conn.close()
        return customers

    async def add_note(
        self,
        customer_id: str,
        user_id: str,
        note: str
    ) -> Customer:
        """Add a note to customer profile"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get existing notes
        customer = await self.get_customer(customer_id, user_id)
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        existing_notes = customer.notes or ""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        new_note = f"[{timestamp}] {note}"

        updated_notes = f"{existing_notes}\n{new_note}" if existing_notes else new_note

        cursor.execute("""
            UPDATE customers
            SET notes = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (updated_notes, datetime.utcnow().isoformat(), customer_id, user_id))

        conn.commit()

        updated_customer = await self.get_customer(customer_id, user_id)
        conn.close()

        return updated_customer
