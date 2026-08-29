# Architecture Diagram — Trust Boundaries & Zones

**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. Trust Boundaries Diagram

```mermaid
flowchart TB
    subgraph UntrustedClientZone["Zone 0: Untrusted Client Zone"]
        BrowserClient["React Web Client (Browser DOM)"]
        AttackerClient["Hostile / Malicious Actor"]
    end

    subgraph TrustBoundary1["Trust Boundary B-1: API Gateway & Session Filter"]
        direction TB
        AuthMiddleware["FastAPI Session Guard & Rate Limiter"]
        InputSanitizer["Schema & Multipart Sanitizer"]
    end

    subgraph ApplicationTrustZone["Zone 1: Application Trust Zone"]
        TransferOrchestrator["Transfer Orchestrator"]
        CryptoSubsystem["Crypto Subsystem (AES-256-GCM / SHA-256)"]
        StateMachine["Transfer State Machine"]
        StorageEngine["Path-Traversial Safe Storage Engine"]
        AuditPipeline["Tamper-Evident Audit Engine"]
    end

    subgraph TrustBoundary2["Trust Boundary B-2: Storage & Persistence Isolation"]
        direction TB
        DBIsolation["PostgreSQL DB Driver / Parameterized Queries"]
        StorageIsolation["UUID Path Scoper / Quarantine Boundary"]
    end

    subgraph PersistenceZone["Zone 2: Persistence & Metadata Zone"]
        PostgresDB[("PostgreSQL 16 Database")]
        EncryptedStore[("Encrypted Blob Storage")]
        QuarantineStore[("Quarantine Storage")]
    end

    subgraph TrustBoundary3["Trust Boundary B-3: Inter-Branch Transport Tunnel"]
        direction TB
        WireGuardTunnel["WireGuard VPN (ChaCha20-Poly1305 / Noise)"]
    end

    subgraph RemoteBranchZone["Zone 3: Remote Branch (Branch B)"]
        RemoteBackend["Branch B Backend Service"]
    end

    BrowserClient -->|HTTPS + Session Cookie| AuthMiddleware
    AttackerClient -->|Tampered Requests / Payloads| AuthMiddleware
    AuthMiddleware --> InputSanitizer
    InputSanitizer --> TransferOrchestrator

    TransferOrchestrator <--> CryptoSubsystem
    TransferOrchestrator <--> StateMachine
    TransferOrchestrator --> StorageEngine
    TransferOrchestrator --> AuditPipeline

    StorageEngine --> StorageIsolation
    AuditPipeline --> DBIsolation
    TransferOrchestrator --> DBIsolation

    DBIsolation --> PostgresDB
    StorageIsolation --> EncryptedStore
    StorageIsolation --> QuarantineStore

    TransferOrchestrator --> WireGuardTunnel
    WireGuardTunnel --> RemoteBackend
```

---

## 2. Trust Boundary Rules & Invariants

1. **Untrusted to Application (B-1)**: No parameter, header, or body is assumed valid. All inputs are validated via Pydantic; cookies must match an unexpired, unrevoked server session.
2. **Application to Persistence (B-2)**: No raw plaintext master key is ever stored in PostgreSQL; file storage paths are exclusively derived from server-generated UUIDs.
3. **Branch-to-Branch Network (B-3)**: Transmitted traffic is encapsulated in WireGuard; all file payloads are additionally encrypted at Layer 7 using AES-256-GCM with individual DEKs.
