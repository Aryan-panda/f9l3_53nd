from fastapi import Cookie, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.user import User
from app.security.authorization import UserRole, UserStatus
from app.services.auth_service import AuthService


async def get_session_token_from_request(
    request: Request,
    session_cookie: str | None = Cookie(default=None, alias="f9l3_session"),
    authorization: str | None = Header(default=None),
) -> str:
    """Extract session token from HttpOnly cookie or Authorization Bearer header."""
    if session_cookie:
        return session_cookie

    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ", 1)[1].strip()

    raise AuthenticationError("Authentication credentials not provided.")


async def get_current_user(
    token: str = Depends(get_session_token_from_request),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency for authenticating callers via session token."""
    res = await AuthService.validate_session(db, token)
    if res is None:
        raise AuthenticationError("Invalid or expired session. Please log in again.")

    user, _ = res
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """FastAPI dependency enforcing that the authenticated user account is ACTIVE."""
    if current_user.status != UserStatus.ACTIVE.value:
        raise AuthorizationError(
            f"Account is {current_user.status.lower()}. Please contact an administrator."
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """FastAPI dependency enforcing that the authenticated caller has the ADMIN role."""
    if current_user.role != UserRole.ADMIN.value:
        raise AuthorizationError("Administrator privileges required for this resource.")
    return current_user


__all__ = [
    "get_db",
    "get_settings",
    "Settings",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
]
