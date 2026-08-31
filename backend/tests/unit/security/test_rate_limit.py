import time

import pytest

from app.core.exceptions import RateLimitError
from app.security.rate_limit import InMemoryRateLimiter


@pytest.mark.unit
def test_rate_limiter_allows_under_capacity() -> None:
    """Verify rate limiter allows requests within capacity burst."""
    limiter = InMemoryRateLimiter(rate=1.0, capacity=3.0)
    key = "192.168.1.10:alice"

    assert limiter.allow_request(key) is True
    assert limiter.allow_request(key) is True
    assert limiter.allow_request(key) is True
    # 4th request exceeds burst capacity of 3
    assert limiter.allow_request(key) is False


@pytest.mark.unit
def test_rate_limiter_refills_over_time() -> None:
    """Verify tokens refill according to refill rate."""
    limiter = InMemoryRateLimiter(rate=10.0, capacity=2.0)
    key = "192.168.1.10:bob"

    assert limiter.allow_request(key) is True
    assert limiter.allow_request(key) is True
    assert limiter.allow_request(key) is False

    # Sleep 0.25s -> refills ~2.5 tokens
    time.sleep(0.25)
    assert limiter.allow_request(key) is True


@pytest.mark.unit
def test_rate_limiter_assert_raises_exception() -> None:
    """Verify assert_allowed raises RateLimitError when limit is exceeded."""
    limiter = InMemoryRateLimiter(rate=1.0, capacity=1.0)
    key = "192.168.1.50:admin"

    limiter.assert_allowed(key)
    with pytest.raises(RateLimitError, match="Too many requests"):
        limiter.assert_allowed(key)


@pytest.mark.unit
def test_upload_limiter_instance() -> None:
    """Verify global upload_limiter instance is initialized with burst capacity."""
    from app.security.rate_limit import upload_limiter

    upload_limiter.reset()
    user_id = "11111111-2222-3333-4444-555555555555"
    # Consumes capacity up to 15
    for _ in range(15):
        assert upload_limiter.allow_request(user_id) is True
    # 16th is rejected
    assert upload_limiter.allow_request(user_id) is False
    upload_limiter.reset()

