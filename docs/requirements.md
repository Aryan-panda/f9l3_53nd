# System Requirements Specification — f9l3_53nd

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  
**Classification**: Educational Security Engineering Specification  

---

## 1. System Vision & Objective

`f9l3_53nd` is an enterprise-grade secure file transfer platform designed to simulate secure, authenticated, and auditable data exchange between two distinct branch offices (Branch A and Branch B) across an untrusted network. The system enforces **defense-in-depth** by combining network-level encapsulation via WireGuard VPN with application-layer authenticated envelope encryption (AES-256-GCM), pre- and post-transfer cryptographic digest verification (SHA-256), strict role-based access control (Argon2id + HTTP-only sessions), and tamper-evident audit logging.

---

## 2. Protected Assets

The platform identifies and classifies the following assets:

| Asset ID | Asset Name | Sensitivity | Security Requirements |
| :--- | :--- | :--- | :--- |
| **AST-01** | **Plaintext File Payloads** | Critical | Confidentiality, Integrity, Non-repudiation |
| **AST-02** | **Encrypted File Payloads (Ciphertexts)** | High | Integrity, Availability, Path Traversal Protection |
| **AST-03** | **Master Key (KEK - Key Encryption Key)** | Critical | Strict Confidentiality, Isolation (never in DB or Git) |
| **AST-04** | **Data Encryption Keys (DEKs)** | Critical | Ephemeral existence, Wrapped at rest with KEK |
| **AST-05** | **User Credentials & Passwords** | Critical | Irreversible Hashing (Argon2id), Zero Plaintext Storage |
| **AST-06** | **Active User Sessions** | High | Unpredictability, HttpOnly, SameSite, Expiry, Revocation |
| **AST-07** | **Transfer Metadata & State Records** | Medium | Integrity, Complete Mediation (BOLA/IDOR protection) |
| **AST-08** | **Audit Logs & Security Events** | High | Tamper-evidence, Non-repudiation, Append-only |
| **AST-09** | **WireGuard VPN Configuration & Keys** | Critical | Transport Isolation, Private Key Secrecy |

---

## 3. User Roles & Permission Matrix

The platform strictly enforces two distinct user roles:

| Action / Capability | Anonymous | Authenticated USER | Authenticated ADMIN |
| :--- | :---: | :---: | :---: |
| **View Login Page / Authenticate** | ✅ | ✅ | ✅ |
| **View Own Identity (`/auth/me`)** | ❌ | ✅ | ✅ |
| **Initiate File Transfer Upload** | ❌ | ✅ | ✅ |
| **View Own Transfers List** | ❌ | ✅ | ✅ |
| **View Own Transfer Status & Detail** | ❌ | ✅ | ✅ |
| **Download Authorized Transferred Files**| ❌ | ✅ | ✅ |
| **View Other Users' Transfers** | ❌ | ❌ | ✅ |
| **Download Other Users' Transfers** | ❌ | ❌ | ❌ (Strict Deny) |
| **Manage System Users (List/Status)** | ❌ | ❌ | ✅ |
| **Inspect System-Wide Audit Log Events** | ❌ | ❌ | ✅ |
| **Inspect Security Failure Forensics** | ❌ | ❌ | ✅ |

---

## 4. Functional Requirements (FR)

### 4.1 Identity & Access Management (IAM)
- **FR-IAM-01 (Authentication)**: The system shall authenticate users via username and password, hashed using **Argon2id** (RFC 9106).
- **FR-IAM-02 (Session Handling)**: The system shall issue cryptographically unpredictable session identifiers stored exclusively in `HttpOnly`, `SameSite=Lax`, and `Secure`-aware HTTP cookies.
- **FR-IAM-03 (Session Lifecycle)**: The system shall support session expiration (default 24h) and explicit server-side session revocation upon logout or administrative action.
- **FR-IAM-04 (Brute-Force Protection)**: The system shall rate-limit failed authentication attempts to mitigate brute-force and credential-stuffing attacks without disclosing whether a username exists.
- **FR-IAM-05 (User Management)**: Administrators shall be able to list users, inspect account status, and deactivate accounts. Deactivated accounts must immediately lose all access.

### 4.2 File Ingestion & Pre-Processing
- **FR-ING-01 (Hostile Input Assumption)**: The server shall validate all incoming files assuming hostile input (validating size, filename sanitization, character sets, and path semantics).
- **FR-ING-02 (Storage Path Abstraction)**: The system shall never use user-supplied filenames as physical filesystem paths. Storage files shall be assigned UUID-derived internal paths outside the web root.
- **FR-ING-03 (Original Digest Computation)**: Prior to encryption, the sender system shall compute the **SHA-256** digest of the original plaintext payload.

### 4.3 Cryptographic Processing & Envelope Construction
- **FR-CRP-01 (Authenticated Encryption)**: The system shall encrypt file payloads using **AES-256-GCM** (NIST SP 800-38D).
- **FR-CRP-02 (Key Hierarchy)**: The system shall generate a cryptographically random 256-bit Data Encryption Key (DEK) per transfer. The DEK shall be wrapped using the 256-bit Key Encryption Key (KEK / Master Key).
- **FR-CRP-03 (Unique Nonce Generation)**: Every AES-GCM encryption shall utilize a 96-bit cryptographically secure random nonce (`os.urandom(12)`). Nonces shall never be reused under the same key.
- **FR-CRP-04 (AAD Binding)**: The system shall construct Authenticated Associated Data (AAD) containing transfer metadata (`protocol_version`, `transfer_id`, `sender_id`, `recipient_id`, `file_size`, `algorithm`) to bind ciphertext to its transfer context.
- **FR-CRP-05 (Envelope Structure)**: The system shall format the encrypted package into a versioned transfer envelope (`f9l3_v1`).

### 4.4 Transmission & State Machine Execution
- **FR-TRN-01 (Network Transport)**: File payload transmission between Branch A and Branch B shall occur over a dedicated **WireGuard VPN** tunnel.
- **FR-TRN-02 (Deterministic State Transitions)**: Transfers shall progress through a strict, sequential state machine:
  `CREATED` → `VALIDATING` → `HASHING` → `ENCRYPTING` → `READY` → `TRANSFERRING` → `RECEIVED` → `AUTHENTICATING` → `DECRYPTING` → `VERIFYING` → `COMPLETED`.
- **FR-TRN-03 (Replay Detection)**: The system shall reject duplicate, already-completed, or stale transfer IDs and payloads, transitioning replayed attempts to `REPLAY_DETECTED`.

### 4.5 Reception, Decryption & Verification
- **FR-REC-01 (AEAD Tag Authentication)**: Upon reception, the recipient subsystem shall verify the AES-GCM authentication tag and AAD. Any tampering shall immediately fail the transfer without outputting decrypted plaintext.
- **FR-REC-02 (Post-Decryption SHA-256 Verification)**: Upon successful GCM decryption, the recipient subsystem shall compute the SHA-256 digest of the resulting plaintext and compare it with the expected sender digest.
- **FR-REC-03 (Fail-Closed Quarantine)**: If either AES-GCM authentication or SHA-256 hash comparison fails, the payload shall be moved to isolated `storage/quarantine/`, the transfer marked `FAILED`, and an audit alert emitted.
- **FR-REC-04 (Authorized Retrieval)**: Only authorized recipients or senders shall be permitted to download verified, completed plaintext payloads.

### 4.6 Audit Subsystem & Reporting
- **FR-AUD-01 (Structured Audit Logging)**: All security-relevant events (`LOGIN_SUCCESS`, `LOGIN_FAILURE`, `TRANSFER_CREATED`, `TRANSFER_COMPLETED`, `DECRYPTION_FAILURE`, `INTEGRITY_MISMATCH`, `REPLAY_DETECTED`, `ACCESS_DENIED`) shall be recorded in structured JSON format with actor ID, timestamp, event type, severity, request ID, and transfer ID.
- **FR-AUD-02 (Tamper-Evident Chaining)**: Each audit log event shall incorporate a cryptographic digest including the digest of the previous log event to provide tamper evidence.
- **FR-AUD-03 (Zero Secret Leakage in Logs)**: Audit logs shall never contain passwords, password hashes, encryption keys, session tokens, or plaintext payload contents.

---

## 5. Security Requirements (SR)

| Requirement ID | Requirement Description | Threat Mitigated | Standard / Control |
| :--- | :--- | :--- | :--- |
| **SR-CONF-01** | AES-256-GCM encryption for all stored & transmitted file payloads. | Passive network eavesdropping, disk theft | NIST SP 800-38D / RFC 5116 |
| **SR-INT-01** | Dual-layer integrity: AES-GCM 128-bit tag + SHA-256 payload digest. | Ciphertext bit-flipping, payload tampering | FIPS 180-4 / NIST SP 800-38D |
| **SR-AUTH-01** | AAD binding of transfer ID, sender, recipient, and size to GCM tag. | Metadata tampering, ciphertext splicing | RFC 5116 Section 2.1 |
| **SR-NET-01** | Point-to-point WireGuard VPN tunnel between branches. | Man-in-the-Middle (MitM), routing hijack | Noise Protocol Framework |
| **SR-IAM-01** | Argon2id password hashing with memory and time cost parameters. | Offline dictionary and GPU rainbow attacks | RFC 9106 |
| **SR-IAM-02** | HttpOnly, SameSite=Lax, Secure session cookies. | Cross-Site Scripting (XSS) session theft | OWASP Session Management |
| **SR-AC-01** | Server-side complete mediation verifying user ownership on every transfer access. | Insecure Direct Object Reference (IDOR/BOLA) | OWASP ASVS v4.0 (V4) |
| **SR-RES-01** | Nonce uniqueness guaranteed; never reuse 96-bit nonce under same DEK. | GCM forbidden attack, key recovery | NIST SP 800-38D Section 8 |
| **SR-RES-02** | Replay detection cache tracking transfer tokens and sequence states. | Replay attacks, duplicate state injection | Transfer State Machine |
| **SR-STO-01** | Strict path canonicalization and UUID file storage outside web root. | Path traversal (`../`), arbitrary file overwrite | CWE-22, CWE-73 |
| **SR-ERR-01** | Uniform error envelopes returning generic error codes without stack traces. | Information disclosure, banner grabbing | CWE-209 |

---

## 6. Non-Functional Requirements (NFR)

### 6.1 Performance & Scalability
- **NFR-PERF-01 (Throughput)**: The backend shall process encryption and SHA-256 hashing at native OpenSSL / C-extension speeds (>= 50 MB/s on standard hardware).
- **NFR-PERF-02 (Memory Overhead)**: Cryptographic processing and file handling shall support chunked/buffered operations with peak memory consumption strictly bounded to <= 128 MB per active transfer.
- **NFR-PERF-03 (Payload Ceiling)**: Default maximum individual file transfer size shall be 50 MB in development/educational topology.

### 6.2 Reliability & Availability
- **NFR-REL-01 (Fail-Closed Operation)**: Any error condition (network timeout, storage write failure, verification failure) shall transition the transfer to a clean terminal error state without orphaned partial plaintexts.
- **NFR-REL-02 (Idempotency)**: Redundant status queries or re-requested transfer status shall return consistent state without side-effects.

### 6.3 Usability & Observability
- **NFR-OBS-01 (Health Probes)**: The application shall expose `/health/live` and `/health/ready` endpoints returning sub-10ms diagnostic checks for container orchestration.
- **NFR-UI-01 (Security Transparency)**: The React frontend shall clearly present transfer cryptographic status (AES-256-GCM, SHA-256 verification result, WireGuard transport indicator) to the user.

---

## 7. Assumptions, Dependencies & Constraints

### 7.1 Assumptions
1. The server OS hosts an uncompromised entropy pool (`/dev/urandom`).
2. The WireGuard private keys for Branch A and Branch B are securely provisioned during deployment.
3. Administrative users are trusted not to intentionally destroy their own physical hosting infrastructure.

### 7.2 Explicit Non-Goals (Out of Scope)
- **Out-of-Scope 1**: Protection against rootkits or kernel-level keyloggers on client user machines.
- **Out-of-Scope 2**: Multi-datacenter Byzantine fault-tolerant consensus mechanisms.
- **Out-of-Scope 3**: Direct public cloud HSM hardware integration (the educational model provides software KEK wrapping with production KMS migration pathways documented).
- **Out-of-Scope 4**: Arbitrary multi-gigabyte video streaming pipeline (the platform is optimized for secure document and payload transfer).

---

## 8. Quantitative Success Criteria

The system shall be evaluated against the following strict verification benchmarks:

1. **Cryptographic Correctness**: 100% pass rate across round-trip AES-256-GCM encryption/decryption, SHA-256 digest matching, and negative tests (single-bit flipped ciphertext, modified AAD, corrupted tag).
2. **Adversarial Resilience**: 100% detection and rejection of replay attempts, path traversal strings, unauthorized cross-user download attempts (IDOR), and tampered audit logs.
3. **Type Safety & Code Quality**: Zero type errors under `mypy --strict` and `tsc --noEmit`; zero lint violations under `ruff` and `eslint`.
4. **Test Suite Coverage**: Comprehensive automated unit, integration, and security test suites executable with a single `make test` command.

---

## 9. Assignment Traceability Matrix

| Assignment Requirement | Implementation in `f9l3_53nd` | Test Verification | Target Evidence |
| :--- | :--- | :--- | :--- |
| **AES-256 File Encryption** | AES-256-GCM with 96-bit nonce & AAD (`app.crypto.aead`) | `tests/unit/crypto/test_aead.py` | Encrypted envelope & round-trip verification |
| **SHA-256 Integrity Verification**| Pre/Post SHA-256 hashing (`app.crypto.hashing`) | `tests/unit/crypto/test_hashing.py` | Digest match and mismatch quarantine |
| **VPN Network Transport** | WireGuard point-to-point Branch A ↔ Branch B tunnel | `tests/integration/test_network.py` | Network isolation & topology verification |
| **User Authentication** | Argon2id password hashing + HTTP-only session cookies | `tests/unit/security/test_auth.py` | Login/logout and session protection |
| **File Upload & Handling** | Path-traversal safe storage with internal UUID paths | `tests/unit/storage/test_storage.py` | Hostile filename & traversal rejection |
| **Integrity Guard Action** | Fail-closed transfer abortion & quarantine on error | `tests/adversarial/test_tampering.py` | Transfer transitioned to `FAILED`/`QUARANTINED` |
| **Decryption Subsystem** | AES-GCM tag authentication prior to plaintext emission | `tests/adversarial/test_crypto_attacks.py` | Zero plaintext leakage on corrupted tags |
| **Activity Logging** | Structured audit events with tamper-evident hash chaining | `tests/unit/audit/test_audit.py` | Admin audit log inspector & digest chain |
