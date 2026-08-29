# ADR-009: WireGuard VPN for Branch-to-Branch Network Isolation

## Status
Accepted

## Context
Transfers between Branch A and Branch B traverse untrusted public networks. We require point-to-point network transport encryption, network isolation, and protection against Man-in-the-Middle (MitM) traffic tampering.

## Decision
We select **WireGuard VPN** running on UDP port 51820:
- Branch A: `10.50.0.1/24`
- Branch B: `10.50.0.2/24`
- Modern cryptographic primitives: Noise Protocol Framework, Curve25519 (key exchange), ChaCha20-Poly1305 (AEAD transport), BLAKE2s (hashing).

## Alternatives Considered & Rejected
- **OpenVPN / IPsec**: Extremely large codebases (> 100k lines), complex certificate and cipher negotiations, higher configuration error surface.
- **Pure HTTPS over Public Internet**: Exposes application HTTP ports directly to internet scanners and DDoS probes.

## Security Impact
- WireGuard operates silently: drops all unauthenticated UDP packets without replying, making the port invisible to unauthorized internet port scanners.
- Cryptographically binds peer IP addresses to public keys.

## Consequences
- Requires WireGuard interface setup and peer configuration in deployment environments.
