# Backup and Disaster Recovery Runbook

## 1. Scope & Recovery Objectives
This runbook defines backup procedures and disaster recovery (DR) protocols for the `f9l3_53nd` platform.

- **Recovery Point Objective (RPO)**: < 1 hour (maximum 1 hour of transfer metadata loss).
- **Recovery Time Objective (RTO)**: < 30 minutes (full service restoration time).

---

## 2. Backup Architecture & Data Categories

| Data Asset | Storage Location | Backup Method | Frequency | Retention |
|---|---|---|---|---|
| **PostgreSQL Database** | `/var/lib/postgresql/data` | `pg_dump` (encrypted) + WAL archiving | Hourly / Continuous | 90 days |
| **Encrypted File Store** | `storage/encrypted/` | Incremental encrypted snapshot (`rsync` / `restic`) | Every 6 hours | 180 days |
| **Audit Logs (Tamper-evident)** | Database `audit_events` | Offsite immutable write-once sync | Real-time / Daily | 7 years |
| **Cryptographic Master Keys** | Environment / KMS / HSM | Split-key paper backup / Key escrow | On rotation | Indefinite |

---

## 3. Automated Backup Procedure

### 3.1 Database Backup Script (`backup-db.sh`)
```bash
#!/usr/bin/env bash
set -euo pipefail

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_DIR="/var/backups/f9l3/db"
mkdir -p "${BACKUP_DIR}"

echo "==> Creating encrypted PostgreSQL dump..."
docker exec f9l3_postgres pg_dump -U f9l3_user -Fc f9l3_db | \
  openssl enc -aes-256-cbc -salt -pbkdf2 -out "${BACKUP_DIR}/f9l3_db_${TIMESTAMP}.dump.enc" -pass file:/etc/f9l3/backup_passphrase.txt

echo "[+] Database backup created: ${BACKUP_DIR}/f9l3_db_${TIMESTAMP}.dump.enc"
```

### 3.2 Payload Storage Backup Script (`backup-storage.sh`)
```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_TARGET="s3://f9l3-backups-immutable/storage-payloads/"
echo "==> Synchronizing encrypted payload store..."
aws s3 sync storage/encrypted/ "${BACKUP_TARGET}" --sse aws:kms
echo "[+] Payload store synchronized."
```

---

## 4. Disaster Recovery & Restoration Procedure

### 4.1 Step 1: Provision Clean Hardware & Runtimes
Clone repository and initialize base environment:
```bash
git clone https://github.com/Aryan-panda/f9l3_53nd.git /opt/f9l3_53nd
cd /opt/f9l3_53nd
bash scripts/bootstrap.sh
```

### 4.2 Step 2: Restore Master Cryptographic Key (KEK)
Inject verified master key from backup escrow:
```bash
export MASTER_KEY_HEX="<RestoredHexKey>"
export SECRET_KEY="<RestoredSecretKey>"
```

### 4.3 Step 3: Decrypt and Restore PostgreSQL Database
```bash
# Decrypt backup dump
openssl enc -d -aes-256-cbc -pbkdf2 -in /var/backups/f9l3/db/f9l3_db_<TIMESTAMP>.dump.enc \
  -out /tmp/restored.dump -pass file:/etc/f9l3/backup_passphrase.txt

# Start postgres container
docker compose up -d postgres
sleep 5

# Restore database schema and records
docker exec -i f9l3_postgres pg_restore -U f9l3_user -d f9l3_db --clean /tmp/restored.dump
rm /tmp/restored.dump
```

### 4.4 Step 4: Restore Encrypted Payload Directory
```bash
aws s3 sync s3://f9l3-backups-immutable/storage-payloads/ storage/encrypted/
```

### 4.5 Step 5: Verify Audit Log Cryptographic Integrity
```bash
scripts/f9l3ctl.sh login -u admin -p "<AdminPass>"
scripts/f9l3ctl.sh verify-audit --json
```
If `is_valid` is `true`, all restored records and cryptographic chains are intact.
