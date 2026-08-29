# ADR-010: Tamper-Evident Structured Audit Logging & Hash Chaining

## Status
Accepted

## Context
Enterprise security compliance and forensic post-mortems require auditable, non-repudiable records of security-sensitive events (logins, transfer creations, integrity failures, authorization denials).

## Decision
We implement a **Chained Tamper-Evident Audit Subsystem**:
1. **Structured Event Schema**: Standard JSON structure storing `id`, `timestamp`, `event_type`, `severity`, `actor_id`, `request_id`, `transfer_id`, and `metadata`.
2. **Zero Sensitive Data**: Passwords, encryption keys, session secrets, and plaintext payloads are strictly forbidden from logs.
3. **Cryptographic Chaining**: Each audit entry includes the SHA-256 digest of the preceding event:
   $$\text{event\_digest}_n = \text{SHA-256}(\text{event\_digest}_{n-1} \parallel \text{id}_n \parallel \text{timestamp}_n \parallel \text{event\_type}_n \parallel \text{actor\_id}_n \parallel \text{metadata}_n)$$

## Alternatives Considered & Rejected
- **Unstructured Plain Text Log Files (`app.log`)**: Prone to parsing errors, lack queryable indexing, and easily modified/truncated on disk without detection.
- **Third-Party Blockchain Service**: Unnecessary performance overhead and external dependency for internal enterprise file transfer.

## Security Impact
- Any unauthorized modification, insertion, or deletion of historical audit records breaks the mathematical hash chain.
- Provides immediate non-repudiation and forensic accountability.

## Consequences
- Requires serializing event hashing to maintain consecutive digest dependencies.
