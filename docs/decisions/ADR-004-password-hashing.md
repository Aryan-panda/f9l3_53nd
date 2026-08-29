# ADR-004: Password Hashing Algorithm Selection (Argon2id)

## Status
Accepted

## Context
User passwords must be stored irreversibly to defend against offline dictionary attacks, GPU cluster cracking, and side-channel timing attacks if database credentials are breached.

## Decision
We select **Argon2id** (RFC 9106) utilizing `argon2-cffi` with parameters:
- Memory: $65536 \text{ KiB}$ ($64 \text{ MiB}$)
- Iterations: $3$
- Parallelism: $4$ lanes
- Salt: 16-byte random salt generated per hash.

## Alternatives Considered & Rejected
- **bcrypt**: Good algorithm, but limited memory hardness makes it vulnerable to customized FPGA/ASIC cracking arrays; also truncates passwords at 72 bytes.
- **PBKDF2-HMAC-SHA256**: CPU-bound with zero memory hardness; easily accelerated on modern GPUs.
- **MD5 / SHA-256 / SHA-512**: Unsalted/fast hashes; completely insecure for password storage.

## Security Impact
- Argon2id combines Argon2d (data-dependent memory access for GPU resistance) and Argon2i (data-independent memory access for side-channel resistance).
- High memory footprint renders mass offline parallel cracking infeasible.

## Consequences
- Requires approximately 30-50ms CPU time per login attempt on the server, which also serves as a natural rate-limiting friction against online brute-force attacks.
