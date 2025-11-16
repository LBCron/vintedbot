"""
Stripe Payment Service
Handles subscriptions, payments, and billing
"""
import os
import stripe
from typing import Dict, Optional, List
from loguru import logger
from datetime import datetime


class StripeService:
    """
    Stripe payment processing service

    Plans:
    - Free: 0€/month - 10 listings max
    - Starter: 9.99€/month - 100 listings
    - Pro: 29.99€/month - Unlimited listings + AI features
    - Enterprise: 99.99€/month - All features + priority support
    """

    PLANS = {
        "free": {
            "name": "Free",
            "price": 0,
            "currency": "eur",
            "interval": "month",
            "listings_limit": 10,
            "ai_features": False,
            "priority_support": False
        },
        "starter": {
            "name": "Starter",
            "price": 999,  # in cents
            "currency": "eur",
            "interval": "month",
            "listings_limit": 100,
            "ai_features": False,
            "priority_support": False,
            "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID")
        },
        "pro": {
            "name": "Pro",
            "price": 2999,
            "currency": "eur",
            "interval": "month",
            "listings_limit": -1,  # Unlimited
            "ai_features": True,
            "priority_support": False,
            "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID")
        },
        "enterprise": {
            "name": "Enterprise",
            "price": 9999,
            "currency": "eur",
            "interval": "month",
            "listings_limit": -1,
            "ai_features": True,
            "priority_support": True,
            "stripe_price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID")
        }
    }

    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if self.api_key:
            stripe.api_key = self.api_key
            logger.info("✅ Stripe initialized")
        else:
            logger.warning("⚠️ Stripe API key not found")

    def is_enabled(self) -> bool:
        """Check if Stripe is properly configured"""
        return self.api_key is not None

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Create a Stripe customer

        Args:
            email: Customer email
            name: Customer name
            metadata: Additional metadata

        Returns:
            Customer ID or None if failed
        """
        if not self.is_enabled():
            logger.warning("Stripe not enabled - skipping customer creation")
            return None

        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )

            logger.info(f"✅ Created Stripe customer: {customer.id}")
            return customer.id

        except Exception as e:
            logger.error(f"❌ Failed to create Stripe customer: {e}")
            return None

    async def create_checkout_session(
        self,
        customer_id: str,
        plan: str,
        success_url: str,
        cancel_url: str,
        user_id: str
    ) -> Optional[Dict]:
        """
        Create a Stripe checkout session for subscription

        Args:
            customer_id: Stripe customer ID
            plan: Plan name (starter, pro, enterprise)
            success_url: Redirect URL after success
            cancel_url: Redirect URL after cancel
            user_id: Internal user ID

        Returns:
            Session data or None if failed
        """
        if not self.is_enabled():
            return None

        if plan not in self.PLANS or plan == "free":
            logger.error(f"Invalid plan: {plan}")
            return None

        plan_config = self.PLANS[plan]
        price_id = plan_config.get("stripe_price_id")

        if not price_id:
            logger.error(f"Price ID not configured for plan: {plan}")
            return None

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id,
                    'plan': plan
                }
            )

            logger.info(f"✅ Created checkout session: {session.id}")

            return {
                "session_id": session.id,
                "url": session.url,
                "customer_id": customer_id
            }

        except Exception as e:
            logger.error(f"❌ Failed to create checkout session: {e}")
            return None

    async def create_subscription(
        self,
        customer_id: str,
        plan: str
    ) -> Optional[str]:
        """
        Create a subscription directly (without checkout)

        Args:
            customer_id: Stripe customer ID
            plan: Plan name

        Returns:
            Subscription ID or None
        """
        if not self.is_enabled():
            return None

        if plan not in self.PLANS or plan == "free":
            return None

        plan_config = self.PLANS[plan]
        price_id = plan_config.get("stripe_price_id")

        if not price_id:
            return None

        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                metadata={'plan': plan}
            )

            logger.info(f"✅ Created subscription: {subscription.id}")
            return subscription.id

        except Exception as e:
            logger.error(f"❌ Failed to create subscription: {e}")
            return None

    async def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False
    ) -> bool:
        """
        Cancel a subscription

        Args:
            subscription_id: Stripe subscription ID
            immediately: Cancel immediately or at period end

        Returns:
            True if successful
        """
        if not self.is_enabled():
            return False

        try:
            if immediately:
                stripe.Subscription.delete(subscription_id)
                logger.info(f"✅ Cancelled subscription immediately: {subscription_id}")
            else:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                logger.info(f"✅ Subscription will cancel at period end: {subscription_id}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to cancel subscription: {e}")
            return False

    async def get_subscription(self, subscription_id: str) -> Optional[Dict]:
        """
        Get subscription details

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription data or None
        """
        if not self.is_enabled():
            return None

        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            return {
                "id": subscription.id,
                "customer_id": subscription.customer,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "plan": subscription.metadata.get("plan", "unknown")
            }

        except Exception as e:
            logger.error(f"❌ Failed to get subscription: {e}")
            return None

    async def get_customer_subscriptions(self, customer_id: str) -> List[Dict]:
        """
        Get all subscriptions for a customer

        Args:
            customer_id: Stripe customer ID

        Returns:
            List of subscriptions
        """
        if not self.is_enabled():
            return []

        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='all'
            )

            return [
                {
                    "id": sub.id,
                    "status": sub.status,
                    "plan": sub.metadata.get("plan", "unknown"),
                    "current_period_end": datetime.fromtimestamp(sub.current_period_end)
                }
                for sub in subscriptions.data
            ]

        except Exception as e:
            logger.error(f"❌ Failed to get customer subscriptions: {e}")
            return []

    async def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Optional[str]:
        """
        Create a billing portal session for customer to manage subscription

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal

        Returns:
            Portal URL or None
        """
        if not self.is_enabled():
            return None

        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )

            logger.info(f"✅ Created billing portal session for {customer_id}")
            return session.url

        except Exception as e:
            logger.error(f"❌ Failed to create billing portal session: {e}")
            return None

    def get_plan_limits(self, plan: str) -> Dict:
        """
        Get limits for a plan

        Args:
            plan: Plan name

        Returns:
            Plan limits
        """
        if plan not in self.PLANS:
            plan = "free"

        config = self.PLANS[plan]

        return {
            "listings_limit": config["listings_limit"],
            "ai_features": config["ai_features"],
            "priority_support": config["priority_support"]
        }

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> Optional[Dict]:
        """
        Verify Stripe webhook signature

        Args:
            payload: Raw request body
            signature: Stripe-Signature header

        Returns:
            Event object or None if invalid
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return None

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            logger.info(f"✅ Verified webhook: {event['type']}")
            return event

        except Exception as e:
            logger.error(f"❌ Webhook verification failed: {e}")
            return None


# Global instance
stripe_service = StripeService()
