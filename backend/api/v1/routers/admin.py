"""
Admin endpoints for system management
Requires super-admin authentication (ronanchenlopes@gmail.com)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from typing import Optional, List, Dict, Any
import os
from backend.core.backup import (
    create_backup,
    restore_backup,
    list_backups,
    get_backup_info,
    export_to_json,
    export_to_sql
)
from backend.core.monitoring import get_system_health, get_system_metrics
from backend.core.job_wrapper import get_job_stats, reset_job_stats
from backend.core.circuit_breaker import get_all_circuit_states
from backend.core.admin import is_super_admin, AdminLogger
from backend.api.v1.routers.auth import get_current_user
from backend.core.storage import get_store
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])


class BackupRequest(BaseModel):
    compress: bool = True


class RestoreRequest(BaseModel):
    backup_path: str


class ExportRequest(BaseModel):
    output_path: str
    tables: Optional[List[str]] = None
    format: str = "json"  # "json" or "sql"


# Super-admin authentication dependency
def require_super_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that ensures the current user is a super admin

    Usage:
        @router.get("/admin/endpoint")
        async def admin_endpoint(admin: dict = Depends(require_super_admin)):
            ...
    """
    if not is_super_admin(current_user["email"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user


@router.post("/bootstrap/set-admin")
async def bootstrap_set_admin(
    email: str = Query(...),
    is_admin: bool = Query(True),
    x_bootstrap_key: Optional[str] = Header(None)
):
    """
    Bootstrap endpoint to set admin status without authentication
    Requires bootstrap key from environment variable
    """
    bootstrap_key = os.getenv("BOOTSTRAP_KEY", "")
    if not bootstrap_key or x_bootstrap_key != bootstrap_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bootstrap key"
        )

    from backend.core.storage import get_storage
    storage = get_storage()
    user = storage.get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update directly in database
    with storage.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_admin = ? WHERE email = ?",
            (1 if is_admin else 0, email)
        )
        conn.commit()

    return {"success": True, "message": f"User {email} admin status set to {is_admin}"}


@router.get("/users")
async def get_all_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    admin: dict = Depends(require_super_admin)
):
    """Get all users (super-admin only)"""
    AdminLogger.log_action(admin["email"], "view_users", details={"search": search})

    store = get_store()
    users = store.get_all_users()

    # Filter by search if provided
    if search:
        search_lower = search.lower()
        users = [u for u in users if search_lower in u.get("email", "").lower() or search_lower in u.get("name", "").lower()]

    # Pagination
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "users": users[start:end],
        "total": len(users),
        "page": page,
        "page_size": page_size
    }


@router.get("/users/stats")
async def get_users_stats(admin: dict = Depends(require_super_admin)):
    """Get user statistics (super-admin only)"""
    store = get_store()
    users = store.get_all_users()

    premium_users = len([u for u in users if u.get("plan") in ["premium", "enterprise"]])
    active_users = len([u for u in users if u.get("status") == "active"])

    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    users_today = len([u for u in users if u.get("created_at") and datetime.fromisoformat(u["created_at"]).date() == today])

    return {
        "total_users": len(users),
        "premium_users": premium_users,
        "users_today": users_today,
        "active_users": active_users
    }


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_super_admin)):
    """Delete a user (super-admin only)"""
    AdminLogger.log_action(admin["email"], "delete_user", target=user_id)

    store = get_store()
    user = store.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    store.delete_user(user_id)

    return {"success": True, "message": f"User {user_id} deleted"}


@router.post("/users/{user_id}/change-plan")
async def change_user_plan(
    user_id: str,
    plan: str = Query(..., regex="^(free|premium|enterprise)$"),
    admin: dict = Depends(require_super_admin)
):
    """Change user's plan (super-admin only)"""
    AdminLogger.log_action(admin["email"], "change_plan", target=user_id, details={"new_plan": plan})

    store = get_store()
    user = store.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    store.update_user(user_id, {"plan": plan})

    return {"success": True, "message": f"User {user_id} plan changed to {plan}"}


@router.post("/users/{user_id}/set-admin")
async def set_user_admin_status(
    user_id: str,
    is_admin: bool = Query(...),
    admin: dict = Depends(require_super_admin)
):
    """Set user's admin status (super-admin only)"""
    from backend.core.storage import get_storage

    AdminLogger.log_action(admin["email"], "set_admin", target=user_id, details={"is_admin": is_admin})

    storage = get_storage()
    user = storage.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update directly in database
    with storage.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_admin = ? WHERE id = ?",
            (1 if is_admin else 0, user_id)
        )
        conn.commit()

    return {"success": True, "message": f"User {user_id} admin status set to {is_admin}"}


@router.post("/impersonate")
async def impersonate_user(user_id: str, admin: dict = Depends(require_super_admin)):
    """Impersonate another user (super-admin only)"""
    from backend.core.auth import create_access_token

    AdminLogger.log_action(admin["email"], "impersonate", target=user_id)

    store = get_store()
    target_user = store.get_user_by_id(user_id)

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create token for target user
    access_token = create_access_token(target_user["id"])

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/system/stats")
async def get_system_stats(admin: dict = Depends(require_super_admin)):
    """Get system resource statistics (super-admin only)"""
    # Mock data for now - will be replaced with real metrics
    return {
        "postgres": {
            "total_connections": 50,
            "active_connections": 12,
            "database_size_mb": 1250.5
        },
        "redis": {
            "connected_clients": 5,
            "used_memory_mb": 45.2,
            "cache_hit_rate": 82.3
        },
        "s3": {
            "total_files": 1523,
            "total_size_mb": 8950.3
        },
        "ai": {
            "total_cost_today": 12.45,
            "total_cost_month": 145.80,
            "requests_today": 234
        }
    }


@router.get("/system/logs")
async def get_system_logs(
    level: Optional[str] = Query(None, regex="^(error|warning|info|all)$"),
    limit: int = Query(100, ge=1, le=1000),
    admin: dict = Depends(require_super_admin)
):
    """Get system logs (super-admin only)"""
    # Mock data - will be replaced with real log aggregation
    logs = [
        {
            "timestamp": "2025-01-04T12:30:00Z",
            "level": "info",
            "message": "User registration successful",
            "details": {"user_id": "123"}
        },
        {
            "timestamp": "2025-01-04T12:25:00Z",
            "level": "warning",
            "message": "High memory usage detected",
            "details": {"memory_mb": 450}
        },
        {
            "timestamp": "2025-01-04T12:20:00Z",
            "level": "error",
            "message": "Failed to connect to Vinted API",
            "details": {"retry_count": 3}
        }
    ]

    if level and level != "all":
        logs = [log for log in logs if log["level"] == level]

    return {"logs": logs[:limit]}


@router.post("/system/cache/clear")
async def clear_system_cache(admin: dict = Depends(require_super_admin)):
    """Clear Redis cache (super-admin only)"""
    AdminLogger.log_action(admin["email"], "clear_cache")

    # TODO: Implement Redis cache clearing
    return {"success": True, "message": "Cache cleared"}


@router.get("/analytics/all")
async def get_all_analytics(admin: dict = Depends(require_super_admin)):
    """Get analytics for all users (super-admin only)"""
    # Mock data
    return {
        "total_revenue": 5240.50,
        "total_ai_cost": 145.80,
        "total_automations": 523,
        "total_listings": 2341
    }


@router.get("/ai/costs")
async def get_ai_costs(admin: dict = Depends(require_super_admin)):
    """Get detailed AI costs breakdown (super-admin only)"""
    # Mock data
    return {
        "today": 12.45,
        "this_week": 78.90,
        "this_month": 145.80,
        "by_model": {
            "gpt-4o": 45.20,
            "gpt-4o-mini": 100.60
        },
        "by_user": [
            {"user_id": "123", "email": "user1@example.com", "cost": 25.30},
            {"user_id": "456", "email": "user2@example.com", "cost": 15.80}
        ]
    }


@router.post("/backup/create")
async def create_database_backup(
    request: BackupRequest,
    admin: dict = Depends(require_super_admin)
):
    """
    Create a new database backup (super-admin only)

    Args:
        compress: Whether to compress the backup with gzip

    Returns:
        Backup metadata including path and size
    """
    AdminLogger.log_action(admin["email"], "create_backup", details={"compress": request.compress})

    result = create_backup(compress=request.compress)

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Backup failed')
        )

    return result


@router.get("/system/backups")
async def get_backups_alias(admin: dict = Depends(require_super_admin)):
    """Alias for /backup/list (super-admin only)"""
    return {"backups": list_backups()}


@router.post("/backup/restore")
async def restore_database_backup(
    request: RestoreRequest,
    admin: dict = Depends(require_super_admin)
):
    """
    Restore database from a backup

    Args:
        backup_path: Path to the backup file to restore

    Returns:
        Restore result

    [WARN] WARNING: This will replace the current database!
    """
    AdminLogger.log_action(admin["email"], "restore_backup", details={"backup_path": request.backup_path})

    result = restore_backup(request.backup_path)

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Restore failed')
        )

    return result


@router.get("/backup/list")
async def list_available_backups(admin: dict = Depends(require_super_admin)):
    """
    List all available database backups

    Returns:
        List of backups with metadata (filename, size, age, etc.)

    Note: Requires admin authentication (TODO)
    """
    return {
        "backups": list_backups()
    }


@router.get("/backup/info")
async def get_backup_system_info(admin: dict = Depends(require_super_admin)):
    """
    Get backup system information

    Returns:
        - Total number of backups
        - Total size
        - Latest backup info
        - Backup configuration

    Note: Requires admin authentication (TODO)
    """
    return get_backup_info()


@router.post("/export")
async def export_database(
    request: ExportRequest,
    admin: dict = Depends(require_super_admin)
):
    """
    Export database to JSON or SQL format

    Args:
        output_path: Path for the export file
        tables: Optional list of tables to export (None = all)
        format: Export format ("json" or "sql")

    Returns:
        Export result with file path and size

    Note: Requires admin authentication (TODO)
    """
    if request.format == "json":
        result = export_to_json(request.output_path, request.tables)
    elif request.format == "sql":
        result = export_to_sql(request.output_path)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid format: {request.format}. Must be 'json' or 'sql'"
        )

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get('error', 'Export failed')
        )

    return result


@router.get("/system/health")
async def admin_system_health(admin: dict = Depends(require_super_admin)):
    """
    Get comprehensive system health (admin view)

    Returns:
        - All health checks
        - System metrics
        - Job statistics
        - Circuit breaker states

    Note: Requires admin authentication (TODO)
    """
    health = await get_system_health()
    metrics = await get_system_metrics()
    jobs = get_job_stats()
    circuit_breakers = get_all_circuit_states()

    return {
        "health": health,
        "metrics": metrics,
        "jobs": jobs,
        "circuit_breakers": circuit_breakers
    }


@router.post("/jobs/reset-stats")
async def reset_job_statistics(
    job_name: Optional[str] = Query(None),
    admin: dict = Depends(require_super_admin)
):
    """
    Reset statistics for a specific job or all jobs

    Args:
        job_name: Name of job to reset (None = reset all)

    Note: Requires admin authentication (TODO)
    """
    reset_job_stats(job_name)

    return {
        "success": True,
        "message": f"Reset statistics for {job_name or 'all jobs'}"
    }
