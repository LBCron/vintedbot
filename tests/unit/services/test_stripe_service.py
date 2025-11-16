"""
Unit tests for Stripe service
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from backend.services.stripe_service import StripeService, stripe_service


class TestStripeService:
    """Test suite for Stripe payment service"""
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_success(self, mock_stripe, mock_db_pool):
        """Test successful checkout session creation"""
        result = await stripe_service.create_checkout_session(
            user_id=1,
            plan="pro",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        
        assert "checkout_url" in result
        assert "session_id" in result
        assert result["session_id"] == "cs_test_123"
        mock_stripe["checkout"].assert_called_once()
    
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_invalid_plan(self):
        """Test checkout with invalid plan raises error"""
        with pytest.raises(ValueError, match="Invalid plan"):
            await stripe_service.create_checkout_session(
                user_id=1,
                plan="invalid_plan",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel"
            )
    
    
    @pytest.mark.asyncio
    async def test_create_checkout_session_free_plan(self):
        """Test that free plan cannot be checked out"""
        with pytest.raises(ValueError, match="Invalid plan"):
            await stripe_service.create_checkout_session(
                user_id=1,
                plan="free",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel"
            )
    
    
    @pytest.mark.asyncio
    async def test_create_billing_portal_success(self, mock_stripe):
        """Test successful billing portal session creation"""
        result = await stripe_service.create_billing_portal_session(
            customer_id="cus_test_123",
            return_url="https://example.com/dashboard"
        )
        
        assert "portal_url" in result
        mock_stripe["portal"].assert_called_once()
    
    
    @pytest.mark.asyncio
    async def test_create_billing_portal_invalid_customer_id(self):
        """Test billing portal with invalid customer ID"""
        with pytest.raises(ValueError, match="Invalid customer ID"):
            await stripe_service.create_billing_portal_session(
                customer_id="invalid_id",
                return_url="https://example.com/dashboard"
            )
    
    
    @pytest.mark.asyncio
    async def test_verify_webhook_signature_success(self, mock_stripe):
        """Test successful webhook signature verification"""
        payload = b'{"type": "checkout.session.completed"}'
        signature = "test_signature"
        
        event = await stripe_service.verify_webhook_signature(payload, signature)
        
        assert event["type"] == "checkout.session.completed"
        mock_stripe["webhook"].assert_called_once()
    
    
    @pytest.mark.asyncio
    async def test_handle_checkout_completed(self, mock_db_pool):
        """Test handling checkout completed webhook"""
        event_data = {
            "object": {
                "client_reference_id": "1",
                "customer": "cus_test_123",
                "subscription": "sub_test_123",
                "metadata": {"plan": "pro"}
            }
        }
        
        await stripe_service.handle_checkout_completed(event_data, mock_db_pool)
        
        # Verify database update was called
        conn = await mock_db_pool.acquire()
        conn.execute.assert_called_once()
    
    
    @pytest.mark.asyncio
    async def test_check_plan_limits(self, mock_db_pool):
        """Test checking plan limits"""
        # Mock user with free plan
        conn = await mock_db_pool.acquire()
        conn.fetchrow.side_effect = [
            {"subscription_plan": "free", "subscription_status": "inactive"},
            {"count": 5}  # 5 listings this month
        ]
        
        result = await stripe_service.check_plan_limits(1, mock_db_pool)
        
        assert result["plan"] == "free"
        assert result["limit"] == 10
        assert result["current_usage"] == 5
        assert result["can_create"] is True
        assert result["remaining"] == 5
    
    
    @pytest.mark.asyncio
    async def test_check_plan_limits_exceeded(self, mock_db_pool):
        """Test plan limits when exceeded"""
        conn = await mock_db_pool.acquire()
        conn.fetchrow.side_effect = [
            {"subscription_plan": "free", "subscription_status": "inactive"},
            {"count": 15}  # 15 listings (over limit of 10)
        ]
        
        result = await stripe_service.check_plan_limits(1, mock_db_pool)
        
        assert result["can_create"] is False
        assert result["remaining"] == 0
    
    
    def test_plans_configuration(self):
        """Test that all plans are properly configured"""
        assert "free" in StripeService.PLANS
        assert "starter" in StripeService.PLANS
        assert "pro" in StripeService.PLANS
        assert "enterprise" in StripeService.PLANS
        
        # Verify free plan has no Stripe price ID
        assert "stripe_price_id" not in StripeService.PLANS["free"]
        
        # Verify paid plans have limits
        assert StripeService.PLANS["starter"]["listing_limit"] == 100
        assert StripeService.PLANS["pro"]["listing_limit"] == -1  # unlimited
        assert StripeService.PLANS["enterprise"]["listing_limit"] == -1
