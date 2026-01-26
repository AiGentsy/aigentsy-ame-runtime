"""
RATE LIMITER: Per-Host Token Bucket Rate Limiting

Features:
- Token bucket algorithm
- Per-host rate limits
- Configurable defaults
- Burst handling
"""

import asyncio
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    tokens: float
    last_update: float
    rate: float  # tokens per second
    capacity: float  # max tokens


# Default rate limits per host
DEFAULT_RATES: Dict[str, Dict] = {
    # High rate (1 req/s)
    'hackernews.ycombinator.com': {'rate': 1.0, 'capacity': 5},
    'news.ycombinator.com': {'rate': 1.0, 'capacity': 5},

    # Medium rate (0.5 req/s)
    'reddit.com': {'rate': 0.5, 'capacity': 3},
    'www.reddit.com': {'rate': 0.5, 'capacity': 3},
    'old.reddit.com': {'rate': 0.5, 'capacity': 3},
    'twitter.com': {'rate': 0.5, 'capacity': 3},
    'x.com': {'rate': 0.5, 'capacity': 3},
    'linkedin.com': {'rate': 0.3, 'capacity': 2},
    'www.linkedin.com': {'rate': 0.3, 'capacity': 2},

    # Lower rate for sensitive platforms
    'github.com': {'rate': 0.5, 'capacity': 3},
    'api.github.com': {'rate': 0.5, 'capacity': 5},

    # Job boards (respect TOS)
    'upwork.com': {'rate': 0.2, 'capacity': 2},
    'www.upwork.com': {'rate': 0.2, 'capacity': 2},
    'freelancer.com': {'rate': 0.2, 'capacity': 2},
    'www.freelancer.com': {'rate': 0.2, 'capacity': 2},
    'fiverr.com': {'rate': 0.2, 'capacity': 2},
    'www.fiverr.com': {'rate': 0.2, 'capacity': 2},

    # Government sites (be very respectful)
    'regulations.gov': {'rate': 0.1, 'capacity': 1},
    'www.regulations.gov': {'rate': 0.1, 'capacity': 1},
    'grants.gov': {'rate': 0.1, 'capacity': 1},
    'www.grants.gov': {'rate': 0.1, 'capacity': 1},
}


class RateLimiter:
    """
    Per-host token bucket rate limiter.

    Features:
    - Configurable per-host rates
    - Burst capacity
    - Async waiting
    """

    DEFAULT_RATE = 0.5  # requests per second
    DEFAULT_CAPACITY = 3  # burst capacity

    def __init__(
        self,
        default_rate: Optional[float] = None,
        default_capacity: Optional[float] = None,
        host_rates: Optional[Dict[str, Dict]] = None
    ):
        self.default_rate = default_rate or self.DEFAULT_RATE
        self.default_capacity = default_capacity or self.DEFAULT_CAPACITY
        self.host_rates = host_rates or DEFAULT_RATES

        self.buckets: Dict[str, TokenBucket] = {}
        self.stats = {
            'requests': 0,
            'waited': 0,
            'total_wait_time': 0.0,
        }
        self._lock = asyncio.Lock()

    def _get_bucket(self, host: str) -> TokenBucket:
        """Get or create token bucket for host"""
        if host not in self.buckets:
            config = self.host_rates.get(host, {})
            rate = config.get('rate', self.default_rate)
            capacity = config.get('capacity', self.default_capacity)

            self.buckets[host] = TokenBucket(
                tokens=capacity,  # Start full
                last_update=time.time(),
                rate=rate,
                capacity=capacity,
            )

        return self.buckets[host]

    def _refill(self, bucket: TokenBucket):
        """Refill bucket based on elapsed time"""
        now = time.time()
        elapsed = now - bucket.last_update

        # Add tokens based on elapsed time
        bucket.tokens = min(
            bucket.capacity,
            bucket.tokens + elapsed * bucket.rate
        )
        bucket.last_update = now

    async def acquire(self, host: str, tokens: float = 1.0) -> float:
        """
        Acquire tokens from bucket, waiting if necessary.

        Returns wait time in seconds.
        """
        async with self._lock:
            self.stats['requests'] += 1
            bucket = self._get_bucket(host)
            self._refill(bucket)

            if bucket.tokens >= tokens:
                # Have enough tokens
                bucket.tokens -= tokens
                return 0.0

            # Need to wait
            wait_time = (tokens - bucket.tokens) / bucket.rate
            self.stats['waited'] += 1
            self.stats['total_wait_time'] += wait_time

        # Wait outside lock
        if wait_time > 0:
            logger.debug(f"[rate_limit] Waiting {wait_time:.2f}s for {host}")
            await asyncio.sleep(wait_time)

        # Deduct tokens after wait
        async with self._lock:
            bucket = self._get_bucket(host)
            self._refill(bucket)
            bucket.tokens -= tokens

        return wait_time

    async def try_acquire(self, host: str, tokens: float = 1.0) -> bool:
        """
        Try to acquire tokens without waiting.

        Returns True if tokens were acquired.
        """
        async with self._lock:
            bucket = self._get_bucket(host)
            self._refill(bucket)

            if bucket.tokens >= tokens:
                bucket.tokens -= tokens
                return True

            return False

    def get_wait_time(self, host: str, tokens: float = 1.0) -> float:
        """Get estimated wait time without acquiring"""
        bucket = self._get_bucket(host)
        self._refill(bucket)

        if bucket.tokens >= tokens:
            return 0.0

        return (tokens - bucket.tokens) / bucket.rate

    def set_rate(self, host: str, rate: float, capacity: Optional[float] = None):
        """Set rate limit for specific host"""
        self.host_rates[host] = {
            'rate': rate,
            'capacity': capacity or self.default_capacity,
        }
        # Reset bucket
        if host in self.buckets:
            del self.buckets[host]

    def get_stats(self) -> Dict:
        """Get rate limiter stats"""
        return {
            **self.stats,
            'avg_wait_time': (
                self.stats['total_wait_time'] / max(1, self.stats['waited'])
            ),
            'hosts_tracked': len(self.buckets),
        }


# Singleton
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
