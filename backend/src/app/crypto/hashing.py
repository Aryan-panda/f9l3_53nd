import hashlib
import hmac
from typing import BinaryIO

from app.core.exceptions import CryptoError, IntegrityError

DEFAULT_CHUNK_SIZE: int = 65536  # 64 KB chunks for streaming


def compute_buffer_sha256(data: bytes) -> str:
    """Compute the SHA-256 hex digest of an in-memory byte buffer.

    Args:
        data: Plaintext bytes.

    Returns:
        str: 64-character lowercase hexadecimal SHA-256 digest.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise CryptoError("Data buffer for SHA-256 hashing must be bytes.")
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest().lower()


def compute_stream_sha256(stream: BinaryIO, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    """Compute the SHA-256 hex digest of a readable binary stream.

    Args:
        stream: Binary readable stream (e.g. file or BytesIO).
        chunk_size: Buffer size per read pass.

    Returns:
        str: 64-character lowercase hexadecimal SHA-256 digest.
    """
    hasher = hashlib.sha256()
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        hasher.update(chunk)
    return hasher.hexdigest().lower()


def verify_sha256_digest(computed_digest: str, expected_digest: str) -> bool:
    """Compare two SHA-256 hex digests using constant-time comparison.

    Args:
        computed_digest: Hex digest calculated on received/decrypted data.
        expected_digest: Original hex digest recorded during sender ingestion.

    Returns:
        bool: True if digests match exactly, False otherwise.
    """
    if not computed_digest or not expected_digest:
        return False
    # Normalize to lowercase and strip whitespace
    comp_norm = computed_digest.strip().lower()
    exp_norm = expected_digest.strip().lower()

    if len(comp_norm) != 64 or len(exp_norm) != 64:
        return False

    return hmac.compare_digest(comp_norm, exp_norm)


def assert_sha256_integrity(computed_digest: str, expected_digest: str) -> None:
    """Assert integrity and raise IntegrityError if digests mismatch.

    Args:
        computed_digest: Hex digest calculated on received/decrypted data.
        expected_digest: Original hex digest recorded during sender ingestion.

    Raises:
        IntegrityError: If digests do not match.
    """
    if not verify_sha256_digest(computed_digest, expected_digest):
        raise IntegrityError(
            f"File integrity mismatch: expected SHA-256 '{expected_digest}', "
            f"got '{computed_digest}'."
        )
