# Security Policy — f9l3_53nd

## 1. Scope and Educational Purpose

`f9l3_53nd` is developed as an educational, secure file transfer platform. It demonstrates modern cryptographic engineering, network isolation via VPN, defense-in-depth authorization, and tamper-evident audit logging.

---

## 2. Security Assumptions & Trust Boundaries

The security guarantees of `f9l3_53nd` depend on the following explicit assumptions:

1. **Endpoint Integrity**: The host executing the browser and the host executing the backend server are not actively compromised by ring-0 / rootkit malware.
2. **KMS / Master Key Isolation**: The Key Encryption Key (KEK) is securely provisioned in production via environment injection, secret manager, or HSM.
3. **Database Separation**: Database credentials and administrative rights are separated from untrusted public networks.
4. **Operating System Entropy**: The underlying OS provides high-entropy random generation (`/dev/urandom` / `os.urandom`).

---

## 3. Explicit Non-Guarantees & Out-of-Scope Threats

The system explicitly does **NOT** claim protection against:
- Compromised user endpoints where malware reads browser DOM or captures keystrokes directly.
- Rogue administrators with direct database root access rewriting entire tables and filesystem storage simultaneously.
- Physical hardware extraction attacks against unencrypted RAM on hosting servers.
- Denial of Service (DoS) attacks exceeding physical network bandwidth limits.

---

## 4. Reporting Vulnerabilities

If you discover a security vulnerability within this repository:
1. Do **NOT** open a public issue on GitHub.
2. Draft a detailed advisory including:
   - Vulnerability classification (e.g., CWE identifier).
   - Step-by-step reproduction steps / proof of concept.
   - Affected components and impact analysis.
   - Suggested remediation.
3. Submit the report securely to the repository security maintainers.

---

## 5. Development Secret Hygiene Policy

- **No Production Secrets in Git**: Any key, token, or password committed to version control is deemed immediately compromised and must be revoked.
- **Automated Dev Secret Generation**: Local development must use dynamically generated secrets via `scripts/generate-dev-secrets.sh`.
- **Pre-commit Secret Scanning**: CI and local hooks prevent committing `.env` or cryptographic key material.
