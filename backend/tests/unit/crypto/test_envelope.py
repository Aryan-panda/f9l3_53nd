import pytest

from app.core.exceptions import CryptoError
from app.crypto.envelope import (
    ALGORITHM_AES_256_GCM,
    CURRENT_PROTOCOL_VERSION,
    TransferEnvelope,
    pack_envelope,
    unpack_envelope,
)
from app.crypto.nonce import generate_nonce


@pytest.mark.unit
def test_envelope_packing_roundtrip() -> None:
    """Verify serialization and deserialization of a TransferEnvelope."""
    nonce = generate_nonce()
    tag = b"0123456789abcdef"
    aad = b"f9l3_v1|transfer-uuid-1234|sender-alice|recipient-bob|1024"
    ciphertext = b"Encrypted file binary contents..."

    envelope = TransferEnvelope(
        protocol_version=CURRENT_PROTOCOL_VERSION,
        algorithm_id=ALGORITHM_AES_256_GCM,
        nonce=nonce,
        tag=tag,
        aad=aad,
        ciphertext=ciphertext,
    )

    packed_bytes = pack_envelope(envelope)
    assert packed_bytes.startswith(b"F9L3")

    unpacked = unpack_envelope(packed_bytes)
    assert unpacked.protocol_version == CURRENT_PROTOCOL_VERSION
    assert unpacked.algorithm_id == ALGORITHM_AES_256_GCM
    assert unpacked.nonce == nonce
    assert unpacked.tag == tag
    assert unpacked.aad == aad
    assert unpacked.ciphertext == ciphertext


@pytest.mark.unit
def test_envelope_invalid_magic_header_rejection() -> None:
    """Tampering with magic bytes must raise CryptoError."""
    envelope = TransferEnvelope(
        protocol_version=1,
        algorithm_id=1,
        nonce=generate_nonce(),
        tag=b"0123456789abcdef",
        aad=b"test-aad",
        ciphertext=b"ciphertext",
    )
    packed = bytearray(pack_envelope(envelope))
    packed[0:4] = b"XXXX"

    with pytest.raises(CryptoError, match="Invalid envelope magic header"):
        unpack_envelope(bytes(packed))


@pytest.mark.unit
def test_envelope_truncated_data_rejection() -> None:
    """Truncating envelope bytes must raise CryptoError."""
    envelope = TransferEnvelope(
        protocol_version=1,
        algorithm_id=1,
        nonce=generate_nonce(),
        tag=b"0123456789abcdef",
        aad=b"test-aad",
        ciphertext=b"ciphertext",
    )
    packed = pack_envelope(envelope)

    with pytest.raises(CryptoError, match="truncated or too small"):
        unpack_envelope(packed[:10])

    with pytest.raises(CryptoError, match="ciphertext truncated"):
        unpack_envelope(packed[:-5])
