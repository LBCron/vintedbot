"""
Circuit Breaker Pattern for Vinted API calls
Prevents cascading failures when Vinted is down or rate-limiting
"""
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps
import asyncio
from loguru import logger


class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failures detected, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Testing recovery, allow limited requests

    Configuration:
    - failure_threshold: Number of failures before opening circuit
    - recovery_timeout: Seconds to wait before attempting recovery
    - success_threshold: Successful calls needed to close circuit from half-open
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        timeout: int = 30
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.timeout = timeout

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()

        logger.info(f"Circuit breaker '{name}' initialized with threshold={failure_threshold}")

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.state != CircuitState.OPEN:
            return False

        if self.last_failure_time is None:
            return False

        time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout

    def _record_success(self):
        """Record successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(f"Circuit breaker '{self.name}': success {self.success_count}/{self.success_threshold}")

            if self.success_count >= self.success_threshold:
                self._close_circuit()
        else:
            # Reset failure count on success
            self.failure_count = 0

    def _record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        logger.warning(
            f"Circuit breaker '{self.name}': failure {self.failure_count}/{self.failure_threshold}"
        )

        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery attempt, reopen circuit
            self._open_circuit()
        elif self.failure_count >= self.failure_threshold:
            self._open_circuit()

    def _open_circuit(self):
        """Open circuit (reject requests)"""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
        self.success_count = 0

        logger.error(
            f"Circuit breaker '{self.name}' OPENED after {self.failure_count} failures. "
            f"Will attempt recovery in {self.recovery_timeout}s"
        )

    def _close_circuit(self):
        """Close circuit (normal operation)"""
        self.state = CircuitState.CLOSED
        self.last_state_change = datetime.now()
        self.failure_count = 0
        self.success_count = 0

        logger.info(f"Circuit breaker '{self.name}' CLOSED - service recovered")

    def _half_open_circuit(self):
        """Half-open circuit (testing recovery)"""
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = datetime.now()
        self.success_count = 0

        logger.info(f"Circuit breaker '{self.name}' HALF-OPEN - testing recovery")

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection"""

        # Check if we should attempt recovery
        if self._should_attempt_reset():
            self._half_open_circuit()

        # Reject if circuit is open
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable. Retry after {self.recovery_timeout}s"
            )

        try:
            # Execute function with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout
            )
            self._record_success()
            return result

        except asyncio.TimeoutError:
            logger.error(f"Circuit breaker '{self.name}': call timed out after {self.timeout}s")
            self._record_failure()
            raise

        except Exception as e:
            logger.error(f"Circuit breaker '{self.name}': call failed with {type(e).__name__}: {e}")
            self._record_failure()
            raise

    def call_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Execute sync function with circuit breaker protection"""

        # Check if we should attempt recovery
        if self._should_attempt_reset():
            self._half_open_circuit()

        # Reject if circuit is open
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable. Retry after {self.recovery_timeout}s"
            )

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result

        except Exception as e:
            logger.error(f"Circuit breaker '{self.name}': call failed with {type(e).__name__}: {e}")
            self._record_failure()
            raise

    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "recovery_timeout": self.recovery_timeout
        }


def circuit_breaker_decorator(breaker: CircuitBreaker):
    """Decorator to apply circuit breaker to async functions"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call_async(func, *args, **kwargs)
        return wrapper
    return decorator


# Global circuit breakers for different services
vinted_api_breaker = CircuitBreaker(
    name="vinted_api",
    failure_threshold=5,
    recovery_timeout=60,
    success_threshold=2,
    timeout=30
)

playwright_breaker = CircuitBreaker(
    name="playwright",
    failure_threshold=3,
    recovery_timeout=120,
    success_threshold=2,
    timeout=60
)

openai_breaker = CircuitBreaker(
    name="openai",
    failure_threshold=5,
    recovery_timeout=30,
    success_threshold=2,
    timeout=60
)


def get_all_circuit_states() -> dict:
    """Get state of all circuit breakers"""
    return {
        "vinted_api": vinted_api_breaker.get_state(),
        "playwright": playwright_breaker.get_state(),
        "openai": openai_breaker.get_state()
    }
