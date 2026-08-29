# C4 Model — Backend Component Diagram (Level 3)

**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. Backend Component Diagram

The Component diagram decomposes the Backend Application container into internal modular services, dependency injection layers, and cryptographic boundaries.

```mermaid
C4Component
    title Component diagram for Backend Application

    Container_Boundary(api_boundary, "FastAPI Backend Application") {
        Component(api_routes, "API Routing Layer", "FastAPI Routers", "Validates request schemas, maps HTTP status codes, handles route dispatch.")
        Component(auth_guard, "Security & Auth Guard", "FastAPI Dependencies", "Enforces session validation, rate limiting, and RBAC complete mediation.")
        Component(transfer_service, "Transfer Service", "Application Service Layer", "Coordinates transfer lifecycle, state transitions, and file ingestion.")
        Component(crypto_service, "Cryptographic Service", "app.crypto", "Manages AES-256-GCM AEAD, SHA-256 hashing, KEK key wrapping, and CSPRNG nonces.")
        Component(state_machine, "Transfer State Machine", "app.transfer", "Validates state transitions and detects replayed transfer tokens.")
        Component(storage_service, "Storage Service", "app.storage", "Handles path canonicalization, disk writes, UUID allocation, and quarantine isolation.")
        Component(audit_service, "Audit Subsystem", "app.audit", "Emits structured security events and computes cryptographic digest chain.")
    }

    ContainerDb(db_ext, "PostgreSQL Database", "Tables: users, sessions, transfers, audit_events, key_references")
    Container(storage_ext, "Encrypted / Quarantine File Store", "Directories: storage/encrypted/, storage/quarantine/")

    Rel(api_routes, auth_guard, "Authenticates caller before route entry")
    Rel(api_routes, transfer_service, "Delegates transfer operations")
    Rel(transfer_service, state_machine, "Evaluates state transitions")
    Rel(transfer_service, crypto_service, "Performs encryption, hashing & verification")
    Rel(transfer_service, storage_service, "Reads/writes physical blobs")
    Rel(transfer_service, audit_service, "Emits transfer lifecycle events")
    Rel(auth_guard, audit_service, "Emits authentication & authorization events")

    Rel(transfer_service, db_ext, "Persists metadata and wrapped DEKs")
    Rel(audit_service, db_ext, "Persists chained audit records")
    Rel(storage_service, storage_ext, "Writes encrypted/quarantine files")
```

---

## 2. Component Coupling & Invariants

1. **No Crypto in API Handlers**: Cryptographic operations are isolated strictly within `app.crypto.*`. Route handlers are thin controllers performing only request parsing, dependency injection, and response serializing.
2. **No Direct Filesystem Calls in Services**: All disk interactions pass through `app.storage.file_store.FileStore`, enforcing path traversal checks and UUID directory scoping.
3. **Mandatory Audit Side-Effects**: State transitions and security-sensitive events must invoke `AuditService.record_event()` inside the same database transaction.
