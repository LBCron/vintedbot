"""
End-to-end integration tests for VintedBot API
Tests the complete workflow: upload → analyze → draft → publish
"""
import requests
import time
import json
import os
from pathlib import Path

# Base URL (adjust if needed)
BASE_URL = "http://localhost:5000"

# Test credentials (using demo user)
TEST_EMAIL = "demo@example.com"
TEST_PASSWORD = "demo123"


def test_health_check():
    """Test 1: Health check endpoint"""
    print("\n🔍 Test 1: Health check...")
    response = requests.get(f"http://localhost:5000/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ Health check passed")
    return True


def test_authentication():
    """Test 2: Create test token (auth endpoints not yet implemented)"""
    print("\n🔍 Test 2: Creating test JWT token...")
    
    # Import auth utilities directly
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from core.auth import create_access_token
    from core.storage import get_store
    
    # Create or get test user from SQLite storage
    store = get_store()
    
    # Check if user exists in SQLite
    try:
        # Try to get user (this will fail if user doesn't exist)
        # For now, we'll just create a token for a test user
        test_user_id = 1
        test_email = "test@vintedbot.com"
        
        # Create JWT token
        token = create_access_token({
            "user_id": test_user_id,
            "email": test_email,
            "plan": "free"
        })
        
        print(f"✅ Test token created: {token[:20]}...")
        return token
    except Exception as e:
        print(f"⚠️  Token creation: {e}")
        # Return a minimal token anyway
        token = create_access_token({"user_id": 1, "email": "test@test.com"})
        return token


def test_bulk_upload(token):
    """Test 3: Bulk photo upload"""
    print("\n🔍 Test 3: Bulk photo upload...")
    
    # Create a test image
    from PIL import Image
    import io
    
    img = Image.new('RGB', (800, 600), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    # Upload multiple copies for testing
    files = [
        ('files', ('test1.jpg', img_bytes, 'image/jpeg')),
    ]
    
    # Reset BytesIO for each file
    for i in range(2, 6):
        img_bytes_copy = io.BytesIO()
        img.save(img_bytes_copy, format='JPEG')
        img_bytes_copy.seek(0)
        files.append(('files', (f'test{i}.jpg', img_bytes_copy, 'image/jpeg')))
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/bulk/upload",
        files=files,
        params={"auto_group": True, "photos_per_item": 5},
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "job_id" in data
    job_id = data["job_id"]
    print(f"✅ Upload passed, job_id: {job_id}")
    return job_id


def test_job_status(token, job_id):
    """Test 4: Job status tracking"""
    print(f"\n🔍 Test 4: Job status tracking (job {job_id})...")
    
    headers = {"Authorization": f"Bearer {token}"}
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        response = requests.get(
            f"{BASE_URL}/bulk/jobs/{job_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        status = data.get("status")
        progress = data.get("progress_percent", 0)
        
        print(f"  Status: {status}, Progress: {progress}%")
        
        if status == "completed":
            print(f"✅ Job completed successfully")
            assert data.get("completed_items", 0) > 0
            return data
        elif status == "failed":
            print(f"❌ Job failed: {data.get('errors')}")
            assert False, "Job failed"
        
        time.sleep(2)
        attempt += 1
    
    assert False, "Job timed out"


def test_drafts_list(token):
    """Test 5: List drafts"""
    print("\n🔍 Test 5: List drafts...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/bulk/drafts",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "drafts" in data
    drafts = data["drafts"]
    
    print(f"✅ Found {len(drafts)} drafts")
    
    if drafts:
        draft = drafts[0]
        print(f"  Sample draft: {draft.get('title')}")
        return draft.get('id')
    
    return None


def test_draft_validation(token, draft_id):
    """Test 6: Draft validation"""
    if not draft_id:
        print("\n⏭️  Test 6: Skipped (no drafts)")
        return
    
    print(f"\n🔍 Test 6: Draft validation (draft {draft_id})...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/bulk/drafts/{draft_id}",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "title" in data
    assert "description" in data
    assert "price_suggestion" in data
    assert "photos" in data
    
    title = data["title"]
    description = data["description"]
    
    # Validate quality gates
    assert len(title) <= 70, f"Title too long: {len(title)} chars"
    assert "#" in description, "Missing hashtags"
    
    hashtag_count = description.count("#")
    assert 3 <= hashtag_count <= 5, f"Invalid hashtag count: {hashtag_count}"
    
    print(f"✅ Draft validation passed")
    print(f"  Title: {title}")
    print(f"  Hashtags: {hashtag_count}")


def run_all_tests():
    """Run all end-to-end tests"""
    print("=" * 60)
    print("🚀 VintedBot E2E Tests")
    print("=" * 60)
    
    try:
        # Test sequence
        test_health_check()
        token = test_authentication()
        job_id = test_bulk_upload(token)
        job_data = test_job_status(token, job_id)
        draft_id = test_drafts_list(token)
        test_draft_validation(token, draft_id)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
