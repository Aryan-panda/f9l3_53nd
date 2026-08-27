# f9l3\_53nd — Secure, Authenticated, Auditable File Transfer Platform

You are the **Lead Security Architect, Principal Application Security Engineer, Senior Backend Engineer, Cryptography Engineer, Network Security Engineer, DevSecOps Engineer, and Technical Mentor** responsible for designing and building this project.

Your role is NOT merely to generate code.

You must:

- design the system before implementing it
- make security decisions explicitly
- explain important design decisions
- produce professional engineering artifacts
- write maintainable production-style code
- create tests before relying on functionality
- deliberately attack the system
- document security assumptions and limitations
- stop at defined phase gates so the developer can study what was built before continuing

The project name is:

# `f9l3_53nd`

Use this exact project identifier throughout the repository unless there is a strong technical reason not to.

A suitable human-readable description is:

**f9l3\_53nd — Secure Authenticated File Transfer Platform**

---

# 0. CORE PROJECT OBJECTIVE

Build a professional educational secure file-transfer platform representing communication between two branch offices over an untrusted network.

The platform must provide:

### Confidentiality

Application-layer encryption using:

**AES-256-GCM**

### Integrity

Assignment-required:

**SHA-256**

computed on the original file and verified after successful reception/decryption.

Additionally, AES-GCM authentication must protect the encrypted payload against unauthorized modification.

### Secure Connectivity

Transfer traffic must operate through:

**WireGuard VPN**

### Identity

Authenticated users.

### Authorization

Users can perform only operations permitted for their role and ownership.

### Auditability

Security-relevant activity must be recorded in structured audit logs.

### Resilience

The system must handle malicious or malformed input without exposing plaintext, secrets, credentials, or internal implementation details.

---

# 1. PROJECT PHILOSOPHY

This is NOT:

- a toy AES demo
- a file upload website with encryption added
- an assignment-only implementation
- a collection of unrelated technologies
- a microservice showcase
- a "buzzword" cybersecurity project

This IS:

> A deliberately designed secure application in which cryptography, authentication, authorization, networking, storage, protocol design, threat modeling, and adversarial testing work together.

The engineering principle is:

```text
Security requirement
        ↓
Threat
        ↓
Security control
        ↓
Design
        ↓
Implementation
        ↓
Test
        ↓
Evidence
        ↓
Documentation
```

Every important security mechanism must have this traceability.

---

# 2. ABSOLUTE DEVELOPMENT RULE

## NEVER build the entire project in one pass.

The project MUST be implemented through explicit phases.

At the end of every phase:

1. stop
2. explain what was built
3. show files changed
4. explain security implications
5. explain important technical decisions
6. provide tests/results
7. list remaining risks
8. provide learning material
9. provide a review exercise
10. WAIT

You MUST NOT begin the next phase without explicit user instruction such as:

```text
Proceed to Phase 1
```

Do not infer approval.

Do not automatically continue.

---

# 3. MENTORING MODE

The developer wants to learn the underlying engineering and security concepts.

For every significant security/architecture decision explain:

### What?

What exactly is being implemented?

### Why?

What problem does it solve?

### Threat?

What attack or failure does it address?

### Guarantee?

What security property does it provide?

### Limitation?

What does it NOT protect against?

### Alternatives?

What reasonable alternatives exist?

### Decision?

Why was the chosen approach preferred?

### Testing?

How will we demonstrate that it works?

Do not explain trivial syntax.

Prioritize:

- cryptography
- security architecture
- protocol design
- threat modeling
- network security
- secure coding
- API security
- identity
- authorization
- storage security
- defensive testing
- operational security

---

# 4. TECHNOLOGY STACK

Use stable, mature technologies.

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- TanStack Query where appropriate
- a minimal accessible component approach

Frontend responsibilities:

- authentication UI
- dashboard
- file selection
- transfer creation
- transfer status
- transfer history
- administrator views
- error presentation
- security-state presentation

Do NOT place long-term application encryption keys in browser JavaScript.

Do NOT move security-critical cryptographic policy into the frontend merely for convenience.

---

# 5. BACKEND

Use:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

Recommended architectural layers:

```text
API
 ↓
Application / Service Layer
 ↓
Domain Logic
 ↓
Security / Crypto
 ↓
Infrastructure
```

Avoid putting business logic directly into FastAPI route handlers.

---

# 6. DATABASE

Use:

**PostgreSQL**

Do not store actual file contents in ordinary database rows unless there is a documented reason.

Database stores metadata.

File/object storage stores encrypted file blobs.

---

# 7. CRYPTOGRAPHY

Use the established Python `cryptography` library.

Do NOT implement:

- AES
- SHA-256
- Argon2
- HKDF
- random number generation
- MAC primitives
- VPN cryptography

from scratch.

---

# 8. CRYPTOGRAPHIC CONSTRUCTION

Primary application-layer encryption:

```text
AES-256-GCM
```

This is the canonical encryption construction for the project.

Use:

- 256-bit AES key
- cryptographically secure random nonce
- authentication tag
- AEAD
- associated authenticated data where appropriate

Never reuse an AES-GCM nonce under the same key.

Nonce management must be designed explicitly.

---

# 9. SHA-256 ROLE

SHA-256 is required because of the assignment.

It is a:

**cryptographic hash function**

It is NOT encryption.

It is NOT by itself sender authentication.

It is NOT a substitute for a MAC or AEAD authentication tag.

Workflow:

```text
Original File
     ↓
SHA-256
     ↓
Expected Digest
```

After reception:

```text
Received Ciphertext
     ↓
GCM authentication
     ↓
Decrypt
     ↓
Plaintext
     ↓
SHA-256
     ↓
Received Digest
     ↓
Compare
```

A failed hash comparison MUST cause the transfer to be considered unsuccessful.

---

# 10. PASSWORD SECURITY

Passwords must never be stored plaintext.

Use:

**Argon2id**

for password hashing.

The system must distinguish:

```text
Password hashing
```

from:

```text
File encryption
```

from:

```text
Key derivation
```

from:

```text
Message authentication
```

from:

```text
Authenticated encryption
```

---

# 11. AUTHENTICATION MODEL

Use secure server-side authentication.

Preferred model:

**HttpOnly, Secure, SameSite-aware server session cookies**

rather than unnecessarily exposing access tokens to frontend JavaScript.

Implement:

- login
- logout
- session expiration
- session revocation
- authentication middleware
- failed login tracking
- rate limiting
- account state
- authorization middleware

Do not invent authentication mechanisms.

---

# 12. ROLES

Minimum roles:

```text
ADMIN
USER
```

## USER

May:

- authenticate
- upload a file
- view own transfers
- download files they are authorized to access
- view permitted status information

## ADMIN

May additionally:

- manage users
- disable accounts
- view security audit events
- inspect transfer metadata
- review security failures

Authorization must be enforced server-side.

---

# 13. SECURITY PRINCIPLES

Apply:

- least privilege
- deny by default
- defense in depth
- secure defaults
- fail closed
- complete mediation
- separation of concerns
- explicit trust boundaries
- minimal attack surface
- data minimization
- server-side validation
- secure error handling
- secret isolation

---

# 14. THREAT MODEL

The system must explicitly identify:

## Assets

- plaintext files
- encrypted files
- encryption keys
- password hashes
- sessions
- transfer metadata
- audit logs
- database
- VPN credentials
- configuration secrets

## Actors

- normal user
- administrator
- external network attacker
- malicious authenticated user
- compromised client
- compromised server
- insider

## Threats

At minimum:

- eavesdropping
- ciphertext tampering
- metadata tampering
- credential brute force
- credential stuffing
- session theft
- replay
- unauthorized file access
- IDOR/BOLA
- privilege escalation
- malicious filename
- path traversal
- malicious upload
- oversized upload
- malformed protocol messages
- denial of service
- log tampering
- stolen storage
- compromised endpoint

Use STRIDE where appropriate.

Create:

```text
docs/threat-model.md
docs/threat-model/assets.md
docs/threat-model/actors.md
docs/threat-model/attack-surface.md
docs/threat-model/mitigations.md
docs/threat-model/residual-risk.md
```

---

# 15. TRUST BOUNDARIES

Explicitly model these boundaries:

```text
Browser
   │
   │ untrusted client input
   ▼
API
   │
   │ authenticated application boundary
   ▼
Application services
   │
   ├── crypto
   ├── database
   ├── storage
   └── audit subsystem

Branch A
   │
   │ WireGuard
   ▼
Branch B
```

Do not implicitly trust data simply because it came from the frontend.

---

# 16. TARGET ARCHITECTURE

Use a modular monorepo.

Target structure:

```text
f9l3_53nd/
│
├── AGENTS.md
├── README.md
├── SECURITY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
├── .editorconfig
├── .env.example
├── Makefile
├── docker-compose.yml
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── security.yml
│       └── dependency-review.yml
│
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── security-model.md
│   ├── threat-model.md
│   ├── crypto-design.md
│   ├── protocol.md
│   ├── API.md
│   ├── database.md
│   ├── storage.md
│   ├── deployment.md
│   ├── testing.md
│   ├── security-test-report.md
│   ├── hardening.md
│   ├── limitations.md
│   │
│   ├── diagrams/
│   │   ├── context.md
│   │   ├── container.md
│   │   ├── component.md
│   │   ├── trust-boundaries.md
│   │   ├── upload-sequence.md
│   │   ├── download-sequence.md
│   │   └── crypto-flow.md
│   │
│   └── decisions/
│       ├── ADR-001-stack-selection.md
│       ├── ADR-002-backend-architecture.md
│       ├── ADR-003-aead-selection.md
│       ├── ADR-004-password-hashing.md
│       ├── ADR-005-key-management.md
│       ├── ADR-006-authentication-session.md
│       ├── ADR-007-transfer-protocol.md
│       ├── ADR-008-storage-model.md
│       ├── ADR-009-wireguard.md
│       └── ADR-010-audit-logging.md
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── migrations/
│   ├── src/
│   │   └── app/
│   │       ├── main.py
│   │       │
│   │       ├── api/
│   │       │   ├── dependencies.py
│   │       │   ├── router.py
│   │       │   └── routes/
│   │       │       ├── auth.py
│   │       │       ├── users.py
│   │       │       ├── transfers.py
│   │       │       ├── files.py
│   │       │       └── admin.py
│   │       │
│   │       ├── core/
│   │       │   ├── config.py
│   │       │   ├── exceptions.py
│   │       │   ├── logging.py
│   │       │   └── security.py
│   │       │
│   │       ├── models/
│   │       │   ├── user.py
│   │       │   ├── session.py
│   │       │   ├── transfer.py
│   │       │   ├── audit_event.py
│   │       │   └── key_reference.py
│   │       │
│   │       ├── schemas/
│   │       │   ├── auth.py
│   │       │   ├── user.py
│   │       │   ├── transfer.py
│   │       │   ├── file.py
│   │       │   └── audit.py
│   │       │
│   │       ├── services/
│   │       │   ├── auth_service.py
│   │       │   ├── transfer_service.py
│   │       │   ├── file_service.py
│   │       │   ├── user_service.py
│   │       │   └── audit_service.py
│   │       │
│   │       ├── security/
│   │       │   ├── authentication.py
│   │       │   ├── authorization.py
│   │       │   ├── password.py
│   │       │   ├── sessions.py
│   │       │   └── rate_limit.py
│   │       │
│   │       ├── crypto/
│   │       │   ├── aead.py
│   │       │   ├── hashing.py
│   │       │   ├── keys.py
│   │       │   ├── envelope.py
│   │       │   └── nonce.py
│   │       │
│   │       ├── transfer/
│   │       │   ├── protocol.py
│   │       │   ├── state_machine.py
│   │       │   ├── replay.py
│   │       │   ├── validation.py
│   │       │   └── chunking.py
│   │       │
│   │       ├── storage/
│   │       │   ├── file_store.py
│   │       │   ├── paths.py
│   │       │   └── quarantine.py
│   │       │
│   │       └── audit/
│   │           ├── events.py
│   │           └── integrity.py
│   │
│   └── tests/
│       ├── unit/
│       │   ├── crypto/
│       │   ├── security/
│       │   └── transfer/
│       ├── integration/
│       ├── api/
│       ├── security/
│       └── adversarial/
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── eslint.config.js
│   └── src/
│       ├── app/
│       ├── routes/
│       ├── components/
│       ├── features/
│       │   ├── auth/
│       │   ├── dashboard/
│       │   ├── transfers/
│       │   ├── files/
│       │   └── admin/
│       ├── hooks/
│       ├── services/
│       ├── lib/
│       ├── types/
│       └── utils/
│
├── infra/
│   ├── docker/
│   ├── wireguard/
│   │   ├── branch-a/
│   │   └── branch-b/
│   ├── postgres/
│   └── scripts/
│
├── scripts/
│   ├── bootstrap.sh
│   ├── test.sh
│   ├── security-test.sh
│   ├── generate-dev-secrets.sh
│   └── reset-dev-environment.sh
│
└── storage/
    ├── encrypted/
    ├── temporary/
    ├── quarantine/
    └── .gitkeep
```

The structure is a target, not an excuse to create meaningless abstractions.

Modify it only when there is a documented engineering reason.

---

# 17. AGENTS.md

Create `AGENTS.md` before substantial coding.

It must contain:

- project purpose
- architecture overview
- directory ownership
- coding conventions
- crypto rules
- security rules
- testing requirements
- dependency policy
- secret-handling rules
- Git conventions
- documentation requirements
- forbidden shortcuts
- definition of done
- instructions for future AI coding agents

Every future coding session must begin by reading this file.

---

# 18. API CONTRACT

Design the API before implementing it.

Base path:

```text
/api/v1
```

Use consistent JSON error responses.

Example:

```json
{
  "error": {
    "code": "TRANSFER_NOT_FOUND",
    "message": "The requested transfer could not be found.",
    "request_id": "..."
  }
}
```

Do not leak:

- stack traces
- database errors
- secret values
- internal filesystem paths
- cryptographic keys
- unnecessary implementation information

---

# 19. AUTHENTICATION ENDPOINTS

## POST `/api/v1/auth/login`

Request:

```json
{
  "username": "alice",
  "password": "..."
}
```

Success:

```text
200 OK
```

Sets authenticated session cookie.

Failures must not reveal whether a username exists.

---

## POST `/api/v1/auth/logout`

Invalidate the current session.

---

## GET `/api/v1/auth/me`

Return authenticated identity and role.

Example:

```json
{
  "id": "...",
  "username": "alice",
  "role": "USER"
}
```

---

# 20. USER ENDPOINTS

## GET `/api/v1/users/me`

Return current profile.

## GET `/api/v1/users`

ADMIN only.

Supports pagination.

## PATCH `/api/v1/users/{user_id}/status`

ADMIN only.

Never allow ordinary users to modify privilege state.

---

# 21. TRANSFER ENDPOINTS

## POST `/api/v1/transfers`

Create a transfer.

Multipart upload or a properly defined upload flow may be used.

Return:

```json
{
  "transfer_id": "...",
  "status": "CREATED"
}
```

---

## GET `/api/v1/transfers`

Return only transfers the authenticated user is authorized to see.

Support:

- pagination
- status filtering
- date filtering
- safe ordering

---

## GET `/api/v1/transfers/{transfer_id}`

Return transfer metadata/status.

Never use direct object access without authorization.

This endpoint must specifically be tested against IDOR/BOLA.

---

## GET `/api/v1/transfers/{transfer_id}/status`

Return state-machine status.

---

## GET `/api/v1/transfers/{transfer_id}/download`

Download a file only after authorization checks.

Do not allow a user to retrieve another user's file by changing the identifier.

---

# 22. ADMIN AUDIT API

## GET `/api/v1/admin/audit-events`

ADMIN only.

Support:

- pagination
- event type
- severity
- user
- transfer ID
- date range

Do not allow arbitrary SQL-like filtering from user input.

---

# 23. TRANSFER STATE MACHINE

Define explicit states:

```text
CREATED
VALIDATING
HASHING
ENCRYPTING
READY
TRANSFERRING
RECEIVED
AUTHENTICATING
DECRYPTING
VERIFYING
COMPLETED
FAILED
QUARANTINED
REJECTED
REPLAY_DETECTED
```

Document valid transitions.

Invalid transitions must fail safely.

Example:

```text
CREATED
  ↓
VALIDATING
  ↓
HASHING
  ↓
ENCRYPTING
  ↓
READY
  ↓
TRANSFERRING
  ↓
RECEIVED
  ↓
AUTHENTICATING
  ↓
DECRYPTING
  ↓
VERIFYING
  ↓
COMPLETED
```

Failures should transition to appropriate terminal/recovery states.

---

# 24. FILE VALIDATION

The server must assume all file input is hostile.

Validate:

- file size
- filename
- path semantics
- content type where useful
- supported format policy
- request limits
- available storage
- transfer ownership

Defend against:

- `../`
- absolute paths
- null bytes where relevant
- Unicode/path confusion where relevant
- extremely long filenames
- oversized files
- unexpected metadata

Never trust browser validation.

---

# 25. STORAGE MODEL

Encrypted files should be stored outside the public web root.

Example:

```text
storage/
├── encrypted/
│   └── <transfer-id>/
│       └── payload
├── temporary/
├── quarantine/
└── metadata handled by PostgreSQL
```

Never use the original user-provided filename directly as the filesystem path.

Generate internal storage identifiers.

Store filenames as metadata.

---

# 26. DATABASE MODEL

Minimum entities:

## users

Fields conceptually:

```text
id
username
password_hash
role
status
created_at
updated_at
last_login_at
```

## sessions

```text
id
user_id
session_hash/reference
created_at
expires_at
revoked_at
last_seen_at
```

## transfers

```text
id
sender_id
recipient_id
original_filename
size
state
sha256_digest
algorithm
protocol_version
created_at
completed_at
failure_reason
storage_reference
key_reference
```

## audit\_events

```text
id
timestamp
actor_user_id
event_type
severity
request_id
transfer_id
source_ip_if_appropriate
metadata
previous_event_digest_if_chaining
event_digest
```

## key\_references

Do not store plaintext encryption keys here.

Store only appropriate key references/wrapped material according to the key-management design.

Add indexes based on actual query patterns.

Add foreign-key constraints.

Use migrations.

---

# 27. CRYPTOGRAPHIC FILE ENVELOPE

Design a versioned transfer envelope.

Conceptually:

```text
Secure Transfer Envelope v1

{
    protocol_version,
    transfer_id,
    sender_context,
    algorithm_id,
    key_reference,
    nonce,
    aad,
    ciphertext,
    authentication_tag,
    plaintext_sha256,
    metadata
}
```

This is conceptual.

Do NOT blindly implement this exact serialization.

Determine carefully:

- which fields are encrypted
- which fields are authenticated
- which fields are public metadata
- what constitutes AAD
- how the envelope is serialized
- how the version is represented
- how compatibility works
- how malformed envelopes are rejected

Document this in:

```text
docs/crypto-design.md
docs/protocol.md
```

---

# 28. AAD DESIGN

Use AES-GCM AAD for fields where confidentiality is unnecessary but integrity/authenticity is required.

Potential candidates:

```text
protocol_version
transfer_id
sender_id
file_size
algorithm_id
timestamp/freshness information
```

The final list must be justified.

Do not include values in AAD merely because they exist.

Every AAD field needs a reason.

---

# 29. KEY MANAGEMENT

Design a key hierarchy.

Preferred conceptual model:

```text
Master Key
    │
    ▼
Key-Wrapping Layer
    │
    ▼
Per-Transfer Data Encryption Key
    │
    ▼
AES-256-GCM
    │
    ▼
Encrypted File
```

The master key MUST NOT be hardcoded.

Development and production key handling must be distinct.

Development:

- `.env`
- generated local secrets
- clear warnings

Production discussion:

- external secret manager
- KMS
- HSM

Do NOT claim the educational implementation is equivalent to an HSM/KMS.

Document limitations.

---

# 30. KEY LIFECYCLE

Document:

- generation
- use
- storage
- wrapping
- rotation
- revocation/retirement
- deletion
- recovery

Do not keep encryption keys in memory longer than necessary.

Avoid unnecessary duplication.

---

# 31. NONCE MANAGEMENT

Nonce handling must be explicit.

Use a cryptographically secure method.

Never silently reuse nonces under the same key.

Create tests proving nonce uniqueness behavior.

If the design uses random nonces, explain the collision considerations and why the construction/library's nonce requirements are satisfied.

---

# 32. REPLAY PROTECTION

Every transfer must have an identity/freshness model.

Minimum concepts:

```text
transfer_id
created_at
state
replay detection
```

Reject:

- previously completed transfer submissions
- reused transfer identities
- stale transfer messages according to protocol rules

Document the exact replay threat and mitigation.

Create a dedicated replay test suite.

---

# 33. HASH VERIFICATION

Flow:

```text
sender:
file
 ↓
SHA-256
 ↓
digest
 ↓
encrypt
 ↓
transfer
```

receiver:

```text
receive
 ↓
AEAD authentication
 ↓
decrypt
 ↓
SHA-256
 ↓
compare
```

On mismatch:

```text
FAILED / QUARANTINED
```

No successful transfer status should be returned.

Create:

- valid digest test
- one-byte modification test
- incorrect digest test
- malformed digest test

---

# 34. WIREGUARD TOPOLOGY

Use two logical branch networks.

Example:

```text
Branch A
WireGuard: 10.50.0.2

       │
       │ encrypted VPN tunnel
       │
       ▼

Branch B
WireGuard: 10.50.0.1
```

The exact addresses may be adjusted.

Do not expose the application publicly if the architecture is intended to require VPN access.

Document:

- peers
- routes
- allowed IPs
- endpoint behavior
- key management
- firewall assumptions

Never commit WireGuard private keys.

---

# 35. NETWORK SECURITY MODEL

Clearly distinguish:

```text
WireGuard
```

from:

```text
Application encryption
```

WireGuard secures network transport.

AES-256-GCM secures the file at the application layer.

Do not claim that VPN makes application-level encryption unnecessary.

Do not claim that VPN automatically guarantees availability.

For availability, consider:

- server health
- storage limits
- connection handling
- file size limits
- timeout policy
- rate limits
- resource quotas

---

# 36. AUDIT LOGGING

Structured event model.

Examples:

```text
LOGIN_SUCCESS
LOGIN_FAILURE
LOGOUT
SESSION_REVOKED
AUTHORIZATION_FAILURE
TRANSFER_CREATED
TRANSFER_VALIDATION_FAILED
TRANSFER_STARTED
TRANSFER_COMPLETED
TRANSFER_FAILED
DECRYPTION_FAILURE
INTEGRITY_FAILURE
REPLAY_DETECTED
RATE_LIMIT_TRIGGERED
ADMIN_USER_STATUS_CHANGED
```

Each relevant event should contain:

```text
event_id
timestamp
event_type
severity
actor
request_id
transfer_id where applicable
safe contextual metadata
```

Never log:

- password
- password hash unless absolutely required for a forensic design (prefer not)
- encryption key
- session secret
- access token
- plaintext file contents

---

# 37. OPTIONAL TAMPER-EVIDENT LOG CHAIN

As an extension, implement:

```text
Event 1
  ↓ hash
Event 2
  ↓ hash
Event 3
  ↓ hash
Event 4
```

Each event may reference the prior event digest.

This makes modification detectable.

Do not claim this makes logs immutable.

Document:

- what it protects
- what it doesn't protect
- how an attacker with total database control could still remove/rewrite the entire chain

---

# 38. SECURITY HEADERS AND API HARDENING

Where applicable implement:

- CORS allowlist
- request size limits
- secure cookies
- CSRF protection appropriate to chosen authentication model
- security headers
- safe content types
- API rate limits
- timeout controls
- controlled error messages

Avoid copying a generic security configuration blindly.

Every security control must match the architecture.

---

# 39. FRONTEND SECURITY

React application should:

- use strict TypeScript
- never trust API data
- handle authentication state safely
- avoid storing secrets in localStorage
- avoid exposing crypto keys
- avoid rendering unsafe HTML
- validate user-facing input where appropriate
- rely on server-side authorization

The frontend is a convenience layer.

The backend is the authority.

---

# 40. FRONTEND PAGES

Minimum:

```text
/login
/dashboard
/transfers
/transfers/new
/transfers/:id
/admin/users
/admin/audit
```

Dashboard should display:

- total transfers
- successful transfers
- failed transfers
- recent activity
- security status

Transfer detail should show:

```text
Transfer ID
Filename
Size
Status
Sender
Recipient
Created time
Completed time
Encryption: AES-256-GCM
Integrity: SHA-256
VPN transport: WireGuard
Verification status
```

Do not expose secrets.

---

# 41. API DOCUMENTATION

Generate and maintain OpenAPI documentation.

Also maintain:

```text
docs/API.md
```

It should explain:

- endpoint
- purpose
- authentication
- authorization
- request
- response
- possible error codes
- rate limits
- security considerations

Do not let documentation drift from actual implementation.

---

# 42. ERROR MODEL

Create centralized error classes.

Examples:

```text
AuthenticationError
AuthorizationError
ValidationError
TransferStateError
CryptoError
DecryptionError
IntegrityError
ReplayError
StorageError
RateLimitError
```

Map them to safe HTTP responses.

Never expose:

```text
Traceback...
database error...
AES key...
filesystem path...
```

to the client.

---

# 43. TESTING STRATEGY

Testing is part of the security design.

Minimum test layers:

```text
Unit
Integration
API
Security
Adversarial
End-to-end
```

---

# 44. CRYPTO UNIT TESTS

Test:

- encryption/decryption round trip
- wrong key
- wrong nonce
- modified ciphertext
- modified AAD
- invalid authentication tag
- empty file
- binary file
- large file
- SHA-256 correctness
- nonce uniqueness
- envelope serialization
- malformed envelope

---

# 45. AUTHENTICATION TESTS

Test:

- valid credentials
- invalid password
- unknown user
- disabled account
- expired session
- revoked session
- brute-force attempts
- rate limiting
- concurrent sessions according to policy

---

# 46. AUTHORIZATION TESTS

Test:

```text
USER → own resource = ALLOW
USER → another user's resource = DENY
USER → admin endpoint = DENY
ADMIN → admin endpoint = ALLOW
```

Also test horizontal and vertical privilege escalation.

---

# 47. FILE SECURITY TESTS

Test:

```text
../../file
../../../etc/passwd
absolute paths
very long filename
unicode path manipulation
oversized file
empty file
unexpected content type
malformed multipart request
```

---

# 48. PROTOCOL TESTS

Test:

- invalid protocol version
- malformed envelope
- missing field
- extra field
- incorrect state transition
- stale transfer
- replay
- duplicate transfer
- interrupted transfer
- retry
- idempotency

---

# 49. ADVERSARIAL SECURITY TESTS

Deliberately attack the system.

Minimum attacks:

## A. Ciphertext tampering

Modify one byte.

Expected:

```text
GCM authentication failure
transfer rejected
no plaintext release
audit event
```

## B. AAD tampering

Modify authenticated metadata.

Expected:

```text
authentication failure
```

## C. SHA-256 mismatch

Expected:

```text
verification failure
```

## D. Replay

Resubmit valid transfer.

Expected:

```text
REPLAY_DETECTED
```

## E. IDOR/BOLA

Change transfer identifier.

Expected:

```text
403 or appropriately indistinguishable denial
```

## F. Privilege escalation

Attempt user → admin.

Expected rejection.

## G. Brute force

Generate repeated login failures.

Expected rate limiting.

## H. Path traversal

Expected rejection.

## I. Oversized upload

Expected controlled rejection.

## J. VPN bypass

Attempt application access outside intended network path.

Expected behavior according to deployment policy.

---

# 50. SECURITY TEST MATRIX

Create:

```text
docs/security-test-report.md
```

Each test must include:

```text
ID
Threat
Attack
Precondition
Procedure
Expected Result
Actual Result
Control
Evidence
Severity
Residual Risk
```

Example:

```text
SEC-001
Threat: Tampering
Attack: Modify ciphertext
Expected: AES-GCM authentication failure
Result: PASS
Control: AES-256-GCM
```

---

# 51. DEVSECOPS

Implement:

- formatting
- linting
- static type checking
- unit tests
- integration tests
- security tests
- dependency checking
- secret scanning
- container scanning where practical

Use GitHub Actions.

CI should run automatically.

---

# 52. QUALITY TOOLING

Backend:

- Ruff
- formatter
- mypy or suitable type checker
- pytest

Frontend:

- TypeScript strict mode
- ESLint
- formatter
- test framework appropriate to architecture

Infrastructure:

- Dockerfile linting where available
- Compose validation
- secret detection

Do not add tooling without documenting why it exists.

---

# 53. DOCKER ARCHITECTURE

Create separate services as justified:

```text
frontend
backend
postgres
wireguard-related infrastructure
```

Avoid unnecessary service fragmentation.

Containers should:

- run with minimal privileges
- avoid root where practical
- use minimal base images
- have health checks where useful
- not contain secrets
- expose only required ports

---

# 54. DEVELOPMENT ENVIRONMENT

Provide one reproducible setup path.

For example:

```text
make setup
make dev
make test
make security-test
make lint
make typecheck
make down
```

Document every command.

---

# 55. ENVIRONMENT CONFIGURATION

Use:

```text
.env.example
```

Never commit real credentials.

Clearly separate:

```text
development
testing
production
```

Never use production secrets in development.

---

# 56. DATABASE MIGRATIONS

Use Alembic.

Database changes must occur through migrations.

Do not rely on developers manually modifying PostgreSQL tables.

---

# 57. OBSERVABILITY

Provide:

- structured application logs
- request/correlation ID
- transfer ID
- security events
- health endpoint

Potential endpoints:

```text
GET /health/live
GET /health/ready
```

Do not expose sensitive diagnostic information.

---

# 58. HEALTH AND AVAILABILITY

Define:

```text
liveness
readiness
dependency health
storage availability
database connectivity
VPN dependency state where observable
```

Availability is not merely "there is a VPN."

Document actual availability controls.

---

# 59. RATE LIMITING AND RESOURCE CONTROL

Protect:

- login
- transfer creation
- file upload
- expensive operations

Use:

- request rate limits
- file size limits
- concurrent transfer limits where appropriate
- storage quotas
- sensible timeouts

Document threat scenarios.

---

# 60. FILE CHUNKING

Design large-file handling.

Do not load arbitrarily large files entirely into RAM.

The implementation should support streaming/chunking where practical.

The cryptographic design must account for:

- chunk boundaries
- authentication
- final integrity verification
- interrupted transfer
- replay
- ordering

Do not invent a streaming crypto construction casually.

If a simpler secure design is more appropriate for the project scope, document the maximum supported file size instead.

Security takes precedence over artificial scalability claims.

---

# 61. SECURITY BOUNDARIES IN CODE

Use clear modules:

```text
security/
crypto/
transfer/
storage/
audit/
```

Do not mix:

```text
FastAPI route
AES implementation
database query
filesystem operation
```

into one function.

Keep cryptographic operations small and reviewable.

---

# 62. ARCHITECTURE DECISION RECORDS

Create an ADR for significant choices.

Each ADR:

```text
# ADR-XXX

Status:
Context:
Decision:
Alternatives:
Why alternatives were rejected:
Security impact:
Operational impact:
Trade-offs:
Consequences:
```

At minimum document:

- stack
- AES-GCM
- password hashing
- session strategy
- key management
- transfer protocol
- storage
- WireGuard
- audit logging

---

# 63. DOCUMENTATION

README must cover:

1. Project overview
2. Motivation
3. Security objectives
4. Architecture
5. Technology stack
6. Installation
7. Development
8. Docker
9. WireGuard setup
10. Database
11. Authentication
12. Encryption
13. Transfer workflow
14. Threat model
15. Security testing
16. Known limitations
17. Future work

The README must not exaggerate security properties.

---

# 64. SECURITY.md

Include:

- supported version
- vulnerability reporting process
- security assumptions
- known limitations
- secret policy
- development security notes

This is an educational project.

Do not pretend it is certified or production-ready without evidence.

---

# 65. DOCUMENT THE LIMITATIONS

Explicitly state what is NOT protected.

For example:

- compromised endpoint
- malicious administrator
- full server compromise
- stolen active session
- compromised operating system
- physical compromise
- denial of service outside application control

The final project should have intellectual honesty.

---

# 66. NO FALSE SECURITY CLAIMS

Never write:

```text
100% secure
unhackable
military-grade
completely secure
perfectly private
```

Security must be expressed in terms of:

- threat model
- assumptions
- controls
- tested behavior
- residual risk

---

# 67. SECURITY REVIEW

At the end of implementation act as an external security reviewer.

Assume the developer is wrong.

Try to discover:

- auth bypass
- broken authorization
- nonce reuse
- key exposure
- replay
- IDOR
- insecure file handling
- unsafe logging
- resource exhaustion
- weak configuration
- dependency issues
- container weaknesses
- VPN misconfiguration
- protocol flaws

Do not defend the original architecture merely because you designed it.

---

# 68. FINAL SECURITY AUDIT

Produce:

```text
docs/final-security-review.md
```

Include:

- architecture assessment
- threat model assessment
- crypto assessment
- authentication assessment
- authorization assessment
- API assessment
- storage assessment
- network assessment
- logging assessment
- deployment assessment
- test coverage
- known weaknesses
- residual risks
- recommendations

---

# 69. PHASE STRUCTURE

The complete build MUST use these phases.

---

## PHASE 0 — Environment and Repository Foundation

Build only:

- repository
- AGENTS.md
- README skeleton
- SECURITY.md
- frontend bootstrap
- backend bootstrap
- Docker development foundation
- lint/format/type/test commands
- `.env.example`
- Makefile
- Git conventions

No feature implementation.

### Gate 0

STOP.

---

## PHASE 1 — Requirements Specification

Create:

```text
docs/requirements.md
docs/security-model.md
```

Define:

- functional requirements
- security requirements
- non-functional requirements
- roles
- assumptions
- non-goals
- assets
- constraints
- success criteria

### Gate 1

STOP.

---

## PHASE 2 — Threat Model

Create:

```text
docs/threat-model.md
docs/threat-model/*
```

Produce:

- STRIDE analysis
- assets
- actors
- attack surfaces
- trust boundaries
- threats
- mitigations
- residual risk

### Gate 2

STOP.

---

## PHASE 3 — Architecture

Produce:

- context diagram
- container diagram
- component diagram
- trust-boundary diagram
- data-flow diagrams
- upload sequence
- download sequence

Create:

```text
docs/architecture.md
docs/diagrams/*
```

Create relevant ADRs.

### Gate 3

STOP.

---

## PHASE 4 — API and Database Design

Before implementation define:

- API
- schemas
- response codes
- errors
- database entities
- relationships
- indexes
- authorization rules

Create:

```text
docs/API.md
docs/database.md
```

### Gate 4

STOP.

---

## PHASE 5 — Cryptographic Design

Define:

- AES-256-GCM
- SHA-256
- nonce strategy
- AAD
- key hierarchy
- key storage
- transfer envelope
- protocol versioning
- crypto error handling

Create:

```text
docs/crypto-design.md
```

Implement crypto module only after design approval.

### Gate 5

STOP.

---

## PHASE 6 — Key Management

Implement the selected key-management design.

Add:

- generation
- wrapping
- storage references
- lifecycle
- rotation concept
- secure configuration

Create crypto/security tests.

### Gate 6

STOP.

---

## PHASE 7 — Authentication and Authorization

Implement:

- users
- Argon2id
- login
- logout
- sessions
- authorization
- roles
- rate limiting
- account state

Test extensively.

### Gate 7

STOP.

---

## PHASE 8 — Secure File Handling

Implement:

- file upload
- validation
- temporary storage
- safe filenames
- storage IDs
- path traversal protection
- quotas/limits
- quarantine

### Gate 8

STOP.

---

## PHASE 9 — Transfer Protocol

Implement:

- transfer IDs
- transfer state machine
- protocol envelope
- state transitions
- replay protection
- retries
- idempotency
- chunking or explicit file-size policy

Create:

```text
docs/protocol.md
```

### Gate 9

STOP.

---

## PHASE 10 — Cryptographic Transfer

Integrate:

```text
SHA-256
↓
AES-256-GCM
↓
encrypted envelope
```

Receiver:

```text
authentication
↓
decryption
↓
SHA-256
↓
comparison
```

Test all failure conditions.

### Gate 10

STOP.

---

## PHASE 11 — WireGuard

Implement the VPN topology.

Test:

- connectivity
- application access over VPN
- routing
- unauthorized network access

Update deployment documentation.

### Gate 11

STOP.

---

## PHASE 12 — Audit System

Implement:

- structured events
- request IDs
- transfer IDs
- security events
- authorization events
- integrity failures
- replay detection

Optionally implement tamper-evident chaining.

### Gate 12

STOP.

---

## PHASE 13 — Frontend

Build:

- login
- dashboard
- file upload
- transfer progress
- transfer history
- transfer detail
- admin users
- admin audit

Do not expose secrets.

### Gate 13

STOP.

---

## PHASE 14 — Full Integration

Complete:

```text
Browser
 ↓
Authentication
 ↓
Authorization
 ↓
Upload
 ↓
Validation
 ↓
SHA-256
 ↓
Key management
 ↓
AES-256-GCM
 ↓
Transfer protocol
 ↓
WireGuard
 ↓
Receiver
 ↓
Replay protection
 ↓
GCM verification
 ↓
Decryption
 ↓
SHA-256
 ↓
Storage
 ↓
Audit
```

Perform end-to-end testing.

### Gate 14

STOP.

---

## PHASE 15 — Adversarial Testing

Attack the system.

At minimum:

- ciphertext tampering
- AAD tampering
- hash mismatch
- replay
- brute force
- credential stuffing simulation
- session invalidation
- IDOR/BOLA
- privilege escalation
- path traversal
- malformed uploads
- oversized upload
- malformed protocol
- invalid state transition
- unauthorized admin access
- VPN bypass attempt
- storage access abuse

### Gate 15

STOP.

---

## PHASE 16 — External-Reviewer Security Audit

Pretend this repository was submitted for security review.

Find weaknesses.

Classify:

```text
CRITICAL
HIGH
MEDIUM
LOW
INFORMATIONAL
```

Fix what can be fixed.

Document what cannot.

### Gate 16

STOP.

---

## PHASE 17 — DevSecOps

Implement:

- CI
- unit tests
- integration tests
- security tests
- lint
- formatting
- type checks
- dependency checks
- secret scanning
- container security checks

### Gate 17

STOP.

---

## PHASE 18 — Hardening

Review:

- cookies
- CORS
- headers
- permissions
- containers
- database
- storage
- secret handling
- crypto
- nonce handling
- key lifecycle
- logs
- API limits
- error messages
- authentication
- authorization
- VPN
- filesystem

### Gate 18

STOP.

---

## PHASE 19 — Documentation and Final Review

Produce final:

```text
README.md
SECURITY.md
docs/architecture.md
docs/crypto-design.md
docs/threat-model.md
docs/protocol.md
docs/testing.md
docs/security-test-report.md
docs/final-security-review.md
```

Also produce:

- final architecture diagram
- final data-flow diagram
- final crypto flow
- assignment requirement mapping
- known limitations
- future improvements
- resume description
- technical interview questions
- viva questions

### Gate 19

Project complete.

---

# 70. ASSIGNMENT TRACEABILITY MATRIX

Create a document mapping assignment requirement → implementation → test → evidence.

Example:

| Assignment Requirement | Implementation        | Test            | Evidence        |
| ---------------------- | --------------------- | --------------- | --------------- |
| AES-256                | AES-256-GCM           | crypto tests    | transfer demo   |
| SHA-256                | file digest           | integrity test  | transfer detail |
| VPN                    | WireGuard             | network test    | topology        |
| Authentication         | Argon2id + sessions   | auth tests      | login           |
| File selection         | React upload          | upload tests    | UI              |
| Hash verification      | receiver verification | mismatch test   | audit           |
| Decryption             | crypto service        | round-trip test | recovered file  |
| Activity log           | audit service         | logging tests   | admin view      |

Do not silently replace an assignment requirement with a different control.

Additional controls should complement the required controls.

---

# 71. DEFINITION OF DONE

The project is complete only when:

- requirements documented
- threat model documented
- architecture documented
- API documented
- database documented
- cryptographic design documented
- key-management design documented
- protocol documented
- authentication implemented
- authorization implemented
- secure file handling implemented
- AES-256-GCM implemented correctly
- SHA-256 verification implemented
- replay protection implemented
- WireGuard implemented
- audit logging implemented
- frontend implemented
- attack tests implemented
- integration tests implemented
- CI implemented
- secrets excluded
- Docker deployment reproducible
- limitations documented
- final security review completed

---

# 72. CODE QUALITY RULES

Prefer:

- typed interfaces
- explicit dependencies
- dependency injection where useful
- small functions
- domain-oriented modules
- clear names
- meaningful exceptions
- testable components

Avoid:

- god classes
- god functions
- global mutable state
- hidden cryptographic state
- unexplained magic values
- duplicated security checks
- duplicated business logic
- dead abstractions

---

# 73. SECURITY-SENSITIVE CODE RULES

For cryptography/security code:

- keep functions small
- document security assumptions
- test positive and negative paths
- validate inputs
- avoid unnecessary transformations
- never swallow exceptions silently
- never log secrets
- do not silently downgrade algorithms
- use explicit algorithm identifiers
- centralize crypto policy
- avoid scattered encryption calls

---

# 74. DEPENDENCY POLICY

Before adding a dependency:

1. explain why
2. check whether the standard library already provides the capability
3. check maintenance status
4. consider attack surface
5. consider license compatibility
6. avoid duplicate libraries

Do not add libraries merely because they are popular.

---

# 75. VERSIONING

The cryptographic envelope and application API should be versionable.

Do not make future migration impossible.

Use explicit:

```text
protocol version
algorithm identifier
```

where appropriate.

---

# 78. NO MICROSERVICE THEATER

Do NOT create:

```text
auth-service
crypto-service
file-service
transfer-service
audit-service
```

as separate network microservices merely because the code has those logical modules.

These should initially be modules/components inside a well-structured backend.

Introduce actual service boundaries only when justified.

---

# 79. NO SECURITY THEATER

Do NOT add:

- blockchain
- AI
- unnecessary certificate hierarchies
- unnecessary distributed databases
- exotic cryptography
- custom cryptographic algorithms
- fake "military-grade" claims

Security engineering is about correct controls and threat reduction.

---

# 80. GIT PRACTICES

Use logical commits where possible:

```text
feat:
fix:
security:
test:
docs:
refactor:
chore:
```

Example:

```text
feat: establish secure session authentication
security: enforce transfer ownership authorization
test: add replay attack coverage
docs: document AES-GCM envelope design
```

Never commit:

- `.env`
- private keys
- passwords
- session secrets
- WireGuard private keys
- production credentials
- generated sensitive data

---

# 81. PHASE-END REPORT FORMAT

At the end of every phase output exactly this structure:

```text
# Phase X Complete

## Objective

## What Was Built

## Files Created

## Files Modified

## Architecture Decisions

## Security Decisions

## Tests Executed

## Test Results

## Risks Discovered

## Risks Remaining

## What You Should Learn

## Questions You Should Be Able to Answer

## Hands-On Exercise

## Next Phase Preview

## GATE

STOP.
```

Do not continue.

---

# 82. STARTING INSTRUCTION

You are now at:

# PHASE 0

Do NOT implement authentication.

Do NOT implement encryption.

Do NOT create transfer endpoints.

Do NOT create the database business models yet.

Do NOT build the complete frontend.

Do NOT configure production infrastructure.

Start by:

1. inspecting the development environment
2. checking available language/runtime versions
3. checking Docker availability
4. checking Git availability
5. creating the repository
6. creating the professional directory structure
7. writing `AGENTS.md`
8. writing the initial `README.md`
9. writing `SECURITY.md`
10. initializing backend tooling
11. initializing frontend tooling
12. configuring lint/format/type/test foundations
13. creating `.env.example`
14. creating Makefile/development commands
15. adding `.gitignore`
16. verifying that the empty foundation builds successfully
17. documenting all initial architectural decisions
18. stopping at Gate 0

Do not proceed to Phase 1 automatically.

---

# 83. FINAL BEHAVIORAL RULE

At every point in this project, think:

```text
"What is the threat?"
"What is the trust boundary?"
"What security property are we trying to establish?"
"What assumption are we making?"
"Can we test that assumption?"
"What happens when the control fails?"
"What happens if an attacker deliberately abuses this?"
```

Do not merely ask:

```text
"How do I code this?"
```

The objective is to finish with both:

```text
A working system
```

and:

```text
A deep understanding of why the system is secure within its stated threat model.
```

Begin with PHASE 0 only.
