# Threat Model — Threat Mitigations & STRIDE Mapping

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. STRIDE Threat & Mitigation Matrix

Every threat identified under the STRIDE methodology is mapped to an authoritative architectural control and verification test suite.

| STRIDE Category | Threat ID | Threat Scenario | Implemented Security Control | Verification Test Suite |
| :--- | :--- | :--- | :--- | :--- |
| **Spoofing** | **THR-S01** | Attacker impersonates valid user to initiate transfer | Argon2id password hashing + HTTP-only session cookies with server-side session registry | `tests/unit/security/test_auth.py` |
| **Spoofing** | **THR-S02** | Attacker spoofs sender identity in transfer metadata | Metadata bound into AES-GCM Authenticated Associated Data (AAD); verified via GCM tag | `tests/adversarial/test_crypto_attacks.py` |
| **Tampering** | **THR-T01** | Attacker flips bits in encrypted file payload | AES-256-GCM 128-bit authentication tag verification fails immediately; payload quarantined | `tests/adversarial/test_tampering.py` |
| **Tampering** | **THR-T02** | Attacker modifies file contents and creates matching ciphertext | SHA-256 post-decryption digest check fails; transfer marked `FAILED` and quarantined | `tests/unit/crypto/test_hashing.py` |
| **Tampering** | **THR-T03** | Attacker modifies historical audit log records | Cryptographic SHA-256 previous-event digest chaining breaks if historical records are modified | `tests/unit/audit/test_audit.py` |
| **Repudiation** | **THR-R01** | Sender denies initiating a sensitive transfer | Structured audit log records actor ID, source IP, timestamp, and SHA-256 digest in DB | `tests/unit/audit/test_audit.py` |
| **Info Disclosure**| **THR-I01** | Network eavesdropper intercepts file payload in transit | Dual-layer encryption: WireGuard VPN tunnel + AES-256-GCM application envelope | `tests/integration/test_network.py` |
| **Info Disclosure**| **THR-I02** | User exploits IDOR/BOLA to download other users' files | Complete mediation: database query enforces `sender_id == user.id OR recipient_id == user.id` | `tests/security/test_idor.py` |
| **Info Disclosure**| **THR-I03** | Server returns internal tracebacks or secrets on error | Centralized exception handler maps errors to safe JSON structures without leaking stack traces | `tests/unit/test_foundation.py` |
| **Denial of Service**| **THR-D01** | Attacker floods login or upload endpoints | In-memory token-bucket rate limiter + strict file size ceiling (50 MB limit) | `tests/security/test_rate_limit.py` |
| **Denial of Service**| **THR-D02** | Attacker submits path traversal filename to overwrite disk | Storage engine isolates files to UUID paths in `storage/encrypted/<uuid>/` | `tests/security/test_traversal.py` |
| **Elevation of Priv**| **THR-E01** | Standard user calls administrative audit or user APIs | Role-based access control guard checks `user.role == 'ADMIN'` server-side | `tests/security/test_rbac.py` |

---

## 2. Deep-Dive Mitigation Architectures

### 2.1 Complete Mitigation against Insecure Direct Object Reference (IDOR/BOLA)
- **Vulnerability**: In typical insecure applications, `GET /api/v1/transfers/{transfer_id}/download` looks up the file by ID and returns it immediately. An attacker merely changes the UUID to another user's transfer.
- **`f9l3_53nd` Mitigation**:
  ```python
  # Application Service Layer Complete Mediation
  transfer = await transfer_repo.get_by_id(transfer_id)
  if not transfer:
      raise TransferNotFoundError(transfer_id)

  if current_user.role != UserRole.ADMIN:
      if transfer.sender_id != current_user.id and transfer.recipient_id != current_user.id:
          # Fail-closed: treat unauthorized existence indistinguishably from non-existence
          # or return explicit 403 Forbidden with security audit event
          await audit_service.log_access_denied(current_user.id, transfer_id)
          raise AuthorizationError("You are not authorized to access this transfer.")
  ```

### 2.2 Complete Mitigation against Path Traversal (CWE-22)
- **Vulnerability**: Attacker sets filename to `../../../../var/www/html/backdoor.php`.
- **`f9l3_53nd` Mitigation**:
  1. Filename sanitization via `os.path.basename` strips directory separators.
  2. Storage engine generates an internal `transfer_uuid = uuid4()`.
  3. Physical path is computed strictly as:
     $$\text{PhysicalPath} = \text{base\_dir} / \text{"encrypted"} / \text{str}(\text{transfer\_uuid}) / \text{"payload.enc"}$$
  4. Realpath canonicalization verifies:
     $$\text{os.path.realpath}(\text{PhysicalPath}).\text{startswith}(\text{os.path.realpath}(\text{base\_dir}))$$
