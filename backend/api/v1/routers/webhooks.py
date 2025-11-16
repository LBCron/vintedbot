"""
Webhooks API Router
Manage external webhooks (Zapier, Make, custom integrations)

SECURITY: SSRF protection inherited from webhook_service
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict
from loguru import logger
import secrets

from backend.core.auth import get_current_user
from backend.core.database import get_db_pool
from backend.services.webhook_service import webhook_service
from backend.models.user import User


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Request/Response Models
class CreateWebhookRequest(BaseModel):
    url: HttpUrl
    events: List[str] = Field(..., min_items=1, max_items=10)
    description: Optional[str] = Field(None, max_length=200)


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: List[str]
    description: Optional[str]
    secret: str
    is_active: bool
    created_at: str
    last_triggered_at: Optional[str]
    delivery_count: int
    failure_count: int


class TestWebhookRequest(BaseModel):
    url: HttpUrl
    secret: Optional[str] = None


# Available webhook events
AVAILABLE_EVENTS = [
    "listing.created",
    "listing.updated",
    "listing.sold",
    "listing.deleted",
    "message.received",
    "account.connected",
    "subscription.updated",
]


@router.get("/events")
async def get_available_events():
    """
    Get list of available webhook events

    Public endpoint - shows what events can be subscribed to
    """
    return {
        "events": AVAILABLE_EVENTS,
        "description": {
            "listing.created": "Triggered when a new listing is created",
            "listing.updated": "Triggered when a listing is updated",
            "listing.sold": "Triggered when a listing is marked as sold",
            "listing.deleted": "Triggered when a listing is deleted",
            "message.received": "Triggered when a new message is received",
            "account.connected": "Triggered when a Vinted account is connected",
            "subscription.updated": "Triggered when subscription plan changes"
        }
    }


@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    request: CreateWebhookRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new webhook

    SECURITY:
    - ✅ SSRF protection via webhook_service.validate_webhook_url()
    - ✅ URL validation (must be HTTP/HTTPS)
    - ✅ Event validation
    - ✅ Rate limiting (max 10 webhooks per user)
    """
    # SECURITY: Validate URL to prevent SSRF
    url_str = str(request.url)
    is_valid = await webhook_service.validate_webhook_url(url_str)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook URL. Cannot target private IPs, localhost, or metadata endpoints."
        )

    # Validate events
    invalid_events = [e for e in request.events if e not in AVAILABLE_EVENTS]
    if invalid_events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid events: {', '.join(invalid_events)}"
        )

    # SECURITY: Rate limiting - max 10 webhooks per user
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        count_row = await conn.fetchrow("""
            SELECT COUNT(*) as count
            FROM webhooks
            WHERE user_id = $1
        """, current_user.id)

        if count_row and count_row["count"] >= 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 webhooks per user. Delete unused webhooks first."
            )

        # Generate secure secret for webhook verification
        secret = secrets.token_urlsafe(32)

        # Create webhook
        row = await conn.fetchrow("""
            INSERT INTO webhooks (
                user_id, url, events, description, secret,
                is_active, delivery_count, failure_count
            )
            VALUES ($1, $2, $3, $4, $5, true, 0, 0)
            RETURNING id, url, events, description, secret, is_active,
                      created_at, last_triggered_at, delivery_count, failure_count
        """, current_user.id, url_str, request.events, request.description, secret)

        logger.info(f"✅ Webhook created: {row['id']} for user {current_user.id}")

        return WebhookResponse(
            id=row["id"],
            url=row["url"],
            events=row["events"],
            description=row["description"],
            secret=row["secret"],
            is_active=row["is_active"],
            created_at=row["created_at"].isoformat(),
            last_triggered_at=row["last_triggered_at"].isoformat() if row["last_triggered_at"] else None,
            delivery_count=row["delivery_count"],
            failure_count=row["failure_count"]
        )


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_user)
):
    """
    List all webhooks for current user
    """
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, url, events, description, secret, is_active,
                   created_at, last_triggered_at, delivery_count, failure_count
            FROM webhooks
            WHERE user_id = $1
            ORDER BY created_at DESC
        """, current_user.id)

        return [
            WebhookResponse(
                id=row["id"],
                url=row["url"],
                events=row["events"],
                description=row["description"],
                secret=row["secret"],
                is_active=row["is_active"],
                created_at=row["created_at"].isoformat(),
                last_triggered_at=row["last_triggered_at"].isoformat() if row["last_triggered_at"] else None,
                delivery_count=row["delivery_count"],
                failure_count=row["failure_count"]
            )
            for row in rows
        ]


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a webhook

    SECURITY: Only owner can delete
    """
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        # Check ownership
        row = await conn.fetchrow("""
            SELECT id FROM webhooks
            WHERE id = $1 AND user_id = $2
        """, webhook_id, current_user.id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )

        # Delete
        await conn.execute("""
            DELETE FROM webhooks
            WHERE id = $1
        """, webhook_id)

        logger.info(f"✅ Webhook deleted: {webhook_id}")

        return {"status": "deleted", "id": webhook_id}


@router.post("/{webhook_id}/toggle")
async def toggle_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Enable/disable a webhook

    SECURITY: Only owner can toggle
    """
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        # Check ownership and get current status
        row = await conn.fetchrow("""
            SELECT is_active FROM webhooks
            WHERE id = $1 AND user_id = $2
        """, webhook_id, current_user.id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )

        new_status = not row["is_active"]

        # Toggle
        await conn.execute("""
            UPDATE webhooks
            SET is_active = $1
            WHERE id = $2
        """, new_status, webhook_id)

        return {
            "status": "updated",
            "id": webhook_id,
            "is_active": new_status
        }


@router.post("/test")
async def test_webhook(
    request: TestWebhookRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Test a webhook URL before creating it

    SECURITY:
    - ✅ SSRF protection
    - ✅ No database persistence
    - ✅ Rate limiting (inherited)
    """
    url_str = str(request.url)

    # SECURITY: Validate URL
    is_valid = await webhook_service.validate_webhook_url(url_str)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook URL. Cannot target private IPs, localhost, or metadata endpoints."
        )

    # Test webhook
    result = await webhook_service.test_webhook(
        url=url_str,
        secret=request.secret
    )

    return result


@router.get("/{webhook_id}/stats")
async def get_webhook_stats(
    webhook_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics for a webhook

    SECURITY: Only owner can view stats
    """
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                delivery_count,
                failure_count,
                last_triggered_at,
                created_at,
                is_active
            FROM webhooks
            WHERE id = $1 AND user_id = $2
        """, webhook_id, current_user.id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )

        total = row["delivery_count"] + row["failure_count"]
        success_rate = (row["delivery_count"] / total * 100) if total > 0 else 0

        return {
            "webhook_id": webhook_id,
            "total_attempts": total,
            "successful_deliveries": row["delivery_count"],
            "failed_deliveries": row["failure_count"],
            "success_rate": round(success_rate, 2),
            "last_triggered_at": row["last_triggered_at"].isoformat() if row["last_triggered_at"] else None,
            "is_active": row["is_active"]
        }
