"""
Sentry Error Tracking Configuration
Production-grade error monitoring and performance tracking
"""
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from loguru import logger


def init_sentry():
    """
    Initialize Sentry error tracking
    
    Only enables in production/staging environments
    """
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("ENVIRONMENT", "development")
    
    if not sentry_dsn:
        logger.info("Sentry DSN not configured - error tracking disabled")
        return
    
    if environment == "development":
        logger.info("Development environment - Sentry disabled")
        return
    
    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            
            # Performance monitoring
            traces_sample_rate=0.1,  # 10% of transactions
            profiles_sample_rate=0.1,  # 10% profiling
            
            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            
            # Filter sensitive data
            send_default_pii=False,
            
            # Before send hook to scrub sensitive data
            before_send=before_send_handler,
            
            # Release tracking
            release=os.getenv("GIT_COMMIT_SHA", "unknown"),
        )
        
        logger.info(f"✅ Sentry initialized for {environment}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_handler(event, hint):
    """
    Scrub sensitive data before sending to Sentry
    """
    # Remove Authorization headers
    if "request" in event and "headers" in event["request"]:
        headers = event["request"]["headers"]
        if "Authorization" in headers:
            headers["Authorization"] = "[Filtered]"
        if "Cookie" in headers:
            headers["Cookie"] = "[Filtered]"
    
    # Remove sensitive query parameters
    if "request" in event and "query_string" in event["request"]:
        query = event["request"]["query_string"]
        if query:
            # Filter common sensitive params
            sensitive_params = ["password", "token", "api_key", "secret"]
            for param in sensitive_params:
                if param in query.lower():
                    event["request"]["query_string"] = "[Filtered]"
                    break
    
    return event
