import io

import pytest

from app.core.exceptions import IntegrityError
from app.crypto.hashing import (
    assert_sha256_integrity,
    compute_buffer_sha256,
    compute_stream_sha256,
    verify_sha256_digest,
)


@pytest.mark.unit
def test_sha256_known_vectors() -> None:
    """Verify SHA-256 implementation against standard NIST FIPS 180-4 test vectors."""
    # Vector 1: Empty string
    empty_digest = compute_buffer_sha256(b"")
    assert empty_digest == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    # Vector 2: 'abc'
    abc_digest = compute_buffer_sha256(b"abc")
    assert abc_digest == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


@pytest.mark.unit
def test_sha256_stream_matches_buffer() -> None:
    """Ensure streaming hashing matches buffer hashing exactly."""
    payload = b"Streaming file chunk test buffer with various byte patterns 1234567890"
    stream = io.BytesIO(payload)

    buffer_digest = compute_buffer_sha256(payload)
    stream_digest = compute_stream_sha256(stream, chunk_size=16)

    assert buffer_digest == stream_digest


@pytest.mark.unit
def test_sha256_digest_verification_positive() -> None:
    """Verify constant-time equality check for identical digests."""
    digest = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert verify_sha256_digest(digest, digest) is True
    assert verify_sha256_digest(digest.upper(), digest.lower()) is True


@pytest.mark.unit
def test_sha256_digest_verification_negative() -> None:
    """Verify that a 1-character difference returns False."""
    digest1 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    # Flip last character 'd' -> 'e'
    digest2 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ae"

    assert verify_sha256_digest(digest1, digest2) is False


@pytest.mark.unit
def test_assert_sha256_integrity_raises_on_mismatch() -> None:
    """Verify assert_sha256_integrity throws IntegrityError on digest mismatch."""
    d1 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    d2 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"

    with pytest.raises(IntegrityError, match="File integrity mismatch"):
        assert_sha256_integrity(d1, d2)
