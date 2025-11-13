"""
Super-Admin System - Full Access Control
Gives ronanchenlopes@gmail.com complete control over the platform
"""
import os
from typing import Optional
from functools import wraps
from fastapi import HTTPException, status
from backend.utils.logger import logger

# Super-Admin Email (you!)
SUPER_ADMIN_EMAIL = "ronanchenlopes@gmail.com"

# Admin role permissions
ADMIN_ROLES = {
    "super_admin": {
        "email": SUPER_ADMIN_EMAIL,
        "permissions": [
            "users.view",
            "users.edit",
            "users.delete",
            "users.impersonate",  # Login as any user
            "analytics.view_all",  # See all users' analytics
            "billing.view_all",    # See all payments
            "billing.refund",      # Refund users
            "system.metrics",      # View Prometheus metrics
            "system.logs",         # View all logs
            "system.backup",       # Trigger backups
            "system.config",       # Change config
            "automation.view_all", # See all automations
            "automation.kill",     # Stop any automation
            "vinted.debug",        # Debug Vinted API
            "telegram.send",       # Send Telegram messages
            "database.query",      # Direct DB access
            "api.unlimited",       # No rate limits
        ]
    },
    "admin": {
        "permissions": [
            "users.view",
            "analytics.view_all",
            "system.metrics",
            "system.logs",
        ]
    },
    "moderator": {
        "permissions": [
            "users.view",
            "system.logs",
        ]
    }
}


def is_super_admin(email: str) -> bool:
    """Check if user is super admin"""
    return email.lower() == SUPER_ADMIN_EMAIL.lower()


def has_permission(email: str, permission: str) -> bool:
    """Check if user has specific permission"""
    if is_super_admin(email):
        return True  # Super admin has all permissions

    # Check other roles (can be expanded later)
    for role, config in ADMIN_ROLES.items():
        if config.get("email") == email and permission in config.get("permissions", []):
            return True

    return False


def require_super_admin(func):
    """Decorator to require super admin access"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract user from request (assuming it's in kwargs or args)
        user = None

        # Try to get user from kwargs
        if "current_user" in kwargs:
            user = kwargs["current_user"]
        elif "user" in kwargs:
            user = kwargs["user"]

        # Try to get user from args (typically first arg after self/cls)
        if not user and len(args) > 0:
            for arg in args:
                if hasattr(arg, "email"):
                    user = arg
                    break

        if not user or not is_super_admin(user.email):
            logger.warning(f"Unauthorized admin access attempt: {user.email if user else 'unknown'}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required"
            )

        logger.info(f"Super admin access granted: {user.email}")
        return await func(*args, **kwargs)

    return wrapper


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = None

            # Extract user (same logic as above)
            if "current_user" in kwargs:
                user = kwargs["current_user"]
            elif "user" in kwargs:
                user = kwargs["user"]

            if not user and len(args) > 0:
                for arg in args:
                    if hasattr(arg, "email"):
                        user = arg
                        break

            if not user or not has_permission(user.email, permission):
                logger.warning(f"Permission denied: {user.email if user else 'unknown'} -> {permission}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


class AdminLogger:
    """Log all admin actions for audit trail"""

    @staticmethod
    def log_action(admin_email: str, action: str, target: Optional[str] = None, details: Optional[dict] = None):
        """Log admin action to audit trail"""
        from datetime import datetime

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "admin": admin_email,
            "action": action,
            "target": target,
            "details": details or {}
        }

        logger.info(f"[ADMIN ACTION] {log_entry}")

        # TODO: Store in database for audit trail
        # store.create_audit_log(log_entry)


# Quick permission checks
def can_view_users(email: str) -> bool:
    return has_permission(email, "users.view")

def can_edit_users(email: str) -> bool:
    return has_permission(email, "users.edit")

def can_delete_users(email: str) -> bool:
    return has_permission(email, "users.delete")

def can_impersonate(email: str) -> bool:
    return has_permission(email, "users.impersonate")

def can_view_all_analytics(email: str) -> bool:
    return has_permission(email, "analytics.view_all")

def can_view_metrics(email: str) -> bool:
    return has_permission(email, "system.metrics")

def can_view_logs(email: str) -> bool:
    return has_permission(email, "system.logs")

def can_trigger_backup(email: str) -> bool:
    return has_permission(email, "system.backup")

def can_query_database(email: str) -> bool:
    return has_permission(email, "database.query")
