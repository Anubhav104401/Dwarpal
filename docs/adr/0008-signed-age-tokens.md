# ADR-0008: EdDSA-signed minimal age tokens, JWKS, HMAC-signed webhooks

- **Status:** Accepted — 2026-10-15

## Context
The RP must be able to trust the outcome without trusting the user's browser, and should learn as little as possible about the user.

## Decision
- Results are delivered as **JWS tokens signed with Ed25519 (EdDSA)**, `typ: dwarpal-age+jwt`.
- Minimal claims: `iss`, `aud` = RP project, `iat`, `nbf`, `exp` (default 10 min), `jti`, `sid`, optional RP `nonce`, `outcome`, `age_over`, `assurance`, `methods`, `policy`, `model`. **Never** the estimated age, images or any stable user identifier.
- Public keys are published at `/.well-known/jwks.json`. Keys rotate every 30 days, with a 7-day overlap. Private keys are encrypted at rest under a master key.
- A server-side `/v1/tokens/introspect` endpoint serves RPs that prefer not to handle JWKS; it marks the token's `jti` as used.
- Browser redirects carry **only the session id**.
- Webhooks are signed with **HMAC-SHA256** over `timestamp.body`, with a replay window.

## Consequences
- **Good:** offline verification at the RP; tamper evidence; minimal disclosure; standard tooling (any JOSE library verifies EdDSA).
- **Cost:** key-management code (generation, encryption, rotation, JWKS caching).

## Alternatives considered
Unsigned redirects or webhooks (forgeable), RS256 (larger keys and signatures, no benefit here), mutual TLS for RPs (heavy for integrators), SD-JWT VC reusable credentials and zero-knowledge proofs (valuable later — "Age Pass" in v2 — but not needed for the per-session flow).
