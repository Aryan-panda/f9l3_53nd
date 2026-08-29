import struct
from dataclasses import dataclass

from app.core.exceptions import CryptoError

MAGIC_HEADER: bytes = b"F9L3"
CURRENT_PROTOCOL_VERSION: int = 1
ALGORITHM_AES_256_GCM: int = 1

# Header fixed prefix format:
# 4s: Magic ('F9L3')
# H:  Protocol Version (uint16)
# B:  Algorithm ID (uint8, 1 = AES-256-GCM)
# 12s: Nonce (12 bytes)
# 16s: Tag (16 bytes)
# H:  AAD Length (uint16)
HEADER_PREFIX_STRUCT = struct.Struct("!4s H B 12s 16s H")
HEADER_PREFIX_SIZE: int = HEADER_PREFIX_STRUCT.size  # 4 + 2 + 1 + 12 + 16 + 2 = 37 bytes

# Ciphertext length prefix struct (uint64)
CT_LEN_STRUCT = struct.Struct("!Q")
CT_LEN_SIZE: int = CT_LEN_STRUCT.size  # 8 bytes


@dataclass(frozen=True)
class TransferEnvelope:
    """Versioned transfer envelope containing encrypted payload and cryptographic metadata."""

    protocol_version: int
    algorithm_id: int
    nonce: bytes
    tag: bytes
    aad: bytes
    ciphertext: bytes


def pack_envelope(envelope: TransferEnvelope) -> bytes:
    """Serialize a TransferEnvelope into binary format.

    Args:
        envelope: TransferEnvelope instance.

    Returns:
        bytes: Packed binary envelope payload.
    """
    if len(envelope.nonce) != 12:
        raise CryptoError(f"Envelope nonce must be 12 bytes, got {len(envelope.nonce)}.")
    if len(envelope.tag) != 16:
        raise CryptoError(f"Envelope tag must be 16 bytes, got {len(envelope.tag)}.")

    aad_len = len(envelope.aad)
    if aad_len > 65535:
        raise CryptoError(f"AAD payload exceeds maximum 65535 bytes (got {aad_len}).")

    ct_len = len(envelope.ciphertext)

    prefix_bytes = HEADER_PREFIX_STRUCT.pack(
        MAGIC_HEADER,
        envelope.protocol_version,
        envelope.algorithm_id,
        envelope.nonce,
        envelope.tag,
        aad_len,
    )
    ct_len_bytes = CT_LEN_STRUCT.pack(ct_len)

    return prefix_bytes + envelope.aad + ct_len_bytes + envelope.ciphertext


def unpack_envelope(data: bytes) -> TransferEnvelope:
    """Parse and validate binary data into a TransferEnvelope instance.

    Args:
        data: Serialized envelope bytes.

    Returns:
        TransferEnvelope: Deserialized envelope.

    Raises:
        CryptoError: If header, magic, length, or data format is invalid.
    """
    if len(data) < HEADER_PREFIX_SIZE + CT_LEN_SIZE:
        raise CryptoError("Envelope binary data is truncated or too small.")

    magic, version, algo_id, nonce, tag, aad_len = HEADER_PREFIX_STRUCT.unpack_from(data, 0)

    if magic != MAGIC_HEADER:
        raise CryptoError(
            f"Invalid envelope magic header: expected {MAGIC_HEADER!r}, got {magic!r}."
        )

    if version != CURRENT_PROTOCOL_VERSION:
        raise CryptoError(f"Unsupported envelope protocol version: {version}.")

    if algo_id != ALGORITHM_AES_256_GCM:
        raise CryptoError(f"Unsupported envelope algorithm ID: {algo_id}.")

    offset = HEADER_PREFIX_SIZE
    if len(data) < offset + aad_len + CT_LEN_SIZE:
        raise CryptoError("Envelope payload truncated before AAD and CT length header.")

    aad = data[offset : offset + aad_len]
    offset += aad_len

    (ct_len,) = CT_LEN_STRUCT.unpack_from(data, offset)
    offset += CT_LEN_SIZE

    if len(data) < offset + ct_len:
        raise CryptoError(
            f"Envelope ciphertext truncated: expected {ct_len} bytes, "
            f"available {len(data) - offset}."
        )


    ciphertext = data[offset : offset + ct_len]

    return TransferEnvelope(
        protocol_version=version,
        algorithm_id=algo_id,
        nonce=nonce,
        tag=tag,
        aad=aad,
        ciphertext=ciphertext,
    )
