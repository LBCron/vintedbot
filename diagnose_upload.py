"""
Diagnostic script to debug photo upload issues
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.core.storage import get_store
from backend.database import get_photo_plan
from backend.settings import settings

def main():
    print("=" * 60)
    print("DIAGNOSTIC: Photo Upload Issues")
    print("=" * 60)

    # 1. Check database for drafts
    print("\n1. Checking drafts in database...")
    store = get_store()
    drafts = store.get_drafts(limit=20)
    print(f"   Found {len(drafts)} drafts")
    for draft in drafts[:5]:
        print(f"   - ID: {draft['id'][:20]}..., Title: {draft['title'][:40]}, Status: {draft['status']}")

    # 2. Check for photo plans (upload jobs)
    print("\n2. Checking photo plans/jobs...")
    try:
        # Get all jobs from database
        conn = store.conn
        cursor = conn.cursor()
        cursor.execute("""
            SELECT job_id, status, progress_percent, detected_items, created_at, draft_ids
            FROM photo_plans
            ORDER BY created_at DESC
            LIMIT 10
        """)
        plans = cursor.fetchall()
        print(f"   Found {len(plans)} photo plans")
        for plan in plans:
            job_id, status, progress, items, created, draft_ids = plan
            print(f"   - Job: {job_id}, Status: {status}, Progress: {progress}%, Items: {items}, Drafts: {draft_ids}")
    except Exception as e:
        print(f"   Error reading photo plans: {e}")

    # 3. Check temp_photos directory
    print("\n3. Checking temp_photos directory...")
    temp_dir = Path(settings.DATA_DIR) / "temp_photos"
    if temp_dir.exists():
        job_dirs = list(temp_dir.iterdir())
        print(f"   Found {len(job_dirs)} job directories")
        for job_dir in job_dirs[:5]:
            if job_dir.is_dir():
                photos = list(job_dir.glob("*.jpg")) + list(job_dir.glob("*.png"))
                print(f"   - {job_dir.name}: {len(photos)} photos")
    else:
        print(f"   temp_photos directory not found: {temp_dir}")

    # 4. Check for specific problematic draft
    print("\n4. Checking for problematic draft 2647cfd5-45f8-404b-bf94-938baef701c9...")
    draft = store.get_draft("2647cfd5-45f8-404b-bf94-938baef701c9")
    if draft:
        print(f"   ✅ Draft found: {draft['title']}")
    else:
        print(f"   ❌ Draft NOT found in database")

    # 5. Check bulk_jobs in memory (only works if server is running)
    print("\n5. Note: bulk_jobs are in-memory and not persisted between server restarts")

    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
