import pytest
from pydantic import ValidationError

from app.core.exceptions import AuthenticationError
from app.schemas.user import UserCreate
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


@pytest.mark.unit
def test_user_create_password_complexity_enforcement() -> None:
    """Ensure UserCreate rejects passwords lacking uppercase, lowercase, numbers, or symbols."""
    # Missing uppercase
    with pytest.raises(ValidationError, match="uppercase"):
        UserCreate(username="valid_user", password="lowercase_only123!")

    # Missing lowercase
    with pytest.raises(ValidationError, match="lowercase"):
        UserCreate(username="valid_user", password="UPPERCASE_ONLY123!")

    # Missing digit
    with pytest.raises(ValidationError, match="digit"):
        UserCreate(username="valid_user", password="NoDigitsHereAtAll!")

    # Missing special character
    with pytest.raises(ValidationError, match="special character"):
        UserCreate(username="valid_user", password="NoSpecialChar12345")

    # Length < 12
    with pytest.raises(ValidationError):
        UserCreate(username="valid_user", password="Short1!")

    # Valid password passes
    valid_user = UserCreate(username="valid_user", password="StrongValidPassword123!")
    assert valid_user.password == "StrongValidPassword123!"

