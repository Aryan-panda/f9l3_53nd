# System Architecture Specification — f9l3_53nd

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  
**Classification**: High-Level & Detailed Architectural Specification  

---

## 1. Architectural Vision & Design Methodology

`f9l3_53nd` is engineered as a secure, distributed file transfer system structured around clean layer separation, defense-in-depth, and complete mediation. The platform uses a modular monolith backend architecture communicating with a decoupled React SPA frontend, persisting relational metadata in PostgreSQL and encrypted file payloads in isolated filesystem volumes.

### Architecture Diagram Index:
- [C4 Context Diagram](diagrams/context.md)
- [C4 Container Diagram](diagrams/container.md)
- [C4 Component Diagram](diagrams/component.md)
- [Trust Boundaries & Network Zones](diagrams/trust-boundaries.md)
- [Transfer Upload Sequence Diagram](diagrams/upload-sequence.md)
- [Transfer Reception & Download Sequence Diagram](diagrams/download-sequence.md)
- [Cryptographic Pipeline Flowchart](diagrams/crypto-flow.md)

---

## 2. Layered Software Architecture

```text
┌────────────────────────────────────────────────────────┐
│ 1. API & ROUTING LAYER (backend/src/app/api/)           │
│    - Fast routing, Pydantic schema validation, status  │
│    - Dependency injection for auth guards & sessions   │
├────────────────────────────────────────────────────────┤
│ 2. APPLICATION SERVICE LAYER (backend/src/app/services/)│
│    - Business orchestration & state coordination       │
│    - Complete mediation & ownership authorization      │
├────────────────────────────────────────────────────────┤
│ 3. DOMAIN LOGIC & STATE MACHINE (backend/src/app/transfer/)
│    - Finite state machine transitions & validations    │
│    - Replay detection & envelope serialization         │
├────────────────────────────────────────────────────────┤
│ 4. CRYPTOGRAPHIC SUBSYSTEM (backend/src/app/crypto/)   │
│    - AES-256-GCM AEAD, SHA-256 digesting, Key Wrapping │
│    - CSPRNG nonce management & AAD binding             │
├────────────────────────────────────────────────────────┤
│ 5. STORAGE & PATH ISOLATION (backend/src/app/storage/) │
│    - Path canonicalization, UUID allocation            │
│    - Quarantine isolation & fail-closed file removal   │
├────────────────────────────────────────────────────────┤
│ 6. AUDIT & LOGGING ENGINE (backend/src/app/audit/)     │
│    - Structured security event emission                │
│    - Cryptographic SHA-256 previous-digest chaining    │
├────────────────────────────────────────────────────────┤
│ 7. INFRASTRUCTURE & DATABASE (backend/src/app/models/) │
│    - PostgreSQL 16 via SQLAlchemy & asyncpg            │
│    - Alembic asynchronous database migrations          │
└────────────────────────────────────────────────────────┘
```

---

## 3. Network Architecture & WireGuard Topology

```text
┌──────────────────────────────┐              ┌──────────────────────────────┐
│ BRANCH A (Sender Node)       │              │ BRANCH B (Receiver Node)     │
│  - Host IP: 192.168.1.10     │              │  - Host IP: 192.168.2.10     │
│  - WireGuard: 10.50.0.1/24   │              │  - WireGuard: 10.50.0.2/24   │
│  - Endpoint: wg-a:51820      │              │  - Endpoint: wg-b:51820      │
└──────────────┬───────────────┘              └──────────────▲───────────────┘
               │                                             │
               │ ChaCha20-Poly1305 Encrypted UDP Tunnel      │
               └─────────────────────────────────────────────┘
```

- **WireGuard Interface**: Dedicated network interface `wg0` isolating transfer endpoints from public routable internet addresses.
- **AllowedIPs Policy**: Strict subnet restriction (`10.50.0.0/24`) preventing lateral pivot attacks across unrelated internal subnets.

---

## 4. Key Management Architecture

1. **Master Key (KEK)**: 256-bit symmetric AES key injected at startup via environment configuration or secret manager. Never persisted in plaintext.
2. **Data Encryption Key (DEK)**: 256-bit symmetric AES key generated randomly per transfer (`os.urandom(32)`).
3. **Key Wrapping Protocol**: DEKs are wrapped using RFC 3394 AES Key Wrap with the KEK before being stored in the database `key_references` / `transfers` table.
4. **Memory Hygiene**: DEK plaintext bytes are deleted/overwritten in RAM immediately following encryption or decryption operations.

---

## 5. Storage Architecture

```text
storage/
├── encrypted/
│   └── <transfer-uuid>/
│       └── payload.enc       <-- AES-256-GCM ciphertext + tag + nonce
├── temporary/
│   └── <transfer-uuid>/      <-- Ephemeral ingestion buffer
└── quarantine/
    └── <transfer-uuid>/
        ├── payload.enc       <-- Failed / Tampered payload
        └── forensic_info.json<-- Failure diagnostic record
```

- Storage is decoupled from the web application server root.
- Path canonicalization with `os.path.realpath` verifies that all read/write paths remain inside the allowed base directory tree.
