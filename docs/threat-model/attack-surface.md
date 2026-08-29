# Threat Model — Attack Surface Analysis

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. Attack Surface Decomposition

The attack surface comprises all physical, network, and application entry points through which an adversary can introduce untrusted data or interact with system components.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. API Attack Surface (/api/v1/*)                                      │
│    - Authentication: /auth/login, /auth/logout, /auth/me              │
│    - Transfers: POST /transfers, GET /transfers, GET /transfers/{id}   │
│    - Downloads: GET /transfers/{id}/download                           │
│    - Admin: GET /admin/audit-events, PATCH /users/{id}/status          │
├────────────────────────────────────────────────────────────────────────┤
│ 2. File Ingestion Surface                                              │
│    - Multipart upload streams, boundary parsing, filename headers     │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Cryptographic Envelope Parser                                       │
│    - AES-GCM tag validation, AAD bytes, IV/nonce bytes, ciphertext     │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Network Transport Surface                                           │
│    - WireGuard UDP port 51820, Reverse Proxy / HTTP ports 8000/5173    │
├────────────────────────────────────────────────────────────────────────┤
│ 5. Session Management Surface                                          │
│    - Cookie parsing, session lookup, expiration timers                 │
├────────────────────────────────────────────────────────────────────────┤
│ 6. Storage & Path Canonicalization Engine                              │
│    - Storage directory resolution, quarantine movement                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component-by-Component Attack Exposure & Entry Points

### 2.1 File Ingestion & Parsing Subsystem
- **Exposed Inputs**: Multipart form data headers (`Content-Disposition`, `filename`), binary file streams, MIME types.
- **Potential Attack Vectors**:
  - **Path Traversal via Filename**: Submitting filenames like `../../../../etc/shadow` or `C:\boot.ini` aiming to write outside designated storage.
  - **Null Byte & Encoding Attacks**: Filenames containing `%00`, unicode normalization exploits, or excessively long strings (> 255 chars) targeting buffer overflows or filesystem corruption.
  - **Unbounded Uploads (Resource Exhaustion)**: Streaming infinite bytes to exhaust server memory and disk space.
- **Hardening Policy**: Strict filename sanitization; rejection of directory separators (`/`, `\`); file size enforcement before and during stream buffering; UUID-based physical filenames.

### 2.2 API Route Handlers & State Machine
- **Exposed Inputs**: HTTP methods, URL path parameters (`transfer_id`, `user_id`), query filters, JSON payloads.
- **Potential Attack Vectors**:
  - **BOLA / IDOR**: Enumerating UUIDs or incrementing integer IDs to access other users' transfer metadata or download payloads.
  - **State Race Conditions**: Triggering duplicate `TRANSFERRING` or `COMPLETED` transitions concurrently.
  - **Privilege Escalation**: Non-admin users attempting to invoke `/api/v1/admin/*` routes.
- **Hardening Policy**: Pydantic schema validation; FastAPI dependency injection enforcing RBAC and resource ownership queries; database transaction locks for atomic state machine transitions.

### 2.3 Cryptographic Engine & Envelope Deserializer
- **Exposed Inputs**: Ciphertext bytes, 96-bit nonce, 128-bit GCM tag, AAD bytes, expected SHA-256 digest string.
- **Potential Attack Vectors**:
  - **Bit-Flipping / Ciphertext Tampering**: Modifying ciphertext bytes in transit.
  - **AAD Splicing**: Reusing ciphertext from Transfer A with metadata from Transfer B.
  - **Nonce Collision / Reuse**: Forcing reuse of a nonce under the same key.
  - **Digest Injection**: Submitting an attacker-controlled SHA-256 digest alongside a tampered payload.
- **Hardening Policy**: Constant-time cryptographic verification via OpenSSL backend; per-transfer random DEK generation; AAD cryptographic binding; post-decryption digest recalculation.

### 2.4 WireGuard VPN Interface
- **Exposed Inputs**: UDP packets received on port 51820.
- **Potential Attack Vectors**:
  - Unauthenticated network probing or replay of handshake packets.
- **Hardening Policy**: WireGuard 1-RTT Noise IK handshake with silent drop of unauthenticated packets (no response packets sent to unauthorized sources, preventing port scanning and amplification).
