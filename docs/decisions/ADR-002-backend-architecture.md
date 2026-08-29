# ADR-002: Modular Layered Backend Architecture

## Status
Accepted

## Context
A common architectural failure in security-critical web applications is mixing business logic, cryptographic operations, SQL queries, and HTTP route handling into single monolithic route functions. This makes unit testing impossible, complicates security audits, and risks inadvertent information leakage.

## Decision
We implement a strict 6-layer decoupled backend architecture:
1. **API Layer (`app.api`)**: Request schema parsing, dependency injection, and HTTP status mapping.
2. **Service Layer (`app.services`)**: Business workflow orchestration and complete mediation authorization checks.
3. **Crypto Subsystem (`app.crypto`)**: Self-contained cryptographic operations (AES-GCM, SHA-256, Key Wrapping).
4. **Transfer Engine (`app.transfer`)**: State machine definitions, replay cache, and envelope serialization.
5. **Storage Layer (`app.storage`)**: Filesystem path canonicalization, UUID allocation, and quarantine isolation.
6. **Audit Layer (`app.audit`)**: Structured event emission and digest chaining.

## Alternatives Considered & Rejected
- **Microservices Architecture**: Dividing these modules into separate network services (e.g., `crypto-service`, `auth-service`) adds massive network latency, serialized key transit risks over HTTP, and operational complexity without security benefit for this deployment model.
- **Fat Route Handlers**: Putting SQL and crypto directly into FastAPI route functions. Rejected due to unmaintainability and audit risk.

## Security Impact
- Isolated cryptographic routines can be audited and tested independently of web frameworks.
- Authorization logic cannot be accidentally bypassed by route shortcuts.

## Consequences
- Requires strict dependency direction: API -> Services -> Domain/Crypto -> Storage/DB.
- Code across layers communicates via strongly typed Pydantic models and domain exceptions.
