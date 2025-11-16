"""
Admin API Router
Platform administration and statistics (admin-only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict
from loguru import logger
from datetime import datetime, timedelta

from backend.core.auth import get_current_user
from backend.core.database import get_db_pool
from backend.models.user import User


router = APIRouter(prefix="/admin", tags=["admin"])


# Admin middleware
async def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role"""
    admin_emails = ["admin@vintedbot.com", "support@vintedbot.com"]

    if current_user.email not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


# Response Models
class PlatformStatsResponse(BaseModel):
    total_users: int
    active_users_30d: int
    total_accounts: int
    total_listings: int
    total_sales: int
    total_revenue: float
    subscriptions: Dict[str, int]
    growth_rate: float


@router.get("/stats", response_model=PlatformStatsResponse)
async def get_platform_statistics(
    admin: User = Depends(require_admin)
):
    """Get overall platform statistics"""
    pool = await get_db_pool()

    try:
        async with pool.acquire() as conn:
            total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
            thirty_days_ago = datetime.now() - timedelta(days=30)
            active_users = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE last_login > $1",
                thirty_days_ago
            )
            total_accounts = await conn.fetchval("SELECT COUNT(*) FROM accounts")
            total_listings = await conn.fetchval("SELECT COUNT(*) FROM drafts")
            total_sales = await conn.fetchval(
                "SELECT COUNT(*) FROM drafts WHERE sold = true"
            )
            total_revenue = await conn.fetchval(
                "SELECT COALESCE(SUM(price), 0) FROM drafts WHERE sold = true"
            ) or 0.0

            subscription_counts = await conn.fetch("""
                SELECT subscription_plan, COUNT(*) as count
                FROM users
                GROUP BY subscription_plan
            """)

            subscriptions = {
                row['subscription_plan'] or 'free': row['count']
                for row in subscription_counts
            }

            this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

            users_this_month = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE created_at >= $1",
                this_month_start
            )

            users_last_month = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE created_at >= $1 AND created_at < $2",
                last_month_start,
                this_month_start
            )

            growth_rate = 0.0
            if users_last_month > 0:
                growth_rate = ((users_this_month - users_last_month) / users_last_month) * 100

            return PlatformStatsResponse(
                total_users=total_users,
                active_users_30d=active_users,
                total_accounts=total_accounts,
                total_listings=total_listings,
                total_sales=total_sales,
                total_revenue=float(total_revenue),
                subscriptions=subscriptions,
                growth_rate=round(growth_rate, 2)
            )

    except Exception as e:
        logger.error(f"❌ Failed to get platform stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/revenue")
async def get_revenue_stats(
    period: str = "30d",
    admin: User = Depends(require_admin)
):
    """Get revenue statistics"""
    period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = period_days.get(period, 30)
    start_date = datetime.now() - timedelta(days=days)

    pool = await get_db_pool()

    try:
        async with pool.acquire() as conn:
            subscription_revenue = await conn.fetch("""
                SELECT subscription_plan, COUNT(*) as count
                FROM users
                WHERE subscription_plan IS NOT NULL
                  AND subscription_plan != 'free'
                  AND subscription_status = 'active'
                GROUP BY subscription_plan
            """)

            plan_prices = {'starter': 9.99, 'pro': 29.99, 'enterprise': 99.99}
            mrr = sum(
                row['count'] * plan_prices.get(row['subscription_plan'], 0)
                for row in subscription_revenue
            )

            new_subscriptions = await conn.fetchval("""
                SELECT COUNT(*)
                FROM users
                WHERE subscription_plan != 'free'
                  AND created_at >= $1
            """, start_date)

            churned = await conn.fetchval("""
                SELECT COUNT(*)
                FROM users
                WHERE subscription_status = 'cancelled'
                  AND updated_at >= $1
            """, start_date) or 0

            return {
                "period": period,
                "mrr": round(mrr, 2),
                "arr": round(mrr * 12, 2),
                "new_subscriptions": new_subscriptions,
                "churned_subscriptions": churned,
                "subscription_breakdown": [
                    {
                        "plan": row['subscription_plan'],
                        "count": row['count'],
                        "revenue": row['count'] * plan_prices.get(row['subscription_plan'], 0)
                    }
                    for row in subscription_revenue
                ]
            }

    except Exception as e:
        logger.error(f"❌ Failed to get revenue stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/activity")
async def get_recent_activity(
    limit: int = 50,
    admin: User = Depends(require_admin)
):
    """Get recent platform activity"""
    pool = await get_db_pool()

    try:
        async with pool.acquire() as conn:
            recent_users = await conn.fetch("""
                SELECT id, email, username, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT $1
            """, limit // 2)

            recent_listings = await conn.fetch("""
                SELECT d.id, d.title, d.price, d.created_at, u.username
                FROM drafts d
                JOIN users u ON u.id = d.user_id
                WHERE d.status = 'published'
                ORDER BY d.created_at DESC
                LIMIT $1
            """, limit // 2)

            activities = []

            for user in recent_users:
                activities.append({
                    "type": "user_registered",
                    "timestamp": user['created_at'].isoformat(),
                    "data": {
                        "user_id": str(user['id']),
                        "username": user['username']
                    }
                })

            for listing in recent_listings:
                activities.append({
                    "type": "listing_created",
                    "timestamp": listing['created_at'].isoformat(),
                    "data": {
                        "title": listing['title'],
                        "price": float(listing['price']) if listing['price'] else 0,
                        "username": listing['username']
                    }
                })

            activities.sort(key=lambda x: x['timestamp'], reverse=True)

            return {
                "activities": activities[:limit],
                "total": len(activities)
            }

    except Exception as e:
        logger.error(f"❌ Failed to get activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
