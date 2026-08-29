import io
import os
from pathlib import Path
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.transfer import Transfer
from app.models.user import User
from app.schemas.user import UserCreate, UserRole
from app.services.audit_service import AuditService
from app.services.user_service import UserService


@pytest.mark.integration
async def test_e2e_happy_path_full_transfer_lifecycle(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
    db_session: AsyncSession,
) -> None:
    """E2E Test 1: Full happy path transfer between Branch A (Alice) and Branch B (Bob)."""
    # 1. Create Bob (Branch B user)
    bob = await UserService.create_user(
        db=db_session,
        user_in=UserCreate(
            username="bob_branch_b",
            password="BobPassword123!",
            role=UserRole.USER,
        ),
    )

    # 2. Alice (Branch A) logs in
    alice_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    assert alice_login.status_code == 200
    alice_token = alice_login.cookies["f9l3_session"]

    # 3. Alice uploads and encrypts payload for Bob
    original_payload = (
        b"CRITICAL BRANCH REPORT\nBranch: A\nStatus: Normal\nPayload: Secure data stream."
    )
    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": alice_token},
        data={"recipient_id": str(bob.id)},
        files={"file": ("branch_report.txt", io.BytesIO(original_payload), "text/plain")},
    )
    assert upload_res.status_code == 201
    transfer_data = upload_res.json()
    transfer_id = transfer_data["id"]
    assert transfer_data["state"] == "ENCRYPTED"
    assert transfer_data["file_size"] == len(original_payload)

    # 4. Bob (Branch B) logs in
    bob_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "bob_branch_b", "password": "BobPassword123!"},
    )
    assert bob_login.status_code == 200
    bob_token = bob_login.cookies["f9l3_session"]

    # 5. Bob queries transfers and sees Alice's incoming transfer
    list_res = await async_client.get(
        "/api/v1/transfers",
        cookies={"f9l3_session": bob_token},
    )
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert any(t["id"] == transfer_id for t in items)

    # 6. Bob downloads, decrypts, and verifies payload
    download_res = await async_client.get(
        f"/api/v1/transfers/{transfer_id}/download",
        cookies={"f9l3_session": bob_token},
    )
    assert download_res.status_code == 200
    assert download_res.content == original_payload

    # 7. Check transfer state transitioned to COMPLETED
    detail_res = await async_client.get(
        f"/api/v1/transfers/{transfer_id}",
        cookies={"f9l3_session": bob_token},
    )
    assert detail_res.status_code == 200
    updated_data = detail_res.json()
    assert updated_data["state"] == "COMPLETED"
    assert updated_data["completed_at"] is not None
    assert updated_data["decrypted_sha256"] == transfer_data["original_sha256"]

    # 8. Admin verifies audit log chain
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    admin_token = admin_login.cookies["f9l3_session"]

    verify_res = await async_client.post(
        "/api/v1/admin/audit-events/verify",
        cookies={"f9l3_session": admin_token},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["is_valid"] is True


@pytest.mark.integration
async def test_e2e_large_payload_transfer(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """E2E Test 2: Transfer and verification of a large 2MB binary payload."""
    # 1. Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    # 2. Generate 2MB pseudo-random binary payload
    large_payload = os.urandom(2 * 1024 * 1024)

    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": token},
        data={"recipient_id": str(admin_user.id)},
        files={
            "file": ("dataset_large.bin", io.BytesIO(large_payload), "application/octet-stream")
        },
    )
    assert upload_res.status_code == 201
    transfer_id = upload_res.json()["id"]

    # 3. Admin downloads and decrypts large payload
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    admin_token = admin_login.cookies["f9l3_session"]

    download_res = await async_client.get(
        f"/api/v1/transfers/{transfer_id}/download",
        cookies={"f9l3_session": admin_token},
    )
    assert download_res.status_code == 200
    assert len(download_res.content) == len(large_payload)
    assert download_res.content == large_payload


@pytest.mark.integration
async def test_e2e_corrupt_payload_quarantine_flow(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
    db_session: AsyncSession,
) -> None:
    """E2E Test 3: Corrupted ciphertext triggers quarantine isolation and blocks delivery."""
    # 1. Upload file
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    original_bytes = b"TOP SECRET EXECUTIVE DIRECTIVE"
    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": token},
        data={"recipient_id": str(admin_user.id)},
        files={"file": ("directive.doc", io.BytesIO(original_bytes), "application/msword")},
    )
    transfer_id = UUID(upload_res.json()["id"])

    # 2. Adversary corrupts 1 byte of the encrypted file on disk
    stmt = select(Transfer).where(Transfer.id == transfer_id)
    res = await db_session.execute(stmt)
    transfer = res.scalar_one()

    with open(transfer.storage_path, "r+b") as f:
        content = bytearray(f.read())
        content[-3] ^= 0xFF
        f.seek(0)
        f.write(content)

    # 3. Recipient attempts download -> AEAD tag authentication fails -> 400 Bad Request
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    admin_token = admin_login.cookies["f9l3_session"]

    download_res = await async_client.get(
        f"/api/v1/transfers/{transfer_id}/download",
        cookies={"f9l3_session": admin_token},
    )
    assert download_res.status_code == 400
    assert download_res.json()["error"]["code"] == "DECRYPTION_FAILED"

    # 4. Confirm state is QUARANTINED and quarantine copy is stored
    await db_session.refresh(transfer)
    assert transfer.state == "QUARANTINED"
    assert transfer.quarantine_path is not None
    assert Path(transfer.quarantine_path).exists()


@pytest.mark.integration
async def test_e2e_session_revocation_during_transfer(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
    db_session: AsyncSession,
) -> None:
    """E2E Test 4: Revoked/expired session token immediately blocks upload and download requests."""
    # 1. Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    # 2. Revoke all active sessions for this user in DB
    stmt = select(Session).where(Session.user_id == sample_user.id)
    res = await db_session.execute(stmt)
    sessions = res.scalars().all()
    for s in sessions:
        s.revoked_at = s.created_at
    await db_session.flush()

    # 3. Attempt upload with now-revoked session token -> 401 Unauthorized
    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": token},
        data={"recipient_id": str(admin_user.id)},
        files={"file": ("blocked.txt", io.BytesIO(b"data"), "text/plain")},
    )
    assert upload_res.status_code == 401
    assert upload_res.json()["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.integration
async def test_e2e_audit_chain_continuous_integrity(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
    db_session: AsyncSession,
) -> None:
    """E2E Test 5: Validate continuous unbroken audit chain across operations."""
    # Run multi-operation workflow
    user_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    user_token = user_login.cookies["f9l3_session"]

    # Perform upload
    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": user_token},
        data={"recipient_id": str(admin_user.id)},
        files={"file": ("audit_doc.pdf", io.BytesIO(b"auditable payload"), "application/pdf")},
    )
    transfer_id = upload_res.json()["id"]

    # Admin downloads
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": admin_user.username, "password": "AdminMasterPassword123!"},
    )
    admin_token = admin_login.cookies["f9l3_session"]

    await async_client.get(
        f"/api/v1/transfers/{transfer_id}/download",
        cookies={"f9l3_session": admin_token},
    )

    # Perform on-demand cryptographic verification
    is_valid, count, broken_idx, _ = await AuditService.verify_chain_integrity(db_session)
    assert is_valid is True
    assert count >= 4
    assert broken_idx is None
