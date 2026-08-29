import pytest

from app.core.exceptions import CryptoError
from app.crypto.nonce import (
    NONCE_SIZE_BYTES,
    NonceTracker,
    generate_nonce,
    validate_nonce,
)


@pytest.mark.unit
def test_generate_nonce_length() -> None:
    """Verify generated nonce is exactly 12 bytes (96 bits)."""
    nonce = generate_nonce()
    assert len(nonce) == NONCE_SIZE_BYTES
    validate_nonce(nonce)


@pytest.mark.unit
def test_nonce_uniqueness_sample() -> None:
    """Generate 5,000 nonces and verify zero collisions occur."""
    tracker = NonceTracker()
    for _ in range(5000):
        nonce = generate_nonce()
        is_unique = tracker.record_and_verify_unique(nonce)
        assert is_unique is True
    assert tracker.count() == 5000


@pytest.mark.unit
def test_validate_nonce_invalid_length() -> None:
    """Validate that invalid nonce lengths raise CryptoError."""
    with pytest.raises(CryptoError, match="Invalid nonce length"):
        validate_nonce(b"short-nonce")

    with pytest.raises(CryptoError, match="Invalid nonce length"):
        validate_nonce(b"16-byte-long-nonce!")


@pytest.mark.unit
def test_nonce_tracker_duplicate_detection() -> None:
    """Verify NonceTracker correctly flags duplicate nonces."""
    tracker = NonceTracker()
    nonce = generate_nonce()
    assert tracker.record_and_verify_unique(nonce) is True
    # Re-recording same nonce returns False
    assert tracker.record_and_verify_unique(nonce) is False
