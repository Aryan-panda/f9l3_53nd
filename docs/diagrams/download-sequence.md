# Architecture Diagram — Reception & Download Sequence

**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. Reception, Decryption & Download Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as Recipient (Branch B)
    participant Client as React Web App
    participant API as FastAPI Router
    participant Auth as Session & RBAC Guard
    participant TransferSvc as Transfer Service
    participant Crypto as Crypto Subsystem
    participant State as State Machine
    participant Storage as File Storage Store
    participant DB as PostgreSQL DB
    participant Audit as Audit Subsystem

    User->>Client: Requests file download (/transfers/{id}/download)
    Client->>API: GET /api/v1/transfers/{id}/download
    API->>Auth: Validate Session Cookie & Identity
    Auth-->>API: Validated (User Context: Bob, Role: USER)

    API->>TransferSvc: get_decrypted_file(transfer_id, user_context=Bob)
    TransferSvc->>DB: SELECT * FROM transfers WHERE id = transfer_id
    DB-->>TransferSvc: transfer_record

    Note over TransferSvc,DB: Complete Mediation (IDOR/BOLA Prevention)
    alt Bob is NOT recipient, sender, or admin
        TransferSvc->>Audit: record_event(AUTHORIZATION_FAILURE, actor=Bob, transfer_id)
        TransferSvc-->>API: raise AuthorizationError("Access denied")
        API-->>Client: 403 Forbidden
    else Bob is Authorized
        TransferSvc->>State: transition(AUTHENTICATING)
        TransferSvc->>Storage: load_encrypted_payload(transfer_id)
        Storage-->>TransferSvc: ciphertext, nonce, authentication_tag

        TransferSvc->>Crypto: unwrap_key(transfer_record.wrapped_dek, master_kek)
        Crypto-->>TransferSvc: ephemeral_dek

        TransferSvc->>Crypto: aes_256_gcm_decrypt(ciphertext, ephemeral_dek, nonce, aad, tag)
        
        alt AES-GCM Tag / AAD Verification Fails
            Crypto-->>TransferSvc: raise DecryptionError("Tag mismatch / Tampering detected")
            TransferSvc->>State: transition(QUARANTINED)
            TransferSvc->>Storage: move_to_quarantine(transfer_id)
            TransferSvc->>Audit: record_event(DECRYPTION_FAILURE, severity=CRITICAL)
            TransferSvc-->>API: raise DecryptionError()
            API-->>Client: 400 Bad Request (Generic Error Envelope)
        else Tag Validated Successfully
            Crypto-->>TransferSvc: decrypted_plaintext
            TransferSvc->>State: transition(VERIFYING)

            TransferSvc->>Crypto: compute_sha256(decrypted_plaintext)
            Crypto-->>TransferSvc: computed_digest

            alt computed_digest != transfer_record.sha256_digest
                TransferSvc->>State: transition(QUARANTINED)
                TransferSvc->>Storage: move_to_quarantine(transfer_id)
                TransferSvc->>Audit: record_event(INTEGRITY_MISMATCH, severity=CRITICAL)
                TransferSvc-->>API: raise IntegrityError("SHA-256 digest mismatch")
                API-->>Client: 400 Bad Request (Generic Error Envelope)
            else SHA-256 Digest Matches
                TransferSvc->>State: transition(COMPLETED)
                TransferSvc->>Audit: record_event(TRANSFER_COMPLETED, actor=Bob, transfer_id)
                TransferSvc-->>API: FileStream(decrypted_plaintext, filename=transfer.original_filename)
                API-->>Client: 200 OK (Binary Stream with Content-Disposition)
                Client-->>User: Plaintext File Download Complete
            end
        end
    end
```

---

## 2. Invariant Checklist during Download

1. **Complete Mediation (BOLA/IDOR)**: The server verifies that `current_user.id == transfer.recipient_id` (or sender/admin) before initiating any decryption or storage reads.
2. **Zero Plaintext Output on Tag Failure**: If the AES-GCM authentication tag check fails, processing terminates immediately, no partial plaintext is released, and payload is isolated to quarantine.
3. **Double Verification Lock**: Plaintext is delivered to the client *only after* the computed post-decryption SHA-256 digest exactly matches the pre-recorded sender digest.
