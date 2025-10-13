import io
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport
from backend.app import app


def make_image_bytes(w=800, h=600, color=(200, 200, 200)):
    """Create a simple test JPEG image in memory"""
    img = Image.new("RGB", (w, h), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    buf.seek(0)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_ingest_upload_single_image():
    """Test uploading a single image"""
    data = make_image_bytes()
    files = {"files": ("test.jpg", data, "image/jpeg")}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/ingest/upload", files=files)
    
    assert r.status_code == 201, f"Expected 201, got {r.status_code}: {r.text}"
    js = r.json()
    assert js["status"] == "draft"
    assert len(js["photos"]) == 1
    assert js["photos"][0]["media"]["url"].startswith("/media/")
    assert js["title"] == ""


@pytest.mark.asyncio
async def test_ingest_upload_multiple_images():
    """Test uploading multiple images"""
    files = [
        ("files", ("test1.jpg", make_image_bytes(800, 600, (255, 0, 0)), "image/jpeg")),
        ("files", ("test2.jpg", make_image_bytes(600, 800, (0, 255, 0)), "image/jpeg")),
        ("files", ("test3.jpg", make_image_bytes(1200, 1200, (0, 0, 255)), "image/jpeg")),
    ]
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/ingest/upload", files=files)
    
    assert r.status_code == 201
    js = r.json()
    assert js["status"] == "draft"
    assert len(js["photos"]) == 3


@pytest.mark.asyncio
async def test_ingest_upload_with_title():
    """Test uploading with a custom title"""
    data = make_image_bytes()
    files = {"files": ("test.jpg", data, "image/jpeg")}
    form_data = {"title": "My Test Item"}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/ingest/upload", files=files, data=form_data)
    
    assert r.status_code == 201
    js = r.json()
    assert js["title"] == "My Test Item"


@pytest.mark.asyncio
async def test_ingest_upload_large_image_resize():
    """Test that large images are resized to MAX_DIM_PX"""
    data = make_image_bytes(w=3000, h=2000)
    files = {"files": ("large.jpg", data, "image/jpeg")}
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/ingest/upload", files=files)
    
    assert r.status_code == 201
    js = r.json()
    media = js["photos"][0]["media"]
    assert max(media["width"], media["height"]) <= 1600


@pytest.mark.asyncio
async def test_ingest_upload_no_files():
    """Test error when no files provided"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/api/v1/ingest/upload", files={})
    
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test API v1 health endpoint"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/api/v1/health")
    
    assert r.status_code == 200
    js = r.json()
    assert js["status"] == "ok"
    assert js["api_version"] == "v1"
    assert js["media_storage"] == "local"
