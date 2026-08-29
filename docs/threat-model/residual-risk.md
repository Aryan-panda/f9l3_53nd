# Threat Model — Residual Risk & Threat Boundaries

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. Residual Risk Summary Table

Residual risk represents the threat exposure remaining after all architectural, cryptographic, and procedural controls have been implemented.

| Threat Category | Pre-Control Risk | Applied Controls | Residual Risk Level | Reason for Residual Risk |
| :--- | :---: | :--- | :---: | :--- |
| **Network Eavesdropping** | High | WireGuard VPN + AES-256-GCM AEAD | **Negligible** | Dual-layer standard encryption with 256-bit keys. |
| **Ciphertext Tampering** | High | AES-GCM 128-bit Tag + SHA-256 Digest | **Negligible** | $2^{128}$ tag security; automatic fail-closed quarantine. |
| **IDOR / BOLA** | High | Server-side complete mediation & ownership queries | **Low** | Requires zero flaws in service authorization queries. |
| **Audit Log Tampering** | Med | SHA-256 digest chain | **Medium** | Protects against row manipulation by unprivileged users, but root DB admin could rewrite whole chain. |
| **Credential Brute Force** | High | Argon2id + Token Bucket Rate Limiting | **Low** | Slow password derivation ($64 \text{ MB}$, $3$ iterations) stops offline cracking. |
| **Server RAM Dump** | Critical | DEK zeroization + Ephemeral lifespan | **Medium** | KEK is present in application process memory during runtime. |
| **Client Endpoint Compromise** | Critical | HttpOnly cookies + DOM isolation | **High** | Out of application scope: OS-level keyloggers/screen recorders capture data before encryption. |

---

## 2. In-Depth Operational Limitations

### 2.1 The Compromised Host / RAM Introspection Boundary
- **Threat**: An adversary who achieves root / kernel access on the server hosting the FastAPI application can attach a debugger (`gdb`), inspect `/proc/<pid>/mem`, or dump RAM to extract the Key Encryption Key (KEK) and active session tokens.
- **Why Application Code Cannot Prevent This**: Software cannot protect secrets from the operating system kernel executing it.
- **Enterprise Remediation**: In enterprise production, use hardware security modules (HSM), cloud KMS with envelope encryption APIs (AWS KMS / GCP Cloud KMS / Azure Key Vault), and confidential computing enclaves (AMD SEV / Intel SGX).

### 2.2 Volumetric Denial of Service (DDoS)
- **Threat**: Volumetric UDP floods saturating the WireGuard endpoint interface bandwidth or HTTP floods overwhelming TCP sockets before application rate limiting executes.
- **Enterprise Remediation**: Upstream Anycast DDoS scrubbing (Cloudflare Magic Transit, AWS Shield), edge firewall rate limiting, and WireGuard `wg-quick` pre-shared key (PSK) authentication.

### 2.3 Client-Side Hostile Workstations
- **Threat**: Malicious software or keyloggers running on an authorized employee's workstation reading documents before they are uploaded to the browser.
- **Enterprise Remediation**: Endpoint Detection & Response (EDR), hardware security keys (FIDO2 / WebAuthn), and zero-trust mobile device management (MDM).
