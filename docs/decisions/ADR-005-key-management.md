# ADR-005: Key Hierarchy & Envelope Encryption (Two-Tier KEK/DEK)

## Status
Accepted

## Context
Encrypting all files with a single global application key presents severe operational and security liabilities: key compromise exposes all historical and future files, key rotation requires re-encrypting all storage payloads, and high transfer volume risks AES-GCM nonce collision.

## Decision
We implement a **Two-Tier Envelope Key Management Hierarchy**:
1. **Key Encryption Key (KEK / Master Key)**: A long-term 256-bit AES master key injected at application startup via environment variables or KMS.
2. **Data Encryption Key (DEK)**: An ephemeral 256-bit AES key generated uniquely per transfer (`os.urandom(32)`).
3. **Key Wrapping**: DEKs are wrapped using RFC 3394 AES Key Wrap with the KEK and stored in database metadata.

## Alternatives Considered & Rejected
- **Direct Master Key Encryption**: Encrypting every file directly with the KEK. Rejected due to nonce collision risks and lack of blast radius containment.
- **Client-Side Key Generation**: Storing master keys in browser JavaScript. Rejected because client environments are untrusted and exposed to XSS.

## Security Impact
- Nonce collision probability drops to zero since each DEK is used for exactly one payload.
- Compromise of an individual DEK only exposes a single file transfer.
- Master Key rotation only requires re-wrapping stored DEKs in the database, without reading or re-encrypting physical file payloads.

## Consequences
- Requires wrapping/unwrapping operations during transfer upload and download lifecycles.
