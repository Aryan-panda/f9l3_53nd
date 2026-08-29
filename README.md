# f9l3_53nd — Secure Authenticated Inter-Branch File Transfer Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Security: AES-256-GCM](https://img.shields.io/badge/Crypto-AES--256--GCM-green.svg)](docs/crypto-design.md)
[![Key Wrap: RFC-3394](https://img.shields.io/badge/Key%20Wrap-RFC--3394-success.svg)](docs/key-management.md)
[![Integrity: SHA-256](https://img.shields.io/badge/Integrity-SHA--256-brightgreen.svg)](docs/crypto-design.md)
[![KDF: Argon2id](https://img.shields.io/badge/KDF-Argon2id-blueviolet.svg)](docs/security-model.md)
[![Network: WireGuard](https://img.shields.io/badge/Network-WireGuard-red.svg)](docs/architecture.md)
[![Audit: HMAC-SHA256](https://img.shields.io/badge/Audit-HMAC--SHA256-orange.svg)](docs/runbooks/audit-forensics-guide.md)
[![Tests: 115 Passed](https://img.shields.io/badge/Tests-115%20Passed-brightgreen.svg)](docs/final-verification-report.md)

`f9l3_53nd` is an enterprise-grade, defense-in-depth secure file transfer platform designed to simulate auditable, authenticated, and encrypted file transfer between two distinct branch offices (Branch A and Branch B) across an untrusted network.

---

## 1. Core Security Guarantees & Cryptographic Primitives

| Security Dimension | Implemented Primitive | Security Guarantee |
|---|---|---|
| **Confidentiality** | **AES-256-GCM (AEAD)** via OpenSSL / PyCA | Authenticated encryption with 128-bit MAC tag |
| **Key Hierarchy** | **RFC 3394 AES Key Wrap** | Two-tier KEK/DEK hierarchy with zero-downtime rotation |
| **Integrity Verification** | **SHA-256 Pre- & Post-Verification** | Byte-for-byte ground truth digest confirmation |
| **Nonce Freshness** | **96-bit CSPRNG Nonces** (`os.urandom`) | Strict nonce uniqueness with sliding-window replay detection |
| **Authentication & RBAC** | **Argon2id** + **HttpOnly Session Cookies** | Complete mediation, rate limiting, and role isolation |
| **Tamper-Evident Audit** | **HMAC-SHA256 Predecessor Chaining** | Mathematical tamper detection across chronological events |
| **Transport Security** | **WireGuard VPN** (Curve25519) | Point-to-point kernel-level cryptokey routing |
| **Resilience / Fail-Closed** | **Automated Quarantine Storage** | Immediate stream abort & isolation on tag or hash mismatch |

---

## 2. System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Branch A (HQ / 10.13.37.1)                       │
│                                                                             │
│   ┌──────────────────────────┐         ┌────────────────────────────────┐   │
│   │ React 18 Web Client / TS │ ◄──────►│ FastApi Backend Application    │   │
│   │ (Vite / Tailwind CSS)    │  HTTP   │ - AES-256-GCM AEAD Engine      │   │
│   └──────────────────────────┘         │ - RFC 3394 KeyManager (KEK/DEK)│   │
│   ┌──────────────────────────┐         │ - Argon2id Auth & Sessions     │   │
│   │ f9l3ctl CLI Tool         │ ◄──────►│ - 15-State Transfer FSM        │   │
│   └──────────────────────────┘         └───────────────┬────────────────┘   │
└────────────────────────────────────────────────────────┼────────────────────┘
                                                         │
                                      WireGuard VPN      │ (Encrypted UDP / Port 51820)
                                      Overlay Subnet     │ (AllowedIPs = 10.13.37.0/24)
                                                         │
┌────────────────────────────────────────────────────────▼────────────────────┐
│                            Branch B (Remote / 10.13.37.2)                   │
│                                                                             │
│   ┌────────────────────────────────┐         ┌──────────────────────────┐   │
│   │ FastApi Backend Application    │ ◄──────►│ PostgreSQL 16 Cluster    │   │
│   │ - Streaming Decryption         │         │ - Key References (Wrapped│   │
│   │ - SHA-256 Verification         │         │ - Transfers & Metadata   │   │
│   │ - Quarantine Path Isolation    │         │ - HMAC-SHA256 Audit Log  │   │
│   └────────────────────────────────┘         └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Quick Start (Development & Demonstration)

### Prerequisites
- Linux / macOS
- Python 3.12+ (tested up to Python 3.14)
- Node.js 20+ & npm
- Docker & Docker Compose v2
- GNU Make

### 3.1 Bootstrap in 3 Commands
```bash
# 1. Setup virtualenv, npm modules, and developer secrets
make setup && make secrets

# 2. Run full automated verification suite (115 tests + linters + types)
make test && make lint

# 3. Launch full multi-branch Docker container cluster
make docker-up
```

Access the applications:
- **Web UI (Branch A)**: [http://localhost:5173](http://localhost:5173)
- **Branch A Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Branch B Backend API**: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 4. Interactive Security Demonstration Script

Experience the complete end-to-end security workflow (encryption, SHA-256 digest check, MITM tampering simulation, quarantine trigger, WireGuard telemetry, and HMAC chain validation) with a single command:

```bash
bash scripts/demo.sh
```

```text
================================================================================
    f9l3_53nd — Secure Authenticated File Transfer Platform Demo
    AES-256-GCM • SHA-256 Digest • Argon2id • WireGuard VPN • HMAC Audit Log
================================================================================

[DEMO STEP 1/6] Authenticating Alice at Branch A (HQ)...
  [+] Alice Authenticated. Session Token: Fl1bIiqj... (Branch: 10.13.37.1)

[DEMO STEP 2/6] Alice Encrypts & Transmits Critical Report for Bob at Branch B...
  [+] Transfer Created: 0db25f9e-d8e3-48e7-a64c-befdfd2638fa
  [+] State: ENCRYPTED
  [+] SHA-256 Ground Truth: 0c84f43e691280303bcbb4e3318a850760ae21cafe800a4b5ceafc623965a9ae

[DEMO STEP 3/6] Bob Authenticates at Branch B & Receives Verified Decrypted Payload...
  [+] State Transition: ENCRYPTED -> COMPLETED
  [+] Decrypted SHA-256: 0c84f43e691280303bcbb4e3318a850760ae21cafe800a4b5ceafc623965a9ae
  [+] Digest Match:      100% IDENTICAL

[DEMO STEP 4/6] Adversary MITM Simulation: Corrupting On-Disk Ciphertext Byte...
  [!] Adversary injected bit-flip at offset -5
  [+] AEAD Tag Authentication Failed (Fail-Closed)
  [+] Automated Quarantine Triggered!
  [+] Transfer State: QUARANTINED

[DEMO STEP 5/6] WireGuard Point-to-Point Tunnel Telemetry Inspection...
  [+] Branch A Local IP: 10.13.37.1 | Branch B Peer IP: 10.13.37.2 (ACTIVE)

[DEMO STEP 6/6] Cryptographic Audit Log Chain Verification...
  [+] Total HMAC-SHA256 Chained Events Verified: 13
  [+] Broken Links: None (0)
  [+] Chain Mathematical Integrity: 100% VALID
```

---

## 5. CLI Automation Tooling (`f9l3ctl`)

The repository includes a dedicated security administrator and transfer CLI located at [scripts/f9l3ctl.sh](scripts/f9l3ctl.sh):

```bash
# 1. Authenticate session
scripts/f9l3ctl.sh login -u alice -p "StrongPassword123!"

# 2. Upload and encrypt file
scripts/f9l3ctl.sh send -f financial_report.pdf -r "<bob_uuid>"

# 3. List visible transfers
scripts/f9l3ctl.sh list --json

# 4. Download, decrypt, and verify file
scripts/f9l3ctl.sh receive -t "<transfer_uuid>" -o downloaded_report.pdf

# 5. Verify cryptographic audit chain integrity
scripts/f9l3ctl.sh verify-audit --json

# 6. Inspect WireGuard mesh telemetry
scripts/f9l3ctl.sh network-status --json
```

---

## 6. Monorepo Directory Structure

```text
f9l3_53nd/
├── docs/                 # Architectural specifications, threat models, ADRs, runbooks
│   ├── decisions/        # 10 Architecture Decision Records (ADR-001 to ADR-010)
│   ├── runbooks/         # 6 Production Runbooks (Deployment, Backup, Key Compromise, etc.)
│   ├── final-verification-report.md # Comprehensive Grade A+ Audit Report
│   └── README.md         # Master Documentation Index
├── backend/              # FastAPI application & Cryptographic Domain Core
│   ├── src/app/
│   │   ├── api/          # Route handlers & dependency injection guards
│   │   ├── crypto/       # AES-256-GCM, SHA-256, RFC 3394 KeyWrap, Nonce, Envelope
│   │   ├── security/     # Argon2id, Session lifecycle, RBAC, Token Bucket Rate Limiting
│   │   ├── transfer/     # 15-state Transfer FSM & Replay Detector
│   │   ├── storage/      # Path-traversal safe storage & Quarantine isolation
│   │   ├── audit/        # HMAC-SHA256 predecessor hash chaining
│   │   └── cli/          # f9l3ctl CLI application
│   └── tests/            # 115 tests (Unit, API, Integration, Adversarial)
├── frontend/             # React 18 + TypeScript + Vite + Tailwind CSS Client
├── infra/                # Dockerfiles, Docker Compose topology, WireGuard configurations
├── scripts/              # Automation (demo.sh, healthcheck.sh, docker-up.sh, security-test.sh)
└── storage/              # Encrypted and Quarantine payload directories
```

---

## 7. Complete Documentation Map

For detailed architectural specifications, threat analyses, and operator guides, consult the [docs/](docs/) directory:
- [System Architecture](docs/architecture.md)
- [Threat Model & STRIDE Analysis](docs/threat-model.md)
- [Cryptographic Specifications](docs/crypto-design.md)
- [Key Management & Lifecycle Policy](docs/key-management.md)
- [REST API Specifications](docs/API.md)
- [Database Schema & Models](docs/database.md)
- [Architecture Decision Records (ADRs)](docs/decisions/)
- [Production Deployment Runbook](docs/runbooks/deployment-guide.md)
- [Key Compromise Recovery Runbook](docs/runbooks/key-compromise-recovery.md)
- [Audit Log Forensics Manual](docs/runbooks/audit-forensics-guide.md)
- [Final Verification & Security Audit Report](docs/final-verification-report.md)

---

## 8. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
