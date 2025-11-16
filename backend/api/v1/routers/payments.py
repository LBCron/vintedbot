"""
Payments API Router
Handles subscriptions and billing
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from backend.core.auth import get_current_user
from backend.core.database import get_db_pool
from backend.services.stripe_service import stripe_service
from backend.models.user import User


router = APIRouter(prefix="/payments", tags=["payments"])


# Request/Response Models
class CheckoutRequest(BaseModel):
    plan: str  # starter, pro, enterprise


class CheckoutResponse(BaseModel):
    session_id: str
    url: str
    message: str


class SubscriptionResponse(BaseModel):
    id: str
    status: str
    plan: str
    current_period_end: str
    cancel_at_period_end: bool


class BillingPortalResponse(BaseModel):
    url: str


class PlanLimitsResponse(BaseModel):
    plan: str
    listings_limit: int
    ai_features: bool
    priority_support: bool


@router.get("/plans")
async def get_available_plans():
    """
    Get all available subscription plans

    Returns:
        List of plans with pricing
    """
    plans = []

    for plan_id, config in stripe_service.PLANS.items():
        plans.append({
            "id": plan_id,
            "name": config["name"],
            "price": config["price"] / 100 if config["price"] > 0 else 0,  # Convert cents to euros
            "currency": config["currency"],
            "interval": config["interval"],
            "listings_limit": config["listings_limit"],
            "ai_features": config["ai_features"],
            "priority_support": config["priority_support"]
        })

    return {"plans": plans}


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a Stripe checkout session for subscription

    Args:
        request: Checkout request with plan
        current_user: Authenticated user

    Returns:
        Checkout session URL
    """
    if not stripe_service.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not available"
        )

    # Validate plan
    if request.plan not in stripe_service.PLANS or request.plan == "free":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan: {request.plan}"
        )

    # Get or create Stripe customer
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow(
            "SELECT stripe_customer_id FROM users WHERE id = $1",
            current_user.id
        )

        stripe_customer_id = user_data.get("stripe_customer_id") if user_data else None

        # Create customer if doesn't exist
        if not stripe_customer_id:
            stripe_customer_id = await stripe_service.create_customer(
                email=current_user.email,
                name=current_user.username,
                metadata={"user_id": str(current_user.id)}
            )

            if not stripe_customer_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create customer"
                )

            # Save customer ID
            await conn.execute(
                "UPDATE users SET stripe_customer_id = $1 WHERE id = $2",
                stripe_customer_id,
                current_user.id
            )

    # Create checkout session
    success_url = f"{os.getenv('FRONTEND_URL', 'https://vintedbot-staging.fly.dev')}/subscription/success"
    cancel_url = f"{os.getenv('FRONTEND_URL', 'https://vintedbot-staging.fly.dev')}/subscription/cancel"

    session_data = await stripe_service.create_checkout_session(
        customer_id=stripe_customer_id,
        plan=request.plan,
        success_url=success_url,
        cancel_url=cancel_url,
        user_id=str(current_user.id)
    )

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

    return CheckoutResponse(
        session_id=session_data["session_id"],
        url=session_data["url"],
        message=f"Checkout session created for {request.plan} plan"
    )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's subscription

    Returns:
        Subscription details
    """
    if not stripe_service.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not available"
        )

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow(
            "SELECT stripe_subscription_id, subscription_plan FROM users WHERE id = $1",
            current_user.id
        )

        if not user_data or not user_data.get("stripe_subscription_id"):
            # Return free plan
            return SubscriptionResponse(
                id="free",
                status="active",
                plan="free",
                current_period_end="",
                cancel_at_period_end=False
            )

        subscription_id = user_data.get("stripe_subscription_id")

        # Get subscription from Stripe
        subscription = await stripe_service.get_subscription(subscription_id)

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        return SubscriptionResponse(
            id=subscription["id"],
            status=subscription["status"],
            plan=subscription["plan"],
            current_period_end=subscription["current_period_end"].isoformat(),
            cancel_at_period_end=subscription["cancel_at_period_end"]
        )


@router.post("/subscription/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user)
):
    """
    Cancel current subscription (at period end)

    Returns:
        Success message
    """
    if not stripe_service.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not available"
        )

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow(
            "SELECT stripe_subscription_id FROM users WHERE id = $1",
            current_user.id
        )

        if not user_data or not user_data.get("stripe_subscription_id"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )

        subscription_id = user_data.get("stripe_subscription_id")

        # Cancel subscription
        success = await stripe_service.cancel_subscription(
            subscription_id=subscription_id,
            immediately=False
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )

        return {
            "success": True,
            "message": "Subscription will cancel at the end of the billing period"
        }


@router.get("/billing-portal", response_model=BillingPortalResponse)
async def get_billing_portal(
    current_user: User = Depends(get_current_user)
):
    """
    Get Stripe billing portal URL

    Returns:
        Portal URL
    """
    if not stripe_service.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not available"
        )

    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow(
            "SELECT stripe_customer_id FROM users WHERE id = $1",
            current_user.id
        )

        if not user_data or not user_data.get("stripe_customer_id"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No customer found"
            )

        customer_id = user_data.get("stripe_customer_id")

        return_url = f"{os.getenv('FRONTEND_URL', 'https://vintedbot-staging.fly.dev')}/subscription"

        portal_url = await stripe_service.create_billing_portal_session(
            customer_id=customer_id,
            return_url=return_url
        )

        if not portal_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create billing portal session"
            )

        return BillingPortalResponse(url=portal_url)


@router.get("/plan-limits", response_model=PlanLimitsResponse)
async def get_plan_limits(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's plan limits

    Returns:
        Plan limits
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        user_data = await conn.fetchrow(
            "SELECT subscription_plan FROM users WHERE id = $1",
            current_user.id
        )

        plan = user_data.get("subscription_plan", "free") if user_data else "free"

        limits = stripe_service.get_plan_limits(plan)

        return PlanLimitsResponse(
            plan=plan,
            listings_limit=limits["listings_limit"],
            ai_features=limits["ai_features"],
            priority_support=limits["priority_support"]
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    """
    Stripe webhook endpoint

    Handles:
    - checkout.session.completed
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    if not stripe_service.is_enabled():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Get raw body
    payload = await request.body()

    # Verify signature
    event = stripe_service.verify_webhook_signature(payload, stripe_signature)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )

    event_type = event['type']
    data = event['data']['object']

    logger.info(f"📨 Webhook received: {event_type}")

    # Handle events
    pool = await get_db_pool()

    try:
        if event_type == 'checkout.session.completed':
            # Payment successful - activate subscription
            user_id = data['metadata'].get('user_id')
            plan = data['metadata'].get('plan')
            subscription_id = data.get('subscription')

            if user_id and subscription_id:
                async with pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE users
                        SET stripe_subscription_id = $1,
                            subscription_plan = $2,
                            subscription_status = 'active'
                        WHERE id = $3
                    """, subscription_id, plan, user_id)

                logger.info(f"✅ Activated subscription for user {user_id}")

        elif event_type == 'customer.subscription.updated':
            # Subscription updated
            subscription_id = data['id']
            status = data['status']

            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE users
                    SET subscription_status = $1
                    WHERE stripe_subscription_id = $2
                """, status, subscription_id)

            logger.info(f"✅ Updated subscription {subscription_id} to {status}")

        elif event_type == 'customer.subscription.deleted':
            # Subscription cancelled
            subscription_id = data['id']

            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE users
                    SET subscription_plan = 'free',
                        subscription_status = 'cancelled'
                    WHERE stripe_subscription_id = $1
                """, subscription_id)

            logger.info(f"✅ Cancelled subscription {subscription_id}")

        elif event_type == 'invoice.payment_failed':
            # Payment failed
            subscription_id = data.get('subscription')

            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE users
                    SET subscription_status = 'past_due'
                    WHERE stripe_subscription_id = $1
                """, subscription_id)

            logger.warning(f"⚠️ Payment failed for subscription {subscription_id}")

    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return {"status": "success"}


# Import os for environment variables
import os
