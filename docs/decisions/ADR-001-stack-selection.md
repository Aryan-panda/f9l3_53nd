# ADR-001: Technology Stack Selection

## Status
Accepted

## Context
`f9l3_53nd` requires a robust, security-focused architecture to facilitate encrypted, authenticated, and auditable file transfers between two branch offices over untrusted networks. We evaluated options across language ecosystems, backend frameworks, cryptographic libraries, relational storage, and frontend client frameworks.

## Decision
We select the following core stack:
1. **Backend**: Python 3.12+ with FastAPI, Pydantic v2, and SQLAlchemy.
   - *Rationale*: FastAPI provides high-performance async capabilities, automatic OpenAPI schema generation, strict Pydantic input validation, and clean dependency injection.
2. **Cryptography**: Standard Python `cryptography` library (OpenSSL backend).
   - *Rationale*: Battle-tested, constant-time primitives, actively audited, and strict prevention of custom cipher rollouts.
3. **Database**: PostgreSQL 16 with Alembic migrations.
   - *Rationale*: ACID compliance, robust foreign-key constraints, JSONB audit indexing support, and mature UUID extensions.
4. **Network Isolation**: WireGuard VPN.
   - *Rationale*: State-of-the-art Noise protocol, minimal attack surface (approx. 4,000 lines of kernel code vs. 100k+ in OpenVPN/IPsec), high throughput, and simple key exchange.
5. **Frontend**: React 18 with TypeScript, Vite, and Tailwind CSS.
   - *Rationale*: Type safety, deterministic UI state handling, rapid build times, and clean separation between client rendering and backend authority.

## Alternatives Considered & Rejected
- **Node.js / Express**: Lacks built-in strict schema typing comparable to Pydantic without extensive boilerplate; Node `crypto` wrapper has historical API inconsistencies across runtime versions.
- **Go / Gin**: Excellent performance, but Python's `cryptography` library provides clearer cryptographic pedagogy and rapid development while maintaining C-extension performance.
- **OpenVPN**: Far larger codebase and complexity compared to WireGuard, with higher risk of protocol configuration errors.

## Security Impact
- Centralized cryptographic policy in Python `cryptography`.
- Complete memory-safe parsing in high-level language with OpenSSL core.
- WireGuard provides transport-level confidentiality independent of application-layer AES-256-GCM.

## Consequences
- Requires Python virtual environment and Node.js environments locally.
- Development tooling must support both ecosystems through unified `Makefile` and scripts.
