import time
from dataclasses import dataclass
from threading import Lock

from app.core.exceptions import RateLimitError


@dataclass
class Bucket:
    tokens: float
    last_updated: float


class InMemoryRateLimiter:
    """Thread-safe Token Bucket rate limiter for API endpoints."""

    def __init__(self, rate: float = 5.0, capacity: float = 10.0) -> None:
        """Initialize Token Bucket rate limiter.

        Args:
            rate: Token refill rate in tokens per second.
            capacity: Maximum burst capacity (tokens).
        """
        self.rate = rate
        self.capacity = capacity
        self._buckets: dict[str, Bucket] = {}
        self._lock = Lock()

    def allow_request(self, key: str, cost: float = 1.0) -> bool:
        """Check if request for given key is allowed and consume token.

        Args:
            key: Rate-limiting identifier (e.g. client IP or username:IP).
            cost: Number of tokens consumed per request.

        Returns:
            bool: True if allowed, False if rate limit exceeded.
        """
        now = time.monotonic()
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = Bucket(tokens=self.capacity, last_updated=now)

            bucket = self._buckets[key]
            # Refill tokens based on elapsed time
            elapsed = now - bucket.last_updated
            bucket.tokens = min(self.capacity, bucket.tokens + (elapsed * self.rate))
            bucket.last_updated = now

            if bucket.tokens >= cost:
                bucket.tokens -= cost
                return True
            return False

    def assert_allowed(self, key: str, cost: float = 1.0) -> None:
        """Assert rate limit is not exceeded, raising RateLimitError if exceeded."""
        if not self.allow_request(key, cost):
            raise RateLimitError("Too many requests. Please slow down and try again later.")

    def reset(self) -> None:
        """Clear all stored rate limit buckets (useful for tests)."""
        with self._lock:
            self._buckets.clear()


# Default login limiter: 5 attempts per minute sustained, burst of 10
login_limiter = InMemoryRateLimiter(rate=5.0 / 60.0, capacity=10.0)

# Default upload limiter: 10 uploads per minute sustained, burst of 15
upload_limiter = InMemoryRateLimiter(rate=10.0 / 60.0, capacity=15.0)

