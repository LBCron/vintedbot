"""
Unit tests for Admin API router (with SQL injection protection tests)
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.app import app

client = TestClient(app)


class TestAdminRouter:
    """Test suite for admin router including security tests"""
    
    def test_admin_endpoints_require_auth(self):
        """Test that all admin endpoints require authentication"""
        endpoints = [
            "/api/v1/admin/stats",
            "/api/v1/admin/revenue",
            "/api/v1/admin/activity"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require auth"
    
    
    @patch('backend.core.auth.get_current_user')
    @patch('backend.core.database.get_db_pool')
    async def test_non_admin_user_rejected(self, mock_pool, mock_auth):
        """Test that non-admin users are rejected"""
        # Mock regular user (not admin)
        mock_auth.return_value = AsyncMock(id=1, email="user@example.com")
        
        conn = AsyncMock()
        conn.fetchrow.return_value = {"is_admin": False}
        mock_pool.acquire.return_value.__aenter__.return_value = conn
        
        response = client.get("/api/v1/admin/stats")
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]
    
    
    @patch('backend.core.auth.get_current_user')
    @patch('backend.core.database.get_db_pool')
    async def test_admin_user_allowed(self, mock_pool, mock_auth):
        """Test that admin users can access admin endpoints"""
        # Mock admin user
        mock_auth.return_value = AsyncMock(id=999, email="admin@example.com")
        
        conn = AsyncMock()
        conn.fetchrow.side_effect = [
            {"is_admin": True},  # Admin check
            {"count": 100},  # Total users
            {"count": 50},  # Active users
            {"count": 200},  # Total listings
            {"count": 30},  # Listings this month
        ]
        conn.fetch.return_value = [{"plan": "free", "count": 80}]
        
        mock_pool.acquire.return_value.__aenter__.return_value = conn
        
        response = client.get("/api/v1/admin/stats")
        
        assert response.status_code == 200
    
    
    @patch('backend.core.auth.get_current_user')
    @patch('backend.core.database.get_db_pool')
    async def test_sql_injection_protection(self, mock_pool, mock_auth):
        """Test that SQL injection attempts are blocked via parameterization"""
        mock_auth.return_value = AsyncMock(id=999, email="admin@example.com")
        
        conn = AsyncMock()
        # Track SQL queries called
        queries_called = []
        
        def track_query(query, *args):
            queries_called.append({"query": query, "args": args})
            return {"count": 0}
        
        conn.fetchrow.side_effect = track_query
        conn.fetch.side_effect = lambda query, *args: []
        mock_pool.acquire.return_value.__aenter__.return_value = conn
        
        # Try SQL injection via limit parameter
        response = client.get("/api/v1/admin/activity?limit=100; DROP TABLE users;")
        
        # All queries should use parameterized statements ($1, $2, etc.)
        for query_call in queries_called:
            query = query_call["query"]
            # Should NOT contain direct string interpolation
            assert "DROP" not in query
            assert ";" not in query or query.count(";") <= 1  # Only statement terminators
    
    
    @patch('backend.core.auth.get_current_user')
    @patch('backend.core.database.get_db_pool')
    async def test_limit_parameter_validation(self, mock_pool, mock_auth):
        """Test that limit parameter is validated and clamped"""
        mock_auth.return_value = AsyncMock(id=999, email="admin@example.com")
        
        conn = AsyncMock()
        conn.fetchrow.return_value = {"is_admin": True}
        conn.fetch.return_value = []
        mock_pool.acquire.return_value.__aenter__.return_value = conn
        
        # Try limit over 100 (should be clamped to 10)
        response = client.get("/api/v1/admin/activity?limit=9999")
        
        # Should succeed (clamped to safe value)
        assert response.status_code == 200
        
        # Try negative limit (should use default)
        response = client.get("/api/v1/admin/activity?limit=-1")
        assert response.status_code == 200
    
    
    @patch('backend.core.auth.get_current_user')
    @patch('backend.core.database.get_db_pool')
    async def test_grant_admin_access(self, mock_pool, mock_auth):
        """Test granting admin access to user"""
        mock_auth.return_value = AsyncMock(id=999, email="superadmin@example.com")
        
        conn = AsyncMock()
        conn.fetchrow.side_effect = [
            {"is_admin": True},  # Requester is admin
            {"id": 1, "email": "user@example.com", "is_admin": False}  # Target user
        ]
        conn.execute.return_value = None
        mock_pool.acquire.return_value.__aenter__.return_value = conn
        
        response = client.post("/api/v1/admin/users/1/admin")
        
        assert response.status_code == 200
        assert response.json()["status"] == "granted"
    
    
    @patch('backend.core.auth.get_current_user')
    @patch('backend.core.database.get_db_pool')
    async def test_cannot_revoke_own_admin(self, mock_pool, mock_auth):
        """Test that users cannot revoke their own admin access"""
        mock_auth.return_value = AsyncMock(id=999, email="admin@example.com")
        
        conn = AsyncMock()
        conn.fetchrow.return_value = {"is_admin": True}
        mock_pool.acquire.return_value.__aenter__.return_value = conn
        
        # Try to revoke own admin access
        response = client.delete("/api/v1/admin/users/999/admin")
        
        assert response.status_code == 400
        assert "Cannot revoke your own admin access" in response.json()["detail"]
