"""Cryptographic primitives and key management package for f9l3_53nd."""

from app.crypto.aead import AES256GCMCipher, build_canonical_aad
from app.crypto.envelope import (
    ALGORITHM_AES_256_GCM,
    CURRENT_PROTOCOL_VERSION,
    MAGIC_HEADER,
    TransferEnvelope,
    pack_envelope,
    unpack_envelope,
)
from app.crypto.hashing import (
    compute_buffer_sha256,
    compute_stream_sha256,
    verify_sha256_digest,
)
from app.crypto.keys import (
    KEY_SIZE_BYTES,
    KeyLifecycleState,
    KeyManager,
    generate_dek,
    unwrap_dek,
    wrap_dek,
    zeroize_bytes,
)
from app.crypto.nonce import generate_nonce
from app.crypto.wireguard import (
    WireGuardKeypair,
    generate_preshared_key,
    generate_wireguard_config,
    generate_wireguard_keypair,
)

__all__ = [
    "AES256GCMCipher",
    "build_canonical_aad",
    "compute_buffer_sha256",
    "compute_stream_sha256",
    "verify_sha256_digest",
    "generate_dek",
    "wrap_dek",
    "unwrap_dek",
    "zeroize_bytes",
    "KeyManager",
    "KeyLifecycleState",
    "generate_nonce",
    "KEY_SIZE_BYTES",
    "MAGIC_HEADER",
    "CURRENT_PROTOCOL_VERSION",
    "ALGORITHM_AES_256_GCM",
    "TransferEnvelope",
    "pack_envelope",
    "unpack_envelope",
    "WireGuardKeypair",
    "generate_wireguard_keypair",
    "generate_preshared_key",
    "generate_wireguard_config",
]
