# C4 Model — Container Diagram (Level 2)

**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. Container Diagram

The Container diagram zooms into the `f9l3_53nd` system, showing high-level software blocks, execution environments, and communication protocols.

```mermaid
C4Container
    title Container diagram for f9l3_53nd Platform

    Person(user, "Branch User", "Authenticated user transferring or receiving files.")
    Person(admin, "Administrator", "Auditor inspecting system logs and users.")

    Container_Boundary(c1, "f9l3_53nd Platform Scope") {
        Container(spa, "Web Client (SPA)", "React, TypeScript, Vite, Tailwind CSS", "Provides user interface for authentication, file selection, transfer monitoring, and admin audit dashboard.")
        Container(api, "Backend Application", "Python 3.12+, FastAPI, SQLAlchemy, Pydantic", "Enforces authentication, authorization, AES-256-GCM AEAD, SHA-256 integrity, state machine, and audit generation.")
        ContainerDb(db, "Relational Database", "PostgreSQL 16", "Stores user credentials (Argon2id), session states, transfer metadata, wrapped DEKs, and chained audit logs.")
        Container(storage, "Payload Storage Store", "Filesystem Volume (Ext4/ZFS)", "Maintains encrypted payloads in storage/encrypted/ and quarantined payloads in storage/quarantine/.")
    }

    System_Ext(wireguard, "WireGuard Tunnel", "Noise Protocol / Linux Kernel", "Point-to-point network tunnel between Branch A (10.50.0.1) and Branch B (10.50.0.2).")

    Rel(user, spa, "Interacts with UI", "HTTPS")
    Rel(admin, spa, "Interacts with Admin UI", "HTTPS")
    Rel(spa, api, "API calls", "JSON / HTTPS / Session Cookie")
    Rel(api, db, "Reads & writes metadata, logs, sessions", "asyncpg / SQL / Port 5432")
    Rel(api, storage, "Reads & writes encrypted blobs", "Filesystem POSIX I/O")
    Rel(api, wireguard, "Routes transfer payloads to remote branch", "WireGuard UDP 51820")
```

---

## 2. Container Characteristics & Isolation

| Container | Technology | Responsibilities | Security Controls |
| :--- | :--- | :--- | :--- |
| **Web Client** | React 18 / TypeScript | Presentation, file selection, state display | No crypto keys stored; strict HTML sanitization |
| **Backend App** | FastAPI / Python 3.12+ | Orchestration, AEAD, SHA-256, State Machine | Non-root container (appuser), Least privilege |
| **Database** | PostgreSQL 16 | ACID metadata persistence, JSONB audit indexing | Parameterized queries, UUID primary keys |
| **Blob Storage**| Filesystem Volume | Encrypted payload and quarantine containment | UUID path abstraction outside web root |
| **WireGuard** | Noise Protocol / UDP | Branch network tunnel encapsulation | Curve25519 public key peer authentication |
