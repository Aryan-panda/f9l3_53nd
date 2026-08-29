import io

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.integration
async def test_download_transfer_by_recipient(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Test designated recipient can download, decrypt, and verify transfer."""
    # 1. Sender logs in and uploads file
    sender_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    sender_token = sender_login.cookies["f9l3_session"]

    original_bytes = b"Financial quarterly audit report contents for Branch B."
    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": sender_token},
        data={"recipient_id": str(admin_user.id)},
        files={"file": ("audit_report.pdf", io.BytesIO(original_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 201
    transfer_id = upload_res.json()["id"]

    # 2. Recipient logs in and downloads file
    recipient_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    recipient_token = recipient_login.cookies["f9l3_session"]

    download_res = await async_client.get(
        f"/api/v1/transfers/{transfer_id}/download",
        cookies={"f9l3_session": recipient_token},
    )
    assert download_res.status_code == 200
    assert download_res.content == original_bytes
    disposition = download_res.headers["content-disposition"]
    assert 'attachment; filename="audit_report.pdf"' in disposition

    # 3. Verify transfer record transitioned to COMPLETED
    detail_res = await async_client.get(
        f"/api/v1/transfers/{transfer_id}",
        cookies={"f9l3_session": recipient_token},
    )
    assert detail_res.status_code == 200
    assert detail_res.json()["state"] == "COMPLETED"
    assert detail_res.json()["completed_at"] is not None
    assert detail_res.json()["decrypted_sha256"] == detail_res.json()["original_sha256"]


@pytest.mark.integration
async def test_download_transfer_by_sender(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Test sender can also download and verify their own uploaded transfer."""
    sender_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    sender_token = sender_login.cookies["f9l3_session"]

    original_bytes = b"Sender copy retrieval test."
    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": sender_token},
        data={"recipient_id": str(admin_user.id)},
        files={"file": ("notes.txt", io.BytesIO(original_bytes), "text/plain")},
    )
    transfer_id = upload_res.json()["id"]

    download_res = await async_client.get(
        f"/api/v1/transfers/{transfer_id}/download",
        cookies={"f9l3_session": sender_token},
    )
    assert download_res.status_code == 200
    assert download_res.content == original_bytes
