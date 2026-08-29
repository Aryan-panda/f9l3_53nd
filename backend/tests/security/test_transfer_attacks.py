import io

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.storage.paths import sanitize_filename


@pytest.mark.security
def test_path_traversal_filename_sanitization() -> None:
    """Security Test: Path traversal sequences must be stripped from filenames."""
    dirty_names = [
        ("../../../../../etc/passwd", "passwd"),
        ("..\\..\\..\\windows\\system32\\cmd.exe", "cmd.exe"),
        ("evil/payload/../../something.txt", "something.txt"),
        ("\x00hidden.exe", "hidden.exe"),
        ("../", "sanitized_payload.bin"),
        ("", "unnamed_payload.bin"),
    ]
    for raw, _expected in dirty_names:
        safe = sanitize_filename(raw)
        assert "/" not in safe

        assert "\\" not in safe
        assert "\x00" not in safe
        assert ".." not in safe


@pytest.mark.security
async def test_path_traversal_upload_injection_neutralized(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Security Test: Uploading a file with path traversal in filename is safely sanitized."""
    # Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    malicious_filename = "../../../etc/shadow.txt"
    files = {"file": (malicious_filename, io.BytesIO(b"malicious intent"), "text/plain")}
    data = {"recipient_id": str(admin_user.id)}

    res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": token},
        data=data,
        files=files,
    )
    assert res.status_code == 201
    transfer = res.json()
    assert transfer["filename"] == "shadow.txt"
    assert ".." not in transfer["filename"]
