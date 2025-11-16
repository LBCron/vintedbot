"""
Pytest configuration and shared fixtures
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/vintedbot_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_mock"
os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test_mock"
os.environ["JWT_SECRET"] = "test_secret_key_for_testing_only"
os.environ["OPENAI_API_KEY"] = "sk-test-mock"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db_pool():
    """Mock database connection pool"""
    pool = AsyncMock()
    
    # Mock connection
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetch = AsyncMock(return_value=[])
    conn.execute = AsyncMock()
    
    pool.acquire = AsyncMock(return_value=conn)
    pool.__aenter__ = AsyncMock(return_value=conn)
    pool.__aexit__ = AsyncMock()
    
    return pool


@pytest.fixture
def mock_user():
    """Mock user object"""
    from backend.models.user import User
    
    return User(
        id=1,
        email="test@example.com",
        hashed_password="hashed_test_password",
        is_admin=False,
        subscription_plan="free",
        subscription_status="inactive"
    )


@pytest.fixture
def mock_admin_user():
    """Mock admin user object"""
    from backend.models.user import User
    
    return User(
        id=999,
        email="admin@example.com",
        hashed_password="hashed_admin_password",
        is_admin=True,
        subscription_plan="enterprise",
        subscription_status="active"
    )


@pytest.fixture
def mock_stripe():
    """Mock Stripe API"""
    with patch('stripe.checkout.Session.create') as mock_checkout, \
         patch('stripe.billing_portal.Session.create') as mock_portal, \
         patch('stripe.Webhook.construct_event') as mock_webhook:
        
        mock_checkout.return_value = MagicMock(
            id="cs_test_123",
            url="https://checkout.stripe.com/test"
        )
        
        mock_portal.return_value = MagicMock(
            url="https://billing.stripe.com/test"
        )
        
        mock_webhook.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_123"}}
        }
        
        yield {
            "checkout": mock_checkout,
            "portal": mock_portal,
            "webhook": mock_webhook
        }


@pytest.fixture
async def mock_httpx_client():
    """Mock httpx async client for webhooks"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = '{"success": true}'
        
        mock_instance = AsyncMock()
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock()
        
        mock_client.return_value = mock_instance
        
        yield mock_client


@pytest.fixture
def sample_webhook_payload():
    """Sample webhook payload for testing"""
    return {
        "event": "listing.created",
        "data": {
            "listing_id": 123,
            "title": "Test Listing",
            "price": 29.99
        },
        "timestamp": "2025-11-16T12:00:00Z",
        "version": "1.0"
    }
