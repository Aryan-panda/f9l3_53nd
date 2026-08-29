# C4 Model — System Context Diagram (Level 1)

**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. System Context Diagram

The System Context diagram illustrates how `f9l3_53nd` fits into the broader enterprise environment, interacting with users and external boundary systems.

```mermaid
C4Context
    title System Context diagram for f9l3_53nd Secure File Transfer Platform

    Person(branchAUser, "Branch A User", "Employee at Branch A initiating secure transfers or downloading received files.")
    Person(branchBUser, "Branch B User", "Employee at Branch B receiving and validating encrypted files.")
    Person(adminUser, "Security Administrator", "Audits security events, manages user accounts, and reviews transfer forensics.")

    Enterprise_Boundary(b0, "Enterprise Multi-Branch Infrastructure") {
        System(f9l3_system, "f9l3_53nd Platform", "Facilitates end-to-end encrypted, SHA-256 verified, auditable file transfers between branch offices.")
        System_Ext(wireguard_vpn, "WireGuard VPN Network", "Encapsulated UDP point-to-point network tunnel connecting branch LANs.")
        System_Ext(postgres_db, "PostgreSQL Database", "Stores user metadata, sessions, transfer state, wrapped keys, and chained audit logs.")
    }

    Rel(branchAUser, f9l3_system, "Uploads files, monitors transfers", "HTTPS / Session Cookie")
    Rel(branchBUser, f9l3_system, "Downloads verified files, checks status", "HTTPS / Session Cookie")
    Rel(adminUser, f9l3_system, "Inspects audit logs, manages accounts", "HTTPS / Session Cookie")

    Rel(f9l3_system, wireguard_vpn, "Transports encrypted envelopes between branch nodes", "WireGuard / UDP 51820")
    Rel(f9l3_system, postgres_db, "Persists metadata and chained audit logs", "PostgreSQL Wire Protocol / TLS")
```

---

## 2. Context Interactions & Responsibilities

| Interacting Entity | Interaction Channel | Security Controls Enforced |
| :--- | :--- | :--- |
| **Branch Users (A & B)** | Web Browser (HTTPS) | Session Authentication (Argon2id + HttpOnly cookie), RBAC, Object Ownership |
| **Security Administrator** | Admin Web Console (HTTPS) | RBAC (`ADMIN` role check), Strict audit log access |
| **WireGuard Transport** | UDP Port 51820 | ChaCha20-Poly1305 network encapsulation, Curve25519 peer verification |
| **PostgreSQL Database** | Port 5432 (TLS) | Parameterized queries, No plaintext keys stored, Encrypted password hashes |
