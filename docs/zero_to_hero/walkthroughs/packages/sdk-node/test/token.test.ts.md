---
fingerprint: bf7f6c7b7b851367
---
The tests for `verifyAgeToken`. They don't need the real API: they make their **own** Ed25519 key pair, sign tokens with it exactly as the API would, and check what the SDK decides. That way each test can make precisely the token it wants — including tokens the real API would never produce, such as forgeries.

Tests run with **Vitest** (§4.20), whose building blocks read almost like English: `describe` groups tests, `it("does something", …)` is one test, and `expect(value).toBe(expected)` is one check.

@@ 1-9
From jose, the tools for *making* tokens:

- `generateKeyPair` and `exportJWK` — a fresh key pair, and its public half as a JWK;
- `createLocalJWKSet` — a key set held in memory, instead of fetched from an address;
- `SignJWT` — builds and signs a token;
- `UnsecuredJWT` — builds a token with **no signature at all**, for the attack test below;
- `CryptoKey` and `JWTPayload` — types.

@@ 10
From Vitest: `beforeAll` (run once before the tests), `describe`, `expect` and `it`.

@@ 12
The code under test, imported from the SDK's front door — exactly as a website would.

@@ 14-16
A made-up issuer, audience and session, shaped like real ones.

@@ 18-19
Two variables, filled in by `beforeAll`: the private key for signing, and the options for verifying. `let` (rather than `const`) allows a variable to be assigned later.

@@ 21-23
Before any test: make a new Ed25519 key pair, and keep its private half.

@@ 24
Export the public half as a JWK, and add the three labels the API's keys carry: `kid`, `alg` and `use`. The `...` (**spread**) copies all of the JWK's own properties into the new object first.

@@ 25-31
The verification options every test starts from: the issuer, the audience, an 18+ requirement, the expected session, and a key set containing just the test key.

@@ 32
The end of `beforeAll`.

@@ 34-37
**`claims`** — the claims of a perfect "pass" token, with any changes a test asks for. Because `...changes` comes last, a test's values replace the defaults: `claims({ outcome: "fail" })` changes only the outcome.

@@ 39-43
**`sign`** — make a signed token from claims. Two optional parameters with defaults: the token type (normally the right one) and the expiry (normally 10 minutes from now; `"10m"` is jose's short way of saying so).

@@ 44-48
jose builds tokens step by step, each step returning the builder again — a style called **method chaining**: set the header (algorithm, type, key ID), stamp the issue time, set the expiry, and sign with the private key.

@@ 49
The end of `sign`.

@@ 51
All the tests below are about `verifyAgeToken`.

@@ 52-60
**A passed check, at exactly the required age, allows entry** — and every field of the verdict carries the token's facts, with an expiry in the future.

@@ 62-67
**A failed check never allows entry, whatever the age claim says.** The first token is an honest "fail". The second is contradictory: `outcome: fail`, but still `age_over_18: true` (inherited from the defaults). The real API never makes such a token, but the SDK must not be fooled by one: both must give `allowed: false`.

@@ 69-73
**A check for a lower age can't satisfy a higher requirement.** The token says `age_over_13: true` — and `delete` removes its `age_over_18` claim. A website requiring 18 must not let this visitor in (ADR-0020).

@@ 75-84
**Tokens for someone else, of another type, or about another session are refused.** One valid token is checked as if by a website with a different project ID; another token is signed with the generic type `JWT`; and the valid token is checked against a different expected session. `rejects.toThrow(…)` says: "this promise must fail with this kind of error" — or with a message matching `/different session/`.

@@ 86-89
**Expired tokens are refused**: this one expired 60 seconds ago. `Math.floor(Date.now() / 1000)` is the current time in whole seconds, as JWTs count it.

@@ 91-96
**Only Ed25519.** The first forgery is signed with `HS256` — a *shared-secret* algorithm. A careless verifier that let the token choose its algorithm could be tricked into checking it with a secret the attacker knows. `TextEncoder` turns text into bytes for the secret.

@@ 97
The second forgery has **no signature at all**: the historic `"alg": "none"` attack (§4.12).

@@ 98-100
Both must be refused.

@@ 102-106
**`minAge` must be a whole number**: 17.5 is a mistake in the website's code, reported as a `RangeError` rather than silently never matching.

@@ 107
The end of the group.
