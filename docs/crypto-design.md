# Cryptographic Design & Implementation Specification — f9l3_53nd

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  
**Classification**: Cryptographic Architecture & Primitive Specifications  

---

## 1. Cryptographic Architecture Overview

`f9l3_53nd` provides application-layer confidentiality, payload integrity, and metadata authenticity through standard, audited cryptographic primitives provided by the Python `cryptography` library (OpenSSL backend).

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CRYPTOGRAPHIC PRIMITIVES                        │
├──────────────────────────┬─────────────────────────────────────────────┤
│ **Payload AEAD**         │ AES-256-GCM (NIST SP 800-38D / RFC 5116)   │
│ **Integrity Guard**      │ SHA-256 (FIPS 180-4)                        │
│ **Key Wrapping**         │ AES Key Wrap 256-bit (NIST SP 800-38F / RFC 3394) │
│ **Password KDF**         │ Argon2id (RFC 9106)                         │
│ **Entropy Source**       │ OS CSPRNG (`os.urandom` / `/dev/urandom`)   │
│ **Envelope Format**      │ Versioned Binary/JSON Envelope (`f9l3_v1`)  │
└──────────────────────────┴─────────────────────────────────────────────┘
```

---

## 2. Key Management & Two-Tier Hierarchy

To prevent encrypting multiple distinct file payloads under a single static key, `f9l3_53nd` implements a two-tier key hierarchy:

```text
                       ┌─────────────────────────┐
                       │    Master Key (KEK)     │  256-bit AES Key
                       │ (Environment / Root KMS)│
                       └────────────┬────────────┘
                                    │
                                    │ AES Key Wrap (RFC 3394)
                                    ▼
                       ┌─────────────────────────┐
                       │ Ephemeral DEK (per file)│  256-bit Random AES Key
                       └────────────┬────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │                                               │
            ▼                                               ▼
┌───────────────────────┐                       ┌───────────────────────┐
│ AES-256-GCM Encrypt   │                       │ AES-256-GCM Decrypt   │
│ (Sender Pipeline)     │                       │ (Receiver Pipeline)   │
└───────────────────────┘                       └───────────────────────┘
```

### 2.1 Key Encryption Key (KEK)
- **Size**: 256 bits (32 bytes).
- **Format in Config**: 64-character hexadecimal string (`MASTER_KEY_HEX`).
- **Storage**: Never persisted to disk, database, or version control. Injected at process startup.
- **Purpose**: Exclusively used to wrap and unwrap ephemeral Data Encryption Keys.

### 2.2 Data Encryption Key (DEK)
- **Size**: 256 bits (32 bytes).
- **Generation**: High-entropy cryptographically secure random bytes generated uniquely per transfer (`os.urandom(32)`).
- **Wrapping**: Wrapped using RFC 3394 AES Key Wrap:
  $$\text{WrappedDEK} = \text{AES-KeyWrap}_{\text{KEK}}(\text{DEK})$$
- **Unwrapping**:
  $$\text{DEK} = \text{AES-KeyUnwrap}_{\text{KEK}}(\text{WrappedDEK})$$
- **Lifecycle**: Plaintext DEK resides in memory only during active encryption or decryption passes, after which its buffer is cleared.

---

## 3. AES-256-GCM AEAD Construction

### 3.1 Nonce (IV) Management
- **Size**: Standard 96 bits (12 bytes) as recommended by NIST SP 800-38D for Galois/Counter Mode.
- **Generation**: `os.urandom(12)` per encryption operation.
- **Security Invariant**: Nonces must **never** be reused under the same key. Because a fresh, unique DEK is generated for every transfer, the probability of nonce reuse under the same DEK is exactly zero.

### 3.2 Authenticated Associated Data (AAD) Construction
The system constructs a canonical byte string for Authenticated Associated Data (AAD) to bind transfer metadata to the ciphertext. The GCM authentication tag covers both the ciphertext and the AAD:

```text
AAD Canonical Serialization:
protocol_version|transfer_id|sender_id|recipient_id|file_size|algorithm
```

Example:
```text
f9l3_v1|9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d|11111111-1111-4111-8111-111111111111|22222222-2222-4222-8222-222222222222|1048576|AES-256-GCM
```

**Security Property**:
- If an adversary alters any metadata attribute in the database (e.g., changes `recipient_id` to redirect the file, or alters `file_size`), the GCM authentication tag verification will fail during decryption, aborting the transfer and releasing zero plaintext.

### 3.3 Encryption & Decryption Mathematics

$$\text{Encrypt}(K, IV, PT, AAD) \longrightarrow (CT, Tag_{128})$$
$$\text{Decrypt}(K, IV, CT, AAD, Tag_{128}) \longrightarrow PT \quad (\text{or } \bot \text{ on failure})$$

---

## 4. SHA-256 Digest Verification Architecture

SHA-256 operates as an independent, second layer of defense verifying the end-to-end integrity of the original plaintext.

```text
[SENDER]
Original Plaintext File ──► SHA-256 ──► Expected Digest (64 hex chars)
                                              │
                                              ▼ (Stored in DB transfers table)
[RECEIVER]
Decrypted Plaintext File ──► SHA-256 ──► Computed Digest (64 hex chars)
                                              │
                                              ▼
                                 Compare(Computed, Expected)
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                             │
                  [Match: True]                                [Match: False]
                       │                                             │
                       ▼                                             ▼
             Status: COMPLETED                             Status: QUARANTINED
       (Plaintext delivered to user)                 (Payload quarantined, alert emitted)
```

**Constant-Time Comparison**: Digest strings are compared using `hmac.compare_digest()` to prevent side-channel timing attacks.

---

## 5. Versioned Transfer Envelope (`f9l3_v1`)

The transfer envelope standardizes the binary/serialized packaging of an encrypted transfer for transport across WireGuard and storage on disk.

```text
┌────────────────────────────────────────────────────────┐
│ f9l3_v1 Transfer Envelope Structure                    │
├───────────────────┬──────────────┬─────────────────────┤
│ Field             │ Type / Size  │ Purpose             │
├───────────────────┼──────────────┼─────────────────────┤
│ magic_header      │ 4 bytes      │ ASCII "F9L3"        │
│ protocol_version  │ 2 bytes      │ uint16 (1 for v1)   │
│ algorithm_id      │ 1 byte       │ 0x01 (AES-256-GCM)  │
│ nonce             │ 12 bytes     │ 96-bit CSPRNG Nonce │
│ tag               │ 16 bytes     │ 128-bit GCM Tag     │
│ aad_length        │ 2 bytes      │ uint16 size of AAD  │
│ aad               │ variable     │ Canonical AAD bytes │
│ ciphertext_length │ 8 bytes      │ uint64 size of CT   │
│ ciphertext        │ variable     │ AES-256-GCM CT      │
└───────────────────┴──────────────┴─────────────────────┘
```

---

## 6. Cryptographic Error Handling & Fail-Closed Hierarchy

All cryptographic errors derive from `app.core.exceptions.CryptoError` and guarantee fail-closed behavior:

| Exception Class | Trigger Condition | HTTP Status | Action Taken |
| :--- | :--- | :---: | :--- |
| `DecryptionError` | GCM tag mismatch, corrupted ciphertext, modified AAD, wrong DEK | 400 Bad Request | Abort transfer, transition to `QUARANTINED`, emit `DECRYPTION_FAILURE` audit log |
| `IntegrityError` | SHA-256 post-decryption digest mismatch | 400 Bad Request | Abort transfer, transition to `QUARANTINED`, emit `INTEGRITY_MISMATCH` audit log |
| `KeyWrappingError` | RFC 3394 unwrapping tag failure, corrupted KEK | 500 Server Error | Abort transfer, emit `KEY_UNWRAP_FAILURE` audit log |
| `EnvelopeParseError`| Invalid magic header, unsupported version, truncated payload | 400 Bad Request | Reject envelope, transition to `REJECTED` |
