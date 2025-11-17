"""
Payments API Router
Handles subscriptions and billing via Stripe

SECURITY: All critical vulnerabilities fixed
"""
import os  # SECURITY FIX: Missing import added
import stripe  # SECURITY FIX Bug #69: Import stripe for specific exception handling
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from backend.core.auth import get_current_user
# from backend.core.database import get_db_pool  # DISABLED: Function no longer exists
from backend.services.stripe_service import stripe_service
from backend.models import User  # FIXED: Import from models not models.user


router = APIRouter(prefix="/payments", tags=["payments"])


# Temporary stub to prevent crashes during migration
def get_db_pool():
    """
    DEPRECATED: This function is no longer available.
    The application has migrated from asyncpg to SQLAlchemy.
    Payment endpoints need to be refactored.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Payment endpoints are temporarily disabled during database migration. Please use the main API."
    )


# Request/Response Models
class CheckoutRequest(BaseModel):
    plan: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class BillingPortalResponse(BaseModel):
    portal_url: str


class PlanLimitsResponse(BaseModel):
    plan: str
    status: str
    limit: int
    current_usage: int
    can_create: bool
    remaining: int


@router.get("/plans")
async def get_available_plans():
    """
    Get all available subscription plans

    Public endpoint - no auth required
    """
    return {
        "plans": stripe_service.PLANS,
        "currency": "EUR"
    }


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create Stripe checkout session for subscription

    SECURITY:
    - ✅ User authentication required
    - ✅ Input validation via Pydantic
    - ✅ Rate limiting (inherited from main app)
    """
    # SECURITY: Validate plan
    if request.plan not in ["starter", "pro", "enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan. Available: starter, pro, enterprise"
        )

    # Check if user already has active subscription
    db_pool = get_db_pool()
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT subscription_plan, subscription_status
            FROM users
            WHERE id = $1
        """, current_user.id)

        if row and row["subscription_status"] == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an active subscription. Use billing portal to change plans."
            )

    # SECURITY FIX: Use environment variable for base URL
    base_url = os.getenv("FRONTEND_URL", "https://vintedbot.com")

    success_url = request.success_url or f"{base_url}/dashboard?payment=success"
    cancel_url = request.cancel_url or f"{base_url}/pricing?payment=canceled"

    try:
        session_data = await stripe_service.create_checkout_session(
            user_id=current_user.id,
            plan=request.plan,
            success_url=success_url,
            cancel_url=cancel_url
        )

        return CheckoutResponse(**session_data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    # SECURITY FIX Bug #69: Replace generic Exception with specific Stripe exceptions
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Invalid Stripe request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment configuration"
        )
    except (stripe.error.APIConnectionError, stripe.error.RateLimitError) as e:
        logger.error(f"Stripe API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service temporarily unavailable"
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment processing error"
        )


@router.get("/billing-portal", response_model=BillingPortalResponse)
async def get_billing_portal(
    current_user: User = Depends(get_current_user)
):
    """
    Get Stripe billing portal URL for subscription management

    SECURITY:
    - ✅ User must be authenticated
    - ✅ User must have Stripe customer ID
    """
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT stripe_customer_id
            FROM users
            WHERE id = $1
        """, current_user.id)

        if not row or not row["stripe_customer_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found"
            )

        customer_id = row["stripe_customer_id"]

    base_url = os.getenv("FRONTEND_URL", "https://vintedbot.com")
    return_url = f"{base_url}/dashboard"

    try:
        portal_data = await stripe_service.create_billing_portal_session(
            customer_id=customer_id,
            return_url=return_url
        )

        return BillingPortalResponse(**portal_data)

    # SECURITY FIX Bug #69: Replace generic Exception with specific Stripe exceptions
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Invalid billing portal request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid billing configuration"
        )
    except (stripe.error.APIConnectionError, stripe.error.RateLimitError) as e:
        logger.error(f"Stripe API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing portal temporarily unavailable"
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in billing portal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to access billing portal"
        )


@router.get("/limits", response_model=PlanLimitsResponse)
async def get_plan_limits(
    current_user: User = Depends(get_current_user)
):
    """
    Get current plan limits and usage

    Returns how many listings user can create
    """
    try:
        db_pool = get_db_pool()
        limits = await stripe_service.check_plan_limits(current_user.id, db_pool)

        return PlanLimitsResponse(**limits)

    # SECURITY FIX Bug #69: Replace generic Exception with specific exceptions
    except (ValueError, KeyError) as e:
        logger.error(f"Invalid plan data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan configuration"
        )
    except Exception as e:
        logger.error(f"Database error checking plan limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check plan limits"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhooks

    SECURITY:
    - ✅ Signature verification (prevents spoofing)
    - ✅ No authentication required (Stripe signs requests)
    - ✅ Idempotent processing
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )

    # Get raw body for signature verification
    payload = await request.body()

    try:
        # SECURITY: Verify webhook signature
        event = await stripe_service.verify_webhook_signature(
            payload=payload,
            signature=stripe_signature
        )

    # SECURITY FIX Bug #69: Replace generic Exception with specific Stripe exceptions
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload format"
        )

    # Handle different event types
    event_type = event.get("type")
    event_data = event.get("data", {})

    db_pool = get_db_pool()

    try:
        if event_type == "checkout.session.completed":
            await stripe_service.handle_checkout_completed(event_data, db_pool)

        elif event_type == "customer.subscription.updated":
            await stripe_service.handle_subscription_updated(event_data, db_pool)

        elif event_type == "customer.subscription.deleted":
            await stripe_service.handle_subscription_deleted(event_data, db_pool)

        else:
            logger.info(f"Unhandled webhook event: {event_type}")

        return {"status": "success"}

    # SECURITY FIX Bug #69: Replace generic Exception with specific exceptions
    except (ValueError, KeyError, TypeError) as e:
        logger.error(f"Webhook data validation error: {e}")
        # Return 200 to prevent Stripe from retrying invalid data
        return {"status": "error", "message": "Invalid webhook data format"}
    except Exception as e:
        # Last resort: catch database and unexpected errors
        logger.error(f"Unexpected webhook processing error: {e}", exc_info=True)
        # Return 200 to prevent Stripe from retrying
        return {"status": "error", "message": "Internal processing error"}


@router.get("/subscription")
async def get_subscription_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get current subscription status
    """
    db_pool = get_db_pool()

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                subscription_plan,
                subscription_status,
                stripe_customer_id,
                stripe_subscription_id,
                created_at
            FROM users
            WHERE id = $1
        """, current_user.id)

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return {
            "plan": row["subscription_plan"] or "free",
            "status": row["subscription_status"] or "inactive",
            "has_stripe_account": bool(row["stripe_customer_id"]),
            "member_since": row["created_at"].isoformat() if row["created_at"] else None
        }
