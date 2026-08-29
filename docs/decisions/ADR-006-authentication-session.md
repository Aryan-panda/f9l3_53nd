# ADR-006: Session-Based Authentication with HttpOnly Cookies

## Status
Accepted

## Context
Web authentication must authenticate users securely while preventing credential theft via Cross-Site Scripting (XSS), Cross-Site Request Forgery (CSRF), and session fixation.

## Decision
We select **Server-Side Session Identifiers via Secure Cookies**:
- Session tokens: 256-bit cryptographically secure random values (`secrets.token_urlsafe(32)`).
- Cookies flagged with `HttpOnly = True`, `SameSite = Lax`, and `Secure = True` (in HTTPS production).
- Session metadata stored in PostgreSQL `sessions` table tracking `user_id`, `created_at`, `expires_at`, and `revoked_at`.

## Alternatives Considered & Rejected
- **Stateless JWTs stored in localStorage**: Extremely vulnerable to XSS attacks (any injected script can read localStorage). Also makes instantaneous session revocation impossible without implementing complex token blocklists.
- **HTTP Basic Authentication**: Sends base64-encoded credentials on every request; cannot be revoked cleanly on the server side.

## Security Impact
- JavaScript code in the browser cannot read or exfiltrate the session token.
- `SameSite=Lax` prevents CSRF on cross-origin transfer creation.
- Instantaneous revocation upon logout or administrative account suspension.

## Consequences
- Requires a database query to validate active session state upon each authenticated API request (mitigated with database indexing on `session_token`).
