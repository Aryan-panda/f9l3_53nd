import io

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_event import AuditEvent
from app.models.user import User
from app.services.audit_service import AuditService


@pytest.mark.security
async def test_audit_log_database_tamper_detection(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
    db_session: AsyncSession,
) -> None:
    """Security Test: Direct DB tampering with an audit record is mathematically detected."""
    # 1. Admin login & upload to generate chained audit records
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    admin_token = admin_login.cookies["f9l3_session"]

    await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": admin_token},
        data={"recipient_id": str(sample_user.id)},
        files={"file": ("log_test.txt", io.BytesIO(b"audit chain test data"), "text/plain")},
    )

    # 2. Verify initial chain is valid
    is_valid, count, broken_idx, _ = await AuditService.verify_chain_integrity(db_session)
    assert is_valid is True
    assert count >= 2
    assert broken_idx is None

    # 3. Malicious insider / attacker modifies record #1 directly in database
    stmt = select(AuditEvent).order_by(AuditEvent.timestamp.asc())
    res = await db_session.execute(stmt)
    records = list(res.scalars().all())

    target_record = records[1]
    target_record.details = {"forged_tampered_data": True}
    await db_session.flush()

    # 4. Run chain verification -> Must detect tampering at index 1
    is_valid_after, _, broken_idx_after, msg_after = await AuditService.verify_chain_integrity(
        db_session
    )
    assert is_valid_after is False
    assert broken_idx_after == 1
    assert "Tampered record content" in msg_after

    # 5. Verify admin verification API also reports failure
    api_verify_res = await async_client.post(
        "/api/v1/admin/audit-events/verify",
        cookies={"f9l3_session": admin_token},
    )
    assert api_verify_res.status_code == 200
    api_data = api_verify_res.json()
    assert api_data["is_valid"] is False
    assert api_data["broken_record_index"] == 1
