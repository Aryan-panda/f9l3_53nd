import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Response

from app.core.config import Settings, get_settings


def generate_session_token() -> str:
    """Generate a cryptographically secure 256-bit URL-safe session token.

    Returns:
        str: 43-character base64 URL-safe random string.
    """
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Compute the SHA-256 hash of a session token for storage at rest.

    Storing hashed tokens in the database ensures that a database breach
    does not allow an attacker to hijack active user sessions.

    Args:
        token: Raw session token from cookie.

    Returns:
        str: 64-character lowercase hexadecimal hash string.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest().lower()


def compute_session_expiry(seconds: int | None = None) -> datetime:
    """Calculate the future expiration timestamp for a new session."""
    expiry_seconds = seconds if seconds is not None else get_settings().SESSION_EXPIRY_SECONDS
    return datetime.now(UTC) + timedelta(seconds=expiry_seconds)


def set_session_cookie(
    response: Response,
    token: str,
    settings: Settings | None = None,
) -> None:
    """Attach the authenticated session token to an HTTP response as a secure cookie.

    Args:
        response: FastAPI Response instance.
        token: Raw session token string.
        settings: Application settings.
    """
    app_settings = settings or get_settings()
    response.set_cookie(
        key=app_settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=app_settings.SESSION_EXPIRY_SECONDS,
        expires=app_settings.SESSION_EXPIRY_SECONDS,
        path="/",
        domain=None,
        secure=app_settings.SESSION_COOKIE_SECURE,
        httponly=app_settings.SESSION_COOKIE_HTTPONLY,
        samesite=app_settings.SESSION_COOKIE_SAMESITE,  # type: ignore[arg-type]
    )


def clear_session_cookie(
    response: Response,
    settings: Settings | None = None,
) -> None:
    """Instruct the client browser to delete the session cookie."""
    app_settings = settings or get_settings()
    response.delete_cookie(
        key=app_settings.SESSION_COOKIE_NAME,
        path="/",
        domain=None,
        secure=app_settings.SESSION_COOKIE_SECURE,
        httponly=app_settings.SESSION_COOKIE_HTTPONLY,
        samesite=app_settings.SESSION_COOKIE_SAMESITE,  # type: ignore[arg-type]
    )
