import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_health_ok():
    """Test health endpoint returns 200"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptime_seconds" in data


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_mock_messages_list():
    """Test GET /vinted/messages returns list in mock mode"""
    response = client.get("/vinted/messages")
    assert response.status_code == 200
    data = response.json()
    assert "threads" in data
    assert isinstance(data["threads"], list)


def test_mock_listings():
    """Test GET /listings returns list"""
    response = client.get("/listings")
    assert response.status_code == 200
    data = response.json()
    assert "listings" in data
    assert isinstance(data["listings"], list)


def test_create_session_mock():
    """Test session creation in mock mode"""
    response = client.post(
        "/vinted/auth/session",
        json={"cookie_value": "test_cookie_123", "note": "Test session"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "session_id" in data


def test_queue_publish_job():
    """Test queuing a publish job"""
    # First create a session
    session_response = client.post(
        "/vinted/auth/session",
        json={"cookie_value": "test_cookie_456"}
    )
    session_id = session_response.json()["session_id"]
    
    # Queue a job
    response = client.post(
        "/vinted/publish/queue",
        json={
            "item_id": 1,
            "session_id": session_id,
            "mode": "manual"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"


def test_get_notifications():
    """Test notifications endpoint"""
    response = client.get("/vinted/messages/notifications")
    assert response.status_code == 200
    data = response.json()
    assert "total_unread" in data
    assert "unread_threads_count" in data
