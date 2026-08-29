import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.integration
async def test_admin_network_status_endpoint(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Admin can query network status; non-admin receives 403."""
    # 1. Non-admin login
    user_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    user_token = user_login.cookies["f9l3_session"]

    non_admin_res = await async_client.get(
        "/api/v1/admin/network/status",
        cookies={"f9l3_session": user_token},
    )
    assert non_admin_res.status_code == 403

    # 2. Admin login
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    admin_token = admin_login.cookies["f9l3_session"]

    admin_res = await async_client.get(
        "/api/v1/admin/network/status",
        cookies={"f9l3_session": admin_token},
    )
    assert admin_res.status_code == 200
    data = admin_res.json()
    assert data["interface"] == "wg0"
    assert data["local_ip"] == "10.13.37.1"
    assert data["peer_ip"] == "10.13.37.2"
    assert data["is_connected"] is True
