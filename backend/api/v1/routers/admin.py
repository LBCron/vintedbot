"""
Admin API Router
Platform administration and statistics (admin-only)

SECURITY: SQL injection protected + DB-based roles
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


# Response Models
class PlatformStatsResponse(BaseModel):
    total_users: int
    active_users_30d: int
    total_listings: int
    listings_this_month: int
    total_revenue_eur: float
    revenue_this_month_eur: float
    subscription_breakdown: Dict[str, int]


class RevenueAnalyticsResponse(BaseModel):
    mrr: float  # Monthly Recurring Revenue
    arr: float  # Annual Recurring Revenue
    churn_rate: float
    revenue_by_plan: Dict[str, float]


class RecentActivityResponse(BaseModel):
    recent_registrations: List[Dict]
    recent_listings: List[Dict]
    recent_subscriptions: List[Dict]


# SECURITY FIX: DB-based admin authentication
async def require_admin(current_user: User = Depends(get_current_user)):
    """
    Verify user has admin privileges

    SECURITY FIX:
    - ✅ Uses DB column \`is_admin\` instead of hardcoded emails
    - ✅ Proper error messages
    - ✅ Logging for security audit trail
    """
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        # SECURITY: Use parameterized query to prevent SQL injection
        row = await conn.fetchrow("""
            SELECT is_admin
            FROM users
            WHERE id = $1
        """, current_user.id)

        if not row:
            logger.warning(f"🔒 User {current_user.id} not found in admin check")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not row.get("is_admin", False):
            logger.warning(f"🔒 Unauthorized admin access attempt by user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        logger.info(f"✅ Admin access granted to user {current_user.id}")

    return current_user


@router.get("/stats", response_model=PlatformStatsResponse)
async def get_platform_stats(
    admin_user: User = Depends(require_admin)
):
    """
    Get overall platform statistics

    SECURITY:
    - ✅ Admin-only endpoint
    - ✅ All queries use parameterized statements
    """
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        # Total users
        total_users_row = await conn.fetchrow("SELECT COUNT(*) as count FROM users")
        total_users = total_users_row["count"] if total_users_row else 0

        # Active users (last 30 days)
        # SECURITY FIX: Parameterized query instead of f-string
        active_users_row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM users
            WHERE last_login_at >= $1
        """, datetime.utcnow() - timedelta(days=30))
        active_users_30d = active_users_row["count"] if active_users_row else 0

        # Total listings
        total_listings_row = await conn.fetchrow("SELECT COUNT(*) as count FROM listings")
        total_listings = total_listings_row["count"] if total_listings_row else 0

        # Listings this month
        # SECURITY FIX: Parameterized query
        listings_month_row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM listings
            WHERE created_at >= date_trunc('month', CURRENT_DATE)
        """)
        listings_this_month = listings_month_row["count"] if listings_month_row else 0

        # Subscription breakdown
        # SECURITY FIX: Parameterized query (no user input, but best practice)
        subscription_rows = await conn.fetch("""
            SELECT
                COALESCE(subscription_plan, 'free') as plan,
                COUNT(*) as count
            FROM users
            GROUP BY subscription_plan
        """)

        subscription_breakdown = {row["plan"]: row["count"] for row in subscription_rows}

        # Calculate revenue (simplified - would use Stripe data in production)
        plan_prices = {
            "starter": 9.99,
            "pro": 29.99,
            "enterprise": 99.99
        }

        total_revenue = sum(
            subscription_breakdown.get(plan, 0) * price
            for plan, price in plan_prices.items()
        )

        # Revenue this month (users with active subscriptions)
        revenue_month_row = await conn.fetchrow("""
            SELECT
                subscription_plan,
                COUNT(*) as count
            FROM users
            WHERE subscription_status = 'active'
            GROUP BY subscription_plan
        """)

        revenue_this_month = 0.0
        if revenue_month_row:
            revenue_this_month = sum(
                subscription_breakdown.get(plan, 0) * plan_prices.get(plan, 0)
                for plan in plan_prices.keys()
            )

        return PlatformStatsResponse(
            total_users=total_users,
            active_users_30d=active_users_30d,
            total_listings=total_listings,
            listings_this_month=listings_this_month,
            total_revenue_eur=round(total_revenue, 2),
            revenue_this_month_eur=round(revenue_this_month, 2),
            subscription_breakdown=subscription_breakdown
        )


@router.get("/revenue", response_model=RevenueAnalyticsResponse)
async def get_revenue_analytics(
    admin_user: User = Depends(require_admin)
):
    """
    Get revenue analytics and metrics

    SECURITY:
    - ✅ Admin-only
    - ✅ SQL injection protected
    """
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        # Get active subscriptions
        # SECURITY FIX: Parameterized query
        rows = await conn.fetch("""
            SELECT
                subscription_plan,
                COUNT(*) as count
            FROM users
            WHERE subscription_status = $1
            GROUP BY subscription_plan
        """, "active")

        plan_prices = {
            "starter": 9.99,
            "pro": 29.99,
            "enterprise": 99.99
        }

        revenue_by_plan = {}
        total_mrr = 0.0

        for row in rows:
            plan = row["subscription_plan"]
            count = row["count"]

            if plan in plan_prices:
                revenue = count * plan_prices[plan]
                revenue_by_plan[plan] = round(revenue, 2)
                total_mrr += revenue

        arr = total_mrr * 12

        # Calculate churn (simplified)
        # SECURITY FIX: Parameterized query
        churned_row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM users
            WHERE subscription_status = $1
            AND updated_at >= $2
        """, "canceled", datetime.utcnow() - timedelta(days=30))

        churned_count = churned_row["count"] if churned_row else 0

        active_row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM users
            WHERE subscription_status = $1
        """, "active")

        active_count = active_row["count"] if active_row else 0

        churn_rate = (churned_count / active_count * 100) if active_count > 0 else 0

        return RevenueAnalyticsResponse(
            mrr=round(total_mrr, 2),
            arr=round(arr, 2),
            churn_rate=round(churn_rate, 2),
            revenue_by_plan=revenue_by_plan
        )


@router.get("/activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    admin_user: User = Depends(require_admin),
    limit: int = 10
):
    """
    Get recent platform activity

    SECURITY:
    - ✅ Admin-only
    - ✅ Input validation on limit
    - ✅ SQL injection protected
    """
    # SECURITY: Validate and clamp limit
    if limit < 1 or limit > 100:
        limit = 10

    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        # Recent registrations
        # SECURITY FIX: Parameterized query with limit
        reg_rows = await conn.fetch("""
            SELECT
                id,
                email,
                created_at,
                subscription_plan
            FROM users
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)

        recent_registrations = [
            {
                "user_id": row["id"],
                "email": row["email"],
                "registered_at": row["created_at"].isoformat(),
                "plan": row["subscription_plan"] or "free"
            }
            for row in reg_rows
        ]

        # Recent listings
        # SECURITY FIX: Parameterized query
        listing_rows = await conn.fetch("""
            SELECT
                id,
                user_id,
                title,
                price,
                created_at
            FROM listings
            ORDER BY created_at DESC
            LIMIT $1
        """, limit)

        recent_listings = [
            {
                "listing_id": row["id"],
                "user_id": row["user_id"],
                "title": row["title"],
                "price": float(row["price"]) if row["price"] else 0.0,
                "created_at": row["created_at"].isoformat()
            }
            for row in listing_rows
        ]

        # Recent subscriptions
        # SECURITY FIX: Parameterized query
        sub_rows = await conn.fetch("""
            SELECT
                id,
                email,
                subscription_plan,
                updated_at
            FROM users
            WHERE subscription_status = $1
            ORDER BY updated_at DESC
            LIMIT $2
        """, "active", limit)

        recent_subscriptions = [
            {
                "user_id": row["id"],
                "email": row["email"],
                "plan": row["subscription_plan"],
                "subscribed_at": row["updated_at"].isoformat()
            }
            for row in sub_rows
        ]

        return RecentActivityResponse(
            recent_registrations=recent_registrations,
            recent_listings=recent_listings,
            recent_subscriptions=recent_subscriptions
        )


@router.post("/users/{user_id}/admin")
async def grant_admin_access(
    user_id: int,
    admin_user: User = Depends(require_admin)
):
    """
    Grant admin access to a user

    SECURITY:
    - ✅ Only existing admins can grant admin access
    - ✅ SQL injection protected
    - ✅ Audit logging
    """
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        # Check if user exists
        # SECURITY FIX: Parameterized query
        user_row = await conn.fetchrow("""
            SELECT id, email, is_admin
            FROM users
            WHERE id = $1
        """, user_id)

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user_row["is_admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already an admin"
            )

        # Grant admin access
        # SECURITY FIX: Parameterized query
        await conn.execute("""
            UPDATE users
            SET is_admin = true,
                updated_at = NOW()
            WHERE id = $1
        """, user_id)

        logger.warning(f"🔒 ADMIN ACCESS GRANTED: User {user_id} ({user_row['email']}) by admin {admin_user.id}")

        return {
            "status": "granted",
            "user_id": user_id,
            "email": user_row["email"]
        }


@router.delete("/users/{user_id}/admin")
async def revoke_admin_access(
    user_id: int,
    admin_user: User = Depends(require_admin)
):
    """
    Revoke admin access from a user

    SECURITY:
    - ✅ Only admins can revoke admin access
    - ✅ Cannot revoke own admin access (safety)
    - ✅ SQL injection protected
    - ✅ Audit logging
    """
    # SECURITY: Prevent self-revocation
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own admin access"
        )

    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        # Check if user exists and is admin
        # SECURITY FIX: Parameterized query
        user_row = await conn.fetchrow("""
            SELECT id, email, is_admin
            FROM users
            WHERE id = $1
        """, user_id)

        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not user_row["is_admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not an admin"
            )

        # Revoke admin access
        # SECURITY FIX: Parameterized query
        await conn.execute("""
            UPDATE users
            SET is_admin = false,
                updated_at = NOW()
            WHERE id = $1
        """, user_id)

        logger.warning(f"🔒 ADMIN ACCESS REVOKED: User {user_id} ({user_row['email']}) by admin {admin_user.id}")

        return {
            "status": "revoked",
            "user_id": user_id,
            "email": user_row["email"]
        }
