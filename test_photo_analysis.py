"""
Test photo analysis to identify the issue
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.settings import settings

print("=" * 60)
print("TEST: Photo Analysis")
print("=" * 60)

# Check if there are any photos to test with
temp_dir = Path(settings.DATA_DIR) / "temp_photos"
print(f"\n1. Checking for test photos in: {temp_dir}")

if not temp_dir.exists():
    print("   ERROR: temp_photos directory doesn't exist!")
    sys.exit(1)

# Find any photos
all_photos = list(temp_dir.rglob("*.jpg")) + list(temp_dir.rglob("*.png"))
print(f"   Found {len(all_photos)} photos total")

if len(all_photos) == 0:
    print("   No photos to test with. Upload some photos first!")
    sys.exit(0)

# Take first photo for testing
test_photo = str(all_photos[0])
print(f"   Using test photo: {test_photo}")

# Try to analyze it
print("\n2. Testing AI analysis...")
try:
    from backend.core.ai_analyzer import analyze_clothing_photos

    print("   Analyzing...")
    result = analyze_clothing_photos([test_photo])

    print("\n   SUCCESS! Analysis result:")
    print(f"   - Title: {result.get('title', 'N/A')}")
    print(f"   - Price: {result.get('price', 'N/A')} EUR")
    print(f"   - Brand: {result.get('brand', 'N/A')}")
    print(f"   - Category: {result.get('category', 'N/A')}")
    print(f"   - Confidence: {result.get('confidence', 'N/A')}")

except Exception as e:
    print(f"\n   FAILED! Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
