from fastapi import APIRouter, Cookie, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_current_active_user,
    get_settings,
)
from app.core.config import Settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.user import UserRead
from app.security.rate_limit import login_limiter
from app.security.sessions import clear_session_cookie, set_session_cookie
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Authenticate user with Argon2id and establish an HttpOnly session cookie."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    rate_key = f"{client_ip}:{login_data.username.lower()}"
    login_limiter.assert_allowed(rate_key)

    user, raw_token = await AuthService.authenticate_user(
        db=db,
        username=login_data.username,
        password=login_data.password,
    )

    set_session_cookie(response=response, token=raw_token, settings=settings)
    return LoginResponse(
        message="Authenticated successfully",
        user=UserRead.model_validate(user),
    )


@router.post("/logout")
async def logout(
    response: Response,
    session_cookie: str | None = Cookie(default=None, alias="f9l3_session"),
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, str]:
    """Revoke session token on the server and instruct browser to delete session cookie."""
    token: str | None = session_cookie
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if token:
        await AuthService.revoke_session(db=db, raw_token=token)

    clear_session_cookie(response=response, settings=settings)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserRead:
    """Retrieve profile and roles of currently authenticated caller."""
    return UserRead.model_validate(current_user)
