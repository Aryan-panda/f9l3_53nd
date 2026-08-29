import pytest

from app.core.exceptions import AuthenticationError
from app.security.password import hash_password, needs_rehash, verify_password


@pytest.mark.unit
def test_argon2id_hash_and_verify() -> None:
    """Verify Argon2id hashes passwords securely and verifies correct passwords."""
    password = "CorrectHorseBatteryStaple123!"
    pwd_hash = hash_password(password)

    assert pwd_hash.startswith("$argon2id$")
    assert verify_password(password, pwd_hash) is True
    assert verify_password("WrongPassword123!", pwd_hash) is False


@pytest.mark.unit
def test_argon2id_unique_salts() -> None:
    """Ensure two hashes of the same password produce distinct salt values."""
    password = "SamePassword123!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    assert hash1 != hash2
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


@pytest.mark.unit
def test_argon2id_empty_password_rejection() -> None:
    """Empty or invalid password strings must raise AuthenticationError."""
    with pytest.raises(AuthenticationError, match="must be a non-empty string"):
        hash_password("")


@pytest.mark.unit
def test_argon2id_verify_malformed_hash() -> None:
    """Verifying against corrupted/malformed hash strings returns False safely."""
    assert verify_password("Password123!", "corrupted_hash_string") is False
    assert verify_password("Password123!", "") is False


@pytest.mark.unit
def test_argon2id_needs_rehash() -> None:
    """Freshly generated hashes using current parameters should not need rehash."""
    pwd_hash = hash_password("SecurePassword123!")
    assert needs_rehash(pwd_hash) is False
