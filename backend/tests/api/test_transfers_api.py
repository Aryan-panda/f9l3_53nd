import io
import uuid

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.schemas.user import UserCreate, UserRole
from app.services.user_service import UserService


@pytest.mark.integration
async def test_create_transfer_upload_success(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Test successful multipart upload encrypts file and creates transfer record."""
    # 1. Login as sender
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    # 2. Upload file targeting admin_user
    file_content = b"Confidential business strategy document for Branch B."
    files = {"file": ("strategy.docx", io.BytesIO(file_content), "application/octet-stream")}
    data = {"recipient_id": str(admin_user.id)}

    response = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": token},
        data=data,
        files=files,
    )
    assert response.status_code == 201
    transfer_data = response.json()

    assert transfer_data["filename"] == "strategy.docx"
    assert transfer_data["file_size"] == len(file_content)
    assert transfer_data["state"] == "ENCRYPTED"
    assert len(transfer_data["original_sha256"]) == 64
    assert transfer_data["sender_id"] == str(sample_user.id)
    assert transfer_data["recipient_id"] == str(admin_user.id)


@pytest.mark.integration
async def test_create_transfer_nonexistent_recipient(
    async_client: AsyncClient,
    sample_user: User,
) -> None:
    """Uploading to non-existent recipient ID returns 404 Not Found."""
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    fake_id = uuid.uuid4()
    files = {"file": ("test.txt", io.BytesIO(b"test data"), "text/plain")}
    response = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": token},
        data={"recipient_id": str(fake_id)},
        files=files,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.integration
async def test_list_and_get_transfer_authorization(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
    db_session,
) -> None:
    """Test transfer listing and retrieval complete mediation authorization."""
    # Create 3rd unrelated user
    third_user = await UserService.create_user(
        db=db_session,
        user_in=UserCreate(
            username="eve_eavesdropper",
            password="StrongPassword123!",
            role=UserRole.USER,
        ),
    )

    # 1. Login as sender (sample_user) and upload file
    sender_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    sender_token = sender_login.cookies["f9l3_session"]

    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": sender_token},
        data={"recipient_id": str(admin_user.id)},
        files={"file": ("secret.pdf", io.BytesIO(b"top secret content"), "application/pdf")},
    )
    transfer_id = upload_res.json()["id"]

    # 2. Sender lists transfers -> transfer is present
    list_res = await async_client.get(
        "/api/v1/transfers",
        cookies={"f9l3_session": sender_token},
    )
    assert list_res.status_code == 200
    assert any(t["id"] == transfer_id for t in list_res.json()["items"])

    # 3. Third user logins and attempts to view transfer details -> 403 Forbidden
    eve_login = await async_client.post(
        "/api/v1/auth/login",
        json={"username": third_user.username, "password": "StrongPassword123!"},
    )
    eve_token = eve_login.cookies["f9l3_session"]

    unauthorized_res = await async_client.get(
        f"/api/v1/transfers/{transfer_id}",
        cookies={"f9l3_session": eve_token},
    )
    assert unauthorized_res.status_code == 403
    assert unauthorized_res.json()["error"]["code"] == "AUTHORIZATION_DENIED"

    # 4. Third user lists transfers -> transfer is NOT present
    eve_list = await async_client.get(
        "/api/v1/transfers",
        cookies={"f9l3_session": eve_token},
    )
    assert eve_list.status_code == 200
    assert not any(t["id"] == transfer_id for t in eve_list.json()["items"])
