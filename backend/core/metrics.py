"""
Prometheus Metrics for Performance Monitoring
Exposes comprehensive metrics for Grafana dashboards
"""
import os
import time
from typing import Optional
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CollectorRegistry,
    CONTENT_TYPE_LATEST
)
from fastapi import Response
from backend.utils.logger import logger

# Create registry
registry = CollectorRegistry()

# ============================================================================
# APPLICATION METRICS
# ============================================================================

# Info
app_info = Info(
    'vintedbots_app',
    'Application information',
    registry=registry
)
app_info.info({
    'version': os.getenv('APP_VERSION', '1.0.0'),
    'environment': os.getenv('ENVIRONMENT', 'production')
})

# ============================================================================
# HTTP METRICS
# ============================================================================

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

# ============================================================================
# AI METRICS
# ============================================================================

ai_requests_total = Counter(
    'ai_requests_total',
    'Total AI API requests',
    ['model', 'status'],
    registry=registry
)

ai_cost_total = Counter(
    'ai_cost_total_cents',
    'Total AI cost in cents',
    ['model'],
    registry=registry
)

ai_tokens_total = Counter(
    'ai_tokens_total',
    'Total AI tokens consumed',
    ['model', 'type'],  # type: input/output
    registry=registry
)

# ============================================================================
# VINTED API METRICS
# ============================================================================

vinted_requests_total = Counter(
    'vinted_requests_total',
    'Total Vinted API requests',
    ['endpoint', 'status'],
    registry=registry
)

vinted_automation_runs_total = Counter(
    'vinted_automation_runs_total',
    'Total automation runs',
    ['type', 'status'],  # type: bump/follow/message
    registry=registry
)

captcha_detected_total = Counter(
    'vinted_captcha_detected_total',
    'Total captcha detections',
    registry=registry
)

# ============================================================================
# DATABASE METRICS
# ============================================================================

db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['operation'],  # operation: select/insert/update/delete
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    registry=registry
)

# ============================================================================
# REDIS METRICS
# ============================================================================

redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status'],  # operation: get/set/delete
    registry=registry
)

# ============================================================================
# STORAGE METRICS
# ============================================================================

storage_uploads_total = Counter(
    'storage_uploads_total',
    'Total file uploads',
    ['backend'],  # backend: s3/local
    registry=registry
)

# ============================================================================
# BUSINESS METRICS
# ============================================================================

users_registered_total = Counter(
    'users_registered_total',
    'Total registered users',
    registry=registry
)

listings_published_total = Counter(
    'listings_published_total',
    'Total listings published',
    ['status'],  # status: success/failed
    registry=registry
)

drafts_created_total = Counter(
    'drafts_created_total',
    'Total drafts created',
    registry=registry
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def track_http_request(method: str, endpoint: str, status: int, duration: float):
    """Track HTTP request metrics"""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def track_ai_request(model: str, status: str, cost: float, input_tokens: int, output_tokens: int):
    """Track AI request metrics"""
    ai_requests_total.labels(model=model, status=status).inc()
    ai_cost_total.labels(model=model).inc(int(cost * 100))  # Convert to cents
    ai_tokens_total.labels(model=model, type="input").inc(input_tokens)
    ai_tokens_total.labels(model=model, type="output").inc(output_tokens)


def track_vinted_request(endpoint: str, status: str):
    """Track Vinted API request"""
    vinted_requests_total.labels(endpoint=endpoint, status=status).inc()


def track_automation_run(automation_type: str, status: str):
    """Track automation run"""
    vinted_automation_runs_total.labels(type=automation_type, status=status).inc()


def track_captcha_detection():
    """Track captcha detection"""
    captcha_detected_total.inc()


def track_db_query(operation: str, duration: float):
    """Track database query"""
    db_queries_total.labels(operation=operation).inc()
    db_query_duration_seconds.labels(operation=operation).observe(duration)


def track_redis_operation(operation: str, status: str):
    """Track Redis operation"""
    redis_operations_total.labels(operation=operation, status=status).inc()


def track_storage_upload(backend: str):
    """Track file upload"""
    storage_uploads_total.labels(backend=backend).inc()


def track_user_registration():
    """Track user registration"""
    users_registered_total.inc()


def track_listing_published(status: str):
    """Track listing publication"""
    listings_published_total.labels(status=status).inc()


def track_draft_created():
    """Track draft creation"""
    drafts_created_total.inc()


def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint

    Usage:
        @app.get("/metrics")
        async def metrics():
            return metrics_endpoint()
    """
    metrics = generate_latest(registry)
    return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)
