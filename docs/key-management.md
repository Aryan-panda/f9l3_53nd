# Key Management Architecture & Lifecycle Specification — f9l3_53nd

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  
**Classification**: Cryptographic Key Governance & Lifecycle Management  

---

## 1. Key Hierarchy Architecture

`f9l3_53nd` enforces a strict **Two-Tier Envelope Key Management Hierarchy** separating root key protection from file data protection:

```text
┌────────────────────────────────────────────────────────┐
│ LEVEL 1: Key Encryption Key (KEK / Master Key)         │
│  - 256-bit AES Key (AES-KW-256 / RFC 3394)             │
│  - Injected via environment (`MASTER_KEY_HEX`) / KMS   │
│  - Identified by version string (e.g. 'v1', 'v2')      │
│  - NEVER stored in PostgreSQL or filesystem            │
└───────────────────────────┬────────────────────────────┘
                            │
                            │ RFC 3394 AES Key Wrap
                            ▼
┌────────────────────────────────────────────────────────┐
│ LEVEL 2: Data Encryption Key (DEK)                     │
│  - Ephemeral 256-bit AES Key generated per transfer    │
│  - Used to encrypt/decrypt individual file payload     │
│  - Stored wrapped in PostgreSQL `key_references` table │
│  - Memory lifetime strictly bounded to active passes   │
└───────────────────────────┬────────────────────────────┘
                            │
                            │ AES-256-GCM
                            ▼
┌────────────────────────────────────────────────────────┐
│ Encrypted File Payload (`storage/encrypted/<uuid>/`)   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Key Lifecycle Stages

The lifecycle of every cryptographic key follows 7 formal NIST SP 800-57 stages:

```text
1. Generation ──► 2. Wrapping ──► 3. Storage ──► 4. Use (Active)
                                                     │
6. Destruction ◄── 5. Revocation ◄── 4b. Rotation ◄──┘
```

### Stage 1: Key Generation
- **DEK Generation**: Generated on-demand for every transfer via `os.urandom(32)` providing 256 bits of cryptographic entropy.
- **KEK Generation**: Generated during system deployment via `scripts/generate-dev-secrets.sh` (or AWS KMS / Vault HSM in production).

### Stage 2: Key Wrapping
- Ephemeral DEKs are wrapped immediately after generation using RFC 3394 AES Key Wrap:
  $$\text{WrappedDEK} = \text{AES-KeyWrap}_{\text{KEK}}(\text{DEK})$$
- Produces a 40-byte payload containing an 8-byte Integrity Check Value (`0xA6A6A6A6A6A6A6A6`).

### Stage 3: Storage at Rest
- Wrapped DEKs are stored in the PostgreSQL `key_references` table alongside `key_version` and `algorithm`.
- Plaintext DEKs are **never** written to persistent storage.

### Stage 4: Active Use
- Sender pipeline uses DEK to encrypt plaintext into AES-256-GCM ciphertext + 128-bit tag.
- Receiver pipeline unwraps DEK using the KEK to decrypt and verify the payload.

### Stage 4b: Key Rotation (KEK Rotation)
- **Problem**: When a master key reaches the end of its cryptoperiod or is rotated, re-encrypting gigabytes of file payloads on disk is computationally prohibitive and risks data corruption.
- **Envelope Rotation Solution**: Because files are encrypted with individual DEKs, rotating the master key only requires **re-wrapping the stored DEKs in the database**:
  $$\text{NewWrappedDEK} = \text{AES-KeyWrap}_{\text{KEK}_{\text{new}}}(\text{AES-KeyUnwrap}_{\text{KEK}_{\text{old}}}(\text{OldWrappedDEK}))$$
- Disk ciphertexts remain completely untouched and valid.

### Stage 5: Retirement & Revocation
- When a KEK version is retired, its status is marked `RETIRED`. It remains available for historical unwrapping during rotation passes.
- Compromised keys are marked `REVOKED`, immediately blocking decryption of associated transfers.

### Stage 6: Key Destruction & Memory Zeroization
- Plaintext DEK bytearrays are overwritten in RAM (`bytearray` zeroization) as soon as the cryptographic pass concludes.

---

## 3. Key Reference Database Schema

The `key_references` table connects transfer records to wrapped key material:

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | Primary Key | Random UUID |
| `transfer_id` | UUID | Unique, Foreign Key | References `transfers(id)` ON DELETE CASCADE |
| `wrapped_dek` | BYTEA | NOT NULL | 40-byte RFC 3394 wrapped DEK payload |
| `key_version` | VARCHAR(50) | NOT NULL | KEK version string (e.g. `'v1'`, `'v2'`) |
| `algorithm` | VARCHAR(30) | NOT NULL | `'AES-KW-256'` |
| `created_at` | TIMESTAMPTZ | NOT NULL | Timestamp of initial key generation |
| `rotated_at` | TIMESTAMPTZ | NULL | Timestamp of latest KEK re-wrapping |

---

## 4. Key Management Invariants & Defensive Controls

1. **Blast Radius Containment**: If an ephemeral DEK is exposed, only the single transfer encrypted with that DEK is compromised. The master KEK and all other transfers remain completely secure.
2. **Deterministic Unwrapping Verification**: RFC 3394 AES Key Wrap verifies the 64-bit integrity constant during unwrap. If the wrong KEK is provided or the wrapped key is corrupted by 1 bit, unwrapping throws `InvalidUnwrap` and fails closed.
3. **No Key Material in Logs**: Log formatters and exception handlers are strictly prohibited from serializing KEK, DEK, or wrapped key byte representations.
