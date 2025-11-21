"""
Sentry Error Tracking and Performance Monitoring
Production-grade observability for error tracking and performance
"""
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from backend.utils.logger import logger

# Sentry Configuration
SENTRY_DSN = os.getenv("SENTRY_DSN")
SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT", "production")
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))  # 10% of transactions
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))  # 10% of transactions


def init_sentry():
    """
    Initialize Sentry SDK with production-ready configuration

    Features enabled:
    - Error tracking
    - Performance monitoring (APM)
    - Profiling
    - Release tracking
    - User context
    - Custom tags
    """
    if not SENTRY_DSN:
        logger.info("[WARN] Sentry DSN not configured - error tracking disabled")
        return

    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=SENTRY_ENVIRONMENT,

            # Integrations
            integrations=[
                FastApiIntegration(
                    transaction_style="endpoint",  # Group by endpoint
                    failed_request_status_codes=[400, 499],  # Track client errors
                ),
                SqlalchemyIntegration(),  # Track DB queries
                RedisIntegration(),  # Track Redis operations
                HttpxIntegration(),  # Track HTTP requests (Vinted API, OpenAI, etc.)
            ],

            # Performance Monitoring
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,

            # Error Tracking
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send PII by default (GDPR compliance)

            # Release Tracking
            release=os.getenv("GIT_COMMIT", "unknown"),

            # Performance
            max_breadcrumbs=50,
            before_send=before_send_filter,
            before_send_transaction=before_send_transaction_filter,
        )

        logger.info(f"[OK] Sentry initialized: env={SENTRY_ENVIRONMENT}, sample_rate={SENTRY_TRACES_SAMPLE_RATE}")

    except Exception as e:
        logger.error(f"[ERROR] Sentry initialization failed: {e}")


def before_send_filter(event, hint):
    """
    Filter events before sending to Sentry

    Use this to:
    - Remove sensitive data
    - Ignore certain errors
    - Add custom context
    """
    # Ignore specific errors
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']

        # Ignore expected errors
        ignored_errors = [
            "ConnectionError",  # Network issues
            "TimeoutError",     # Timeout issues
            "RateLimitExceeded",  # Expected rate limiting
        ]

        if exc_type.__name__ in ignored_errors:
            return None  # Don't send to Sentry

    # Remove sensitive data from request
    if 'request' in event:
        request = event['request']

        # Remove sensitive headers
        if 'headers' in request:
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for header in sensitive_headers:
                if header in request['headers']:
                    request['headers'][header] = '[Filtered]'

        # Remove sensitive query params
        if 'query_string' in request:
            sensitive_params = ['token', 'api_key', 'password']
            for param in sensitive_params:
                if param in request['query_string']:
                    request['query_string'] = request['query_string'].replace(
                        param,
                        '[Filtered]'
                    )

    return event


def before_send_transaction_filter(event, hint):
    """
    Filter transactions before sending to Sentry

    Use this to ignore low-value transactions (health checks, etc.)
    """
    # Ignore health check transactions
    if event.get('transaction', '').startswith('/health'):
        return None

    # Ignore static file requests
    if event.get('transaction', '').startswith('/static'):
        return None

    return event


def capture_exception(error: Exception, **kwargs):
    """
    Manually capture exception with custom context

    Usage:
        try:
            risky_operation()
        except Exception as e:
            capture_exception(e, extra={'user_id': user_id})
    """
    if SENTRY_DSN:
        sentry_sdk.capture_exception(error, **kwargs)


def capture_message(message: str, level: str = "info", **kwargs):
    """
    Capture custom message

    Usage:
        capture_message("User exceeded quota", level="warning", extra={'user_id': user_id})
    """
    if SENTRY_DSN:
        sentry_sdk.capture_message(message, level=level, **kwargs)


def set_user_context(user_id: str, email: Optional[str] = None, username: Optional[str] = None):
    """
    Set user context for error tracking

    Usage:
        set_user_context(user_id="123", email="user@example.com")
    """
    if SENTRY_DSN:
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            "username": username
        })


def set_custom_tag(key: str, value: str):
    """
    Set custom tag for filtering in Sentry

    Usage:
        set_custom_tag("plan", "pro")
        set_custom_tag("feature", "auto_bump")
    """
    if SENTRY_DSN:
        sentry_sdk.set_tag(key, value)


def add_breadcrumb(message: str, category: str = "custom", level: str = "info", data: dict = None):
    """
    Add breadcrumb for context

    Usage:
        add_breadcrumb("User started photo upload", category="upload", data={'count': 10})
    """
    if SENTRY_DSN:
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )
