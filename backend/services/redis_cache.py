"""
Redis caching layer for AI analysis results
Reduces OpenAI API costs by caching photo analysis results
Cache key strategy: hash(photo_content) -> analysis_result
"""
import os
import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import timedelta
import redis
from pathlib import Path

# Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Cache TTL (30 days for stable results)
CACHE_TTL = int(os.getenv("AI_CACHE_TTL_DAYS", "30")) * 86400  # seconds

# Initialize Redis client (with fallback if unavailable)
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )
    # Test connection
    redis_client.ping()
    REDIS_AVAILABLE = True
    print(f"[OK] Redis cache connected: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    redis_client = None
    REDIS_AVAILABLE = False
    print(f"[WARN] Redis cache unavailable (running without cache): {e}")


def _compute_photo_hash(photo_paths: List[str]) -> str:
    """
    Compute stable hash from photo file contents
    Uses SHA-256 hash of concatenated file contents

    Args:
        photo_paths: List of photo file paths

    Returns:
        Hex string hash (64 chars)
    """
    hasher = hashlib.sha256()

    # Sort paths for consistent ordering
    sorted_paths = sorted(photo_paths)

    for path in sorted_paths:
        try:
            with open(path, "rb") as f:
                # Read in chunks for memory efficiency
                while chunk := f.read(8192):
                    hasher.update(chunk)
        except Exception as e:
            # If file can't be read, use path as fallback
            hasher.update(path.encode('utf-8'))

    return hasher.hexdigest()


def get_cached_analysis(photo_paths: List[str]) -> Optional[Dict[str, Any]]:
    """
    Get cached AI analysis result for given photos

    Args:
        photo_paths: List of photo file paths

    Returns:
        Cached analysis dict or None if not found
    """
    if not REDIS_AVAILABLE or not redis_client:
        return None

    try:
        # Compute cache key
        photo_hash = _compute_photo_hash(photo_paths)
        cache_key = f"ai_analysis:{photo_hash}"

        # Try to get from cache
        cached_json = redis_client.get(cache_key)

        if cached_json:
            result = json.loads(cached_json)
            print(f"[CACHE HIT] Found cached analysis for {len(photo_paths)} photos")

            # Track cache hit metrics
            redis_client.hincrby("ai_metrics:cache", "hits", 1)

            return result
        else:
            print(f"[CACHE MISS] No cached analysis found")

            # Track cache miss metrics
            redis_client.hincrby("ai_metrics:cache", "misses", 1)

            return None

    except Exception as e:
        print(f"[WARN]  Cache read error: {e}")
        return None


def cache_analysis_result(photo_paths: List[str], result: Dict[str, Any]) -> bool:
    """
    Cache AI analysis result for given photos

    Args:
        photo_paths: List of photo file paths
        result: Analysis result dict to cache

    Returns:
        True if cached successfully, False otherwise
    """
    if not REDIS_AVAILABLE or not redis_client:
        return False

    try:
        # Compute cache key
        photo_hash = _compute_photo_hash(photo_paths)
        cache_key = f"ai_analysis:{photo_hash}"

        # Serialize result
        result_json = json.dumps(result, ensure_ascii=False, default=str)

        # Store in Redis with TTL
        redis_client.setex(cache_key, CACHE_TTL, result_json)

        print(f"[CACHE SAVE] Cached analysis for {len(photo_paths)} photos (TTL: {CACHE_TTL//86400}d)")

        # Track cache save metrics
        redis_client.hincrby("ai_metrics:cache", "saves", 1)

        return True

    except Exception as e:
        print(f"[WARN]  Cache write error: {e}")
        return False


def get_cache_stats() -> Dict[str, int]:
    """
    Get cache performance statistics

    Returns:
        Dict with hits, misses, saves, hit_rate
    """
    if not REDIS_AVAILABLE or not redis_client:
        return {"hits": 0, "misses": 0, "saves": 0, "hit_rate": 0.0}

    try:
        stats = redis_client.hgetall("ai_metrics:cache")

        hits = int(stats.get("hits", 0))
        misses = int(stats.get("misses", 0))
        saves = int(stats.get("saves", 0))

        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0.0

        return {
            "hits": hits,
            "misses": misses,
            "saves": saves,
            "hit_rate": round(hit_rate, 2)
        }

    except Exception as e:
        print(f"[WARN]  Cache stats error: {e}")
        return {"hits": 0, "misses": 0, "saves": 0, "hit_rate": 0.0}


def clear_cache(pattern: str = "ai_analysis:*") -> int:
    """
    Clear cached entries matching pattern

    Args:
        pattern: Redis key pattern (default: all AI analyses)

    Returns:
        Number of keys deleted
    """
    if not REDIS_AVAILABLE or not redis_client:
        return 0

    try:
        keys = redis_client.keys(pattern)
        if keys:
            deleted = redis_client.delete(*keys)
            print(f"[CACHE CLEAR] Deleted {deleted} cached entries")
            return deleted
        return 0

    except Exception as e:
        print(f"[WARN]  Cache clear error: {e}")
        return 0


def track_ai_quality_metrics(result: Dict[str, Any], validation_passed: bool):
    """
    Track AI quality metrics for monitoring

    Args:
        result: AI analysis result
        validation_passed: Whether quality validation passed
    """
    if not REDIS_AVAILABLE or not redis_client:
        return

    try:
        # Increment counters
        redis_client.hincrby("ai_metrics:quality", "total", 1)

        if validation_passed:
            redis_client.hincrby("ai_metrics:quality", "passed", 1)
        else:
            redis_client.hincrby("ai_metrics:quality", "failed", 1)

        # Track confidence scores
        confidence = result.get("confidence", 0.0)
        if confidence >= 0.9:
            redis_client.hincrby("ai_metrics:quality", "confidence_high", 1)
        elif confidence >= 0.7:
            redis_client.hincrby("ai_metrics:quality", "confidence_medium", 1)
        else:
            redis_client.hincrby("ai_metrics:quality", "confidence_low", 1)

        # Track fallback usage
        if result.get("fallback"):
            redis_client.hincrby("ai_metrics:quality", "fallback_used", 1)

    except Exception as e:
        print(f"[WARN]  Metrics tracking error: {e}")


def get_quality_metrics() -> Dict[str, Any]:
    """
    Get AI quality metrics

    Returns:
        Dict with total, passed, failed, pass_rate, confidence_distribution
    """
    if not REDIS_AVAILABLE or not redis_client:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "confidence_high": 0,
            "confidence_medium": 0,
            "confidence_low": 0,
            "fallback_used": 0
        }

    try:
        stats = redis_client.hgetall("ai_metrics:quality")

        total = int(stats.get("total", 0))
        passed = int(stats.get("passed", 0))
        failed = int(stats.get("failed", 0))
        confidence_high = int(stats.get("confidence_high", 0))
        confidence_medium = int(stats.get("confidence_medium", 0))
        confidence_low = int(stats.get("confidence_low", 0))
        fallback_used = int(stats.get("fallback_used", 0))

        pass_rate = (passed / total * 100) if total > 0 else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(pass_rate, 2),
            "confidence_high": confidence_high,
            "confidence_medium": confidence_medium,
            "confidence_low": confidence_low,
            "fallback_used": fallback_used
        }

    except Exception as e:
        print(f"[WARN]  Quality metrics error: {e}")
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0.0,
            "confidence_high": 0,
            "confidence_medium": 0,
            "confidence_low": 0,
            "fallback_used": 0
        }
