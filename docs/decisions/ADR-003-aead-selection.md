# ADR-003: Selection of AES-256-GCM as Primary AEAD Construction

## Status
Accepted

## Context
Securing file transfers at the application layer requires an Authenticated Encryption with Associated Data (AEAD) scheme that provides confidentiality, ciphertext integrity, and metadata authentication simultaneously in a single cryptographic pass.

## Decision
We select **AES-256-GCM** (Galois/Counter Mode) with 256-bit keys, 96-bit random nonces, and 128-bit authentication tags, implemented via the Python `cryptography` library.

## Alternatives Considered & Rejected
- **AES-256-CBC with HMAC-SHA256 (Encrypt-then-MAC)**: Requires two cryptographic passes, explicit MAC key derivation, and is vulnerable to padding oracle attacks if improperly implemented.
- **ChaCha20-Poly1305**: Outstanding cipher (and used at the WireGuard layer), but AES-256-GCM is specifically mandated by the project assignment specification and benefits from native AES-NI CPU acceleration on server hardware.
- **AES-ECB / AES-CTR without MAC**: Insecure modes lacking authentication, completely vulnerable to bit-flipping attacks.

## Security Impact
- Provides both confidentiality and authenticity in constant-time execution.
- Authenticated Associated Data (AAD) binds transfer metadata (`transfer_id`, `sender_id`, `recipient_id`, `file_size`) to the authentication tag, neutralizing ciphertext splicing and metadata substitution attacks.

## Consequences
- Requires strict adherence to nonce uniqueness: a nonce must never be reused under the same key. We resolve this by generating an ephemeral DEK per transfer.
