"""
RETRY: Exponential Backoff Retry Logic

Features:
- Configurable retry attempts
- Exponential backoff with jitter
- Exception filtering
- Circuit breaker integration
"""

import asyncio
import logging
import random
import time
import functools
from typing import Optional, Callable, Type, Tuple, Any, List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: float = 0.1  # 10% jitter
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    non_retryable_exceptions: Tuple[Type[Exception], ...] = ()


class RetryStats:
    """Track retry statistics"""

    def __init__(self):
        self.attempts = 0
        self.successes = 0
        self.failures = 0
        self.retries = 0
        self.total_delay = 0.0

    def to_dict(self) -> Dict:
        return {
            'attempts': self.attempts,
            'successes': self.successes,
            'failures': self.failures,
            'retries': self.retries,
            'total_delay': self.total_delay,
            'success_rate': self.successes / max(1, self.attempts),
        }


# Global stats
_retry_stats = RetryStats()


def get_retry_stats() -> Dict:
    """Get global retry statistics"""
    return _retry_stats.to_dict()


def calculate_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """Calculate delay with exponential backoff and jitter"""
    # Exponential backoff
    delay = config.base_delay * (config.exponential_base ** attempt)

    # Apply max delay cap
    delay = min(delay, config.max_delay)

    # Add jitter (-jitter to +jitter)
    jitter_range = delay * config.jitter
    delay += random.uniform(-jitter_range, jitter_range)

    return max(0, delay)


def is_retryable(
    exception: Exception,
    config: RetryConfig
) -> bool:
    """Check if exception should trigger retry"""
    # Check non-retryable first
    if config.non_retryable_exceptions:
        if isinstance(exception, config.non_retryable_exceptions):
            return False

    # Check retryable
    return isinstance(exception, config.retryable_exceptions)


async def retry_with_backoff(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """
    Execute function with retry and exponential backoff.

    Args:
        func: Function to execute (sync or async)
        *args: Positional arguments for func
        config: Retry configuration
        **kwargs: Keyword arguments for func

    Returns:
        Function result

    Raises:
        Last exception if all retries exhausted
    """
    config = config or RetryConfig()
    last_exception = None

    for attempt in range(config.max_attempts):
        _retry_stats.attempts += 1

        try:
            # Execute function
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result

            _retry_stats.successes += 1
            return result

        except Exception as e:
            last_exception = e

            # Check if should retry
            if not is_retryable(e, config):
                logger.debug(f"[retry] Non-retryable exception: {type(e).__name__}")
                _retry_stats.failures += 1
                raise

            # Check if more attempts
            if attempt >= config.max_attempts - 1:
                logger.warning(
                    f"[retry] All {config.max_attempts} attempts exhausted: {e}"
                )
                _retry_stats.failures += 1
                raise

            # Calculate delay
            delay = calculate_delay(attempt, config)
            _retry_stats.retries += 1
            _retry_stats.total_delay += delay

            logger.debug(
                f"[retry] Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                f"Retrying in {delay:.2f}s"
            )

            await asyncio.sleep(delay)

    # Should not reach here
    if last_exception:
        raise last_exception


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    non_retryable_exceptions: Tuple[Type[Exception], ...] = (),
):
    """
    Decorator for retry with exponential backoff.

    Usage:
        @retry(max_attempts=3, base_delay=1.0)
        async def fetch_data():
            ...
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        retryable_exceptions=retryable_exceptions,
        non_retryable_exceptions=non_retryable_exceptions,
    )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_with_backoff(func, *args, config=config, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(
                retry_with_backoff(func, *args, config=config, **kwargs)
            )

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failing, requests rejected immediately
    - HALF_OPEN: Testing if service recovered
    """

    class State:
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_requests: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests

        self.state = self.State.CLOSED
        self.failures = 0
        self.last_failure_time = 0.0
        self.half_open_successes = 0

    def can_execute(self) -> bool:
        """Check if request can proceed"""
        if self.state == self.State.CLOSED:
            return True

        if self.state == self.State.OPEN:
            # Check if recovery timeout passed
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = self.State.HALF_OPEN
                self.half_open_successes = 0
                return True
            return False

        if self.state == self.State.HALF_OPEN:
            return self.half_open_successes < self.half_open_requests

        return False

    def record_success(self):
        """Record successful request"""
        if self.state == self.State.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_requests:
                self.state = self.State.CLOSED
                self.failures = 0

        elif self.state == self.State.CLOSED:
            self.failures = 0

    def record_failure(self):
        """Record failed request"""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.state == self.State.HALF_OPEN:
            self.state = self.State.OPEN

        elif self.state == self.State.CLOSED:
            if self.failures >= self.failure_threshold:
                self.state = self.State.OPEN

    def get_state(self) -> Dict:
        """Get circuit breaker state"""
        return {
            'state': self.state,
            'failures': self.failures,
            'last_failure_time': self.last_failure_time,
        }
