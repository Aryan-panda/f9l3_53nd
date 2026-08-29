# API Specification & Contract — f9l3_53nd

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  
**Base URL**: `/api/v1`  
**Security Model**: Cookie-based Session Authentication (`HttpOnly`, `SameSite=Lax`, `Secure`)  

---

## 1. Global API Design & Security Conventions

### 1.1 Standard JSON Error Response Envelope
To prevent information leakage (CWE-209), the API returns uniform, structured error payloads. No stack traces, internal paths, or SQL queries are ever returned in responses.

```json
{
  "error": {
    "code": "TRANSFER_NOT_FOUND",
    "message": "The requested transfer could not be found.",
    "details": {
      "transfer_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
    }
  }
}
```

### 1.2 Common HTTP Status Codes

| Status Code | Code Identifier | Description |
| :--- | :--- | :--- |
| **200 OK** | Success | Request succeeded. |
| **201 Created** | Resource Created | File transfer or user session created. |
| **400 Bad Request** | `VALIDATION_FAILED` / `DECRYPTION_FAILED` | Request malformed, or cryptographic tag/hash mismatch. |
| **401 Unauthorized** | `AUTHENTICATION_REQUIRED` | Missing, invalid, expired, or revoked session cookie. |
| **403 Forbidden** | `AUTHORIZATION_DENIED` | Caller lacks permission or ownership of the target resource. |
| **404 Not Found** | `RESOURCE_NOT_FOUND` | Target resource does not exist (or hidden to prevent IDOR probing). |
| **409 Conflict** | `REPLAY_DETECTED` / `INVALID_STATE` | State transition violation or replayed transfer token. |
| **422 Unprocessable** | `SCHEMA_VALIDATION_ERROR` | Request payload failed Pydantic type/field constraints. |
| **429 Too Many Req** | `RATE_LIMIT_EXCEEDED` | Request rate exceeded allowed burst/sustained threshold. |
| **500 Internal Error** | `INTERNAL_SERVER_ERROR` | Generic failure (details logged securely to server audit). |

---

## 2. Authentication Endpoints

### 2.1 Authenticate User (Login)
- **Method / Path**: `POST /api/v1/auth/login`
- **Authentication**: None (Public)
- **Rate Limit**: 5 requests / minute per IP
- **Description**: Authenticates user via Argon2id hash verification and sets an `HttpOnly` session cookie.

#### Request Body
```json
{
  "username": "alice",
  "password": "StrongPassword123!"
}
```

#### Response (`200 OK`)
- **Headers**: `Set-Cookie: f9l3_session=<token>; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400`
```json
{
  "status": "success",
  "user": {
    "id": "11111111-1111-4111-8111-111111111111",
    "username": "alice",
    "role": "USER",
    "status": "ACTIVE"
  }
}
```

#### Security Considerations:
- Error responses for unknown usernames vs. invalid passwords are **identical** (`"Invalid username or password"`) in constant-time processing to prevent username enumeration.

---

### 2.2 Terminate Session (Logout)
- **Method / Path**: `POST /api/v1/auth/logout`
- **Authentication**: Required (`USER` or `ADMIN`)
- **Description**: Immediately revokes the session token server-side and clears the cookie.

#### Response (`200 OK`)
- **Headers**: `Set-Cookie: f9l3_session=; Path=/; HttpOnly; Max-Age=0`
```json
{
  "status": "success",
  "message": "Session successfully terminated."
}
```

---

### 2.3 Get Current User Identity
- **Method / Path**: `GET /api/v1/auth/me`
- **Authentication**: Required (`USER` or `ADMIN`)
- **Description**: Returns authenticated session context.

#### Response (`200 OK`)
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "username": "alice",
  "role": "USER",
  "status": "ACTIVE",
  "created_at": "2026-08-27T10:00:00Z"
}
```

---

## 3. User Management Endpoints

### 3.1 Get Profile (`GET /api/v1/users/me`)
- **Authentication**: Required (`USER` or `ADMIN`)
- **Description**: Returns profile details of the current authenticated user.

---

### 3.2 List Users (`GET /api/v1/users`)
- **Authentication**: Required (**`ADMIN` Only**)
- **Query Parameters**:
  - `page` (integer, default: 1)
  - `page_size` (integer, default: 20, max: 100)
- **Description**: Returns paginated user records.

#### Response (`200 OK`)
```json
{
  "items": [
    {
      "id": "11111111-1111-4111-8111-111111111111",
      "username": "alice",
      "role": "USER",
      "status": "ACTIVE",
      "created_at": "2026-08-27T10:00:00Z",
      "last_login_at": "2026-08-29T17:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 3.3 Update User Status (`PATCH /api/v1/users/{user_id}/status`)
- **Authentication**: Required (**`ADMIN` Only**)
- **Description**: Activates, suspends, or disables a user account. Deactivated users have active sessions revoked immediately.

#### Request Body
```json
{
  "status": "SUSPENDED"
}
```

#### Response (`200 OK`)
```json
{
  "id": "11111111-1111-4111-8111-111111111111",
  "username": "alice",
  "status": "SUSPENDED",
  "updated_at": "2026-08-29T17:35:00Z"
}
```

---

## 4. File Transfer Endpoints

### 4.1 Create Transfer (`POST /api/v1/transfers`)
- **Method / Path**: `POST /api/v1/transfers`
- **Authentication**: Required (`USER` or `ADMIN`)
- **Content-Type**: `multipart/form-data`
- **Description**: Ingests file, computes SHA-256 pre-hash, generates ephemeral DEK, wraps DEK with Master KEK, constructs AAD, encrypts payload using AES-256-GCM, stores ciphertext, and initiates WireGuard transmission.

#### Multipart Form Fields:
- `file`: Binary file stream (max 50 MB)
- `recipient_id`: UUID of recipient user

#### Response (`201 Created`)
```json
{
  "transfer_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "READY",
  "filename": "quarterly_financials.pdf",
  "size_bytes": 1048576,
  "sha256_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "created_at": "2026-08-29T17:30:00Z"
}
```

---

### 4.2 List Authorized Transfers (`GET /api/v1/transfers`)
- **Authentication**: Required (`USER` or `ADMIN`)
- **Query Parameters**:
  - `status` (string, optional, e.g. `COMPLETED`, `TRANSFERRING`)
  - `page` (integer, default: 1)
  - `page_size` (integer, default: 20)
- **Description**: Returns transfers where the authenticated user is either the **sender** or **recipient** (Admins see all transfers).

#### Response (`200 OK`)
```json
{
  "items": [
    {
      "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "sender_id": "11111111-1111-4111-8111-111111111111",
      "recipient_id": "22222222-2222-4222-8222-222222222222",
      "original_filename": "quarterly_financials.pdf",
      "file_size": 1048576,
      "state": "COMPLETED",
      "created_at": "2026-08-29T17:30:00Z",
      "completed_at": "2026-08-29T17:30:02Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

### 4.3 Get Transfer Detail (`GET /api/v1/transfers/{transfer_id}`)
- **Authentication**: Required (`USER` or `ADMIN`)
- **Description**: Retrieves transfer metadata. Complete mediation strictly verifies that caller is sender, recipient, or admin.

#### Response (`200 OK`)
```json
{
  "id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "sender_id": "11111111-1111-4111-8111-111111111111",
  "recipient_id": "22222222-2222-4222-8222-222222222222",
  "original_filename": "quarterly_financials.pdf",
  "file_size": 1048576,
  "state": "COMPLETED",
  "sha256_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "algorithm": "AES-256-GCM",
  "protocol_version": "f9l3_v1",
  "vpn_transport": "WireGuard (10.50.0.1 -> 10.50.0.2)",
  "created_at": "2026-08-29T17:30:00Z",
  "completed_at": "2026-08-29T17:30:02Z"
}
```

---

### 4.4 Download Verified Plaintext (`GET /api/v1/transfers/{transfer_id}/download`)
- **Authentication**: Required (`USER` or `ADMIN`)
- **Description**: Unwraps DEK, authenticates AES-256-GCM tag, decrypts payload, verifies SHA-256 digest against expected value, and streams verified plaintext to client.
- **Fail-Closed Behavior**: If tag or digest check fails, returns `400 Bad Request`, marks transfer `QUARANTINED`, and streams **zero** plaintext bytes.

#### Response (`200 OK`)
- **Headers**:
  - `Content-Type: application/octet-stream`
  - `Content-Disposition: attachment; filename="quarterly_financials.pdf"`
  - `Content-Length: 1048576`
  - `X-Integrity-SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- **Body**: Binary plaintext file stream.

---

## 5. Admin Audit Logging Endpoints

### 5.1 Query Audit Logs (`GET /api/v1/admin/audit-events`)
- **Authentication**: Required (**`ADMIN` Only**)
- **Query Parameters**:
  - `event_type` (string, optional, e.g. `INTEGRITY_MISMATCH`, `LOGIN_FAILURE`)
  - `severity` (string, optional: `INFO`, `WARNING`, `CRITICAL`)
  - `actor_id` (UUID, optional)
  - `transfer_id` (UUID, optional)
  - `page` (integer, default: 1)
  - `page_size` (integer, default: 50, max: 200)

#### Response (`200 OK`)
```json
{
  "items": [
    {
      "id": "e4d3c2b1-0000-4000-8000-000000000001",
      "timestamp": "2026-08-29T17:30:02Z",
      "event_type": "TRANSFER_COMPLETED",
      "severity": "INFO",
      "actor_id": "22222222-2222-4222-8222-222222222222",
      "request_id": "req-9b1deb4d",
      "transfer_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "source_ip": "10.50.0.2",
      "metadata": {
        "verified_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
      },
      "previous_digest": "8a3f...",
      "event_digest": "4c2d..."
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 50
}
```

---

## 6. Observability Endpoints

### 6.1 Liveness Probe (`GET /health/live`)
- **Authentication**: None
- **Response**: `{"status": "alive", "app": "f9l3_53nd", "environment": "development"}`

### 6.2 Readiness Probe (`GET /health/ready`)
- **Authentication**: None
- **Response**: `{"status": "ready", "app": "f9l3_53nd", "storage": "available"}`
