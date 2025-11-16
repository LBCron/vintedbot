"""
Unit tests for Webhook service (with SSRF protection tests)
"""
import pytest
from unittest.mock import patch, AsyncMock
from backend.services.webhook_service import WebhookService, webhook_service


class TestWebhookService:
    """Test suite for webhook service including SSRF protection"""
    
    @pytest.mark.asyncio
    async def test_validate_webhook_url_valid_https(self):
        """Test valid HTTPS URL passes validation"""
        url = "https://example.com/webhook"
        
        is_valid = await webhook_service.validate_webhook_url(url)
        
        assert is_valid is True
    
    
    @pytest.mark.asyncio
    async def test_validate_webhook_url_blocks_localhost(self):
        """Test that localhost is blocked (SSRF protection)"""
        urls = [
            "http://localhost:8000/webhook",
            "http://127.0.0.1/webhook",
            "http://0.0.0.0/webhook",
        ]
        
        for url in urls:
            is_valid = await webhook_service.validate_webhook_url(url)
            assert is_valid is False, f"Should block {url}"
    
    
    @pytest.mark.asyncio
    async def test_validate_webhook_url_blocks_aws_metadata(self):
        """Test that AWS metadata endpoint is blocked"""
        url = "http://169.254.169.254/latest/meta-data/"
        
        is_valid = await webhook_service.validate_webhook_url(url)
        
        assert is_valid is False
    
    
    @pytest.mark.asyncio
    async def test_validate_webhook_url_blocks_private_ips(self):
        """Test that private IP ranges are blocked"""
        urls = [
            "http://10.0.0.1/webhook",
            "http://172.16.0.1/webhook",
            "http://192.168.1.1/webhook",
        ]
        
        for url in urls:
            with patch('socket.gethostbyname', return_value=url.split('/')[2].split(':')[0]):
                is_valid = await webhook_service.validate_webhook_url(url)
                assert is_valid is False, f"Should block private IP: {url}"
    
    
    @pytest.mark.asyncio
    async def test_validate_webhook_url_invalid_scheme(self):
        """Test that non-HTTP(S) schemes are rejected"""
        urls = [
            "ftp://example.com/webhook",
            "file:///etc/passwd",
            "data:text/plain,test",
        ]
        
        for url in urls:
            is_valid = await webhook_service.validate_webhook_url(url)
            assert is_valid is False, f"Should reject scheme: {url}"
    
    
    def test_generate_signature(self):
        """Test HMAC signature generation"""
        payload = '{"event": "test"}'
        secret = "test_secret"
        
        signature = webhook_service.generate_signature(payload, secret)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest length
        
        # Same input should produce same signature
        signature2 = webhook_service.generate_signature(payload, secret)
        assert signature == signature2
    
    
    @pytest.mark.asyncio
    async def test_send_webhook_success(self, mock_httpx_client):
        """Test successful webhook delivery"""
        url = "https://example.com/webhook"
        event_type = "listing.created"
        data = {"listing_id": 123}
        secret = "test_secret"
        
        result = await webhook_service.send_webhook(url, event_type, data, secret)
        
        assert result is True
        mock_httpx_client.assert_called_once()
    
    
    @pytest.mark.asyncio
    async def test_send_webhook_blocks_ssrf(self):
        """Test that SSRF attempts are blocked"""
        url = "http://localhost:8000/webhook"
        event_type = "test.event"
        data = {}
        
        result = await webhook_service.send_webhook(url, event_type, data)
        
        # Should be blocked before making any HTTP request
        assert result is False
    
    
    @pytest.mark.asyncio
    async def test_send_webhook_payload_too_large(self):
        """Test that large payloads are rejected"""
        url = "https://example.com/webhook"
        event_type = "test.event"
        # Create 2MB payload (over 1MB limit)
        data = {"large_data": "x" * (2 * 1024 * 1024)}
        
        result = await webhook_service.send_webhook(url, event_type, data)
        
        assert result is False
    
    
    @pytest.mark.asyncio
    async def test_send_webhook_with_retry(self, mock_httpx_client):
        """Test webhook retry logic on failure"""
        url = "https://example.com/webhook"
        event_type = "test.event"
        data = {}
        
        # Mock first 2 calls to fail, 3rd to succeed
        mock_response_fail = AsyncMock()
        mock_response_fail.status_code = 500
        
        mock_response_success = AsyncMock()
        mock_response_success.status_code = 200
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(side_effect=[
                mock_response_fail,
                mock_response_fail,
                mock_response_success
            ])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock()
            mock_client.return_value = mock_instance
            
            result = await webhook_service.send_webhook(url, event_type, data, retry_count=3)
            
            assert result is True
            assert mock_instance.post.call_count == 3
    
    
    @pytest.mark.asyncio
    async def test_trigger_event(self, mock_db_pool, mock_httpx_client):
        """Test triggering webhook event"""
        # Mock registered webhooks
        conn = await mock_db_pool.acquire()
        conn.fetch.return_value = [
            {
                "id": 1,
                "url": "https://example.com/webhook1",
                "secret": "secret1",
                "events": ["listing.created"]
            },
            {
                "id": 2,
                "url": "https://example.com/webhook2",
                "secret": "secret2",
                "events": ["listing.created", "listing.updated"]
            }
        ]
        
        result = await webhook_service.trigger_event(
            event_type="listing.created",
            data={"listing_id": 123},
            user_id=1,
            db_pool=mock_db_pool
        )
        
        assert result["event"] == "listing.created"
        assert result["delivered"] == 2
        assert result["failed"] == 0
        assert result["total"] == 2
    
    
    @pytest.mark.asyncio
    async def test_test_webhook(self, mock_httpx_client):
        """Test webhook testing functionality"""
        url = "https://example.com/webhook"
        secret = "test_secret"
        
        result = await webhook_service.test_webhook(url, secret)
        
        assert result["success"] is True
        assert "response_time_seconds" in result
        assert "tested_at" in result
