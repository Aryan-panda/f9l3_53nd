# Threat Model — Protected Assets Analysis

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. Asset Classification & Valuation Matrix

Assets in `f9l3_53nd` are classified according to the CIA triad (Confidentiality, Integrity, Availability) and the potential impact if compromised.

| Asset ID | Asset Description | CIA Impact Rating | Storage Location | State in Transit | Primary Threat Vector |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **AST-01** | **Plaintext File Payloads** | **C: High, I: High, A: Med** | Memory during processing; destination upon auth check | Never transmitted in cleartext | Memory dumping, unauthorized download, path traversal |
| **AST-02** | **Encrypted File Payloads (Ciphertexts)** | **C: Med, I: High, A: Med** | `storage/encrypted/<uuid>/payload.enc` | WireGuard UDP packets | Bit-flipping tampering, truncation, deletion |
| **AST-03** | **Master Key (KEK)** | **C: Critical, I: Critical, A: High** | Environment variable (`MASTER_KEY_HEX`), KMS | Never transmitted | Environment leakage, process introspection, git commit |
| **AST-04** | **Data Encryption Keys (DEKs)** | **C: Critical, I: Critical, A: Med** | Ephemeral in RAM; wrapped in PostgreSQL DB | Never transmitted unwrapped | Key recovery, weak entropy, memory retention |
| **AST-05** | **User Passwords & Credentials** | **C: Critical, I: High, A: Low** | Argon2id hashes in PostgreSQL DB | HTTPS POST request body | Brute force, credential stuffing, rainbow tables |
| **AST-06** | **Active User Session Tokens** | **C: High, I: High, A: Low** | PostgreSQL `sessions` table | `HttpOnly` Cookie over HTTPS | Session hijacking, XSS extraction, fixation |
| **AST-07** | **Transfer Metadata & State** | **C: Low, I: High, A: Med** | PostgreSQL `transfers` table | AAD in transfer envelope | IDOR/BOLA tampering, state desynchronization |
| **AST-08** | **Audit Log Records** | **C: Low, I: High, A: High** | PostgreSQL `audit_events` table | Internal structured log pipeline | Retroactive log deletion, log forgery, repudiation |
| **AST-09** | **WireGuard VPN Private Keys** | **C: Critical, I: Critical, A: High** | Host `/etc/wireguard/` (chmod 600) | Never transmitted | Host compromise, unprivileged read access |

---

## 2. In-Depth Asset Profiles & Sensitivity Boundaries

### AST-01: Plaintext File Payloads
- **Description**: The original, sensitive business files (PDFs, documents, database dumps, archives) transferred between branches.
- **Exposure Window**: Ephemeral lifetime in RAM during encryption on sender and decryption on receiver. Stored in temporary memory buffers or streamed chunks.
- **Worst-Case Impact**: Total breach of sensitive enterprise data.

### AST-03: Master Key (KEK - Key Encryption Key)
- **Description**: The 256-bit AES symmetric key used to wrap and unwrap per-transfer Data Encryption Keys (DEKs).
- **Security Boundary**: Sourced securely at application startup. Must never be logged, persisted to disk, or exposed via any API endpoint.
- **Worst-Case Impact**: An adversary possessing the KEK and database access can decrypt all historical and future transfer DEKs.

### AST-04: Data Encryption Keys (DEKs)
- **Description**: 256-bit AES keys generated uniquely for every transfer operation (`os.urandom(32)`).
- **Lifecycle**: Generated → Used to encrypt payload with AES-256-GCM → Wrapped with KEK via RFC 3394 → Stored wrapped in DB → Zeroized from memory.
- **Blast Radius**: Compromise of a single DEK only compromises the specific file payload associated with that transfer.

### AST-07: Transfer Metadata & AAD Elements
- **Description**: Metadata attributes including `transfer_id`, `sender_id`, `recipient_id`, `file_size`, and `sha256_digest`.
- **Integrity Requirement**: Must be cryptographically bound to the ciphertext using AES-GCM Authenticated Associated Data (AAD) so that an attacker cannot reassign a valid ciphertext to a different recipient or transfer session.
