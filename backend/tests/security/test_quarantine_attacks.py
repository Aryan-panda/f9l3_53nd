import io
from pathlib import Path
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transfer import Transfer
from app.models.user import User


@pytest.mark.security
async def test_ciphertext_tampering_triggers_quarantine(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
    db_session: AsyncSession,
) -> None:
    """Security Test: Tampering with on-disk encrypted payload triggers quarantine isolation."""
    # 1. Sender uploads file
    sender_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    sender_token = sender_login.cookies["f9l3_session"]

    original_bytes = b"Sensitive executive meeting notes."
    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": sender_token},
        data={"recipient_id": str(admin_user.id)},
        files={"file": ("meeting_notes.txt", io.BytesIO(original_bytes), "text/plain")},
    )
    assert upload_res.status_code == 201
    transfer_id = UUID(upload_res.json()["id"])

    # 2. Adversary mutates 1 byte of the encrypted file on disk
    stmt = select(Transfer).where(Transfer.id == transfer_id)
    res = await db_session.execute(stmt)
    transfer = res.scalar_one()

    storage_file = Path(transfer.storage_path)
    assert storage_file.exists()

    with open(storage_file, "r+b") as f:
        data = bytearray(f.read())
        # Corrupt one byte in the ciphertext payload
        data[-5] ^= 0xAA
        f.seek(0)
        f.write(data)

    # 3. Recipient attempts download -> AEAD tag check fails -> 400 Decryption Failed
    recipient_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    recipient_token = recipient_login.cookies["f9l3_session"]

    download_res = await async_client.get(
        f"/api/v1/transfers/{transfer_id}/download",
        cookies={"f9l3_session": recipient_token},
    )
    assert download_res.status_code == 400
    assert download_res.json()["error"]["code"] == "DECRYPTION_FAILED"

    # 4. Verify Transfer record is now in QUARANTINED state and quarantine file exists
    await db_session.refresh(transfer)
    assert transfer.state == "QUARANTINED"
    assert transfer.quarantine_path is not None
    assert Path(transfer.quarantine_path).exists()


@pytest.mark.security
async def test_sha256_mismatch_triggers_quarantine(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
    db_session: AsyncSession,
) -> None:
    """Security Test: SHA-256 digest mismatch triggers post-decryption quarantine."""
    # 1. Sender uploads file
    sender_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    sender_token = sender_login.cookies["f9l3_session"]

    original_bytes = b"Integrity check ground truth payload."
    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": sender_token},
        data={"recipient_id": str(admin_user.id)},
        files={"file": ("contract.pdf", io.BytesIO(original_bytes), "application/pdf")},
    )
    transfer_id = UUID(upload_res.json()["id"])

    # 2. Modify ground-truth digest in database directly
    stmt = select(Transfer).where(Transfer.id == transfer_id)
    res = await db_session.execute(stmt)
    transfer = res.scalar_one()
    transfer.original_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
    await db_session.flush()

    # 3. Recipient attempts download -> SHA-256 verification fails -> 400 Integrity Mismatch
    recipient_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    recipient_token = recipient_login.cookies["f9l3_session"]

    download_res = await async_client.get(
        f"/api/v1/transfers/{transfer_id}/download",
        cookies={"f9l3_session": recipient_token},
    )
    assert download_res.status_code == 400
    assert download_res.json()["error"]["code"] == "INTEGRITY_MISMATCH"

    # 4. Verify Transfer record is QUARANTINED
    await db_session.refresh(transfer)
    assert transfer.state == "QUARANTINED"
