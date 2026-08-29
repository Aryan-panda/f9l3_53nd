# Key Compromise & Emergency Recovery Runbook

## 1. Incident Triggers & Severity Definition
Activate this runbook immediately under any of the following conditions:
- **Severity 1 (Critical)**: Suspected or confirmed compromise of Key Encryption Key (KEK) / `MASTER_KEY_HEX`.
- **Severity 1 (Critical)**: WireGuard private key exfiltration or unauthenticated branch traffic injection.
- **Severity 2 (High)**: Session signing key (`SECRET_KEY`) compromise or mass credential leakage.

---

## 2. Phase 1: Immediate Containment (< 5 Minutes)

1. **Sever Ingress Traffic & Block API Endpoints**:
   ```bash
   docker compose stop backend-branch-a backend-branch-b
   ```
2. **Tear Down WireGuard Network Tunnels**:
   ```bash
   sudo wg-quick down infra/wireguard/branch-a/wg0.conf
   sudo wg-quick down infra/wireguard/branch-b/wg0.conf
   ```
3. **Revoke All Active User & Admin Sessions**:
   ```sql
   -- Direct database session invalidation
   UPDATE sessions SET revoked_at = NOW() WHERE revoked_at IS NULL;
   ```

---

## 3. Phase 2: Cryptographic Master Key (KEK) Rotation

When the primary KEK is compromised, transition to a newly generated KEK using dual-key migration.

1. **Generate New 256-bit Master Key**:
   ```bash
   NEW_KEK_HEX=$(python3 -c "import os; print(os.urandom(32).hex())")
   echo "New Master Key Generated."
   ```

2. **Configure Dual-Key Transition State in `KeyManager`**:
   Deploy the new key as primary while retaining the old key as secondary decrypt-only:
   ```bash
   export MASTER_KEY_HEX="${NEW_KEK_HEX}"
   export PREVIOUS_MASTER_KEY_HEX="${COMPROMISED_KEK_HEX}"
   ```

3. **Re-wrap All Historical Data Encryption Keys (DEKs)**:
   Execute automated batch re-wrapping:
   ```bash
   cd backend && .venv/bin/python -m app.cli.main rotate-keys --re-wrap-all
   ```

4. **Retire Compromised Key**:
   Remove `PREVIOUS_MASTER_KEY_HEX` once all stored DEKs are wrapped with the new KEK.

---

## 4. Phase 3: WireGuard Network Re-Keying

1. Generate fresh Curve25519 keypairs for Branch A, Branch B, and a new 256-bit pre-shared key (PSK):
   ```bash
   bash scripts/generate-wg-keys.sh
   ```
2. Distribute updated public keys and PSK out-of-band to branch administrators.
3. Bring up secure tunnels with new credentials:
   ```bash
   sudo wg-quick up infra/wireguard/branch-a/wg0.conf
   sudo wg-quick up infra/wireguard/branch-b/wg0.conf
   ```

---

## 5. Phase 4: Forensic Audit & Integrity Verification

1. Inspect audit logs for unauthorized access during the compromise window:
   ```sql
   SELECT * FROM audit_events 
   WHERE event_type IN ('TRANSFER_DECRYPT_SUCCESS', 'KEY_ROTATION_APPLIED') 
   ORDER BY timestamp DESC LIMIT 50;
   ```
2. Verify cryptographic integrity of all audit records:
   ```bash
   scripts/f9l3ctl.sh login -u admin -p "<AdminPass>"
   scripts/f9l3ctl.sh verify-audit --json
   ```
3. Generate incident report and transition system back to operational status.
