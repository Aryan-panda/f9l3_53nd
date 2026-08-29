from datetime import UTC, datetime

import pytest

from app.security.sessions import (
    compute_session_expiry,
    generate_session_token,
    hash_session_token,
)


@pytest.mark.unit
def test_generate_session_token_format() -> None:
    """Verify session token is 256-bit URL-safe string."""
    t1 = generate_session_token()
    t2 = generate_session_token()

    assert len(t1) >= 43
    assert t1 != t2


@pytest.mark.unit
def test_hash_session_token_sha256() -> None:
    """Verify session token hashing produces 64-char hex SHA-256 digest."""
    token = "abcdefghijklmnopqrstuvwxyz0123456789-_"
    h1 = hash_session_token(token)
    h2 = hash_session_token(token)

    assert len(h1) == 64
    assert h1 == h2
    assert h1 != token


@pytest.mark.unit
def test_compute_session_expiry() -> None:
    """Verify session expiration timestamp calculation."""
    now = datetime.now(UTC)
    expiry = compute_session_expiry(seconds=3600)

    delta = (expiry - now).total_seconds()
    assert 3590 < delta < 3610
