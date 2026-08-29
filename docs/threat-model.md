# Threat Model & Vulnerability Analysis — f9l3_53nd

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  
**Classification**: Formal Threat Model (STRIDE Methodology)  

---

## 1. Executive Summary

This document provides a comprehensive, rigorous threat model for `f9l3_53nd` based on the **STRIDE** methodology (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege). The threat model evaluates threats against all trust boundaries, assets, and attack surfaces, detailing defensive controls and residual risk.

### Sub-Document Index:
- [Assets & Data Classification](threat-model/assets.md)
- [Threat Actors & Adversary Personas](threat-model/actors.md)
- [Attack Surface Analysis](threat-model/attack-surface.md)
- [Threat Mitigations & STRIDE Controls](threat-model/mitigations.md)
- [Residual Risk & Operational Limitations](threat-model/residual-risk.md)

---

## 2. Threat Modeling Methodology (STRIDE)

```text
┌───────────────────────────┬────────────────────────────────────────────────────────┐
│ STRIDE Category           │ Core Security Property Violated                        │
├───────────────────────────┼────────────────────────────────────────────────────────┤
│ **S** — Spoofing Identity │ Authentication (Impersonating an authorized user/node) │
│ **T** — Tampering with Data│ Integrity (Altering ciphertexts, hashes, or metadata)  │
│ **R** — Repudiation       │ Non-repudiation (Denying performed actions or transfers│
│ **I** — Info Disclosure   │ Confidentiality (Eavesdropping plaintext or keys)      │
│ **D** — Denial of Service │ Availability (Exhausting CPU, memory, or disk quotas)  │
│ **E** — Elevation of Priv │ Authorization (Gaining unauthorized administrative data│
└───────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow Diagram (DFD) & Threat Boundaries

```text
                  [ Untrusted Client Zone ]
                             │
                             │ (1) User Credentials / Upload Payload
                             ▼
                    ┌─────────────────┐
  ==================│   Web Client    │==================== [ Boundary B-1: Client/API ]
                    └────────┬────────┘
                             │ (2) HTTPS POST / Multipart + Cookie
                             ▼
                    ┌─────────────────┐
                    │   FastAPI API   │
                    └────────┬────────┘
                             │ (3) Authorize & Validate
                             ▼
                    ┌─────────────────┐
                    │  Crypto Service │
                    │  (AES-256-GCM)  │
                    └────────┬────────┘
                             │ (4) Wrapped DEK / Encrypted Payload
                             ▼
  ==================│ WireGuard Tunnel│==================== [ Boundary B-3: Branch-to-Branch ]
                    └────────┬────────┘
                             │ (5) Encrypted UDP (Noise Protocol)
                             ▼
                    ┌─────────────────┐
                    │ Receiver Branch │
                    │ (AEAD + SHA256) │
                    └────────┬────────┘
                             │ (6) Quarantined / Stored
                             ▼
  ==================│ Database/Storage│==================== [ Boundary B-2: Application/Storage ]
                    └─────────────────┘
```

---

## 4. Comprehensive STRIDE Threat Analysis

### 4.1 Spoofing (S)
1. **Threat S-1: Session Hijacking via Stolen Cookie**
   - *Impact*: Attacker acts as legitimate user.
   - *Control*: Session cookies are `HttpOnly` (mitigates XSS extraction), `SameSite=Lax` (mitigates CSRF), and bound to server-side session revocation tracking.
2. **Threat S-2: WireGuard Endpoint Impersonation**
   - *Impact*: Rogue peer connects to branch network.
   - *Control*: Cryptographic public-key peer authentication using Curve25519 in WireGuard handshake.

### 4.2 Tampering (T)
1. **Threat T-1: Ciphertext Bit-Flipping in Transit**
   - *Impact*: Corrupted or malicious payload delivered.
   - *Control*: AES-256-GCM 128-bit authentication tag verification. Decryption throws `DecryptionError` and aborts if any bit is modified.
2. **Threat T-2: Metadata Modification (Sender/Recipient/Size)**
   - *Impact*: Payload delivered to unauthorized recipient or re-associated with different transfer.
   - *Control*: Authenticated Associated Data (AAD) binds `transfer_id`, `sender_id`, `recipient_id`, and `file_size` directly into the GCM tag.
3. **Threat T-3: Original Payload Substitution with Valid Tag**
   - *Impact*: Attacker creates a different valid encrypted file under their own key.
   - *Control*: Pre-calculated SHA-256 digest comparison post-decryption. If digest does not match expected sender digest, transfer transitions to `FAILED`/`QUARANTINED`.

### 4.3 Repudiation (R)
1. **Threat R-1: Sender Denies Uploading Specific File**
   - *Impact*: Lack of accountability in enterprise audit.
   - *Control*: Audit logging records `TRANSFER_CREATED` event capturing `actor_id`, `timestamp`, `source_ip`, `original_filename`, `file_size`, and `sha256_digest`.
2. **Threat R-2: Administrator Retroactively Deletes Log Entries**
   - *Impact*: Forensic evidence destruction.
   - *Control*: Cryptographic SHA-256 digest chaining across audit log events.

### 4.4 Information Disclosure (I)
1. **Threat I-1: Passive Network Eavesdropping**
   - *Impact*: Plaintext exposure to network sniffers.
   - *Control*: Dual-layer encryption: WireGuard VPN tunnel (ChaCha20-Poly1305) + Application AEAD (AES-256-GCM).
2. **Threat I-2: Insecure Direct Object Reference (IDOR/BOLA)**
   - *Impact*: User A downloads User B's files by modifying transfer UUID in URL.
   - *Control*: Service layer complete mediation enforcing `sender_id == current_user.id OR recipient_id == current_user.id OR role == 'ADMIN'`.
3. **Threat I-3: Error Traceback Leakage**
   - *Impact*: Database schemas and file paths exposed to attacker.
   - *Control*: Centralized exception handler maps errors to generic JSON envelopes.

### 4.5 Denial of Service (D)
1. **Threat D-1: Memory Exhaustion via Gigabyte Uploads**
   - *Impact*: Application crashes (OOM killer).
   - *Control*: Strict max upload limit (50 MB) + streaming chunk validation with bounded 128 MB RAM usage.
2. **Threat D-2: Password Brute-Force Exhaustion**
   - *Impact*: CPU starvation from Argon2id computation.
   - *Control*: In-memory token-bucket rate limiting on `/auth/login` endpoint.

### 4.6 Elevation of Privilege (E)
1. **Threat E-1: Vertical Privilege Escalation to Admin**
   - *Impact*: Unprivileged user accesses audit logs or modifies user statuses.
   - *Control*: FastAPI dependency injection guards (`require_admin`) verifying database role state.
2. **Threat E-2: Path Traversal Arbitrary File Overwrite**
   - *Impact*: Writing outside storage root to overwrite system files.
   - *Control*: Storage decoupling using internal UUID paths and strict canonical path verification.

---

## 5. Defensive Verification Plan

Every threat scenario documented above is mapped to an automated adversarial test in the test suite:

| Threat ID | Adversarial Test Module | Expected Behavior |
| :--- | :--- | :--- |
| **T-1** | `tests/adversarial/test_tampering.py::test_tampered_ciphertext_rejection` | `DecryptionError` raised, state → `QUARANTINED` |
| **T-2** | `tests/adversarial/test_tampering.py::test_tampered_aad_rejection` | `DecryptionError` raised, state → `QUARANTINED` |
| **T-3** | `tests/adversarial/test_tampering.py::test_sha256_mismatch_rejection` | `IntegrityError` raised, state → `QUARANTINED` |
| **I-2** | `tests/security/test_idor.py::test_user_cannot_access_other_transfers` | `403 Forbidden` / `404 Not Found` |
| **E-1** | `tests/security/test_rbac.py::test_user_cannot_access_admin_audit` | `403 Forbidden` |
| **E-2** | `tests/security/test_traversal.py::test_path_traversal_filename_sanitization` | Internal UUID path used, traversal rejected |
