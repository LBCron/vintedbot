"""
Job wrapper with error isolation, monitoring, and alerting.
Prevents one failing job from affecting others.
"""
import asyncio
import time
import traceback
from datetime import datetime
from functools import wraps
from typing import Callable, Optional, Dict, Any
from loguru import logger


class JobExecutionError(Exception):
    """Raised when a job fails after all retries"""
    pass


class JobMetrics:
    """Track metrics for job executions"""

    def __init__(self):
        self.job_stats: Dict[str, Dict[str, Any]] = {}

    def record_execution(
        self,
        job_name: str,
        success: bool,
        duration_ms: float,
        error: Optional[str] = None
    ):
        """Record job execution metrics"""
        if job_name not in self.job_stats:
            self.job_stats[job_name] = {
                'total_runs': 0,
                'successful_runs': 0,
                'failed_runs': 0,
                'total_duration_ms': 0,
                'last_run': None,
                'last_success': None,
                'last_failure': None,
                'consecutive_failures': 0,
                'last_error': None
            }

        stats = self.job_stats[job_name]
        stats['total_runs'] += 1
        stats['total_duration_ms'] += duration_ms
        stats['last_run'] = datetime.now().isoformat()

        if success:
            stats['successful_runs'] += 1
            stats['last_success'] = datetime.now().isoformat()
            stats['consecutive_failures'] = 0
        else:
            stats['failed_runs'] += 1
            stats['last_failure'] = datetime.now().isoformat()
            stats['consecutive_failures'] += 1
            stats['last_error'] = error

    def get_stats(self, job_name: Optional[str] = None) -> Dict:
        """Get job statistics"""
        if job_name:
            return self.job_stats.get(job_name, {})
        return self.job_stats

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of all jobs"""
        total_jobs = len(self.job_stats)
        healthy_jobs = 0
        degraded_jobs = 0
        unhealthy_jobs = 0

        for job_name, stats in self.job_stats.items():
            consecutive_failures = stats.get('consecutive_failures', 0)

            if consecutive_failures == 0:
                healthy_jobs += 1
            elif consecutive_failures < 3:
                degraded_jobs += 1
            else:
                unhealthy_jobs += 1

        overall_status = 'healthy'
        if unhealthy_jobs > 0:
            overall_status = 'unhealthy'
        elif degraded_jobs > 0:
            overall_status = 'degraded'

        return {
            'status': overall_status,
            'total_jobs': total_jobs,
            'healthy_jobs': healthy_jobs,
            'degraded_jobs': degraded_jobs,
            'unhealthy_jobs': unhealthy_jobs,
            'jobs': self.job_stats
        }


# Global metrics tracker
job_metrics = JobMetrics()


def isolated_job(
    job_name: str,
    max_retries: int = 0,
    retry_delay: int = 5,
    timeout: Optional[int] = None,
    alert_on_failure: bool = False
):
    """
    Decorator to isolate job execution with error handling, retries, and monitoring.

    Args:
        job_name: Name of the job for logging and metrics
        max_retries: Number of retries on failure (default 0)
        retry_delay: Seconds to wait between retries (default 5)
        timeout: Job timeout in seconds (default None = no timeout)
        alert_on_failure: Send alert notification on failure (default False)

    Example:
        @isolated_job("inbox_sync", max_retries=2, timeout=300)
        async def inbox_sync_job():
            # job logic here
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            attempt = 0
            last_error = None
            start_time = time.time()

            while attempt <= max_retries:
                try:
                    logger.info(
                        f"🔄 [{job_name}] Starting execution (attempt {attempt + 1}/{max_retries + 1})"
                    )

                    # Execute with timeout if specified
                    if timeout:
                        result = await asyncio.wait_for(
                            func(*args, **kwargs),
                            timeout=timeout
                        )
                    else:
                        result = await func(*args, **kwargs)

                    # Success
                    duration_ms = (time.time() - start_time) * 1000
                    logger.info(
                        f"✅ [{job_name}] Completed successfully in {duration_ms:.0f}ms"
                    )

                    job_metrics.record_execution(
                        job_name=job_name,
                        success=True,
                        duration_ms=duration_ms
                    )

                    return result

                except asyncio.TimeoutError:
                    last_error = f"Job timed out after {timeout}s"
                    logger.error(f"⏰ [{job_name}] {last_error}")

                except Exception as e:
                    last_error = str(e)
                    error_trace = traceback.format_exc()
                    logger.error(f"❌ [{job_name}] Failed: {last_error}")
                    logger.debug(f"Traceback:\n{error_trace}")

                # Retry logic
                attempt += 1
                if attempt <= max_retries:
                    logger.warning(
                        f"⚠️ [{job_name}] Retrying in {retry_delay}s "
                        f"(attempt {attempt + 1}/{max_retries + 1})"
                    )
                    await asyncio.sleep(retry_delay)

            # All retries exhausted
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"💀 [{job_name}] Failed after {max_retries + 1} attempts. "
                f"Last error: {last_error}"
            )

            job_metrics.record_execution(
                job_name=job_name,
                success=False,
                duration_ms=duration_ms,
                error=last_error
            )

            # Send alert if configured
            if alert_on_failure:
                await send_job_failure_alert(job_name, last_error)

            # Don't raise exception - let job fail gracefully without affecting other jobs
            # return None  # Optional: uncomment to return None instead of raising

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, convert to async
            return asyncio.run(async_wrapper(*args, **kwargs))

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def send_job_failure_alert(job_name: str, error: str):
    """
    Send alert notification when job fails.
    Can be extended to send emails, Slack messages, etc.
    """
    logger.critical(f"🚨 ALERT: Job '{job_name}' failed with error: {error}")

    # TODO: Implement actual alerting (email, Slack, PagerDuty, etc.)
    # Example:
    # await send_slack_alert(f"Job '{job_name}' failed: {error}")
    # await send_email_alert(f"Job failure: {job_name}", error)


def get_job_health() -> Dict[str, Any]:
    """Get health status of all jobs"""
    return job_metrics.get_health_status()


def get_job_stats(job_name: Optional[str] = None) -> Dict:
    """Get statistics for a specific job or all jobs"""
    return job_metrics.get_stats(job_name)


def reset_job_stats(job_name: Optional[str] = None):
    """Reset statistics for a job or all jobs"""
    if job_name:
        if job_name in job_metrics.job_stats:
            del job_metrics.job_stats[job_name]
    else:
        job_metrics.job_stats.clear()
