"""
Push Notifications API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Optional
import logging

from backend.core.deps import get_current_user, get_db_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/push", tags=["push-notifications"])


class PushSubscription(BaseModel):
    """Push subscription from browser"""
    endpoint: str
    keys: Dict[str, str]  # { p256dh, auth }


class PushSubscriptionUpdate(BaseModel):
    """Update push subscription"""
    subscription: PushSubscription
    enabled: bool = True


@router.post("/subscribe")
async def subscribe_to_push(
    data: PushSubscriptionUpdate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_pool)
):
    """
    Subscribe to push notifications

    Stores the push subscription for this user
    """

    user_id = current_user["id"]

    try:
        async with db.acquire() as conn:
            # Check if subscription exists
            existing = await conn.fetchrow(
                """
                SELECT id FROM push_subscriptions
                WHERE user_id = $1 AND endpoint = $2
                """,
                user_id,
                data.subscription.endpoint
            )

            if existing:
                # Update existing
                await conn.execute(
                    """
                    UPDATE push_subscriptions
                    SET keys = $1, enabled = $2, updated_at = NOW()
                    WHERE id = $3
                    """,
                    data.subscription.keys,
                    data.enabled,
                    existing['id']
                )

                return {
                    "success": True,
                    "message": "Push subscription updated"
                }

            # Insert new
            await conn.execute(
                """
                INSERT INTO push_subscriptions (user_id, endpoint, keys, enabled)
                VALUES ($1, $2, $3, $4)
                """,
                user_id,
                data.subscription.endpoint,
                data.subscription.keys,
                data.enabled
            )

            logger.info(f"User {user_id} subscribed to push notifications")

            return {
                "success": True,
                "message": "Push subscription created"
            }

    except Exception as e:
        logger.error(f"Subscribe to push error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/unsubscribe")
async def unsubscribe_from_push(
    endpoint: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_pool)
):
    """
    Unsubscribe from push notifications
    """

    user_id = current_user["id"]

    try:
        async with db.acquire() as conn:
            result = await conn.execute(
                """
                DELETE FROM push_subscriptions
                WHERE user_id = $1 AND endpoint = $2
                """,
                user_id,
                endpoint
            )

            logger.info(f"User {user_id} unsubscribed from push notifications")

            return {
                "success": True,
                "message": "Push subscription removed"
            }

    except Exception as e:
        logger.error(f"Unsubscribe from push error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subscription")
async def get_push_subscription(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_pool)
):
    """
    Get user's push subscription status
    """

    user_id = current_user["id"]

    try:
        async with db.acquire() as conn:
            subscriptions = await conn.fetch(
                """
                SELECT endpoint, keys, enabled, created_at
                FROM push_subscriptions
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id
            )

            return {
                "subscriptions": [
                    {
                        "endpoint": sub['endpoint'],
                        "keys": sub['keys'],
                        "enabled": sub['enabled'],
                        "created_at": sub['created_at'].isoformat()
                    }
                    for sub in subscriptions
                ],
                "count": len(subscriptions)
            }

    except Exception as e:
        logger.error(f"Get push subscription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """
    Get VAPID public key for push subscription

    No authentication required - public key is safe to share
    """

    import os

    vapid_public_key = os.getenv("VAPID_PUBLIC_KEY")

    if not vapid_public_key:
        raise HTTPException(
            status_code=503,
            detail="Push notifications not configured"
        )

    return {
        "publicKey": vapid_public_key
    }


@router.post("/test")
async def send_test_notification(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db_pool)
):
    """
    Send a test push notification
    """

    from backend.services.push_notification_service import push_service

    user_id = current_user["id"]

    try:
        async with db.acquire() as conn:
            # Get user's subscriptions
            subscriptions = await conn.fetch(
                """
                SELECT endpoint, keys
                FROM push_subscriptions
                WHERE user_id = $1 AND enabled = true
                """,
                user_id
            )

            if not subscriptions:
                raise HTTPException(
                    status_code=404,
                    detail="No active push subscriptions found"
                )

            # Send test to all subscriptions
            sent_count = 0
            for sub in subscriptions:
                subscription_info = {
                    "endpoint": sub['endpoint'],
                    "keys": sub['keys']
                }

                success = await push_service.send_notification(
                    subscription_info=subscription_info,
                    title="🔔 Test Notification",
                    message="VintedBot push notifications are working!",
                    url="/"
                )

                if success:
                    sent_count += 1

            return {
                "success": True,
                "sent": sent_count,
                "total": len(subscriptions),
                "message": f"Test notification sent to {sent_count} device(s)"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send test notification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
