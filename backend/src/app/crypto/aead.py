
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.exceptions import CryptoError, DecryptionError
from app.crypto.nonce import generate_nonce, validate_nonce

TAG_SIZE_BYTES: int = 16  # 128-bit authentication tag
KEY_SIZE_BYTES: int = 32  # 256-bit AES key


def build_canonical_aad(
    protocol_version: str,
    transfer_id: str,
    sender_id: str,
    recipient_id: str,
    file_size: int,
    algorithm: str = "AES-256-GCM",
) -> bytes:
    """Construct canonical UTF-8 encoded Authenticated Associated Data (AAD) byte string.

    Format:
        protocol_version|transfer_id|sender_id|recipient_id|file_size|algorithm

    Args:
        protocol_version: Transfer protocol identifier (e.g., 'f9l3_v1').
        transfer_id: Canonical UUID string of the transfer.
        sender_id: Canonical UUID string of the sender user.
        recipient_id: Canonical UUID string of the recipient user.
        file_size: Total payload size in bytes.
        algorithm: Encryption algorithm identifier (default 'AES-256-GCM').

    Returns:
        bytes: Canonical AAD bytes to bind into GCM tag.
    """
    fields = [
        str(protocol_version).strip(),
        str(transfer_id).strip(),
        str(sender_id).strip(),
        str(recipient_id).strip(),
        str(file_size).strip(),
        str(algorithm).strip(),
    ]
    canonical_string = "|".join(fields)
    return canonical_string.encode("utf-8")


class AES256GCMCipher:
    """AES-256-GCM Authenticated Encryption with Associated Data (AEAD) handler."""

    def __init__(self, key: bytes) -> None:
        if len(key) != KEY_SIZE_BYTES:
            raise CryptoError(
                f"AES-256 key must be exactly {KEY_SIZE_BYTES} bytes (256 bits), got {len(key)}."
            )
        self._key = key
        self._aesgcm = AESGCM(self._key)

    def encrypt(
        self,
        plaintext: bytes,
        nonce: bytes,
        aad: bytes | None = None,
    ) -> tuple[bytes, bytes]:
        """Encrypt plaintext using AES-256-GCM and compute 128-bit authentication tag.

        Args:
            plaintext: Raw payload bytes.
            nonce: 96-bit (12-byte) unique random nonce.
            aad: Optional Authenticated Associated Data bytes.

        Returns:
            Tuple[bytes, bytes]: (ciphertext_without_tag, 16_byte_authentication_tag)
        """
        validate_nonce(nonce)
        if not isinstance(plaintext, (bytes, bytearray)):
            raise CryptoError("Plaintext must be bytes.")

        try:
            # AESGCM.encrypt returns ciphertext with 16-byte tag appended at the end
            combined = self._aesgcm.encrypt(nonce, plaintext, aad)
            ciphertext = combined[:-TAG_SIZE_BYTES]
            tag = combined[-TAG_SIZE_BYTES:]
            return ciphertext, tag
        except Exception as e:
            raise CryptoError(f"AES-GCM encryption failed: {e}") from e

    def decrypt(
        self,
        ciphertext: bytes,
        tag: bytes,
        nonce: bytes,
        aad: bytes | None = None,
    ) -> bytes:
        """Authenticate GCM tag & AAD, and decrypt ciphertext to recover plaintext.

        Args:
            ciphertext: Encrypted payload bytes (excluding tag).
            tag: 128-bit (16-byte) GCM authentication tag.
            nonce: 96-bit (12-byte) nonce used during encryption.
            aad: Optional Authenticated Associated Data bytes.

        Returns:
            bytes: Recovered plaintext.

        Raises:
            DecryptionError: If authentication tag check fails (tampered CT, tag, nonce, or AAD).
        """
        validate_nonce(nonce)
        if len(tag) != TAG_SIZE_BYTES:
            raise DecryptionError(
                f"Authentication tag length mismatch: expected {TAG_SIZE_BYTES} bytes, "
                f"got {len(tag)}."
            )


        combined = ciphertext + tag
        try:
            return self._aesgcm.decrypt(nonce, combined, aad)
        except InvalidTag as e:
            raise DecryptionError(
                "AEAD tag authentication failed: Ciphertext, tag, nonce, or AAD was tampered with."
            ) from e
        except Exception as e:
            raise DecryptionError(f"Decryption failed: {e}") from e


def encrypt_payload(
    plaintext: bytes,
    key: bytes,
    aad: bytes | None = None,
    nonce: bytes | None = None,
) -> tuple[bytes, bytes, bytes]:
    """Convenience wrapper to encrypt a byte payload.

    Args:
        plaintext: Raw data bytes to encrypt.
        key: 32-byte AES-256 key.
        aad: Optional AAD bytes.
        nonce: Optional 12-byte nonce (generated if omitted).

    Returns:
        Tuple[bytes, bytes, bytes]: (ciphertext, tag, nonce)
    """
    if nonce is None:
        nonce = generate_nonce()
    cipher = AES256GCMCipher(key)
    ciphertext, tag = cipher.encrypt(plaintext, nonce, aad)
    return ciphertext, tag, nonce


def decrypt_payload(
    ciphertext: bytes,
    tag: bytes,
    nonce: bytes,
    key: bytes,
    aad: bytes | None = None,
) -> bytes:
    """Convenience wrapper to decrypt an AEAD-protected payload.

    Args:
        ciphertext: Encrypted bytes.
        tag: 16-byte GCM tag.
        nonce: 12-byte nonce.
        key: 32-byte AES-256 key.
        aad: Optional AAD bytes.

    Returns:
        bytes: Decrypted plaintext.

    Raises:
        DecryptionError: If tag check fails.
    """
    cipher = AES256GCMCipher(key)
    return cipher.decrypt(ciphertext, tag, nonce, aad)
