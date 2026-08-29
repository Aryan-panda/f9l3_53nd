# Production Deployment & Installation Guide

## 1. Overview
This document outlines the step-by-step procedure for deploying `f9l3_53nd` across branch office server nodes in production.

---

## 2. System & Hardware Prerequisites

| Requirement | Minimum | Recommended |
|---|---|---|
| **Operating System** | Ubuntu 22.04 LTS / Debian 12 / RHEL 9 | Ubuntu 24.04 LTS |
| **CPU Architecture** | 2 Cores (x86_64 or ARM64) | 4 Cores with AES-NI hardware acceleration |
| **Memory (RAM)** | 4 GB | 8 GB |
| **Storage** | 20 GB SSD | 100+ GB NVMe SSD (Encrypted with LUKS) |
| **Network** | UDP port 51820 (WireGuard), TCP port 443/8000 | Direct point-to-point fiber/VPN link |
| **Runtimes** | Docker 24+, Docker Compose v2, Python 3.12, Node.js 20 | Docker Engine with rootless mode |

---

## 3. Pre-Deployment Secret Provisioning

Never use default development secrets in staging or production.

1. **Generate 256-bit Cryptographic Master Key (KEK)**:
   ```bash
   python3 -c "import os; print(os.urandom(32).hex())"
   ```
2. **Generate Session Signing Secret**:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. **Generate PostgreSQL Database Password**:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(24))"
   ```
4. **Generate WireGuard Curve25519 Keypairs & PSK**:
   ```bash
   bash scripts/generate-wg-keys.sh
   ```

Store these secrets in an enterprise secret manager (e.g., HashiCorp Vault, AWS Secrets Manager) and inject them as environment variables during process launch.

---

## 4. Multi-Branch Network Configuration (WireGuard)

1. On **Branch A (10.13.37.1)**:
   Deploy `infra/wireguard/branch-a/wg0.conf` with file permissions `chmod 600`.
   Bring up the interface:
   ```bash
   sudo wg-quick up infra/wireguard/branch-a/wg0.conf
   ```

2. On **Branch B (10.13.37.2)**:
   Deploy `infra/wireguard/branch-b/wg0.conf` with file permissions `chmod 600`.
   Bring up the interface:
   ```bash
   sudo wg-quick up infra/wireguard/branch-b/wg0.conf
   ```

3. Validate point-to-point connectivity:
   ```bash
   bash scripts/validate-tunnel.sh
   ```

---

## 5. Database Initialization & Migration

1. Start PostgreSQL 16 cluster:
   ```bash
   docker compose up -d postgres
   ```
2. Run database migrations:
   ```bash
   cd backend && .venv/bin/alembic upgrade head
   ```
3. Seed initial branch accounts with strong Argon2id credentials:
   ```bash
   cd backend && .venv/bin/python -m app.db.seed
   ```

---

## 6. Container Deployment & Cluster Launch

1. Start full multi-branch topology:
   ```bash
   bash scripts/docker-up.sh
   ```
2. Inspect container status:
   ```bash
   docker compose ps
   ```
3. Run comprehensive health probes:
   ```bash
   make healthcheck
   ```

---

## 7. Post-Deployment Smoke Verification

Execute a complete smoke transfer using `f9l3ctl`:
```bash
# 1. Login as Branch A user
scripts/f9l3ctl.sh login -u alice -p "<StrongPassword>"

# 2. Upload test document
scripts/f9l3ctl.sh send -f smoke_test.txt -r "<bob_uuid>" --json

# 3. Verify audit chain
scripts/f9l3ctl.sh verify-audit --json
```
Ensure that `verify-audit` returns `is_valid: true`.
