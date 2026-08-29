import pytest

from app.core.exceptions import CryptoError
from app.crypto.keys import (
    KeyLifecycleState,
    KeyManager,
    generate_dek,
    zeroize_bytes,
)


@pytest.mark.unit
def test_key_manager_initialization() -> None:
    """Verify KeyManager initializes with primary active version."""
    kek = generate_dek()
    km = KeyManager(primary_kek=kek, primary_version="v1")
    assert km.primary_version == "v1"
    assert km.get_kek("v1") == kek


@pytest.mark.unit
def test_key_manager_generate_and_wrap_dek() -> None:
    """Verify generate_and_wrap_dek produces valid DEK and wrapped representation."""
    kek = generate_dek()
    km = KeyManager(primary_kek=kek, primary_version="v1")

    plaintext_dek, wrapped_dek, version = km.generate_and_wrap_dek()
    assert len(plaintext_dek) == 32
    assert len(wrapped_dek) == 40
    assert version == "v1"

    unwrapped = km.unwrap_dek(wrapped_dek, version)
    assert unwrapped == plaintext_dek


@pytest.mark.unit
def test_key_manager_multi_version_and_rotation() -> None:
    """Verify key rotation re-wraps DEKs under a new KEK version successfully."""
    kek_v1 = generate_dek()
    kek_v2 = generate_dek()

    km = KeyManager(primary_kek=kek_v1, primary_version="v1")
    km.register_kek_version(kek_v2, version="v2", state=KeyLifecycleState.ACTIVE, set_primary=True)

    assert km.primary_version == "v2"

    # Generate a DEK under old v1
    orig_dek, wrapped_v1, _ = km.generate_and_wrap_dek(version="v1")

    # Rotate to v2
    wrapped_v2, new_version = km.rotate_wrapped_dek(
        wrapped_dek=wrapped_v1,
        current_version="v1",
        target_version="v2",
    )
    assert new_version == "v2"
    assert wrapped_v2 != wrapped_v1

    # Verify that unwrapping wrapped_v2 recovers the original DEK
    recovered_dek = km.unwrap_dek(wrapped_v2, "v2")
    assert recovered_dek == orig_dek


@pytest.mark.unit
def test_key_manager_revoked_key_rejection() -> None:
    """Attempting to use a revoked KEK version must raise CryptoError."""
    kek = generate_dek()
    km = KeyManager(primary_kek=kek, primary_version="v1")
    km.register_kek_version(
        generate_dek(),
        version="compromised_v0",
        state=KeyLifecycleState.REVOKED,
    )

    with pytest.raises(CryptoError, match="revoked and cannot be used"):
        km.get_kek("compromised_v0")


@pytest.mark.unit
def test_zeroize_bytes() -> None:
    """Verify zeroize_bytes overwrites buffer contents in memory."""
    secret = bytearray(b"HighlyConfidentialSecret12345678")
    assert any(b != 0 for b in secret)

    zeroize_bytes(secret)
    assert all(b == 0 for b in secret)
