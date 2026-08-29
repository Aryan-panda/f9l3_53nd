import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.integration
async def test_users_me_authenticated(
    async_client: AsyncClient,
    sample_user: User,
) -> None:
    """Test GET /api/v1/users/me returns authenticated caller profile."""
    # Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    response = await async_client.get(
        "/api/v1/users/me",
        cookies={"f9l3_session": token},
    )
    assert response.status_code == 200
    assert response.json()["username"] == sample_user.username


@pytest.mark.integration
async def test_list_users_non_admin_forbidden(
    async_client: AsyncClient,
    sample_user: User,
) -> None:
    """Non-admin users must receive 403 when trying to list users."""
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    response = await async_client.get(
        "/api/v1/users",
        cookies={"f9l3_session": token},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "AUTHORIZATION_DENIED"


@pytest.mark.integration
async def test_list_users_admin_allowed(
    async_client: AsyncClient,
    admin_user: User,
    sample_user: User,
) -> None:
    """Admin users receive paginated list of all users."""
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    response = await async_client.get(
        "/api/v1/users",
        cookies={"f9l3_session": token},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


@pytest.mark.integration
async def test_admin_update_user_status(
    async_client: AsyncClient,
    admin_user: User,
    sample_user: User,
) -> None:
    """Admin can update another user's status to SUSPENDED."""
    # Login as admin
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    response = await async_client.patch(
        f"/api/v1/users/{sample_user.id}/status",
        cookies={"f9l3_session": token},
        json={"status": "SUSPENDED"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SUSPENDED"
