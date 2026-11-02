# Phase 9 report — beyond the plan

**Dates:** from 1 Nov 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Design:** [06_age_pass.md](../design/06_age_pass.md) (the Age Pass) · **Status:** 🟡 three of the four stretch items are built and tested — the Python SDK, passkeys for the console, and the Age Pass; the render detector's data is being made (D22: the tools and paperwork are done, filming waits for D23); a Kubernetes deployment stays optional.

**Goal (from the roadmap):** the stretch items, once Phases 0–8 stand: a reusable, unlinkable Age Pass; passkeys for console sign-in; a detector for computer-rendered faces (liveness level 6); a Python SDK; optionally, a Kubernetes deployment from the Helm chart.

## What is built

| Item | Delivered | Book |
| :-- | :-- | :-- |
| Python SDK (`9ca1bfd`) | `packages/sdk-python`: `Client` and `AsyncClient` (create and read sessions), `verify_age_token` (signature, issuer, audience, expiry, session, age), `verify_webhook` (HMAC, constant-time, five-minute window); only `httpx` and `joserfc`, which the services already use. Not published (the owner's call) | §5.9.1 |
| Passkeys (`f902933`) | WebAuthn checks as pure functions (`domain/webauthn.py`: a small CBOR reader, Ed25519 and P-256 keys, origin, site, user verification, signature counter); migration 0010; add, list and remove with the password (and a code if on); sign-in with a take-once challenge and no one-time code (D20, confirmed 2 Nov) | §5.9.2 |
| Age Pass (2 Nov, D21) | SD-JWT VC passes kept in the browser: 20 per passed check, each bound to its own non-extractable WebCrypto key, each used once, stating only age lines behind salted hashes (6 digests per pass, decoys included); migration 0011 (`policies.accept_age_pass`, off for every preset; `verification_sessions.age_pass_issued_at`, the time only); `POST /v1/flow/sessions/{id}/age-pass`, `…/age-pass/nonce`, `…/age-pass/present`; `/.well-known/jwt-vc-issuer`; the verify page's offer to save and to use a pass; the console's switch and list column. Websites need no change: they get the usual age token with `methods: ["age_pass"]` | §5.9.3 |

## What was measured

| Check | Result |
| :-- | :-- |
| Age Pass rules | 12 tests with a software holder and real signatures: one line shown and nothing else; no linkable claim shared between passes of one batch; same digest count whatever the lines; tampering (foreign or dropped disclosures, another key, nonce, audience, time or type) refused with its own code; wrong issuer, type, mode, expiry; keys off the curve or with a private part; any text either parses exactly or is refused with the module's own error (Hypothesis) |
| Age Pass through the API | 2 tests against real PostgreSQL and Valkey: issue once per session; a pass completes a new session (token `methods: ["age_pass"]`); a used pass refused, the next one accepted; a pass-decided session can't renew; presets refuse; too-low line, wrong audience, reused nonce, late issue and a key with a private part refused |
| Contract (Schemathesis) | Found two real faults while building: `accept_age_pass` accepted `0` (now strictly `true`/`false`), and an over-long presentation could hit the 64 KB body limit before its own check (limit now 4096 characters) |
| Browser | 5 unit tests with real WebCrypto keys (non-extractable private key; the presentation's signature verifies); an end-to-end test in Chromium: a camera check, saving 20 passes, the next check answered with one, axe clean |
| Passkeys | 11 unit tests (two CBOR faults found by fuzzing, fixed), 2 API tests, 1 Chromium test with the virtual authenticator |
| CI on GitHub | every job green since `03f3f5b` (2 Nov), including Firefox and Lighthouse for the first time, and the Helm chart's lint and render since `1afb436` |

## Open items

1. **The render detector** (liveness level 6) needs examples of computer-rendered faces — attacks made with game engines and face-swap tools — under a licence that allows training. The owner asked for a search (2 Nov): [render-detector-datasets.md](render-detector-datasets.md) lists what exists — none both allows use in a service and shows renders filmed by a camera — and four options (D22). **The owner chose (3 Nov) to make our own and ask** ([ADR-0021](../adr/0021-render-detector-data.md)): the protocol, consent form, requests and the data tool are done (§5.9.4); filming waits for the downloads (D23), the consent form's review and the requests' answers.
2. **Kubernetes** stays optional: the chart is checked on every push but has never run on a cluster; the Always Free server (O2b) is one machine, where Compose fits better.
3. **The Age Pass**: no fresh batch from a pass (after 20 uses, a new face check gives a new batch); used passes are remembered in Valkey, so losing that memory would let a holder reuse their own pass; passes are offered and saved only on the verify page's own tab (browsers partition storage inside other websites' frames); the Hindi words need a native speaker's review.
4. **The SDKs stay unpublished until launch** (decided 2 Nov); [Integrating Dwarpal](../developers/README.md) shows how to install them from the repository meanwhile.
