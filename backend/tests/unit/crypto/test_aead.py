import os

import pytest

from app.core.exceptions import CryptoError, DecryptionError
from app.crypto.aead import (
    AES256GCMCipher,
    build_canonical_aad,
    decrypt_payload,
    encrypt_payload,
)
from app.crypto.keys import generate_dek
from app.crypto.nonce import generate_nonce


@pytest.mark.unit
def test_aead_roundtrip_with_aad() -> None:
    """Test successful encryption and decryption with canonical AAD."""
    key = generate_dek()
    nonce = generate_nonce()
    plaintext = b"Top secret enterprise payload for Branch B."
    aad = build_canonical_aad(
        protocol_version="f9l3_v1",
        transfer_id="11111111-2222-3333-4444-555555555555",
        sender_id="aaaa-1111",
        recipient_id="bbbb-2222",
        file_size=len(plaintext),
    )

    cipher = AES256GCMCipher(key)
    ciphertext, tag = cipher.encrypt(plaintext, nonce, aad)

    assert len(tag) == 16
    assert ciphertext != plaintext

    recovered = cipher.decrypt(ciphertext, tag, nonce, aad)
    assert recovered == plaintext


@pytest.mark.unit
def test_aead_roundtrip_empty_payload() -> None:
    """Test encryption and decryption of an empty payload."""
    key = generate_dek()
    nonce = generate_nonce()
    plaintext = b""

    cipher = AES256GCMCipher(key)
    ciphertext, tag = cipher.encrypt(plaintext, nonce)
    assert len(ciphertext) == 0
    assert len(tag) == 16

    recovered = cipher.decrypt(ciphertext, tag, nonce)
    assert recovered == b""


@pytest.mark.unit
def test_aead_corrupted_ciphertext_byte_rejection() -> None:
    """Tampering with 1 byte of ciphertext MUST raise DecryptionError."""
    key = generate_dek()
    nonce = generate_nonce()
    plaintext = b"Critical financial transfer records."

    cipher = AES256GCMCipher(key)
    ciphertext, tag = cipher.encrypt(plaintext, nonce)

    # Flip one byte in the middle of the ciphertext
    corrupted_ct = bytearray(ciphertext)
    corrupted_ct[5] ^= 0xFF
    corrupted_bytes = bytes(corrupted_ct)

    with pytest.raises(DecryptionError, match="AEAD tag authentication failed"):
        cipher.decrypt(corrupted_bytes, tag, nonce)


@pytest.mark.unit
def test_aead_corrupted_tag_rejection() -> None:
    """Tampering with the authentication tag MUST raise DecryptionError."""
    key = generate_dek()
    nonce = generate_nonce()
    plaintext = b"Payload with tampered tag test."

    cipher = AES256GCMCipher(key)
    ciphertext, tag = cipher.encrypt(plaintext, nonce)

    corrupted_tag = bytearray(tag)
    corrupted_tag[0] ^= 0x01

    with pytest.raises(DecryptionError):
        cipher.decrypt(ciphertext, bytes(corrupted_tag), nonce)


@pytest.mark.unit
def test_aead_corrupted_aad_rejection() -> None:
    """Tampering with Authenticated Associated Data MUST raise DecryptionError."""
    key = generate_dek()
    nonce = generate_nonce()
    plaintext = b"Payload bound to specific transfer metadata."
    aad_valid = b"transfer-id-001|recipient-alice"
    aad_tampered = b"transfer-id-001|recipient-attacker"

    cipher = AES256GCMCipher(key)
    ciphertext, tag = cipher.encrypt(plaintext, nonce, aad_valid)

    # Attempt decryption with modified AAD
    with pytest.raises(DecryptionError):
        cipher.decrypt(ciphertext, tag, nonce, aad_tampered)


@pytest.mark.unit
def test_aead_wrong_key_rejection() -> None:
    """Attempting decryption with a different key MUST raise DecryptionError."""
    key_correct = generate_dek()
    key_wrong = generate_dek()
    nonce = generate_nonce()
    plaintext = b"Payload protected with key 1."

    ciphertext, tag, _ = encrypt_payload(plaintext, key_correct, nonce=nonce)

    with pytest.raises(DecryptionError):
        decrypt_payload(ciphertext, tag, nonce, key_wrong)


@pytest.mark.unit
def test_aead_wrong_nonce_rejection() -> None:
    """Attempting decryption with a different nonce MUST raise DecryptionError."""
    key = generate_dek()
    nonce1 = generate_nonce()
    nonce2 = generate_nonce()
    plaintext = b"Payload with nonce test."

    cipher = AES256GCMCipher(key)
    ciphertext, tag = cipher.encrypt(plaintext, nonce1)

    with pytest.raises(DecryptionError):
        cipher.decrypt(ciphertext, tag, nonce2)


@pytest.mark.unit
def test_aead_large_payload() -> None:
    """Test AEAD handling with a multi-megabyte binary payload."""
    key = generate_dek()
    nonce = generate_nonce()
    large_plaintext = os.urandom(2 * 1024 * 1024)  # 2 MB random data

    cipher = AES256GCMCipher(key)
    ciphertext, tag = cipher.encrypt(large_plaintext, nonce)
    recovered = cipher.decrypt(ciphertext, tag, nonce)

    assert recovered == large_plaintext


@pytest.mark.unit
def test_aead_invalid_key_length() -> None:
    """Instantiating AES256GCMCipher with key length other than 32 bytes must fail."""
    with pytest.raises(CryptoError, match="must be exactly 32 bytes"):
        AES256GCMCipher(b"short-16-byte-k!")
