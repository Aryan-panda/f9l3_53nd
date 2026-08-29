import io
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CryptoError,
    DecryptionError,
    ReplayError,
    StorageError,
)
from app.crypto.aead import decrypt_payload, encrypt_payload
from app.crypto.envelope import TransferEnvelope, pack_envelope, unpack_envelope
from app.models.user import User
from app.storage.paths import get_encrypted_payload_path, sanitize_filename
from app.transfer.replay import ReplayDetector


@pytest.mark.security
@pytest.mark.adversarial
def test_adversarial_aead_bit_flipping() -> None:
    """Adversary flips single bit in ciphertext; AEAD tag verification fails."""
    key = b"\x00" * 32
    plaintext = b"CONFIDENTIAL ADVERSARIAL TEST DATA"
    aad = b"transfer_id=123;sender=alice;version=1"

    ciphertext, tag, nonce = encrypt_payload(plaintext, key, aad)

    # Flip 1 bit in ciphertext
    corrupted_ciphertext = bytearray(ciphertext)
    corrupted_ciphertext[0] ^= 0x01

    with pytest.raises(DecryptionError, match="AEAD tag authentication failed"):
        decrypt_payload(bytes(corrupted_ciphertext), tag, nonce, key, aad)


@pytest.mark.security
@pytest.mark.adversarial
def test_adversarial_forged_aad_tampering() -> None:
    """Adversary modifies associated metadata (AAD); AEAD tag verification fails."""
    key = b"\x11" * 32
    plaintext = b"TOP SECRET EXECUTIVE MEMO"
    original_aad = b"transfer_id=456;recipient=bob;file_size=25"
    forged_aad = b"transfer_id=456;recipient=eve;file_size=25"

    ciphertext, tag, nonce = encrypt_payload(plaintext, key, original_aad)

    # Tag fails verification when forged AAD is passed
    with pytest.raises(DecryptionError, match="AEAD tag authentication failed"):
        decrypt_payload(ciphertext, tag, nonce, key, forged_aad)


@pytest.mark.security
@pytest.mark.adversarial
def test_adversarial_corrupted_tag_truncation() -> None:
    """Adversary truncates or modifies the 16-byte authentication tag."""
    key = b"\x22" * 32
    plaintext = b"FINANCIAL TRANSACTION"
    aad = b"version=1"

    ciphertext, tag, nonce = encrypt_payload(plaintext, key, aad)

    # Corrupt tag
    corrupted_tag = bytearray(tag)
    corrupted_tag[-1] ^= 0xFF

    with pytest.raises(DecryptionError):
        decrypt_payload(ciphertext, bytes(corrupted_tag), nonce, key, aad)

    # Truncated tag
    with pytest.raises(DecryptionError):
        decrypt_payload(ciphertext, tag[:12], nonce, key, aad)


@pytest.mark.security
@pytest.mark.adversarial
def test_adversarial_corrupted_nonce() -> None:
    """Adversary modifies the 12-byte CSPRNG nonce."""
    key = b"\x33" * 32
    plaintext = b"COMMAND PAYLOAD"
    aad = b"version=1"

    ciphertext, tag, nonce = encrypt_payload(plaintext, key, aad)

    corrupted_nonce = bytearray(nonce)
    corrupted_nonce[0] ^= 0xAA

    with pytest.raises(DecryptionError):
        decrypt_payload(ciphertext, tag, bytes(corrupted_nonce), key, aad)


@pytest.mark.security
@pytest.mark.adversarial
def test_adversarial_malformed_envelope_headers() -> None:
    """Adversary provides corrupted envelope magic bytes, versions, or lengths."""
    # 1. Invalid Magic Bytes
    invalid_magic = b"EVIL" + (b"\x00" * 60)
    with pytest.raises(CryptoError, match="Invalid envelope magic"):
        unpack_envelope(invalid_magic)

    # 2. Truncated Header (shorter than expected)
    truncated_header = b"F9L3\x01\x00\x00"
    with pytest.raises(CryptoError, match="too small"):
        unpack_envelope(truncated_header)

    # 3. Valid Envelope packed and unpacked cleanly
    env = TransferEnvelope(
        protocol_version=1,
        algorithm_id=1,
        nonce=b"\x88" * 12,
        tag=b"\x77" * 16,
        aad=b"transfer_aad",
        ciphertext=b"test payload ciphertext",
    )
    packed = pack_envelope(env)
    unpacked = unpack_envelope(packed)
    assert unpacked.ciphertext == env.ciphertext
    assert unpacked.tag == env.tag
    assert unpacked.nonce == env.nonce


@pytest.mark.security
@pytest.mark.adversarial
def test_adversarial_path_traversal_sanitization() -> None:
    """Verify robust rejection/neutralization of path traversal patterns."""
    assert sanitize_filename("../../../etc/shadow") == "shadow"
    assert sanitize_filename("..\\..\\Windows\\System32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("safe_file.txt\x00.exe") == "safe_file.txt.exe"
    assert sanitize_filename("/var/log/audit.log") == "audit.log"
    assert sanitize_filename("../..") == "sanitized_payload.bin"

    # Base directory escape prevention
    with pytest.raises(StorageError):
        get_encrypted_payload_path("../../escaped_dir")


@pytest.mark.security
@pytest.mark.adversarial
async def test_adversarial_path_traversal_upload_rejection(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Malicious user attempts path traversal in uploaded filename."""
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    token = login_res.cookies["f9l3_session"]

    # Upload with directory traversal filename
    upload_res = await async_client.post(
        "/api/v1/transfers",
        cookies={"f9l3_session": token},
        data={"recipient_id": str(admin_user.id)},
        files={"file": ("../../../../etc/passwd", io.BytesIO(b"malicious"), "text/plain")},
    )
    assert upload_res.status_code == 201
    stored_name = upload_res.json()["filename"]
    assert ".." not in stored_name
    assert "/" not in stored_name


@pytest.mark.security
@pytest.mark.adversarial
async def test_adversarial_unauthorized_idor_access(
    async_client: AsyncClient,
    sample_user: User,
    admin_user: User,
) -> None:
    """Attacker attempts IDOR to download a nonexistent or foreign transfer."""
    login_alice = await async_client.post(
        "/api/v1/auth/login",
        json={"username": sample_user.username, "password": "StrongPassword123!"},
    )
    alice_token = login_alice.cookies["f9l3_session"]

    random_id = uuid4()
    bad_download = await async_client.get(
        f"/api/v1/transfers/{random_id}/download",
        cookies={"f9l3_session": alice_token},
    )
    assert bad_download.status_code == 404


@pytest.mark.security
@pytest.mark.adversarial
def test_adversarial_replay_attack_burst(db_session: AsyncSession) -> None:
    """Adversary submits burst of 10 identical transfers; only 1 is accepted."""
    detector = ReplayDetector(ttl_seconds=60.0)
    transfer_id = uuid4()
    nonce = b"\x99" * 12

    detector.check_and_record(transfer_id, nonce)

    rejections = 0
    for _ in range(9):
        try:
            detector.check_and_record(transfer_id, nonce)
        except ReplayError:
            rejections += 1

    assert rejections == 9
