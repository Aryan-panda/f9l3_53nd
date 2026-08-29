# Threat Model — Threat Actors & Adversary Personas

**Document Version**: 1.0.0  
**Project**: `f9l3_53nd` — Secure Authenticated File Transfer Platform  

---

## 1. Adversary Profiles & Capabilities

We profile threat actors based on their access level, capabilities, motivations, and attack positioning.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ EXTERNAL ADVERSARIES                                                   │
│  [ADV-01: Network Eavesdropper / MitM]                                  │
│  [ADV-02: Internet Script Kiddie / Automated Botnet]                   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ AUTHENTICATED INTERNAL ADVERSARIES                                     │
│  [ADV-03: Malicious Authenticated User (Unauthorized Data Access)]     │
│  [ADV-04: Compromised User Endpoint]                                   │
│  [ADV-05: Malicious Database / Storage Insider]                        │
│  [ADV-06: Rogue Server Administrator (Out of Scope)]                   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Threat Actor Analysis

### ADV-01: External Network Eavesdropper / Active MitM
- **Location**: On the untrusted public network between Branch A and Branch B, or adjacent to the local LAN.
- **Capabilities**:
  - Passive packet capture and traffic analysis.
  - Active packet interception, injection, modification, and replaying.
  - DNS spoofing and ARP cache poisoning.
- **Motivations**: Steal plaintext business files, inject corrupted payloads, or map network communication patterns.
- **Assumed Constraints**: Cannot break modern cryptographic primitives (AES-256, SHA-256, Curve25519) in feasible computational time.

### ADV-02: Internet-Scale Automated Scanner / Botnet
- **Location**: Untrusted public internet.
- **Capabilities**:
  - High-frequency brute-force credential attacks and dictionary password spraying.
  - Automated vulnerability scanning (SQL injection, path traversal, CVE probes).
  - Volumetric Layer 7 HTTP request flooding.
- **Motivations**: Opportunistic exploitation, unauthorized access, denial of service.

### ADV-03: Malicious Authenticated User (`USER` Role)
- **Location**: Legitimate internal employee or contractor holding valid credentials.
- **Capabilities**:
  - Manipulating HTTP requests, URL query parameters, headers, and request bodies.
  - Attempting Insecure Direct Object References (IDOR/BOLA) by modifying `transfer_id` values to view or download files of other users.
  - Attempting horizontal privilege escalation (accessing other users' files) and vertical privilege escalation (calling `/api/v1/admin/*` endpoints).
  - Submitting maliciously crafted files (e.g., polyglot files, zip bombs, directory traversal names like `../../etc/shadow`).
- **Motivations**: Corporate espionage, data exfiltration, bypassing corporate data silos.

### ADV-04: Compromised Client Endpoint
- **Location**: An authenticated user's workstation infected with unprivileged user-space malware or hostile browser extensions.
- **Capabilities**:
  - Inspecting local DOM and frontend variables.
  - Attempting to extract cookies, cached tokens, or keys.
- **System Defense**: Cryptographic master keys are strictly kept server-side; session cookies are flagged `HttpOnly` so JavaScript extensions cannot read them.

### ADV-05: Malicious Storage / Read-Only Database Insider
- **Location**: System administrator or database reader with read access to PostgreSQL backups or disk volumes, but without application server runtime memory access.
- **Capabilities**:
  - Reading database tables (`transfers`, `users`, `audit_events`).
  - Reading files on disk in `storage/encrypted/`.
- **System Defense**: Files on disk are AES-256-GCM ciphertexts; DEKs in the database are wrapped with KEK; passwords in the database are Argon2id hashes.
