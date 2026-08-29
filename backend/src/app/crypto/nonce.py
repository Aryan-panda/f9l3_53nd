import os

from app.core.exceptions import CryptoError

NONCE_SIZE_BYTES: int = 12  # 96-bit standard nonce for AES-GCM (NIST SP 800-38D)


def generate_nonce(size: int = NONCE_SIZE_BYTES) -> bytes:
    """Generate a cryptographically secure random nonce of specified length.

    Args:
        size: Size in bytes (default 12 bytes / 96 bits for AES-GCM).

    Returns:
        bytes: Cryptographically secure random bytes from OS entropy.
    """
    if size != NONCE_SIZE_BYTES:
        raise CryptoError(f"Invalid nonce size: expected {NONCE_SIZE_BYTES} bytes, got {size}.")
    return os.urandom(size)


def validate_nonce(nonce: bytes) -> None:
    """Validate that the provided nonce matches required length.

    Args:
        nonce: Nonce bytes to validate.

    Raises:
        CryptoError: If nonce is invalid or incorrect length.
    """
    if not isinstance(nonce, bytes):
        raise CryptoError("Nonce must be bytes.")
    if len(nonce) != NONCE_SIZE_BYTES:
        raise CryptoError(
            f"Invalid nonce length: expected {NONCE_SIZE_BYTES} bytes, got {len(nonce)}."
        )


class NonceTracker:
    """Helper tracker for verifying nonce uniqueness in test and runtime environments."""

    def __init__(self) -> None:
        self._seen_nonces: set[bytes] = set()

    def record_and_verify_unique(self, nonce: bytes) -> bool:
        """Record a nonce and return True if unique, False if duplicate detected."""
        validate_nonce(nonce)
        if nonce in self._seen_nonces:
            return False
        self._seen_nonces.add(nonce)
        return True

    def count(self) -> int:
        return len(self._seen_nonces)

    def clear(self) -> None:
        self._seen_nonces.clear()
