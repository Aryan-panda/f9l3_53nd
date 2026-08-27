# f9l3_53nd — Secure Authenticated File Transfer Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Security: AES-256-GCM](https://img.shields.io/badge/Crypto-AES--256--GCM-green.svg)](docs/crypto-design.md)
[![Integrity: SHA-256](https://img.shields.io/badge/Integrity-SHA--256-brightgreen.svg)](docs/crypto-design.md)
[![Network: WireGuard](https://img.shields.io/badge/Network-WireGuard-red.svg)](docs/architecture.md)

`f9l3_53nd` is an enterprise-grade, defense-in-depth secure file transfer platform designed to simulate auditable, authenticated, and encrypted file transfer between two branch offices over untrusted networks.

---

## 1. Project Overview & Motivation

In distributed enterprise architectures, branch-to-branch data exchange faces multi-tier adversarial threats: passive network surveillance, active traffic modification, replay attacks, insider threats, and storage tampering. 

`f9l3_53nd` provides dual-layer defense:
- **Transport Security**: Network containment using a dedicated **WireGuard VPN** tunnel.
- **Application Security**: Envelope authenticated encryption (**AES-256-GCM**), pre- and post-transfer cryptographic digest verification (**SHA-256**), strict Role-Based Access Control (**Argon2id + HTTP-only Sessions**), and tamper-evident structured audit logging.

---

## 2. Core Architecture & Technology Stack

```text
┌────────────────────────────────────────────────────────┐
│                   Frontend (React/TS/Vite)             │
└───────────────────────────┬────────────────────────────┘
                            │ HTTPS / Session Cookie
┌───────────────────────────▼────────────────────────────┐
│              Backend Application (FastAPI/Python)       │
│ ┌─────────────────────────┬──────────────────────────┐ │
│ │  Auth & RBAC (Argon2id) │ Storage & Path Isolation │ │
│ ├─────────────────────────┼──────────────────────────┤ │
│ │  AEAD (AES-256-GCM)     │ Audit Logging & Chaining │ │
│ └─────────────────────────┴──────────────────────────┘ │
└───────────────────────────┬────────────────────────────┘
                            │ WireGuard Network Tunnel
┌───────────────────────────▼────────────────────────────┐
│       Branch B / PostgreSQL Metadata / Blob Storage     │
└────────────────────────────────────────────────────────┘
```

- **Backend**: Python 3.14+ / FastAPI / SQLAlchemy / Alembic / Pydantic v2
- **Frontend**: React 18 / TypeScript / Vite / Tailwind CSS
- **Database**: PostgreSQL 16
- **Cryptography**: Python `cryptography` (OpenSSL backend)
- **VPN / Network**: WireGuard
- **Containerization**: Docker Compose

---

## 3. Quick Start (Development)

### Prerequisites
- Python 3.11+ (Python 3.12+ recommended)
- Node.js 20+ & npm
- Docker & Docker Compose
- GNU Make

### Bootstrap Environment
```bash
# 1. Clone & Bootstrap virtualenv, npm dependencies, and dev configs
make setup

# 2. Generate local cryptographically secure development secrets (.env)
make secrets

# 3. Run all tests and validation suites
make test

# 4. Start local development servers
make dev
```

---

## 4. Security Principles & Threat Controls

| Security Objective | Primary Control | Secondary / Defense-in-Depth Control |
| :--- | :--- | :--- |
| **Confidentiality** | AES-256-GCM Payload Encryption | WireGuard VPN encrypted network tunnel |
| **Integrity** | SHA-256 Pre/Post Verification | AES-GCM 128-bit authentication tag |
| **Metadata Protection**| AES-GCM Additional Authenticated Data (AAD) | Foreign-key isolation & DB constraints |
| **Authentication** | Argon2id Password Hashing | HttpOnly, SameSite, Secure session cookies |
| **Authorization** | Server-side complete mediation (RBAC) | IDOR/BOLA UUID object isolation |
| **Replay Prevention** | Transfer state machine & nonce uniqueness | Freshness timestamps & one-time transfer IDs |
| **Auditability** | Structured audit event emission | Cryptographic previous-event digest chaining |

---

## 5. Repository Documentation Roadmap

- [Architecture & Design](docs/architecture.md)
- [Threat Model & STRIDE Analysis](docs/threat-model.md)
- [Cryptographic Specifications](docs/crypto-design.md)
- [API Contract & Schema Documentation](docs/API.md)
- [Transfer Protocol & State Machine](docs/protocol.md)
- [Security Testing & Adversarial Matrix](docs/security-test-report.md)
- [Security Policy & Vulnerability Disclosure](SECURITY.md)

---

## 6. Educational Scope & Limitations

This system is built as an educational and rigorous engineering demonstration of defense-in-depth principles. See [SECURITY.md](SECURITY.md) for explicitly documented assumptions, threat boundaries, and operational non-goals.
