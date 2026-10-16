# ADR-0019: Sign age tokens with the fully-specified JOSE algorithm `Ed25519` (RFC 9864)

- **Status:** Accepted — 2026-10-16
- **Refines:** [ADR-0008](0008-signed-age-tokens.md) (only the `alg` identifier; everything else stands)

## Context
ADR-0008 chose Ed25519 signatures written as JWS with `alg: "EdDSA"`. While implementing token signing in Phase 1, the JOSE library (joserfc 1.7.5) refused `EdDSA` by default and warned:

> EdDSA is deprecated via RFC 9864

RFC 9864 (*Fully-Specified Algorithms for JOSE and COSE*) deprecates "polymorphic" algorithm identifiers like `EdDSA`. The problem with `EdDSA` is that it names a *family*: the actual curve (Ed25519 or Ed448) is only found inside the key. The RFC registers fully-specified names — `Ed25519` and `Ed448` — so the algorithm in a token's header alone says exactly what verification needs. That closes a class of algorithm-confusion mistakes.

## Decision
- Age tokens are signed with Ed25519 keys and carry `alg: "Ed25519"` in the JWS header.
- Verifiers — our SDKs, and the documentation for relying parties — must accept **only** `Ed25519` for our tokens, never a list of algorithms supplied by the token itself.
- The keys and the JWKS format are unchanged: OKP keys, curve `Ed25519`.

## Consequences
- **Good:** standards-current from day one, with no deprecated identifier baked into tokens that relying parties will verify for years. Explicit algorithm allow-lists in our verification code.
- **Cost:** some older JOSE libraries only know `EdDSA`. Relying parties on such libraries can upgrade, or use the server-side introspection endpoint (ADR-0008), which needs no JOSE library at all.

## Alternatives considered
- Keep `EdDSA` and silence the warning: rejected, because it would bake a deprecated identifier into a public contract.
- Switch to ES256 (ECDSA P-256): widely supported, but has larger signatures and needs a good random number for every signature — a historical source of catastrophic key leaks. Ed25519 doesn't, and remains the better primitive.
