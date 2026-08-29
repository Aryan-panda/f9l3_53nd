from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ReplayError
from app.models.user import User
from app.transfer.replay import ReplayDetector


@pytest.mark.integration
async def test_e2e_network_status_access_control(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Non-admin user cannot access network telemetry; admin can access telemetry."""
    # 1. User login -> forbidden on admin endpoint
    user_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    user_token = user_login.cookies["f9l3_session"]

    res_user = await async_client.get(
        "/api/v1/admin/network/status",
        cookies={"f9l3_session": user_token},
    )
    assert res_user.status_code == 403

    # 2. Admin login -> allowed
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    admin_token = admin_login.cookies["f9l3_session"]

    res_admin = await async_client.get(
        "/api/v1/admin/network/status",
        cookies={"f9l3_session": admin_token},
    )
    assert res_admin.status_code == 200
    net_data = res_admin.json()
    assert "local_ip" in net_data
    assert "peer_ip" in net_data
    assert net_data["status"] == "ACTIVE"


@pytest.mark.integration
async def test_e2e_replay_detection_integrity(
    db_session: AsyncSession,
) -> None:
    """Replay detector prevents duplicate submission of transfer payloads and nonces."""
    detector = ReplayDetector(ttl_seconds=60.0)
    transfer_id = uuid4()
    nonce = b"\x01" * 12

    # First registration passes without error
    detector.check_and_record(transfer_id, nonce)

    # Duplicate transfer ID raises ReplayError
    with pytest.raises(ReplayError, match="already processed"):
        detector.check_and_record(transfer_id, b"\x02" * 12)

    # Duplicate nonce raises ReplayError
    with pytest.raises(ReplayError, match="nonce reuse"):
        detector.check_and_record(uuid4(), nonce)
