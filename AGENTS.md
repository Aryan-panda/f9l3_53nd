# AGENTS.md — Engineering & Governance Rules for `f9l3_53nd`

> **Note for AI Coding Agents and Developers**: Every coding or architecture session MUST begin by reviewing this document. Do not violate the constraints defined herein.

---

## 1. Project Purpose & Scope

`f9l3_53nd` is a secure, authenticated, and auditable file transfer platform designed to simulate encrypted, verified communication between two distinct branch offices (Branch A and Branch B) across an untrusted network.

### Core Security Objectives:
1. **Confidentiality**: Application-layer authenticated encryption using **AES-256-GCM** with unique nonces.
2. **Integrity & Authenticity**: SHA-256 digest calculation on original files, combined with AEAD ciphertext authentication tags and authenticated associated data (AAD).
3. **Secure Connectivity**: Point-to-point network transport through **WireGuard VPN**.
4. **Identity & Access Management**: Secure server-side sessions with **Argon2id** password hashing and role-based access control (RBAC: `USER`, `ADMIN`).
5. **Auditability**: Tamper-evident structured audit logging recording all security-sensitive events.
6. **Resilience & Fail-Closed Behavior**: Explicit state machine preventing partial execution, replayed payloads, IDOR/BOLA attacks, and malformed inputs.

---

## 2. Phased Development Model & Phase Gates

Development is strictly partitioned into sequential phases (Phases 0 through 19).
- **Rule**: Never jump ahead or build entire subsystems in a single pass.
- **Rule**: At the end of every phase, an explicit Phase Report matching the standard template must be generated, and execution must STOP at the phase gate.
- **Rule**: Do not infer approval or proceed to the next phase without explicit user confirmation (`Proceed to Phase X`).

---

## 3. Directory Ownership & Monorepo Structure

```text
f9l3_53nd/
├── docs/                 # Architectural specifications, threat models, ADRs, protocols
├── backend/              # FastAPI application, domain services, crypto, storage, audit, tests
├── frontend/             # React, TypeScript, Vite, Tailwind CSS web client
├── infra/                # Dockerfiles, docker-compose, PostgreSQL init, WireGuard topologies
├── scripts/              # Developer automation (bootstrap, test, security-test, keygen)
└── storage/              # Encrypted, quarantine, and temporary file payload stores
```

### Module Responsibilities:
- `backend/src/app/api/`: Request validation, routing, dependency injection, HTTP status mapping. No business or crypto logic directly in route handlers.
- `backend/src/app/services/`: Application orchestration, state coordination.
- `backend/src/app/crypto/`: AES-256-GCM AEAD, SHA-256 hashing, key wrapping, nonce generation.
- `backend/src/app/security/`: Argon2id password hashing, session lifecycle, authorization guards, rate limiting.
- `backend/src/app/transfer/`: Transfer state machine, protocol envelope serialization, replay detection.
- `backend/src/app/storage/`: Path traversal-safe filesystem operations, quarantine isolation.
- `backend/src/app/audit/`: Structured audit event generation and integrity hashing.

---

## 4. Cryptographic Rules (Absolute Non-Negotiables)

1. **Approved Primitives**:
   - Primary AEAD: `AES-256-GCM` via Python `cryptography` library.
   - Integrity Hashing: `SHA-256`.
   - Password KDF / Hashing: `Argon2id`.
   - Key Wrapping: Key Encryption Key (KEK) wrapping per-transfer Data Encryption Keys (DEKs).
2. **Forbidden**:
   - Custom implementations of AES, SHA-256, Argon2, HKDF, or random number generators.
   - ECB, CBC without authenticated HMAC, or unauthenticated encryption modes.
   - Hardcoding encryption keys, master keys, or passwords.
   - Storing long-term cryptographic master keys in browser JavaScript / localStorage.
3. **Nonce Management**:
   - Standard 96-bit (12-byte) cryptographically secure random nonces (`os.urandom(12)`).
   - Never reuse a nonce under the same key.
4. **AAD (Additional Authenticated Data)**:
   - Must bind transfer metadata (e.g., `protocol_version`, `transfer_id`, `sender_id`, `file_size`) into the GCM authentication tag.

---

## 5. Security & Secure Coding Rules

1. **Fail-Closed & Deny by Default**: Any error during authentication, authorization, decryption, or SHA-256 verification must immediately abort the transfer, transition state to `FAILED`/`QUARANTINED`, and emit an audit event.
2. **No Data Leaks**: Never expose raw stack traces, database exceptions, internal file paths, or cryptographic keys in API responses or logs.
3. **IDOR / BOLA Prevention**: Verify resource ownership on every transfer access, status query, and download.
4. **Input & Path Validation**: File inputs must be checked for traversal patterns (`../`, absolute paths, null bytes, suspicious extensions). Filenames are stored only as database metadata; physical storage uses UUID-derived paths.
5. **No False Claims**: Never describe the system as "100% secure" or "unhackable". Security is defined strictly by threat models, controls, and residual risk.

---

## 6. Testing & Quality Standards

- **Test Pyramid**: Unit tests -> Integration tests -> API tests -> Adversarial attack tests.
- **Mandatory Crypto Tests**: Round-trip encryption, corrupted ciphertext byte rejection, corrupted AAD rejection, wrong key rejection, SHA-256 mismatch detection, nonce uniqueness.
- **Mandatory Security Tests**: Replay attack detection, IDOR injection attempts, privilege escalation checks, path traversal injection.
- **Tooling**:
  - Backend: `pytest`, `pytest-asyncio`, `ruff` (linter/formatter), `mypy` (strict type checking).
  - Frontend: `tsc --noEmit` (TypeScript strict mode), `eslint`.

---

## 7. Secret Handling & Git Conventions

- **Never Commit Secrets**: No `.env` files, `.pem`/`.key` files, WireGuard private keys, or passwords in Git.
- **Conventional Commits**:
  - `feat:` New capability or endpoint
  - `fix:` Bug fix
  - `security:` Cryptographic or access-control hardening
  - `test:` Test suite addition or attack test
  - `docs:` Architectural decisions, threat models, guides
  - `chore:` Tooling, deps, configuration

---

## 8. Definition of Done (DoD)

A component or phase is only DONE when:
1. Architectural intent and threat model alignment are documented in `docs/`.
2. Code satisfies strict typing and linting checks.
3. Automated unit and negative/adversarial tests exist and pass.
4. No sensitive information is leaked in logs or error responses.
5. Verification results are presented in the phase report.
