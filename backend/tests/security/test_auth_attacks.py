import pytest
from httpx import AsyncClient

from app.models.user import User
from app.security.rate_limit import InMemoryRateLimiter, login_limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    login_limiter.reset()


@pytest.mark.security
async def test_brute_force_login_rate_limiting(
    async_client: AsyncClient,
    sample_user: User,
) -> None:
    """Security Test: Rapid repeated login attempts must trigger RateLimitError (429)."""
    # Create an aggressive limiter for testing
    test_limiter = InMemoryRateLimiter(rate=0.1, capacity=3.0)
    # Monkeypatch global login_limiter
    import app.api.routes.auth as auth_route

    original_limiter = auth_route.login_limiter
    auth_route.login_limiter = test_limiter

    try:
        # First 3 attempts consume burst tokens
        for _ in range(3):
            res = await async_client.post(
                "/api/v1/auth/login",
                json={"username": sample_user.username, "password": "WrongPassword!"},
            )
            assert res.status_code == 401

        # 4th attempt must be rejected with 429 Too Many Requests
        rate_limited_res = await async_client.post(
            "/api/v1/auth/login",
            json={"username": sample_user.username, "password": "WrongPassword!"},
        )
        assert rate_limited_res.status_code == 429
        assert rate_limited_res.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    finally:
        auth_route.login_limiter = original_limiter


@pytest.mark.security
async def test_privilege_escalation_status_update_blocked(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Security Test: Standard user cannot elevate privileges or modify account statuses."""
    # Login as standard user
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    # Attempt to suspend admin account
    attack_res = await async_client.patch(
        f"/api/v1/users/{admin_user.id}/status",
        cookies={"f9l3_session": token},
        json={"status": "SUSPENDED"},
    )
    assert attack_res.status_code == 403
    assert attack_res.json()["error"]["code"] == "AUTHORIZATION_DENIED"


@pytest.mark.security
async def test_forged_session_token_rejected(async_client: AsyncClient) -> None:
    """Security Test: Forged or random session token is rejected with 401."""
    forged_token = "forged-session-token-999999999999999999999999"
    response = await async_client.get(
        "/api/v1/auth/me",
        cookies={"f9l3_session": forged_token},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"
