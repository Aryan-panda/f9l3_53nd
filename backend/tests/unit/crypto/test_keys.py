import pytest

from app.core.exceptions import CryptoError
from app.crypto.keys import (
    generate_dek,
    parse_kek_from_hex,
    unwrap_dek,
    wrap_dek,
)


@pytest.mark.unit
def test_generate_dek_properties() -> None:
    """Verify generated DEK is 32 bytes (256 bits) and unique."""
    dek1 = generate_dek()
    dek2 = generate_dek()
    assert len(dek1) == 32
    assert len(dek2) == 32
    assert dek1 != dek2


@pytest.mark.unit
def test_parse_kek_from_hex() -> None:
    """Verify parsing valid and invalid 64-char hex strings."""
    valid_hex = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
    kek = parse_kek_from_hex(valid_hex)
    assert len(kek) == 32

    # Invalid length
    with pytest.raises(CryptoError, match="must be exactly 64 characters"):
        parse_kek_from_hex("000102")

    # Invalid non-hex characters
    with pytest.raises(CryptoError, match="invalid non-hexadecimal"):
        parse_kek_from_hex("zz" * 32)


@pytest.mark.unit
def test_rfc3394_key_wrap_roundtrip() -> None:
    """Verify RFC 3394 AES Key Wrap and unwrap roundtrip."""
    kek = generate_dek()
    dek = generate_dek()

    wrapped_dek = wrap_dek(dek, kek)
    # 32-byte key wrapped via RFC 3394 produces 40 bytes (32 bytes + 8 bytes ICV)
    assert len(wrapped_dek) == 40
    assert wrapped_dek != dek

    unwrapped_dek = unwrap_dek(wrapped_dek, kek)
    assert unwrapped_dek == dek


@pytest.mark.unit
def test_key_unwrap_wrong_kek_rejection() -> None:
    """Attempting to unwrap with incorrect KEK must fail with CryptoError."""
    kek1 = generate_dek()
    kek2 = generate_dek()
    dek = generate_dek()

    wrapped_dek = wrap_dek(dek, kek1)

    with pytest.raises(CryptoError, match="integrity check failed"):
        unwrap_dek(wrapped_dek, kek2)


@pytest.mark.unit
def test_key_unwrap_tampered_bytes_rejection() -> None:
    """Modifying 1 byte of wrapped DEK payload must fail unwrap integrity."""
    kek = generate_dek()
    dek = generate_dek()

    wrapped_dek = wrap_dek(dek, kek)
    corrupted = bytearray(wrapped_dek)
    corrupted[0] ^= 0x55

    with pytest.raises(CryptoError, match="integrity check failed"):
        unwrap_dek(bytes(corrupted), kek)
