"""
Integration tests for Lovable.dev frontend connection
Tests all critical endpoints for proper JSON responses and CORS headers
"""

import requests
import os

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")


def test_health():
    """Test health endpoint"""
    print("\n🧪 Testing /health endpoint...")
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "status" in data, "Missing 'status' field"
    assert data["status"] == "healthy", f"Expected 'healthy', got {data['status']}"
    print(f"✅ Health check passed: {data}")
    return data


def test_stats():
    """Test stats endpoint"""
    print("\n🧪 Testing /stats endpoint...")
    r = requests.get(f"{BASE_URL}/stats")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "total_items" in data, "Missing 'total_items' field"
    assert "total_value" in data, "Missing 'total_value' field"
    print(f"✅ Stats check passed: {data}")
    return data


def test_ingest():
    """Test photo ingestion endpoint"""
    print("\n🧪 Testing /ingest/photos endpoint...")
    r = requests.post(
        f"{BASE_URL}/ingest/photos",
        json={"urls": ["https://picsum.photos/seed/test/800/800"]}
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "title" in data, "Missing 'title' field"
    assert "price_suggestion" in data, "Missing 'price_suggestion' field"
    print(f"✅ Ingest check passed: {data['title']}")
    return data


def test_listings_all():
    """Test get all listings endpoint"""
    print("\n🧪 Testing /listings/all endpoint...")
    r = requests.get(f"{BASE_URL}/listings/all")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert isinstance(data, list), "Expected list response"
    print(f"✅ Listings check passed: {len(data)} items")
    return data


def test_export_csv():
    """Test CSV export endpoint"""
    print("\n🧪 Testing /export/csv endpoint...")
    r = requests.get(f"{BASE_URL}/export/csv")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert "text/csv" in r.headers.get("content-type", ""), "Expected CSV content type"
    print(f"✅ CSV export passed: {len(r.text)} bytes")
    return r.text


def test_cors_headers():
    """Test CORS headers are present"""
    print("\n🧪 Testing CORS headers...")
    r = requests.options(
        f"{BASE_URL}/health",
        headers={
            "Origin": "https://example.lovable.dev",
            "Access-Control-Request-Method": "GET"
        }
    )
    headers = r.headers
    assert "access-control-allow-origin" in headers or "Access-Control-Allow-Origin" in headers, \
        "Missing CORS allow-origin header"
    print(f"✅ CORS headers present")
    return headers


def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting Lovable Integration Tests...")
    print(f"📍 Base URL: {BASE_URL}")
    
    try:
        test_health()
        test_stats()
        test_ingest()
        test_listings_all()
        test_export_csv()
        test_cors_headers()
        
        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED - Ready for Lovable integration!")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    return True


if __name__ == "__main__":
    run_all_tests()
