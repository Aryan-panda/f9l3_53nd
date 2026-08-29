# Audit Log Forensics & Investigation Guide

## 1. Overview & Forensic Architecture
`f9l3_53nd` implements a tamper-evident audit logging architecture based on cryptographic HMAC-SHA256 predecessor hashing. Every security-relevant event recorded in the database is inextricably bound to the cryptographic record that preceded it.

```text
Genesis (Prev: 000...0) -> Event 1 (Hash: H1) -> Event 2 (Hash: H2) -> Event N (Hash: HN)
```

---

## 2. Hash Calculation Formula
For each record $i$, the record hash $H_i$ is computed as:
$$H_i = \text{HMAC-SHA256}\Big(K_{\text{audit}},\, H_{i-1} \parallel \text{UUID}_i \parallel \text{Timestamp} \parallel \text{ActorID} \parallel \text{EventType} \parallel \text{Severity} \parallel \text{CanonicalJSON}(\text{Details})\Big)$$

Any unauthorized modification of:
- A timestamp
- An actor ID or username
- Event details or transfer hashes
- Preceding record hash
- Deletion of an intermediate record

...will immediately cause the cryptographic chain validation to fail.

---

## 3. Investigating Chain Integrity Failures

### 3.1 Step 1: Run Automated Cryptographic Verification
Using the CLI:
```bash
scripts/f9l3ctl.sh verify-audit --json
```

Or query the API directly:
```bash
curl -X POST http://localhost:8000/api/v1/admin/audit-events/verify \
  --cookie "f9l3_session=<AdminSessionToken>"
```

### 3.2 Step 2: Interpreting Verification Outputs

#### Case A: Chain Valid
```json
{
  "is_valid": true,
  "verified_count": 142,
  "broken_at_index": null,
  "error_message": null
}
```
**Conclusion**: All 142 audit records in sequence match their cryptographic proofs.

#### Case B: Chain Broken / Tampering Detected
```json
{
  "is_valid": false,
  "verified_count": 45,
  "broken_at_index": 46,
  "error_message": "Chain broken at index 46: Expected prev_hash 'd4f2...', got '9a1c...'."
}
```
**Action**:
1. Query record 45 and 46 in the database:
   ```sql
   SELECT id, event_type, actor_id, previous_hash, record_hash, timestamp, details
   FROM audit_events
   ORDER BY timestamp ASC
   LIMIT 2 OFFSET 45;
   ```
2. Compare the database state against offsite immutable replica logs to pinpoint the altered columns or missing rows.
3. Isolate the affected database server and preserve WAL logs for digital forensics.

---

## 4. Evidence Export & Preservation

Export tamper-evident audit logs with digital signatures for external auditor review:
```bash
# Export chronological audit log with hashes
docker exec f9l3_postgres psql -U f9l3_user -d f9l3_db -c \
  "COPY (SELECT id, timestamp, event_type, severity, actor_id, previous_hash, record_hash, details FROM audit_events ORDER BY timestamp ASC) TO STDOUT WITH CSV HEADER" > /tmp/audit_export_$(date +%s).csv

# Compute cryptographic digest of the export file
sha256sum /tmp/audit_export_*.csv > /tmp/audit_export.sha256
```
