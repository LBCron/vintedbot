"""
Multi-Tier Storage API
Handles photo storage across TEMP/HOT/COLD tiers with automatic lifecycle management
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import Optional, Dict, Any
from backend.core.auth import get_current_user, User
from pydantic import BaseModel, Field
from datetime import datetime
import traceback
from loguru import logger

from backend.storage.storage_manager import StorageManager, PhotoMetadata
from backend.storage.metrics import StorageMetrics
from backend.storage.lifecycle_manager import StorageLifecycleManager

router = APIRouter(prefix="/storage", tags=["storage"])

# Initialize storage manager
storage_manager = StorageManager()
storage_metrics = StorageMetrics()
lifecycle_manager = StorageLifecycleManager(storage_manager)


# Pydantic models
class PhotoUploadResponse(BaseModel):
    """Response after photo upload"""
    photo_id: str
    tier: str
    file_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float
    scheduled_deletion: Optional[datetime]
    cdn_url: Optional[str]


class PublishDraftRequest(BaseModel):
    """Request to mark draft as published to Vinted"""
    draft_id: str
    photo_ids: list[str] = Field(..., description="List of photo IDs in this draft")


class StorageStatsResponse(BaseModel):
    """Storage statistics response"""
    temp_count: int
    temp_size_gb: float
    hot_count: int
    hot_size_gb: float
    cold_count: int
    cold_size_gb: float
    total_count: int
    total_size_gb: float
    monthly_cost_estimate: float
    savings_vs_all_hot: float


@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_photo(
    file: UploadFile = File(..., description="Photo file to upload"),
    draft_id: Optional[str] = Form(None, description="Optional draft ID to associate photo with"),
    current_user: User = Depends(get_current_user)
):
    """
    Upload photo to TIER 1 (TEMP) storage

    Photos are automatically:
    - Compressed (50-70% size reduction)
    - Stored in Fly.io Volumes (free)
    - Scheduled for promotion/deletion based on lifecycle rules

    Lifecycle:
    1. Upload → TIER 1 (TEMP) - 48h
    2. If published → delete after 7 days
    3. If not published → promote to TIER 2 (HOT) after 48h
    4. After 90 days → archive to TIER 3 (COLD)
    5. After 365 days → delete permanently
    """
    try:
        # Read file data
        file_data = await file.read()
        original_size = len(file_data)

        logger.info(f"📸 Uploading photo: {file.filename} ({original_size} bytes) for user {current_user.user_id}")

        # Upload to storage manager (auto-compresses and saves to TIER 1)
        metadata = await storage_manager.upload_photo(
            user_id=current_user.user_id,
            file_data=file_data,
            filename=file.filename,
            draft_id=draft_id
        )

        # Get CDN URL if available
        cdn_url = None
        try:
            cdn_url = await storage_manager.get_photo_url(metadata.photo_id)
        except Exception as e:
            logger.warning(f"Could not get CDN URL: {e}")

        compression_ratio = (1 - (metadata.compressed_size_bytes / original_size)) * 100 if original_size > 0 else 0

        logger.success(f"✅ Photo uploaded: {metadata.photo_id} (tier: {metadata.tier.value}, compressed: {compression_ratio:.1f}%)")

        return PhotoUploadResponse(
            photo_id=metadata.photo_id,
            tier=metadata.tier.value,
            file_size_bytes=original_size,
            compressed_size_bytes=metadata.compressed_size_bytes,
            compression_ratio=round(compression_ratio, 2),
            scheduled_deletion=metadata.scheduled_deletion,
            cdn_url=cdn_url
        )

    except Exception as e:
        logger.error(f"❌ Photo upload failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Photo upload failed: {str(e)}")


@router.post("/drafts/{draft_id}/publish")
async def publish_draft(
    draft_id: str,
    request: PublishDraftRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Mark draft as published to Vinted

    This triggers the lifecycle rule:
    - Photos will be kept for 7 days
    - Then automatically deleted (they're already on Vinted)

    This saves ~80% of storage costs since most photos are published.
    """
    try:
        logger.info(f"📝 Marking draft {draft_id} as published ({len(request.photo_ids)} photos)")

        results = {
            "draft_id": draft_id,
            "photo_ids": request.photo_ids,
            "updated_count": 0,
            "failed": []
        }

        for photo_id in request.photo_ids:
            try:
                await storage_manager.mark_published_to_vinted(photo_id)
                results["updated_count"] += 1
                logger.debug(f"✅ Marked photo {photo_id} as published")
            except Exception as e:
                logger.error(f"❌ Failed to mark photo {photo_id} as published: {e}")
                results["failed"].append({
                    "photo_id": photo_id,
                    "error": str(e)
                })

        logger.success(f"✅ Draft published: {results['updated_count']}/{len(request.photo_ids)} photos updated")

        return {
            "ok": True,
            "message": f"Draft {draft_id} marked as published. Photos will be deleted in 7 days.",
            "results": results
        }

    except Exception as e:
        logger.error(f"❌ Failed to publish draft: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to publish draft: {str(e)}")


@router.get("/stats", response_model=StorageStatsResponse)
async def get_storage_stats(current_user: User = Depends(get_current_user)):
    """
    Get storage statistics and costs

    Returns:
    - Photo count and size per tier
    - Monthly cost estimate
    - Savings vs storing everything in HOT tier
    """
    try:
        stats = await storage_metrics.get_storage_stats()

        logger.info(f"📊 Storage stats: {stats['total_count']} photos, {stats['total_size_gb']} GB, ${stats['monthly_cost_estimate']}/mo")

        return StorageStatsResponse(**stats)

    except Exception as e:
        logger.error(f"❌ Failed to get storage stats: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get storage stats: {str(e)}")


@router.get("/stats/breakdown")
async def get_cost_breakdown(current_user: User = Depends(get_current_user)):
    """
    Get detailed cost breakdown per tier

    Returns cost and percentage for each storage tier
    """
    try:
        breakdown = await storage_metrics.get_cost_breakdown()

        logger.info(f"💰 Cost breakdown: ${breakdown['total']}/mo (HOT: {breakdown['hot']['percentage']}%, COLD: {breakdown['cold']['percentage']}%)")

        return {
            "ok": True,
            "breakdown": breakdown
        }

    except Exception as e:
        logger.error(f"❌ Failed to get cost breakdown: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get cost breakdown: {str(e)}")


@router.get("/metrics/lifecycle")
async def get_lifecycle_metrics(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get lifecycle metrics for the last N days

    Shows how photos move through the tiers:
    - Photos uploaded
    - Photos promoted (TEMP → HOT)
    - Photos archived (HOT → COLD)
    - Photos deleted
    """
    try:
        metrics = await storage_metrics.get_lifecycle_metrics(days=days)

        logger.info(f"📈 Lifecycle metrics (last {days} days): {metrics['photos_uploaded']} uploaded, {metrics['photos_promoted']} promoted, {metrics['photos_archived']} archived")

        return {
            "ok": True,
            "period_days": days,
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"❌ Failed to get lifecycle metrics: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get lifecycle metrics: {str(e)}")


@router.get("/metrics/recommendations")
async def get_optimization_recommendations(current_user: User = Depends(get_current_user)):
    """
    Get storage optimization recommendations

    Analyzes current usage and suggests optimizations:
    - Too many photos in TEMP? Check lifecycle job
    - High HOT storage costs? Reduce archival threshold
    - Few COLD archives? Lifecycle could be more aggressive
    """
    try:
        recommendations = await storage_metrics.get_optimization_recommendations()

        logger.info(f"💡 Generated {len(recommendations)} optimization recommendations")

        return {
            "ok": True,
            "recommendations": recommendations,
            "count": len(recommendations)
        }

    except Exception as e:
        logger.error(f"❌ Failed to get recommendations: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/photo/{photo_id}/url")
async def get_photo_url(
    photo_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get CDN URL for a photo

    Returns the appropriate URL based on current tier:
    - TEMP: Local file path
    - HOT: Cloudflare R2 CDN URL
    - COLD: Backblaze B2 download URL
    """
    try:
        url = await storage_manager.get_photo_url(photo_id)

        logger.debug(f"🔗 Photo URL: {photo_id} → {url}")

        return {
            "ok": True,
            "photo_id": photo_id,
            "url": url
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found")
    except Exception as e:
        logger.error(f"❌ Failed to get photo URL: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get photo URL: {str(e)}")


@router.get("/photo/{photo_id}/metadata")
async def get_photo_metadata(
    photo_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get metadata for a photo

    Returns:
    - Current tier
    - Upload date
    - Last access date
    - Scheduled deletion date
    - File sizes
    - User ID
    """
    try:
        metadata = await storage_manager.get_photo_metadata(photo_id)

        if not metadata:
            raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found")

        return {
            "ok": True,
            "metadata": {
                "photo_id": metadata.photo_id,
                "user_id": metadata.user_id,
                "tier": metadata.tier.value,
                "upload_date": metadata.upload_date.isoformat() if metadata.upload_date else None,
                "last_access_date": metadata.last_access_date.isoformat() if metadata.last_access_date else None,
                "scheduled_deletion": metadata.scheduled_deletion.isoformat() if metadata.scheduled_deletion else None,
                "file_size_bytes": metadata.file_size_bytes,
                "compressed_size_bytes": metadata.compressed_size_bytes,
                "draft_id": metadata.draft_id,
                "published_to_vinted": metadata.published_to_vinted
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get photo metadata: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get photo metadata: {str(e)}")


@router.delete("/photo/{photo_id}")
async def delete_photo(
    photo_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete photo from storage

    Removes photo from current tier and deletes metadata.
    This action is permanent and cannot be undone.
    """
    try:
        logger.info(f"🗑️ Deleting photo: {photo_id}")

        await storage_manager.delete_photo(photo_id)

        logger.success(f"✅ Photo deleted: {photo_id}")

        return {
            "ok": True,
            "message": f"Photo {photo_id} deleted successfully",
            "photo_id": photo_id
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Photo {photo_id} not found")
    except Exception as e:
        logger.error(f"❌ Failed to delete photo: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete photo: {str(e)}")


@router.get("/user/usage")
async def get_user_storage_usage(current_user: User = Depends(get_current_user)):
    """
    Get storage usage for current user

    Returns:
    - Total photos
    - Total size
    - Breakdown by tier
    """
    try:
        usage = await storage_metrics.get_user_storage_usage(current_user.user_id)

        logger.info(f"👤 User {current_user.user_id} storage: {usage['total_photos']} photos, {usage['total_size_gb']} GB")

        return {
            "ok": True,
            "user_id": current_user.user_id,
            "usage": usage
        }

    except Exception as e:
        logger.error(f"❌ Failed to get user storage usage: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get user storage usage: {str(e)}")


@router.post("/lifecycle/run-now")
async def run_lifecycle_now(current_user: User = Depends(get_current_user)):
    """
    Manually trigger lifecycle job (admin only)

    Runs all lifecycle rules:
    1. Delete expired TEMP photos (>48h)
    2. Delete published photos (>7 days)
    3. Promote TEMP → HOT (>48h, not published)
    4. Archive HOT → COLD (>90 days)
    5. Delete COLD → permanent (>365 days)

    Normally runs automatically at 3 AM daily.
    """
    try:
        # TODO: Add admin check
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Admin access required")

        logger.info(f"🔄 Running lifecycle job manually (triggered by {current_user.user_id})")

        stats = await lifecycle_manager.run_daily_lifecycle()

        logger.success(f"✅ Lifecycle job completed: {stats}")

        return {
            "ok": True,
            "message": "Lifecycle job completed successfully",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"❌ Lifecycle job failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Lifecycle job failed: {str(e)}")


@router.get("/tiers/info")
async def get_tier_info(current_user: User = Depends(get_current_user)):
    """
    Get information about storage tiers

    Returns pricing, rules, and characteristics of each tier
    """
    tiers = {
        "temp": {
            "name": "TIER 1 - TEMP",
            "storage": "Fly.io Volumes",
            "cost_per_gb": 0.00,
            "duration": "24-48 hours",
            "description": "Temporary storage for photos awaiting AI analysis",
            "rules": [
                "Photos uploaded here first",
                "Auto-promoted to HOT after 48h (if not published)",
                "Auto-deleted after 48h if no draft created",
                "Free storage (Fly.io Volumes)"
            ]
        },
        "hot": {
            "name": "TIER 2 - HOT",
            "storage": "Cloudflare R2",
            "cost_per_gb": 0.015,
            "duration": "Up to 90 days",
            "description": "Active storage for drafts and recent photos",
            "rules": [
                "Photos promoted from TEMP if not published",
                "Free egress (unlimited CDN bandwidth)",
                "Auto-archived to COLD after 90 days without access",
                "Fast access via CDN"
            ]
        },
        "cold": {
            "name": "TIER 3 - COLD",
            "storage": "Backblaze B2",
            "cost_per_gb": 0.006,
            "duration": "Up to 365 days",
            "description": "Archive storage for old, rarely-accessed photos",
            "rules": [
                "Photos archived from HOT after 90 days",
                "60% cheaper than HOT storage",
                "Auto-deleted after 365 days total",
                "Slower access (retrieval needed)"
            ]
        }
    }

    return {
        "ok": True,
        "tiers": tiers,
        "lifecycle_summary": {
            "upload": "Photo → TEMP (48h)",
            "published": "Published → delete after 7 days (saves 80% cost)",
            "draft": "Draft → TEMP (48h) → HOT (90 days) → COLD (365 days) → delete",
            "total_lifecycle": "Max 365 days retention"
        }
    }
