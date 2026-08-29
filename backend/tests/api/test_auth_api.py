import pytest
from httpx import AsyncClient

from app.models.user import User
from app.security.rate_limit import login_limiter


@pytest.fixture(autouse=True)
def reset_login_rate_limiter() -> None:
    """Reset rate limiter state before each test."""
    login_limiter.reset()


@pytest.mark.integration
async def test_auth_login_success(async_client: AsyncClient, sample_user: User) -> None:
    """Test successful login returns 200 and sets secure session cookie."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Authenticated successfully"
    assert data["user"]["username"] == sample_user.username

    # Verify session cookie was set
    assert "f9l3_session" in response.cookies
    assert response.cookies["f9l3_session"] is not None


@pytest.mark.integration
async def test_auth_login_invalid_password(async_client: AsyncClient, sample_user: User) -> None:
    """Test login with wrong password returns 401 Unauthorized."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.integration
async def test_auth_login_nonexistent_user(async_client: AsyncClient) -> None:
    """Test login with non-existent user returns 401 without revealing user existence."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "ghost_user_does_not_exist", "password": "RandomPassword123!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.integration
async def test_auth_login_suspended_user(
    async_client: AsyncClient,
    suspended_user: User,
) -> None:
    """Test login with suspended account returns 403 Forbidden."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"username": suspended_user.username, "password": "StrongPassword123!"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "AUTHORIZATION_DENIED"


@pytest.mark.integration
async def test_auth_me_with_session(
    async_client: AsyncClient,
    sample_user: User,
) -> None:
    """Test GET /api/v1/auth/me returns profile of logged-in user."""
    # 1. Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    assert login_res.status_code == 200
    session_token = login_res.cookies["f9l3_session"]

    # 2. Call /api/v1/auth/me with cookie
    me_res = await async_client.get(
        "/api/v1/auth/me",
        cookies={"f9l3_session": session_token},
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["username"] == sample_user.username
    assert data["role"] == "USER"


@pytest.mark.integration
async def test_auth_me_unauthenticated(async_client: AsyncClient) -> None:
    """Test GET /api/v1/auth/me without cookie returns 401."""
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.integration
async def test_auth_logout_revocation(
    async_client: AsyncClient,
    sample_user: User,
) -> None:
    """Test logout revokes session token and prevents subsequent access."""
    # 1. Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    session_token = login_res.cookies["f9l3_session"]

    # 2. Logout
    logout_res = await async_client.post(
        "/api/v1/auth/logout",
        cookies={"f9l3_session": session_token},
    )
    assert logout_res.status_code == 200

    # 3. Call /auth/me with revoked session token
    subsequent_res = await async_client.get(
        "/api/v1/auth/me",
        cookies={"f9l3_session": session_token},
    )
    assert subsequent_res.status_code == 401
