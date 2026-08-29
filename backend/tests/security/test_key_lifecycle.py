import uuid

import pytest

from app.core.config import Settings
from app.core.exceptions import CryptoError
from app.crypto.aead import AES256GCMCipher, build_canonical_aad
from app.crypto.nonce import generate_nonce
from app.services.key_service import KeyService


@pytest.mark.security
def test_key_rotation_without_payload_reencryption() -> None:
    """Security Test: Verify KEK rotation re-wraps DEKs while ciphertexts on disk remain valid."""
    kek_v1_hex = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
    kek_v2_hex = "a0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf"

    settings_v1 = Settings(MASTER_KEY_HEX=kek_v1_hex)
    service_v1 = KeyService(settings=settings_v1)

    transfer_id = uuid.uuid4()
    sender_id = uuid.uuid4()
    recipient_id = uuid.uuid4()
    plaintext = b"Strategic enterprise confidential file payload."

    # 1. Create transfer key under KEK v1
    dek, key_ref = service_v1.create_transfer_key(transfer_id)
    assert key_ref.key_version == "v1"

    # 2. Encrypt payload using the DEK
    nonce = generate_nonce()
    aad = build_canonical_aad(
        protocol_version="f9l3_v1",
        transfer_id=str(transfer_id),
        sender_id=str(sender_id),
        recipient_id=str(recipient_id),
        file_size=len(plaintext),
    )
    cipher = AES256GCMCipher(dek)
    ciphertext, tag = cipher.encrypt(plaintext, nonce, aad)

    # 3. Simulate Key Rotation on Server (Register KEK v2 and rotate wrapped DEK)
    kek_v2_bytes = bytes.fromhex(kek_v2_hex)
    service_v1.manager.register_kek_version(kek_v2_bytes, version="v2", set_primary=True)

    new_wrapped_dek, new_version = service_v1.rotate_transfer_key(
        wrapped_dek=key_ref.wrapped_dek,
        current_version=key_ref.key_version,
        target_version="v2",
    )
    assert new_version == "v2"
    assert new_wrapped_dek != key_ref.wrapped_dek

    # 4. Decrypt payload using the rotated DEK (unwrapped via KEK v2)
    recovered_dek = service_v1.unwrap_transfer_key(new_wrapped_dek, "v2")
    assert recovered_dek == dek

    decrypt_cipher = AES256GCMCipher(recovered_dek)
    decrypted_payload = decrypt_cipher.decrypt(ciphertext, tag, nonce, aad)

    assert decrypted_payload == plaintext


@pytest.mark.security
def test_tampered_wrapped_dek_attack_fails_closed() -> None:
    """Security Test: Attacker tampering with wrapped DEK bytes in DB fails unwrap."""
    kek_hex = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
    service = KeyService(settings=Settings(MASTER_KEY_HEX=kek_hex))

    transfer_id = uuid.uuid4()
    _, key_ref = service.create_transfer_key(transfer_id)

    # Tamper with 1 byte of wrapped DEK in database
    corrupted_wrapped = bytearray(key_ref.wrapped_dek)
    corrupted_wrapped[10] ^= 0xFF

    with pytest.raises(CryptoError, match="integrity check failed"):
        service.unwrap_transfer_key(bytes(corrupted_wrapped), key_ref.key_version)
