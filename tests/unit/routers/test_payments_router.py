"""
Unit tests for Payments API router
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.app import app

client = TestClient(app)


class TestPaymentsRouter:
    """Test suite for payments router"""
    
    def test_get_plans_public(self):
        """Test that plans endpoint is public (no auth required)"""
        response = client.get("/api/v1/payments/plans")
        
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert "free" in data["plans"]
        assert "starter" in data["plans"]
        assert "pro" in data["plans"]
        assert "enterprise" in data["plans"]
    
    
    @patch('backend.services.stripe_service.stripe_service.create_checkout_session')
    def test_create_checkout_requires_auth(self, mock_checkout):
        """Test that checkout requires authentication"""
        response = client.post("/api/v1/payments/checkout", json={
            "plan": "pro"
        })
        
        # Should get 401 Unauthorized without token
        assert response.status_code in [401, 403]
    
    
    @pytest.mark.asyncio
    async def test_create_checkout_invalid_plan(self):
        """Test checkout with invalid plan"""
        with patch('backend.core.auth.get_current_user') as mock_auth:
            mock_auth.return_value = AsyncMock(id=1, email="test@example.com")
            
            response = client.post("/api/v1/payments/checkout", json={
                "plan": "invalid_plan"
            })
            
            assert response.status_code == 400
            assert "Invalid plan" in response.json()["detail"]
    
    
    def test_webhook_requires_signature(self):
        """Test that webhook endpoint requires Stripe signature"""
        response = client.post("/api/v1/payments/webhook", 
                              data=b'{"type": "test"}')
        
        assert response.status_code == 400
        assert "stripe-signature" in response.json()["detail"].lower()
    
    
    @patch('backend.services.stripe_service.stripe_service.verify_webhook_signature')
    @patch('backend.services.stripe_service.stripe_service.handle_checkout_completed')
    async def test_webhook_checkout_completed(self, mock_handle, mock_verify):
        """Test webhook handling for checkout completed"""
        mock_verify.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_123"}}
        }
        
        response = client.post("/api/v1/payments/webhook",
                              data=b'{"type": "checkout.session.completed"}',
                              headers={"stripe-signature": "test_sig"})
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"
