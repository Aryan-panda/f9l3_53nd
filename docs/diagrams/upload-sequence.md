# Architecture Diagram — Transfer Upload Sequence

**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. Upload & Transmission Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Sender (Branch A)
    participant Client as React Web App
    participant API as FastAPI Router
    participant Auth as Session & RBAC Guard
    participant TransferSvc as Transfer Service
    participant Crypto as Crypto Subsystem
    participant State as State Machine
    participant Storage as File Storage Store
    participant DB as PostgreSQL DB
    participant Audit as Audit Subsystem
    participant WireGuard as WireGuard VPN (Branch B)

    User->>Client: Selects file & recipient (Branch B)
    Client->>API: POST /api/v1/transfers (Multipart: file, recipient_id)
    API->>Auth: Validate Session Cookie & Permissions
    Auth-->>API: Validated (User Context: Alice, Role: USER)
    
    API->>TransferSvc: create_transfer(file_stream, sender_id, recipient_id)
    TransferSvc->>State: init_state(CREATED)
    TransferSvc->>State: transition(VALIDATING)
    
    TransferSvc->>TransferSvc: Validate file size (<= 50MB) & sanitize filename
    
    TransferSvc->>State: transition(HASHING)
    TransferSvc->>Crypto: compute_sha256(plaintext_stream)
    Crypto-->>TransferSvc: original_sha256_digest
    
    TransferSvc->>State: transition(ENCRYPTING)
    TransferSvc->>Crypto: generate_dek() (256-bit CSPRNG)
    Crypto-->>TransferSvc: ephemeral_dek
    TransferSvc->>Crypto: wrap_key(ephemeral_dek, master_kek)
    Crypto-->>TransferSvc: wrapped_dek
    
    TransferSvc->>Crypto: build_aad(protocol_v1, transfer_id, sender_id, recipient_id, file_size)
    Crypto-->>TransferSvc: aad_bytes
    
    TransferSvc->>Crypto: aes_256_gcm_encrypt(plaintext, ephemeral_dek, nonce, aad_bytes)
    Crypto-->>TransferSvc: ciphertext + 128-bit authentication_tag
    
    TransferSvc->>Storage: save_encrypted_payload(transfer_id, ciphertext, tag, nonce)
    Storage-->>TransferSvc: storage_path
    
    TransferSvc->>DB: INSERT INTO transfers (id, sender, recipient, sha256, wrapped_dek, state=READY)
    TransferSvc->>Audit: record_event(TRANSFER_CREATED, actor=Alice, transfer_id)
    
    TransferSvc->>State: transition(TRANSFERRING)
    TransferSvc->>WireGuard: transmit_transfer_package(envelope)
    WireGuard-->>TransferSvc: ACK_RECEIVED (State -> RECEIVED on Branch B)
    
    TransferSvc-->>API: TransferResponse(transfer_id, status=TRANSFERRING)
    API-->>Client: 201 Created (JSON Response)
    Client-->>User: Display transfer progress & cryptographic status
```

---

## 2. Invariant Checklist during Upload

1. **Pre-encryption Digesting**: SHA-256 is strictly computed on the *original plaintext* before AES-GCM encryption occurs.
2. **Ephemeral DEK Generation**: A new 256-bit random DEK is generated per transfer and never reused across files.
3. **Atomic Persistence**: Transfer metadata, wrapped DEK, and initial audit log record are committed inside a transactional database boundary.
