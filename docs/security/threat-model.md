# Threat model

**Status:** reviewed 26 Oct 2026, covering Phases 0–4 and the start of 5–7 · **Method:** STRIDE per component, then the attacks specific to age assurance · **Owner:** the project owner · Every mitigation names the code or test that proves it; a mitigation without proof is listed as a gap.

## 1. What is protected

| Asset | Why it matters | Where it lives |
| :-- | :-- | :-- |
| The **age decision** | a wrong *pass* admits a child — the harm the system exists to prevent | decided in `domain/decision.py`; recorded in `verification_sessions` |
| **Faces** | biometric data; must never be stored | memory only, inside one request (ADR-0013) |
| **Signing keys** | whoever holds them can forge age tokens | `signing_keys`, sealed under the master key |
| **Master key** | unseals signing keys, webhook secrets, TOTP secrets, idempotent replies; keys recovery-code HMACs | environment variable only |
| **API keys, webhook secrets, session cookies** | impersonating a customer or a console user | stored as digests or sealed; shown once |
| **Tenant data** | one customer must never see another's | PostgreSQL with row-level security |
| **Audit history** | accountability; must not be silently rewritten | hash-chained `audit_log` |

## 2. Trust boundaries

```
person's browser ──(internet)──► verify page (Next.js) ──► flow API ─┐
website's server ──(internet)──► website API (API key) ──────────────┼─► API ──► PostgreSQL (RLS, dwarpal_app role)
console user ─────(internet)──► console pages ─/console-api─► console API (cookie + CSRF) ─┘    │        Valkey
                                                                                                └──► inference service (internal network only)
delivery worker (owner role) ──(internet)──► websites' webhook receivers
```

The browser and everything on the internet is untrusted. The inference service is reached only from the API. The worker and the operator tools hold the database owner's rights, and so sit inside the innermost boundary.

## 3. STRIDE by component

### 3.1 Verify page and flow API

| Threat | Mitigation | Proof |
| :-- | :-- | :-- |
| **S**poofing a live person with a photo, a screen replay, a mask | server-chosen pose challenge; passive anti-spoofing (MiniFASNet) deciding; injection signs | red-team rounds (Phase 3 report); `test_red_team_*` |
| Spoofing the challenge (the page claims what it was asked) | the server's own copy of the challenge replaces the page's | `test_red_team_a_challenge_claimed_by_the_browser_is_ignored` |
| **T**ampering with frames or timings | frames analysed by the server; client signals can only make the check stricter | ADR-0004; `test_red_team_automation_and_virtual_cameras_go_to_step_up` |
| Replaying a challenge or a flow token | one-use challenges; flow tokens hashed in Valkey, short-lived | `test_a_challenge_can_be_used_only_once` |
| **R**epudiation | each attempt's scores and reasons stored (numbers only) | `verification_attempts` |
| **I**nformation disclosure: faces kept | no column can hold an image; frames never logged | ADR-0013; `test_each_request_is_logged_once_with_its_id_and_never_with_secrets` |
| Disclosure: telling an attacker which check fired | outward reasons are vague (`liveness_uncertain`) | `domain/decision.py` |
| **D**enial of service / trial and error | per-session, per-device and per-address challenge budgets; body-size limits | `test_one_device_gets_only_so_many_challenges_*`; `test_oversized_and_unmeasured_bodies_*` |
| **E**levation: reaching another session | flow token bound to one session; RLS by the session's project | `flow_session`; `session_tenant` |
| Clickjacking: framing the verify page (D16, 30 Oct) | `frame-ancestors` names only the origin of the session's return address (an allowed origin the website registered with its key); `'none'` for every other page and on any doubt; the origin is pattern-checked before it enters the header | `test_only_the_website_a_session_returns_to_may_frame_its_verify_page`; `proxy.test.ts`; e2e *no other website may frame a verify page* |
| Spoofed or leaked `postMessage` between the verify page and the website | the page sends only to the return origin; the SDK accepts only from its own frame at the verify origin, for its session, and moves only to its own origin; messages carry no result — the website's server fetches it with its key | `protocol.test.ts`; `open.ts` |

### 3.2 Website API (API keys)

| Threat | Mitigation | Proof |
| :-- | :-- | :-- |
| Stolen or guessed key | 32 random bytes; only a SHA-256 digest stored; constant-time compare; scopes; rotation with grace; instant revocation | `test_credentials_are_checked_*`; `test_a_key_can_do_only_what_its_scopes_allow`; `test_a_rotated_key_*` |
| One customer reading another's sessions | row-level security on every tenant table; the code's own filters as a second lock | `test_each_tenant_sees_only_its_own_rows_*`; `test_one_websites_key_cannot_read_another_websites_session` |
| Forged age tokens | Ed25519 signatures, keys sealed; tokens name their audience and session | `test_an_adult_passes_and_the_website_can_verify_the_signed_token` |
| Token replay | short lifetime; one-use introspection | `test_a_token_can_be_introspected_once_*` |
| Duplicate creation on retries | `Idempotency-Key`, replies sealed in Valkey | `test_a_repeated_request_with_the_same_idempotency_key_*` |
| Flooding | token bucket per key | `test_each_api_key_may_make_only_so_many_requests_at_once` |
| Rules changed under a running check | policy versions immutable; sessions pin their version | `test_policy_versions_can_be_added_but_never_changed_or_deleted` |

### 3.3 Console

| Threat | Mitigation | Proof |
| :-- | :-- | :-- |
| Password guessing | Argon2id; per-account and per-address limits; TOTP (switching it off needs password + code, under the same limits) | `test_sign_in_attempts_are_limited`; `test_one_time_codes_*`; `test_a_recovery_code_signs_in_once_*` |
| Account enumeration | same answer and same work for unknown accounts (decoy hash) | `test_a_person_signs_up_*` |
| Session theft | `__Host-` `HttpOnly` `Secure` `SameSite=Lax` cookie; token stored hashed; 12-hour sliding expiry | `http/console.py` |
| CSRF | synchroniser token plus `Origin` check | `test_changes_need_the_csrf_token_and_the_consoles_own_origin` |
| Elevation between roles | role matrix checked before every action; non-members see 404 | `test_roles_decide_what_each_member_may_do_*`; `test_console_rules.py` |
| Elevation via the page | the page only hides; the API decides | `lib/console-api.ts` (`CAN`) |

### 3.4 Webhooks and the delivery worker

| Threat | Mitigation | Proof |
| :-- | :-- | :-- |
| SSRF into Dwarpal's network | every resolved address must be public; checked at registration and before each delivery; no redirects | `test_webhooks.py`; `test_webhook_endpoints_must_be_public_*` |
| Forged webhooks reaching websites | HMAC-SHA256 over time and body; receivers check freshness | `verifyWebhook`; `webhook.test.ts` |
| A lost or invented outcome notification | transactional outbox | `test_a_completed_session_is_announced_*` |
| Double sending by several workers | `SKIP LOCKED` claims with a lease | `app/delivery.py` |

### 3.5 Data stores and secrets

| Threat | Mitigation | Proof |
| :-- | :-- | :-- |
| A bug forgetting a tenant filter | RLS binds the API's role; a test fails if any table lacks RLS | `test_every_table_but_dwarpals_own_has_row_level_security` |
| The API role rewriting history | `events`, `policies`, `audit_log` are read-and-add only | `test_policy_versions_*`; `test_changes_are_chained_in_the_audit_log_*` |
| Silent edits by someone with the owner's rights | hash chain with head; verifier names the first broken entry | `test_changes_are_chained_in_the_audit_log_and_any_tampering_is_found` |
| Copy of Valkey's memory | flow tokens and console tokens stored hashed; idempotent replies sealed | `test_a_repeated_request_*` (looks inside Valkey) |
| Dependency outage turned into an open door | fail closed: `503` or `retry`, never `pass` | `test_when_valkey_is_unreachable_*`; `test_when_inference_fails_*` |

## 4. Attacks specific to age assurance

| Attack | Status |
| :-- | :-- |
| An adult does the check for a child | **not preventable** by any remote method; the design limits reuse (tokens bound to one session and website, short-lived) |
| A child presents an adult's photo or video | blocked in the owner's red team (Phase 3): 0 of 3 posed-selfie and 0 of 4 video attacks passed with anti-spoofing |
| Virtual camera feeding pre-recorded or synthetic video | **untested** (Phase 3 open item); injection signs only catch naive cases. A render detector (liveness level 6, ADR-0021) is built and records its chance once trained, but waits for data and decides nothing |
| Real-time deepfake | **untested**; no licensed data to train on (render-detector-datasets.md) |
| Masks | **untested** |
| Retrying until the estimate drifts over the line | session attempt limits; device and address budgets; each retry raises the bar |
| Borrowed document (step-up) | face match document ↔ selfie (Phase 6, waiting for a model) |
| Forged MRZ | check digits catch mistakes, not forgeries; MRZ alone is **basic** assurance |

## 5. Gaps and residual risks (ordered by severity)

1. ~~Next.js 16.4.0's two critical remote-code-execution flaws and one high denial-of-service flaw~~ (GHSA-2464-fhr4-w9xw, GHSA-673q-mjm6-r5xr, GHSA-p3m5-59mp-jv5r) — **fixed 27 Oct**: both apps upgraded to 16.4.2 (decision D12); `pnpm audit` reports no known vulnerabilities.
2. **The API logs in as the database owner and switches role** — a fully attacker-controlled statement could `RESET ROLE`. Production must use a login that is only a member of `dwarpal_app` (Phase 8).
3. **Untested presentation attacks** — virtual camera, deepfake, mask; one-person measurement (Phase 3 open items). The render detector's code is ready (3 Nov); its data is being made under ADR-0021.
4. **No dependency or container scanning yet** — Semgrep, pip-audit, Trivy, ZAP pending (D9).
5. **DNS rebinding window** between the webhook address check and the connection — worker egress filtering in Phase 8.
6. **Audit chain not anchored outside the database** — a consistent rewrite by someone controlling the database would go unnoticed.
7. ~~No recovery codes for TOTP~~ — **added 29 Oct** (single-use, stored as HMACs). Still no e-mail verification of accounts, and no password reset.
8. **Console sessions aren't bound to a device** — a stolen cookie works until it expires or the person signs out.

## 6. Review triggers

Review this model when: a new external interface is added; a new kind of data is stored; a dependency handling secrets or images changes; a phase report lists a new security finding; or every three months.
