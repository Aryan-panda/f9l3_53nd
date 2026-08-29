import io

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.integration
async def test_admin_audit_events_access_control(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Non-admin user receives 403; Admin receives 200 with audit events."""
    # 1. Non-admin login
    user_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    user_token = user_login.cookies["f9l3_session"]

    forbidden_res = await async_client.get(
        "/api/v1/admin/audit-events",
        cookies={"f9l3_session": user_token},
    )
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["error"]["code"] == "AUTHORIZATION_DENIED"

    # 2. Admin login
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    admin_token = admin_login.cookies["f9l3_session"]

    admin_res = await async_client.get(
        "/api/v1/admin/audit-events",
        cookies={"f9l3_session": admin_token},
    )
    assert admin_res.status_code == 200
    data = admin_res.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


@pytest.mark.integration
async def test_admin_audit_chain_verification_endpoint(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Verify admin audit chain verification endpoint validates genuine operations."""
    # 1. Admin login
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    admin_token = admin_login.cookies["f9l3_session"]

    # 2. Perform upload to create audit logs
    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": admin_token},
        data={"recipient_id": str(sample_user.id)},
        files={"file": ("report.txt", io.BytesIO(b"sample report"), "text/plain")},
    )
    assert upload_res.status_code == 201

    # 3. Call chain verification endpoint
    verify_res = await async_client.post(
        "/api/v1/admin/audit-events/verify",
        cookies={"f9l3_session": admin_token},
    )
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["total_records"] >= 2
    assert verify_data["broken_record_index"] is None
