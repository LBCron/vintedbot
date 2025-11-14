"""
Financial Dashboard Manager - P&L, tax tracking, and forecasting
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import sqlite3


class TransactionType(str, Enum):
    """Transaction types"""
    SALE = "sale"  # Revenue from sale
    REFUND = "refund"  # Refund issued
    EXPENSE = "expense"  # Business expense
    FEE = "fee"  # Platform fees
    SHIPPING = "shipping"  # Shipping costs
    TAX = "tax"  # Tax payment


@dataclass
class Transaction:
    """A financial transaction"""
    id: str
    user_id: str
    transaction_type: TransactionType
    amount: float  # Positive for revenue, negative for expenses
    description: str
    category: Optional[str]
    listing_id: Optional[str]
    vinted_fee: float  # Vinted's commission
    payment_fee: float  # Payment processor fee
    shipping_cost: float  # Shipping cost (if applicable)
    net_amount: float  # Amount after all fees
    created_at: datetime


@dataclass
class ProfitLossStatement:
    """Profit & Loss statement"""
    period_start: datetime
    period_end: datetime
    # Revenue
    gross_revenue: float
    refunds: float
    net_revenue: float
    # Costs
    platform_fees: float  # Vinted commissions
    payment_fees: float  # Payment processor fees
    shipping_costs: float
    inventory_costs: float  # Cost of goods sold (COGS)
    other_expenses: float
    total_costs: float
    # Profit
    gross_profit: float  # Revenue - COGS
    net_profit: float  # Gross profit - all expenses
    profit_margin: float  # Net profit / Net revenue


@dataclass
class TaxReport:
    """Tax report"""
    period_start: datetime
    period_end: datetime
    gross_revenue: float
    deductible_expenses: float
    taxable_income: float
    estimated_tax: float  # Based on tax rate
    transactions_count: int


@dataclass
class Forecast:
    """Revenue forecast"""
    period: str  # "next_month", "next_quarter"
    forecasted_revenue: float
    forecasted_profit: float
    confidence: float  # 0-1
    based_on_days: int


class FinanceManager:
    """
    Financial Dashboard Manager

    Features:
    - Transaction tracking (sales, expenses, fees)
    - Automatic Vinted fee calculation (5% + 0.70€)
    - P&L statements (daily, weekly, monthly, yearly)
    - Tax reporting
    - Revenue forecasting
    - Expense categorization
    - Break-even analysis
    """

    # Vinted fee structure (as of 2024)
    VINTED_FEE_PERCENTAGE = 0.05  # 5%
    VINTED_FEE_FIXED = 0.70  # 0.70€
    PAYMENT_FEE_PERCENTAGE = 0.03  # ~3% payment processing

    def __init__(self, db_path: str = "/data/vintedbot.db"):
        self.db_path = db_path

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _calculate_vinted_fees(self, sale_amount: float) -> Tuple[float, float]:
        """
        Calculate Vinted fees

        Returns: (vinted_fee, payment_fee)
        """
        vinted_fee = (sale_amount * self.VINTED_FEE_PERCENTAGE) + self.VINTED_FEE_FIXED
        payment_fee = sale_amount * self.PAYMENT_FEE_PERCENTAGE

        return vinted_fee, payment_fee

    async def record_sale(
        self,
        user_id: str,
        amount: float,
        listing_id: str,
        shipping_cost: float = 0,
        inventory_cost: float = 0
    ) -> Transaction:
        """
        Record a sale

        Automatically calculates Vinted fees and net amount
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Calculate fees
        vinted_fee, payment_fee = self._calculate_vinted_fees(amount)

        # Net amount = Sale - Vinted fee - Payment fee - Shipping
        net_amount = amount - vinted_fee - payment_fee - shipping_cost

        transaction_id = f"txn_{datetime.utcnow().timestamp()}"

        cursor.execute("""
            INSERT INTO transactions (
                id, user_id, transaction_type, amount, description,
                category, listing_id, vinted_fee, payment_fee,
                shipping_cost, net_amount, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction_id, user_id, TransactionType.SALE.value, amount,
            f"Sale - Listing {listing_id}", "revenue", listing_id,
            vinted_fee, payment_fee, shipping_cost, net_amount,
            datetime.utcnow().isoformat()
        ))

        # Record shipping cost as separate expense if applicable
        if shipping_cost > 0:
            cursor.execute("""
                INSERT INTO transactions (
                    id, user_id, transaction_type, amount, description,
                    category, listing_id, vinted_fee, payment_fee,
                    shipping_cost, net_amount, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?)
            """, (
                f"txn_ship_{datetime.utcnow().timestamp()}",
                user_id, TransactionType.SHIPPING.value, -shipping_cost,
                f"Shipping - Listing {listing_id}", "shipping", listing_id,
                shipping_cost, -shipping_cost,
                datetime.utcnow().isoformat()
            ))

        # Record inventory cost (COGS)
        if inventory_cost > 0:
            cursor.execute("""
                INSERT INTO transactions (
                    id, user_id, transaction_type, amount, description,
                    category, listing_id, vinted_fee, payment_fee,
                    shipping_cost, net_amount, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?)
            """, (
                f"txn_cogs_{datetime.utcnow().timestamp()}",
                user_id, TransactionType.EXPENSE.value, -inventory_cost,
                f"COGS - Listing {listing_id}", "inventory", listing_id,
                -inventory_cost,
                datetime.utcnow().isoformat()
            ))

        conn.commit()
        conn.close()

        return Transaction(
            id=transaction_id,
            user_id=user_id,
            transaction_type=TransactionType.SALE,
            amount=amount,
            description=f"Sale - Listing {listing_id}",
            category="revenue",
            listing_id=listing_id,
            vinted_fee=vinted_fee,
            payment_fee=payment_fee,
            shipping_cost=shipping_cost,
            net_amount=net_amount,
            created_at=datetime.utcnow()
        )

    async def record_expense(
        self,
        user_id: str,
        amount: float,
        description: str,
        category: str = "other"
    ) -> Transaction:
        """Record a business expense"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        transaction_id = f"txn_{datetime.utcnow().timestamp()}"

        cursor.execute("""
            INSERT INTO transactions (
                id, user_id, transaction_type, amount, description,
                category, listing_id, vinted_fee, payment_fee,
                shipping_cost, net_amount, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, 0, 0, 0, ?, ?)
        """, (
            transaction_id, user_id, TransactionType.EXPENSE.value,
            -amount, description, category, -amount,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        conn.close()

        return Transaction(
            id=transaction_id,
            user_id=user_id,
            transaction_type=TransactionType.EXPENSE,
            amount=-amount,
            description=description,
            category=category,
            listing_id=None,
            vinted_fee=0,
            payment_fee=0,
            shipping_cost=0,
            net_amount=-amount,
            created_at=datetime.utcnow()
        )

    async def get_profit_loss_statement(
        self,
        user_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> ProfitLossStatement:
        """
        Generate Profit & Loss statement

        Default: Current month
        """
        if not period_start:
            # Start of current month
            now = datetime.utcnow()
            period_start = datetime(now.year, now.month, 1)

        if not period_end:
            period_end = datetime.utcnow()

        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get all transactions in period
        cursor.execute("""
            SELECT
                SUM(CASE WHEN transaction_type = 'sale' THEN amount ELSE 0 END) as gross_revenue,
                SUM(CASE WHEN transaction_type = 'refund' THEN ABS(amount) ELSE 0 END) as refunds,
                SUM(CASE WHEN transaction_type = 'sale' THEN vinted_fee ELSE 0 END) as platform_fees,
                SUM(CASE WHEN transaction_type = 'sale' THEN payment_fee ELSE 0 END) as payment_fees,
                SUM(CASE WHEN transaction_type = 'shipping' THEN ABS(amount) ELSE 0 END) as shipping_costs,
                SUM(CASE WHEN category = 'inventory' THEN ABS(amount) ELSE 0 END) as inventory_costs,
                SUM(CASE WHEN transaction_type = 'expense' AND category != 'inventory' THEN ABS(amount) ELSE 0 END) as other_expenses
            FROM transactions
            WHERE user_id = ?
            AND created_at >= ?
            AND created_at <= ?
        """, (user_id, period_start.isoformat(), period_end.isoformat()))

        data = cursor.fetchone()
        conn.close()

        gross_revenue = data['gross_revenue'] or 0
        refunds = data['refunds'] or 0
        platform_fees = data['platform_fees'] or 0
        payment_fees = data['payment_fees'] or 0
        shipping_costs = data['shipping_costs'] or 0
        inventory_costs = data['inventory_costs'] or 0
        other_expenses = data['other_expenses'] or 0

        net_revenue = gross_revenue - refunds
        total_costs = platform_fees + payment_fees + shipping_costs + inventory_costs + other_expenses
        gross_profit = net_revenue - inventory_costs
        net_profit = gross_profit - (platform_fees + payment_fees + shipping_costs + other_expenses)

        profit_margin = (net_profit / net_revenue * 100) if net_revenue > 0 else 0

        return ProfitLossStatement(
            period_start=period_start,
            period_end=period_end,
            gross_revenue=gross_revenue,
            refunds=refunds,
            net_revenue=net_revenue,
            platform_fees=platform_fees,
            payment_fees=payment_fees,
            shipping_costs=shipping_costs,
            inventory_costs=inventory_costs,
            other_expenses=other_expenses,
            total_costs=total_costs,
            gross_profit=gross_profit,
            net_profit=net_profit,
            profit_margin=profit_margin
        )

    async def get_tax_report(
        self,
        user_id: str,
        year: int,
        tax_rate: float = 0.20  # 20% default tax rate
    ) -> TaxReport:
        """
        Generate tax report for a year

        tax_rate: Your applicable tax rate (e.g., 0.20 for 20%)
        """
        period_start = datetime(year, 1, 1)
        period_end = datetime(year, 12, 31, 23, 59, 59)

        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Gross revenue
        cursor.execute("""
            SELECT
                SUM(CASE WHEN transaction_type = 'sale' THEN amount ELSE 0 END) as revenue,
                SUM(CASE WHEN transaction_type IN ('expense', 'shipping') THEN ABS(amount) ELSE 0 END) as expenses,
                SUM(CASE WHEN transaction_type = 'sale' THEN vinted_fee + payment_fee ELSE 0 END) as fees,
                COUNT(*) as count
            FROM transactions
            WHERE user_id = ?
            AND created_at >= ?
            AND created_at <= ?
        """, (user_id, period_start.isoformat(), period_end.isoformat()))

        data = cursor.fetchone()
        conn.close()

        gross_revenue = data['revenue'] or 0
        deductible_expenses = (data['expenses'] or 0) + (data['fees'] or 0)
        taxable_income = max(0, gross_revenue - deductible_expenses)
        estimated_tax = taxable_income * tax_rate

        return TaxReport(
            period_start=period_start,
            period_end=period_end,
            gross_revenue=gross_revenue,
            deductible_expenses=deductible_expenses,
            taxable_income=taxable_income,
            estimated_tax=estimated_tax,
            transactions_count=data['count'] or 0
        )

    async def forecast_revenue(
        self,
        user_id: str,
        period: str = "next_month"
    ) -> Forecast:
        """
        Forecast future revenue based on historical data

        period: "next_week", "next_month", "next_quarter"
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Determine lookback period and forecast days
        if period == "next_week":
            lookback_days = 28  # Last 4 weeks
            forecast_days = 7
        elif period == "next_quarter":
            lookback_days = 180  # Last 6 months
            forecast_days = 90
        else:  # next_month
            lookback_days = 90  # Last 3 months
            forecast_days = 30

        lookback_start = (datetime.utcnow() - timedelta(days=lookback_days)).isoformat()

        # Get historical revenue
        cursor.execute("""
            SELECT
                SUM(CASE WHEN transaction_type = 'sale' THEN amount ELSE 0 END) as revenue,
                SUM(CASE WHEN transaction_type = 'sale' THEN net_amount ELSE 0 END) as profit
            FROM transactions
            WHERE user_id = ?
            AND created_at >= ?
        """, (user_id, lookback_start))

        data = cursor.fetchone()
        conn.close()

        historical_revenue = data['revenue'] or 0
        historical_profit = data['profit'] or 0

        # Calculate daily average
        daily_revenue = historical_revenue / lookback_days
        daily_profit = historical_profit / lookback_days

        # Forecast
        forecasted_revenue = daily_revenue * forecast_days
        forecasted_profit = daily_profit * forecast_days

        # Confidence based on data availability
        if lookback_days >= 90:
            confidence = 0.85
        elif lookback_days >= 30:
            confidence = 0.70
        else:
            confidence = 0.50

        return Forecast(
            period=period,
            forecasted_revenue=forecasted_revenue,
            forecasted_profit=forecasted_profit,
            confidence=confidence,
            based_on_days=lookback_days
        )

    async def get_transactions(
        self,
        user_id: str,
        transaction_type: Optional[TransactionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Transaction]:
        """Get transaction history with filters"""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM transactions WHERE user_id = ?"
        params = [user_id]

        if transaction_type:
            query += " AND transaction_type = ?"
            params.append(transaction_type.value)

        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)

        transactions = []
        for row in cursor.fetchall():
            transactions.append(Transaction(
                id=row['id'],
                user_id=row['user_id'],
                transaction_type=TransactionType(row['transaction_type']),
                amount=row['amount'],
                description=row['description'],
                category=row['category'],
                listing_id=row['listing_id'],
                vinted_fee=row['vinted_fee'],
                payment_fee=row['payment_fee'],
                shipping_cost=row['shipping_cost'],
                net_amount=row['net_amount'],
                created_at=datetime.fromisoformat(row['created_at'])
            ))

        conn.close()
        return transactions

    async def get_financial_summary(
        self,
        user_id: str
    ) -> Dict:
        """
        Get comprehensive financial summary

        Includes:
        - Today's stats
        - This month's P&L
        - YTD summary
        - Next month forecast
        """
        # Today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_pl = await self.get_profit_loss_statement(user_id, today_start)

        # This month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_pl = await self.get_profit_loss_statement(user_id, month_start)

        # Year to date
        year_start = datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        ytd_pl = await self.get_profit_loss_statement(user_id, year_start)

        # Forecast
        forecast = await self.forecast_revenue(user_id, "next_month")

        return {
            'today': {
                'revenue': today_pl.gross_revenue,
                'profit': today_pl.net_profit,
                'sales_count': 0  # Would need separate query
            },
            'this_month': {
                'revenue': month_pl.net_revenue,
                'profit': month_pl.net_profit,
                'margin': month_pl.profit_margin,
                'total_fees': month_pl.platform_fees + month_pl.payment_fees
            },
            'year_to_date': {
                'revenue': ytd_pl.net_revenue,
                'profit': ytd_pl.net_profit,
                'margin': ytd_pl.profit_margin
            },
            'forecast_next_month': {
                'revenue': forecast.forecasted_revenue,
                'profit': forecast.forecasted_profit,
                'confidence': forecast.confidence
            }
        }

    async def get_expense_breakdown(
        self,
        user_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get expense breakdown by category"""
        if not period_start:
            now = datetime.utcnow()
            period_start = datetime(now.year, now.month, 1)

        if not period_end:
            period_end = datetime.utcnow()

        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT category, SUM(ABS(amount)) as total
            FROM transactions
            WHERE user_id = ?
            AND transaction_type IN ('expense', 'shipping')
            AND created_at >= ?
            AND created_at <= ?
            GROUP BY category
        """, (user_id, period_start.isoformat(), period_end.isoformat()))

        breakdown = {}
        for row in cursor.fetchall():
            breakdown[row['category']] = row['total']

        conn.close()
        return breakdown
