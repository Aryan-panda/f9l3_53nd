from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.exceptions import AuthenticationError

# OWASP Recommended Argon2id parameters (RFC 9106)
# Time cost: 3 iterations
# Memory cost: 65536 KiB (64 MiB)
# Parallelism: 4 threads
# Hash length: 32 bytes
# Salt length: 16 bytes
_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id.

    Args:
        password: Raw plaintext password.

    Returns:
        str: Formatted Argon2id hash string including salt, parameters, and digest.
    """
    if not password or not isinstance(password, str):
        raise AuthenticationError("Password must be a non-empty string.")
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash in constant time.

    Args:
        plain_password: User-provided plaintext password.
        hashed_password: Stored Argon2id hash string from database.

    Returns:
        bool: True if password matches, False otherwise.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return _hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Check if a stored Argon2id hash needs updating to newer parameter standards.

    Args:
        hashed_password: Stored Argon2id hash string.

    Returns:
        bool: True if rehash is recommended.
    """
    try:
        return _hasher.check_needs_rehash(hashed_password)
    except Exception:
        return True
