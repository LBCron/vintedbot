"""
Smart Rate Limiter
Rate limiting intelligent qui s'adapte pour éviter la détection
"""
import asyncio
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Dict
import random
from loguru import logger


class SmartRateLimiter:
    """
    Intelligent rate limiter that adapts to avoid detection
    """

    def __init__(
        self,
        max_requests_per_minute: int = 10,
        max_requests_per_hour: int = 300,
        max_requests_per_day: int = 3000,
        adaptive: bool = True,
        randomize_delays: bool = True
    ):
        """
        Initialize rate limiter

        Args:
            max_requests_per_minute: Max requests per minute
            max_requests_per_hour: Max requests per hour
            max_requests_per_day: Max requests per day
            adaptive: Adapt limits if detection suspected
            randomize_delays: Add random delays between requests
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_hour = max_requests_per_hour
        self.max_requests_per_day = max_requests_per_day
        self.adaptive = adaptive
        self.randomize_delays = randomize_delays

        # Request tracking
        self.requests_minute = deque()
        self.requests_hour = deque()
        self.requests_day = deque()

        # Adaptive rate limiting
        self.detection_score = 0
        self.base_delay = 1.0  # Base delay in seconds
        self.current_delay_multiplier = 1.0

        # Statistics
        self.total_requests = 0
        self.total_wait_time = 0
        self.blocked_requests = 0

    def _cleanup_old_requests(self):
        """Remove old requests from tracking"""
        now = time.time()

        # Minute tracking (keep last 60 seconds)
        while self.requests_minute and now - self.requests_minute[0] > 60:
            self.requests_minute.popleft()

        # Hour tracking (keep last 3600 seconds)
        while self.requests_hour and now - self.requests_hour[0] > 3600:
            self.requests_hour.popleft()

        # Day tracking (keep last 86400 seconds)
        while self.requests_day and now - self.requests_day[0] > 86400:
            self.requests_day.popleft()

    def _get_required_wait_time(self) -> float:
        """
        Calculate required wait time before next request

        Returns:
            Wait time in seconds
        """
        self._cleanup_old_requests()

        wait_times = []

        # Check minute limit
        if len(self.requests_minute) >= self.max_requests_per_minute:
            oldest_request = self.requests_minute[0]
            time_to_wait = 60 - (time.time() - oldest_request)
            if time_to_wait > 0:
                wait_times.append(time_to_wait)

        # Check hour limit
        if len(self.requests_hour) >= self.max_requests_per_hour:
            oldest_request = self.requests_hour[0]
            time_to_wait = 3600 - (time.time() - oldest_request)
            if time_to_wait > 0:
                wait_times.append(time_to_wait)

        # Check day limit
        if len(self.requests_day) >= self.max_requests_per_day:
            oldest_request = self.requests_day[0]
            time_to_wait = 86400 - (time.time() - oldest_request)
            if time_to_wait > 0:
                wait_times.append(time_to_wait)

        # Add base delay with multiplier
        base_wait = self.base_delay * self.current_delay_multiplier

        # Add random delay if enabled
        if self.randomize_delays:
            base_wait *= random.uniform(0.8, 1.5)

        wait_times.append(base_wait)

        return max(wait_times)

    async def wait_if_needed(self) -> float:
        """
        Wait if rate limit would be exceeded

        Returns:
            Time waited in seconds
        """
        wait_time = self._get_required_wait_time()

        if wait_time > 0:
            # Log if significant wait
            if wait_time > 5:
                logger.info(f"⏳ Rate limit: waiting {wait_time:.1f}s")

            await asyncio.sleep(wait_time)
            self.total_wait_time += wait_time

            return wait_time

        return 0

    def record_request(self, success: bool = True):
        """
        Record a request

        Args:
            success: Whether request was successful
        """
        now = time.time()

        self.requests_minute.append(now)
        self.requests_hour.append(now)
        self.requests_day.append(now)

        self.total_requests += 1

        # Adapt if adaptive mode enabled
        if self.adaptive:
            self._adapt_to_response(success)

    def _adapt_to_response(self, success: bool):
        """
        Adapt rate limiting based on response

        Args:
            success: Whether request was successful
        """
        if not success:
            # Increase detection score on failure
            self.detection_score += 1

            # Slow down if multiple failures
            if self.detection_score > 3:
                self.current_delay_multiplier *= 1.5
                self.current_delay_multiplier = min(self.current_delay_multiplier, 5.0)
                logger.warning(f"⚠️ Detected issues - slowing down (multiplier: {self.current_delay_multiplier:.1f}x)")

        else:
            # Decrease detection score on success
            if self.detection_score > 0:
                self.detection_score -= 0.5

            # Speed up gradually if no issues
            if self.detection_score == 0 and self.current_delay_multiplier > 1.0:
                self.current_delay_multiplier *= 0.95
                self.current_delay_multiplier = max(self.current_delay_multiplier, 1.0)

    def record_captcha(self):
        """Record captcha detection (severe)"""
        self.detection_score += 5
        self.current_delay_multiplier *= 2.0
        self.current_delay_multiplier = min(self.current_delay_multiplier, 10.0)
        logger.error(f"🚨 Captcha detected - significantly slowing down (multiplier: {self.current_delay_multiplier:.1f}x)")

    def record_rate_limit(self):
        """Record rate limit hit"""
        self.detection_score += 3
        self.current_delay_multiplier *= 1.8
        self.current_delay_multiplier = min(self.current_delay_multiplier, 8.0)
        logger.warning(f"⚠️ Rate limit hit - slowing down (multiplier: {self.current_delay_multiplier:.1f}x)")

    def get_stats(self) -> Dict:
        """Get rate limiter statistics"""
        self._cleanup_old_requests()

        return {
            "total_requests": self.total_requests,
            "total_wait_time_seconds": self.total_wait_time,
            "requests_last_minute": len(self.requests_minute),
            "requests_last_hour": len(self.requests_hour),
            "requests_last_day": len(self.requests_day),
            "detection_score": self.detection_score,
            "current_delay_multiplier": self.current_delay_multiplier,
            "limits": {
                "per_minute": self.max_requests_per_minute,
                "per_hour": self.max_requests_per_hour,
                "per_day": self.max_requests_per_day
            }
        }

    def reset(self):
        """Reset rate limiter"""
        self.requests_minute.clear()
        self.requests_hour.clear()
        self.requests_day.clear()
        self.detection_score = 0
        self.current_delay_multiplier = 1.0
        logger.info("🔄 Rate limiter reset")


# Global rate limiter instance
global_rate_limiter = SmartRateLimiter(
    max_requests_per_minute=8,
    max_requests_per_hour=200,
    max_requests_per_day=1500,
    adaptive=True,
    randomize_delays=True
)


if __name__ == "__main__":
    # Test rate limiter
    async def test():
        limiter = SmartRateLimiter(
            max_requests_per_minute=5,
            max_requests_per_hour=20,
            adaptive=True
        )

        print("🚦 Testing Smart Rate Limiter\n")

        # Simulate requests
        for i in range(10):
            print(f"\n📤 Request {i+1}")

            wait_time = await limiter.wait_if_needed()
            if wait_time > 0:
                print(f"   ⏳ Waited {wait_time:.2f}s")

            # Simulate request
            success = random.random() > 0.2  # 80% success rate
            limiter.record_request(success)

            if not success:
                print("   ❌ Request failed")
            else:
                print("   ✅ Request success")

            # Stats
            stats = limiter.get_stats()
            print(f"   📊 Stats:")
            print(f"      - Requests last minute: {stats['requests_last_minute']}")
            print(f"      - Detection score: {stats['detection_score']}")
            print(f"      - Delay multiplier: {stats['current_delay_multiplier']:.2f}x")

        print("\n✅ Rate limiter test complete!")

    asyncio.run(test())
