import os
from enum import StrEnum

from cryptography.hazmat.primitives.keywrap import (
    InvalidUnwrap,
    aes_key_unwrap,
    aes_key_wrap,
)

from app.core.exceptions import CryptoError

KEY_SIZE_BYTES: int = 32  # 256 bits for AES-256
WRAPPED_KEY_SIZE_BYTES: int = 40  # 32 bytes + 8 bytes RFC 3394 ICV


class KeyLifecycleState(StrEnum):
    """Lifecycle state of a Key Encryption Key (KEK)."""

    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"
    REVOKED = "REVOKED"


def zeroize_bytes(buffer: bytearray) -> None:
    """Securely overwrite a mutable bytearray in RAM with zeros.

    Args:
        buffer: Mutable bytearray containing sensitive key material.
    """
    for i in range(len(buffer)):
        buffer[i] = 0


def generate_dek() -> bytes:
    """Generate a random 256-bit (32-byte) Data Encryption Key (DEK).

    Returns:
        bytes: 32 cryptographically secure random bytes from OS entropy.
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
        wrapped_dek: RFC 3394 wrapped DEK payload (40 bytes).
        kek: 32-byte Master Key.

    Returns:
        bytes: 32-byte recovered plaintext DEK.

    Raises:
        CryptoError: If key unwrap integrity check fails (tampered wrapped key or wrong KEK).
    """
    if len(kek) != KEY_SIZE_BYTES:
        raise CryptoError(f"KEK size must be {KEY_SIZE_BYTES} bytes, got {len(kek)}.")
    if len(wrapped_dek) != WRAPPED_KEY_SIZE_BYTES:
        raise CryptoError(
            f"Wrapped DEK payload must be {WRAPPED_KEY_SIZE_BYTES} bytes, got {len(wrapped_dek)}."
        )

    try:
        dek = aes_key_unwrap(kek, wrapped_dek)
        if len(dek) != KEY_SIZE_BYTES:
            raise CryptoError("Unwrapped DEK length mismatch.")
        return dek
    except InvalidUnwrap as e:
        raise CryptoError("Key unwrap integrity check failed (invalid KEK or tampered key).") from e
    except Exception as e:
        raise CryptoError("Failed to unwrap Data Encryption Key.") from e


class KeyManager:
    """Manages Key Encryption Key (KEK) versions, DEK wrapping, and key rotation."""

    def __init__(self, primary_kek: bytes, primary_version: str = "v1") -> None:
        if len(primary_kek) != KEY_SIZE_BYTES:
            raise CryptoError(
                f"Primary KEK must be {KEY_SIZE_BYTES} bytes, got {len(primary_kek)}."
            )
        self._keys: dict[str, bytes] = {primary_version: primary_kek}
        self._states: dict[str, KeyLifecycleState] = {primary_version: KeyLifecycleState.ACTIVE}
        self._primary_version: str = primary_version

    @property
    def primary_version(self) -> str:
        return self._primary_version

    def register_kek_version(
        self,
        kek: bytes,
        version: str,
        state: KeyLifecycleState = KeyLifecycleState.ACTIVE,
        set_primary: bool = False,
    ) -> None:
        """Register an additional KEK version for historical unwrapping or rotation."""
        if len(kek) != KEY_SIZE_BYTES:
            raise CryptoError(f"KEK must be {KEY_SIZE_BYTES} bytes, got {len(kek)}.")
        self._keys[version] = kek
        self._states[version] = state
        if set_primary:
            self._primary_version = version

    def get_kek(self, version: str) -> bytes:
        """Retrieve KEK bytes by version identifier."""
        if version not in self._keys:
            raise CryptoError(f"KEK version '{version}' is not registered.")
        if self._states.get(version) == KeyLifecycleState.REVOKED:
            raise CryptoError(f"KEK version '{version}' is revoked and cannot be used.")
        return self._keys[version]

    def generate_and_wrap_dek(
        self,
        version: str | None = None,
    ) -> tuple[bytes, bytes, str]:
        """Generate a fresh DEK and wrap it under the target KEK version.

        Args:
            version: Optional KEK version (defaults to primary active version).

        Returns:
            Tuple[bytes, bytes, str]: (plaintext_dek, wrapped_dek, key_version_used)
        """
        target_version = version or self._primary_version
        kek = self.get_kek(target_version)
        dek = generate_dek()
        wrapped = wrap_dek(dek, kek)
        return dek, wrapped, target_version

    def unwrap_dek(self, wrapped_dek: bytes, version: str) -> bytes:
        """Unwrap a DEK using the specified KEK version."""
        kek = self.get_kek(version)
        return unwrap_dek(wrapped_dek, kek)

    def rotate_wrapped_dek(
        self,
        wrapped_dek: bytes,
        current_version: str,
        target_version: str | None = None,
    ) -> tuple[bytes, str]:
        """Rotate a wrapped DEK from an older KEK version to a newer KEK version.

        Args:
            wrapped_dek: Existing wrapped DEK.
            current_version: KEK version used previously.
            target_version: New KEK version (defaults to primary active version).

        Returns:
            Tuple[bytes, str]: (new_wrapped_dek, target_version)
        """
        new_version = target_version or self._primary_version
        if current_version == new_version:
            return wrapped_dek, current_version

        # 1. Unwrap with old KEK
        old_kek = self.get_kek(current_version)
        dek = unwrap_dek(wrapped_dek, old_kek)

        # 2. Re-wrap with new KEK
        new_kek = self.get_kek(new_version)
        new_wrapped = wrap_dek(dek, new_kek)
        return new_wrapped, new_version
