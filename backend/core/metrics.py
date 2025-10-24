"""
Prometheus Metrics for VintedBot API

Tracks:
- Publications (success/fail/captcha/timeout)
- AI analysis (duration, total)
- Queue size
- Captcha detection/resolution
- User activity
"""

from prometheus_client import Counter, Histogram, Gauge, Info

# ========== Publication Metrics ==========
publish_total = Counter(
    "vintedbot_publish_total",
    "Total publications attempts",
    ["status"]  # success, fail, captcha, timeout, retry_exhausted
)

publish_duration_seconds = Histogram(
    "vintedbot_publish_duration_seconds",
    "Duration of publication process",
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

publish_retry_count = Counter(
    "vintedbot_publish_retry_count",
    "Number of retries attempted",
    ["attempt"]  # 1, 2, 3
)

# ========== AI Analysis Metrics ==========
photo_analyze_total = Counter(
    "vintedbot_photo_analyze_total",
    "Total photo analysis jobs",
    ["status"]  # completed, failed, processing
)

photo_analyze_duration_seconds = Histogram(
    "vintedbot_photo_analyze_duration_seconds",
    "Duration of AI photo analysis",
    buckets=[5, 10, 30, 60, 120, 300, 600]
)

gpt4_vision_calls_total = Counter(
    "vintedbot_gpt4_vision_calls_total",
    "Total GPT-4 Vision API calls",
    ["status"]  # success, error, timeout
)

# ========== Queue Metrics ==========
publish_queue_size = Gauge(
    "vintedbot_publish_queue_size",
    "Current size of publish queue"
)

bulk_job_active_total = Gauge(
    "vintedbot_bulk_job_active_total",
    "Number of active bulk jobs"
)

# ========== Captcha Metrics ==========
captcha_detected_total = Counter(
    "vintedbot_captcha_detected_total",
    "Total captchas detected",
    ["type"]  # hcaptcha, recaptcha, unknown
)

captcha_solved_total = Counter(
    "vintedbot_captcha_solved_total",
    "Total captchas solved successfully"
)

captcha_failure_total = Counter(
    "vintedbot_captcha_failure_total",
    "Total captcha resolution failures",
    ["reason"]  # timeout, invalid_solution, quota_exceeded
)

# ========== User Metrics ==========
active_users = Gauge(
    "vintedbot_active_users",
    "Number of active users (sessions)"
)

# REMOVED: publish_per_user_total (cardinality explosion risk)
# DO NOT use raw user_id in labels - creates one time-series per user
# Alternative: Use histogram or aggregate by user tier/segment
# Example: publish_per_tier_total = Counter(..., ["tier"])  # free, premium, enterprise

# ========== Draft Quality Metrics ==========
draft_created_total = Counter(
    "vintedbot_draft_created_total",
    "Total drafts created",
    ["publish_ready"]  # true, false
)

draft_validation_failures = Counter(
    "vintedbot_draft_validation_failures",
    "Draft validation failures",
    ["reason"]  # title_too_long, hashtags_invalid, emoji_detected, etc.
)

# ========== System Info ==========
app_info = Info(
    "vintedbot_app_info",
    "Application information"
)

# Set app info (called once at startup)
app_info.info({
    "version": "1.0.0",
    "name": "VintedBot API",
    "environment": "production"
})
