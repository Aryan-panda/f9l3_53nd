import os

from cryptography.hazmat.primitives.keywrap import (
    InvalidUnwrap,
    aes_key_unwrap,
    aes_key_wrap,
)

from app.core.exceptions import CryptoError

KEY_SIZE_BYTES: int = 32  # 256 bits


def generate_dek() -> bytes:
    """Generate a random 256-bit (32-byte) Data Encryption Key (DEK).

    Returns:
        bytes: 32 cryptographically secure random bytes.
    """
    return os.urandom(KEY_SIZE_BYTES)


def parse_kek_from_hex(kek_hex: str) -> bytes:
    """Parse and validate a 256-bit Master Key (KEK) from a 64-character hex string.

    Args:
        kek_hex: 64-character hexadecimal representation of 32-byte AES key.

    Returns:
        bytes: 32-byte KEK.
    """
    clean_hex = kek_hex.strip()
    if len(clean_hex) != 64:
        raise CryptoError(
            f"Master Key hex length must be exactly 64 characters (256 bits), got {len(clean_hex)}."
        )
    try:
        kek_bytes = bytes.fromhex(clean_hex)
    except ValueError as e:
        raise CryptoError("Master Key contains invalid non-hexadecimal characters.") from e

    if len(kek_bytes) != KEY_SIZE_BYTES:
        raise CryptoError(f"Master Key must be 32 bytes, got {len(kek_bytes)}.")
    return kek_bytes


def wrap_dek(dek: bytes, kek: bytes) -> bytes:
    """Wrap an ephemeral Data Encryption Key using the Master Key via RFC 3394 AES Key Wrap.

    Args:
        dek: 32-byte plaintext DEK to wrap.
        kek: 32-byte Master Key (Key Encryption Key).

    Returns:
        bytes: 40-byte RFC 3394 wrapped DEK payload (includes 8-byte integrity check value).
    """
    if len(dek) != KEY_SIZE_BYTES:
        raise CryptoError(f"DEK size must be {KEY_SIZE_BYTES} bytes, got {len(dek)}.")
    if len(kek) != KEY_SIZE_BYTES:
        raise CryptoError(f"KEK size must be {KEY_SIZE_BYTES} bytes, got {len(kek)}.")

    try:
        return aes_key_wrap(kek, dek)
    except Exception as e:
        raise CryptoError("Failed to wrap Data Encryption Key.") from e


def unwrap_dek(wrapped_dek: bytes, kek: bytes) -> bytes:
    """Unwrap a wrapped Data Encryption Key using the Master Key via RFC 3394.

    Args:
        wrapped_dek: RFC 3394 wrapped DEK payload (typically 40 bytes).
        kek: 32-byte Master Key.

    Returns:
        bytes: 32-byte recovered plaintext DEK.

    Raises:
        CryptoError: If key unwrap integrity check fails (tampered wrapped key or wrong KEK).
    """
    if len(kek) != KEY_SIZE_BYTES:
        raise CryptoError(f"KEK size must be {KEY_SIZE_BYTES} bytes, got {len(kek)}.")
    if len(wrapped_dek) < KEY_SIZE_BYTES + 8:
        raise CryptoError("Wrapped DEK payload is truncated or invalid.")

    try:
        dek = aes_key_unwrap(kek, wrapped_dek)
        if len(dek) != KEY_SIZE_BYTES:
            raise CryptoError("Unwrapped DEK length mismatch.")
        return dek
    except InvalidUnwrap as e:
        raise CryptoError("Key unwrap integrity check failed (invalid KEK or tampered key).") from e
    except Exception as e:
        raise CryptoError("Failed to unwrap Data Encryption Key.") from e
