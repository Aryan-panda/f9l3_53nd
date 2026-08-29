# `f9l3_53nd` Documentation Index & Architecture Map

Welcome to the comprehensive documentation index for `f9l3_53nd` (Secure Authenticated Inter-Branch File Transfer Platform).

---

## 1. System Architecture & Requirements
- [System Requirements & Threat Scope](requirements.md): Functional and non-functional requirements, branch communication model, and failure invariants.
- [High-Level Architecture](architecture.md): C4 container views, component interactions, and data-flow diagrams.
- [Security Model & Guarantees](security-model.md): Detailed threat controls, trust boundaries, and cryptographic invariants.
- [Threat Model & STRIDE Analysis](threat-model.md): Detailed STRIDE vulnerability decomposition, attack vectors, and mitigations.
- [Database & Storage Specifications](database.md): Entity-relationship diagrams, schema definitions, and UUID storage containment.
- [REST API Specifications](API.md): Endpoint definitions, request/response schemas, error codes, and authentication headers.

---

## 2. Cryptography & Key Management
- [Cryptographic Design Specification](crypto-design.md): AES-256-GCM AEAD, SHA-256 integrity, binary envelope binary structure, and canonical AAD serialization.
- [Key Management & Lifecycle Policy](key-management.md): Two-tier KEK/DEK key hierarchy, RFC 3394 key wrapping, and zero-downtime dual-key rotation.

---

## 3. Architecture Decision Records (ADRs)
- [ADR-001: Technology Stack Selection](decisions/ADR-001-stack-selection.md)
- [ADR-002: Backend Layered Architecture](decisions/ADR-002-backend-architecture.md)
- [ADR-003: AEAD Algorithm Selection (AES-256-GCM)](decisions/ADR-003-aead-selection.md)
- [ADR-004: Password Hashing Primitive (Argon2id)](decisions/ADR-004-password-hashing.md)
- [ADR-005: Two-Tier Key Hierarchy & RFC 3394 Key Wrap](decisions/ADR-005-key-management.md)
- [ADR-006: Server-Side HttpOnly Session Authentication](decisions/ADR-006-authentication-session.md)
- [ADR-007: Explicit Transfer State Machine & Envelope Format](decisions/ADR-007-transfer-protocol.md)
- [ADR-008: Secure Storage Model & Quarantine Segregation](decisions/ADR-008-storage-model.md)
- [ADR-009: Point-to-Point WireGuard Network Transport](decisions/ADR-009-wireguard.md)
- [ADR-010: Tamper-Evident HMAC-SHA256 Chained Audit Logging](decisions/ADR-010-audit-logging.md)

---

## 4. Production Runbooks & Operations
- [Production Deployment Guide](runbooks/deployment-guide.md): Hardware prerequisites, secret provisioning, WireGuard setup, and Docker deployment.
- [Backup & Disaster Recovery Runbook](runbooks/backup-and-recovery.md): Encrypted database dumps, payload syncing, and PITR restoration.
- [Key Compromise Recovery Runbook](runbooks/key-compromise-recovery.md): 4-phase incident containment, emergency KEK rotation, and batch DEK re-wrapping.
- [Audit Log Forensics & Investigation Guide](runbooks/audit-forensics-guide.md): HMAC chain verification, database tamper triage, and evidence export.
- [Network Failover & Troubleshooting Guide](runbooks/network-failover-procedure.md): WireGuard telemetry health metrics, handshake diagnostics, and WAN failover.
- [Security Operator Checklist](runbooks/operator-checklist.md): Daily/weekly maintenance tasks and `f9l3ctl` CLI cheat sheet.

---

## 5. Verification & Security Audit Reports
- [Final Verification & Security Audit Report](final-verification-report.md): Formal verification metrics, test results, STRIDE mitigation matrix, and Grade A+ certification.
