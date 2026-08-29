from uuid import UUID

from app.core.config import Settings, get_settings
from app.crypto.keys import KeyManager, parse_kek_from_hex
from app.schemas.key_reference import KeyReferenceCreate


class KeyService:
    """Application service for cryptographic key management, wrapping, and rotation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        primary_kek = parse_kek_from_hex(self._settings.MASTER_KEY_HEX)
        self._manager = KeyManager(primary_kek=primary_kek, primary_version="v1")

    @property
    def manager(self) -> KeyManager:
        return self._manager

    def create_transfer_key(self, transfer_id: UUID) -> tuple[bytes, KeyReferenceCreate]:
        """Generate an ephemeral DEK and prepare its wrapped key reference for storage.

        Args:
            transfer_id: UUID of the transfer.

        Returns:
            Tuple[bytes, KeyReferenceCreate]: (plaintext_dek_for_active_pass, key_reference_schema)
        """
        plaintext_dek, wrapped_dek, version_used = self._manager.generate_and_wrap_dek()
        key_ref = KeyReferenceCreate(
            transfer_id=transfer_id,
            wrapped_dek=wrapped_dek,
            key_version=version_used,
            algorithm="AES-KW-256",
        )
        return plaintext_dek, key_ref

    def unwrap_transfer_key(self, wrapped_dek: bytes, key_version: str) -> bytes:
        """Unwrap a stored DEK using the recorded KEK version.

        Args:
            wrapped_dek: 40-byte wrapped key from database.
            key_version: KEK version identifier.

        Returns:
            bytes: 32-byte plaintext DEK.
        """
        return self._manager.unwrap_dek(wrapped_dek, key_version)

    def rotate_transfer_key(
        self,
        wrapped_dek: bytes,
        current_version: str,
        target_version: str | None = None,
    ) -> tuple[bytes, str]:
        """Rotate a wrapped DEK to a newer KEK version without altering ciphertext.

        Args:
            wrapped_dek: Existing wrapped DEK.
            current_version: Old KEK version.
            target_version: New KEK version.

        Returns:
            Tuple[bytes, str]: (new_wrapped_dek, new_key_version)
        """
        return self._manager.rotate_wrapped_dek(
            wrapped_dek=wrapped_dek,
            current_version=current_version,
            target_version=target_version,
        )
