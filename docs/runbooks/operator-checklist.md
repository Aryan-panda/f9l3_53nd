# Security Operator Checklist & Operations Manual

## 1. Daily Operations Checklist

- [ ] **Audit Log Verification**:
  ```bash
  scripts/f9l3ctl.sh verify-audit --json
  ```
  *Action*: Verify `is_valid: true`. If false, escalate immediately to Security Incident Response.

- [ ] **Quarantine Queue Review**:
  ```sql
  SELECT id, sender_id, recipient_id, filename, created_at, quarantine_path 
  FROM transfers 
  WHERE state = 'QUARANTINED' AND created_at >= NOW() - INTERVAL '24 HOURS';
  ```
  *Action*: Review any new quarantined payloads for signs of tampering or active transmission corruption.

- [ ] **WireGuard Link Health**:
  ```bash
  scripts/f9l3ctl.sh network-status --json
  ```
  *Action*: Confirm handshake age < 60 seconds and zero unexpected packet loss.

---

## 2. Weekly Maintenance Checklist

- [ ] **Database Vacuum & Index Optimization**:
  ```bash
  docker exec f9l3_postgres vacuumdb -U f9l3_user -d f9l3_db --analyze
  ```

- [ ] **Backup Restoration Drill**:
  Test restoring the latest encrypted database backup onto an isolated staging server and execute audit chain validation.

- [ ] **Disk Storage Capacity Review**:
  ```bash
  df -h storage/encrypted/ storage/quarantine/
  ```
  *Action*: Ensure storage partitions remain below 75% capacity threshold.

---

## 3. Monthly Security Review

- [ ] **User Account & Privilege Audit**:
  Review all active user accounts and revoke obsolete contractor or former employee accounts:
  ```bash
  scripts/f9l3ctl.sh login -u admin -p "<AdminPass>"
  ```
  Inspect user listing in the web UI under `/admin` -> `User Access`.

- [ ] **Session & Password Policy Review**:
  Confirm Argon2id memory and iteration configurations match latest NIST guidelines.

- [ ] **Dependency Security Scan**:
  ```bash
  cd backend && .venv/bin/pip-audit || true
  cd frontend && npm audit
  ```

---

## 4. Quick Command Reference Cheat Sheet

| Task | Command |
|---|---|
| **CLI Login** | `scripts/f9l3ctl.sh login -u <username> -p <password>` |
| **Send Encrypted File** | `scripts/f9l3ctl.sh send -f <path> -r <recipient_uuid>` |
| **Download & Verify File** | `scripts/f9l3ctl.sh receive -t <transfer_uuid> -o <out_path>` |
| **List Visible Transfers** | `scripts/f9l3ctl.sh list --json` |
| **Verify Audit Chain** | `scripts/f9l3ctl.sh verify-audit --json` |
| **Check Network Telemetry** | `scripts/f9l3ctl.sh network-status --json` |
| **Run Health Probes** | `make healthcheck` |
| **Run Full Test Suite** | `make test && make lint` |
| **Start Cluster** | `make docker-up` |
| **Stop Cluster** | `make docker-down` |
