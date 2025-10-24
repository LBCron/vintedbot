"""
Retry utilities with exponential backoff for VintedBot API

Uses tenacity for robust retry logic on critical operations.
"""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import logging
from typing import Type, Tuple

logger = logging.getLogger(__name__)

# Custom exceptions for retry logic
class RetryableVintedError(Exception):
    """Base exception for retryable Vinted errors"""
    pass

class VintedNetworkError(RetryableVintedError):
    """Network error when communicating with Vinted"""
    pass

class VintedTimeoutError(RetryableVintedError):
    """Timeout when waiting for Vinted response"""
    pass

class VintedRateLimitError(RetryableVintedError):
    """Rate limit hit on Vinted API"""
    pass

class CaptchaDetectedError(RetryableVintedError):
    """Captcha detected - retryable if captcha solver available"""
    pass

class AIAnalysisError(RetryableVintedError):
    """OpenAI API error - retryable on temporary issues"""
    pass


# Retry decorator for Vinted publication endpoints
def retry_publish_operation(
    max_attempts: int = 3,
    min_wait: int = 5,
    max_wait: int = 60
):
    """
    Retry decorator for Vinted publish operations
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        min_wait: Minimum wait time in seconds (default: 5)
        max_wait: Maximum wait time in seconds (default: 60)
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @retry_publish_operation(max_attempts=3)
        async def publish_listing(draft_id):
            ...
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type((
            VintedNetworkError,
            VintedTimeoutError,
            VintedRateLimitError,
            AIAnalysisError
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True
    )


# Retry decorator for AI analysis operations
def retry_ai_analysis(
    max_attempts: int = 2,
    min_wait: int = 3,
    max_wait: int = 30
):
    """
    Retry decorator for AI analysis operations (GPT-4 Vision)
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 2)
        min_wait: Minimum wait time in seconds (default: 3)
        max_wait: Maximum wait time in seconds (default: 30)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(AIAnalysisError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )


# Retry decorator for captcha solving
def retry_captcha_solve(
    max_attempts: int = 2,
    min_wait: int = 10,
    max_wait: int = 30
):
    """
    Retry decorator for captcha solving operations
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 2)
        min_wait: Minimum wait time in seconds (default: 10)
        max_wait: Maximum wait time in seconds (default: 30)
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(CaptchaDetectedError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
