# Stage 3 — Implementation Design

**Project:** Dwarpal · **Status:** Approved direction, detailed design · 15 Oct 2026
**Inputs:** [01_problem_analysis.md](01_problem_analysis.md), [02_solution_options.md](02_solution_options.md) and the owner's decisions in §23 of that document.
**Purpose:** turn the chosen solution into concrete, buildable specifications — modules, data, interfaces, algorithms, and how each is tested. Stage 4 ([04_architecture.md](04_architecture.md)) shows how the pieces fit and fail. Stage 5 ([05_roadmap.md](05_roadmap.md)) orders the work.

---

## 1. Repository layout (monorepo)

One repository holds every deployable, every library and the documentation. Changes that cross boundaries — say, a new field flowing from the inference service to the console — then land in **one reviewed commit**, and shared contracts can't drift.

```
.
├── apps/
│   ├── web/                    Next.js 16 — marketing site, docs pages, hosted verify flow (/v/…), console (/console)
│   └── demo-shop/              Next.js 16 — fictional age-restricted shop integrating @dwarpal/js + @dwarpal/node
├── packages/                   TypeScript libraries (pnpm workspace)
│   ├── ui/                     design system: tokens, shadcn-based components, motion presets
│   ├── capture/                camera + MediaPipe guidance + challenge runner (used by the verify flow)
│   ├── sdk-js/                 @dwarpal/js — browser SDK (modal / popup / redirect), postMessage protocol
│   ├── sdk-react/              @dwarpal/react — <VerifyAgeButton/>, useDwarpal()
│   ├── sdk-node/               @dwarpal/node — sessions API client, token verification (JWKS), webhook signatures
│   ├── api-types/              TypeScript types generated from the API's OpenAPI document
│   └── config/                 shared tsconfig / Biome / Tailwind presets
├── services/                   Python deployables (uv workspace members)
│   ├── api/                    FastAPI modular monolith — also runs the background worker (same image, other command)
│   └── inference/              FastAPI + ONNX Runtime — face pipeline, liveness signals, age distribution
├── libs/                       Python libraries shared by services and ML
│   ├── contracts/              dwarpal_contracts — Pydantic models crossing service boundaries
│   └── vision/                 dwarpal_vision — decode, detect, align, quality: the SAME code in training and serving
├── ml/                         dwarpal_ml — datasets, training, evaluation, calibration/risk control, export, model cards
├── models/registry/            model manifests (committed) — weights fetched by script, never committed
├── infra/
│   ├── compose/                compose.yaml (dev), compose.prod.yaml, observability profile
│   ├── caddy/                  Caddyfile
│   ├── helm/dwarpal/           Helm chart (artefact for Kubernetes deployments)
│   ├── observability/          Prometheus, Grafana dashboards, Loki, OTel Collector configs
│   └── scripts/                bootstrap, backup/restore, secret generation, model download
├── docs/  design/ adr/ zero_to_hero/ api/ runbooks/
├── .github/workflows/          CI (lint, types, tests, model gates, book --strict, build, scan) and CD
├── pyproject.toml              uv workspace root (Python 3.13)
├── package.json, pnpm-workspace.yaml, turbo.json   (Node 24 LTS, pnpm)
└── .editorconfig, .gitattributes, .gitignore, README.md
```

**Toolchains.** Python 3.13 managed by **uv** (independent of the system Python 3.14). Node 24 LTS with **pnpm**, pinned via Corepack (`packageManager` field). **Turborepo** orchestrates JS tasks; **uv** runs Python tasks; a root task runner script ties the two together.

**Naming.** Python packages `dwarpal_*`; npm scope `@dwarpal/*`; Docker images `ghcr.io/<owner>/dwarpal-<service>`.

---

## 2. Domain model and identifiers

### 2.1 Identifiers
Every entity has a **prefixed, time-ordered ID**: `vs_01JA8XQ2…` (verification session), `org_`, `usr_`, `prj_`, `key_`, `pol_`, `whe_` (webhook endpoint), `evt_`, `att_` (attempt). The body is a UUIDv7, rendered in Crockford base32.

- **Prefixes** make IDs self-describing in logs and support tickets, and stop an ID of one kind being used as another.
- **UUIDv7** is time-ordered, so database indexes stay compact and lists sort by creation without an extra column.

In the database, IDs are native `uuid` columns. PostgreSQL 18's `uuidv7()` generates defaults, and the prefix is applied at the API boundary.

### 2.2 Live and test mode
As in Stripe, every API key, session, webhook endpoint and event carries `livemode: bool`. Test-mode keys (`dk_test_…`) see only test objects; live keys (`dk_live_…`) only live objects. Test mode runs the real pipeline but **never counts toward billing-style analytics**, and supports deterministic *magic inputs* for integration testing — for example, a test session can force `pass` via a special `external_ref`. Websites can therefore test their integration without a camera.

### 2.3 Tables (PostgreSQL 18)

| Table | Key columns | Notes |
| :-- | :-- | :-- |
| `organizations` | id, name, slug | Tenant root |
| `users` | id, email (citext unique), password_hash (Argon2id), totp_secret_enc, created_at, last_login_at | Console users only — **verification end-users are never stored** |
| `memberships` | org_id, user_id, role ∈ {owner, admin, developer, analyst} | RBAC |
| `projects` | id, org_id, name, branding (jsonb: display name, logo URL, accent colour), allowed_origins[] | One RP integration. `allowed_origins` drives the verify page's `frame-ancestors`, `postMessage` targets and `return_url` validation |
| `api_keys` | id, project_id, livemode, prefix, secret_hash (SHA-256), name, scopes[], created_by, last_used_at, revoked_at | Secret shown once |
| `policies` | id, project_id, version, name, preset, min_age, risk_budget, confidence, liveness_level, step_up_methods[], max_face_attempts, token_ttl_s, created_at, superseded_by | **Immutable versions** — editing creates a new row |
| `verification_sessions` | id, project_id, livemode, policy_id, status, outcome, assurance, methods[], client_secret_hash, return_url, external_ref, metadata (jsonb ≤ 2 KB), attempts_count, model_version, created_at, expires_at, completed_at | No biometric data |
| `verification_attempts` | id, session_id, kind ∈ {face, mrz, aadhaar_qr}, result, reason_codes[], scores (jsonb), model_version, duration_ms, created_at | Scores only (see §6.4) |
| `issued_tokens` | jti, session_id, audience, issued_at, expires_at, introspected_at | Replay detection for the introspection endpoint |
| `signing_keys` | kid, alg, public_jwk, private_key_enc, status ∈ {active, retiring, retired}, created_at, activated_at, retired_at | Private key encrypted at rest |
| `webhook_endpoints` | id, project_id, livemode, url, secret_enc, events[], enabled | |
| `events` | id, project_id, livemode, type, data (jsonb), created_at | Source of truth for webhooks and the console |
| `webhook_deliveries` | id, endpoint_id, event_id, status, attempt, next_attempt_at, last_status, last_error | Transactional **outbox** |
| `audit_log` | seq, org_id, actor_type, actor_id, action, target, data, prev_hash, hash, created_at | Hash-chained per organisation |
| `audit_heads` | org_id, last_seq, last_hash | Serialises appends per organisation |
| `idempotency_keys` | project_id, key, request_hash, response (jsonb), created_at | 24-hour retention |
| `model_deployments` | id, model_name, version, role ∈ {active, shadow}, activated_at | Which model decides, and which shadows |

**Row-level security.**

- Every tenant-scoped table has `ENABLE` and `FORCE ROW LEVEL SECURITY` with a policy comparing the row's organisation or project to `current_setting('app.org_id')` or `current_setting('app.project_id')`.
- The API opens each transaction with `SET LOCAL app.org_id = …` (console) or `SET LOCAL app.project_id = …` (API key).
- The application connects as role `dwarpal_app`, which owns no tables. Migrations run as `dwarpal_migrator`.

Result: even a query that forgets its `WHERE project_id = …` can't read another tenant's rows. Tests assert this directly.

**Retention.** Session and attempt *metadata* is kept for 90 days by default, configurable per project from 1 to 365 days, then purged by the worker. Aggregated statistics are kept. Audit logs are kept for 1 year.

---

## 3. API service (`services/api`, package `dwarpal_api`)

### 3.1 Internal structure — hexagonal modules

```
dwarpal_api/
  main.py            create_app(): middleware, routers, lifespan (DB pool, Valkey, inference client, key cache)
  settings.py        typed settings from environment (pydantic-settings); secrets never have defaults in prod
  observability.py   structlog JSON + redaction processor, OpenTelemetry setup, Prometheus metrics
  errors.py          RFC 9457 problem+json; stable error codes; exception → response mapping
  ids.py             prefixed UUIDv7 encode/decode
  db.py              async engine/session (asyncpg), RLS context setter, transaction helper
  security/          api_keys.py, console_session.py, csrf.py, rate_limit.py (Valkey + Lua token bucket), ssrf.py
  modules/
    tenancy/  keys/  policies/  sessions/  attestation/  stepup/  webhooks/  audit/  analytics/  models/
        each: domain.py (pure) · repository.py (SQLAlchemy) · service.py (use cases) · router.py (HTTP) · schemas.py (API models)
    decision/         PURE domain package — liveness fusion, age gate, attempt policy, reason codes (no I/O at all)
  clients/inference.py   HTTP adapter to the inference service (timeouts, retries=0 for analysis, circuit breaker)
  worker.py          arq WorkerSettings: deliver_webhook, expire_sessions, purge_retention, rotate_signing_keys, verify_audit_chain
```

**Dependency rule:**

- `domain` imports nothing from the project.
- `service` depends on `domain` and on abstract *ports* (Protocols). Concrete adapters are injected via FastAPI dependencies.
- `router` only translates HTTP to and from service calls.

Result: the decision engine and token rules are unit-tested in milliseconds without a database, network or model.

### 3.2 HTTP surface (v1)

**Relying-party API** (server-to-server; `Authorization: Bearer dk_(test|live)_…`):

| Method & path | Purpose |
| :-- | :-- |
| `POST /v1/verification-sessions` | Create a session `{policy, return_url?, external_ref?, metadata?}` → `{id, client_secret, url, expires_at, status}`. Supports `Idempotency-Key` |
| `GET /v1/verification-sessions/{id}` | Status, outcome, assurance, methods, timestamps, and `age_token` once completed |
| `GET /v1/verification-sessions` | Cursor-paginated list (`limit`, `starting_after`, filters) |
| `POST /v1/verification-sessions/{id}/cancel` | Cancel a pending session |
| `POST /v1/tokens/introspect` | Server-side token verification for RPs that don't want to handle JWKS; marks the `jti` as introspected (one-time) |
| `GET/POST /v1/policies`, `GET /v1/policies/{id}` | Read presets; create custom policy versions |
| `GET/POST/DELETE /v1/webhook-endpoints[/{id}]` | Manage webhook endpoints; `POST …/{id}/test` sends a test event |
| `GET /.well-known/jwks.json` | Public signing keys (cache-friendly headers) |
| `GET /.well-known/dwarpal-configuration` | Issuer metadata: issuer, jwks_uri, supported policies/methods (discovery, like OIDC) |

**Flow API** (called by the hosted verify page; authenticated with the session's `client_secret`, then a short-lived flow token):

| Method & path | Purpose |
| :-- | :-- |
| `POST /v1/flow/sessions/{id}/start` | Exchange `client_secret` for a flow token (15 min). Returns the public session view: RP display name and branding, policy summary, allowed methods |
| `POST /v1/flow/sessions/{id}/challenge` | Issue a one-time challenge `{challenge_id, nonce, poses[], colours[], step_ms, expires_in}` (stored in Valkey with a TTL) |
| `POST /v1/flow/sessions/{id}/face-attempts` | `multipart/form-data`: `meta` (JSON: challenge_id, per-frame timestamps and phases, capture settings, client signals) plus `frame_0…frame_N` (JPEG, ≤ 200 KB each, ≤ 16 frames). Returns `{outcome, reason_codes, next}` |
| `POST /v1/flow/sessions/{id}/stepup/mrz` | Document image + fresh selfie frames → outcome |
| `POST /v1/flow/sessions/{id}/stepup/aadhaar-qr` | Decoded QR payload (digits) + fresh selfie frames → outcome |
| `POST /v1/flow/sessions/{id}/finish` | Returns the redirect URL (`return_url?session_id=…`); never carries the outcome |

**Console API** (cookie session; same-origin through Caddy at `/api/*`): auth (signup, login, logout, TOTP enrol/verify, me), organisations and members, projects, keys, policies, sessions explorer, analytics, webhooks and deliveries, audit log with chain verification, model information.

**Internal:** `GET /livez`, `GET /readyz` (DB + Valkey + inference reachable + signing key loaded), `GET /metrics` (Prometheus; served on an internal port only).

**Conventions:**

- JSON with `snake_case` fields.
- Timestamps are RFC 3339 UTC.
- Errors are RFC 9457 `application/problem+json`, with a stable `code` (e.g. `session_expired`, `attempt_limit_reached`, `invalid_frames`) plus a `request_id`.
- Every response carries `X-Request-Id`.
- The OpenAPI 3.1 document is generated by FastAPI and published; TypeScript types are generated from it (`packages/api-types`).

### 3.3 Verification session lifecycle

```
created ──start──► in_progress ──(attempt → pass | fail)──────────────► completed
   │                    │  ├─(attempt → retry)──► in_progress (attempt limit applies)
   │                    │  ├─(attempt → step_up)─► awaiting_step_up ──(mrz/aadhaar → pass|fail)──► completed
   │                    │  └─(attempt → reject)──► completed (outcome=reject)
   └──────── expires_at passes / RP cancels ─────► expired / canceled
```

- Transitions are enforced by a small, pure **state machine** in `sessions/domain.py`. Illegal transitions raise, and are tested exhaustively.
- On completion, in **one transaction**, the API writes the outcome, the event and the webhook outbox row, appends to the audit log, and records the issued token. Then it commits.
- Default lifetime: 30 minutes to start, then 15 minutes to complete.

### 3.4 Authentication and authorisation

- **API keys.**
    - Format: `dk_{test|live}_` + 32 random bytes in base62.
    - Lookup uses the first 12 characters (`prefix`), then compares SHA-256 hashes in constant time.
    - Scopes: `sessions:write`, `sessions:read`, `policies:write`, `webhooks:write`.
    - `last_used_at` is updated asynchronously (at most once per minute) to avoid write amplification.
- **Console sessions.**
    - Argon2id password hashing (memory-hard; parameters tuned to about 50 ms).
    - Optional TOTP (RFC 6238).
    - Opaque session ID in an `__Host-` cookie (`HttpOnly`, `Secure`, `SameSite=Lax`, path `/`), with state in Valkey and a 12-hour sliding TTL.
    - Login is rate-limited per account and per IP, with lockout back-off.
- **CSRF.** Console mutations require the cookie **and** a matching `X-CSRF-Token` header (synchroniser token stored in the session), plus an `Origin` check.
- **RBAC matrix:**
    - *owner* — everything;
    - *admin* — everything except deleting the organisation;
    - *developer* — keys, webhooks, policies, sessions;
    - *analyst* — read-only analytics and sessions.

  Enforced in the service layer; tested as a table.

### 3.5 Rate limiting and abuse controls
- **Token bucket** in Valkey, as a single Lua script so it is atomic: per API key (100 req/s, burst 200), per flow session (the challenge endpoint 10/min, attempts as set by the policy), per IP on flow endpoints (60/min).
- **Device-level attempt budget across sessions** — the trial-and-error attack. Key = HMAC(daily salt, /24 IPv4 or /48 IPv6 prefix + user-agent family). Default 10 face attempts per day, then step-up only. The salt rotates daily, so the counter cannot become a long-lived identifier.
- **Retry hardening:** each additional face attempt within a session raises the pass threshold (§5.4).

---

## 4. Hosted verify flow (`apps/web` route `/v/[sessionId]`, package `packages/capture`)

### 4.1 Entry and secrets
The RP's SDK opens `https://verify.<domain>/v/{sessionId}#cs={client_secret}`. The **client secret travels in the URL fragment**: fragments are never sent to servers, so it can't leak into access logs or `Referer` headers. The page reads it, calls `/flow/…/start`, keeps the flow token in memory only, and immediately removes the fragment with `history.replaceState`.

Embedding uses an `<iframe allow="camera; fullscreen">` inside the SDK's modal, communicating with the parent page through `postMessage` with strict origin checks. Popup and full redirect are fallbacks for browsers that block camera access in iframes.

### 4.2 Steps and UX contract

1. **Notice.**
    - Who is asking (the RP's name and logo).
    - What will happen ("about 5 seconds of camera; your image is analysed in memory and never stored").
    - The policy ("you must be 18+").
    - Primary button **Start**; secondary **Use another method**, always visible.
2. **Camera.** `getUserMedia({video: {facingMode: "user", width: {ideal: 1280}, height: {ideal: 720}}})`. Permission-denied and no-camera states route to step-up.
3. **Guidance loop.** MediaPipe Face Landmarker (WASM, GPU delegate where available) runs about 15–30 times per second on the video:
    - computes face box size and centring, head pose (from its transformation matrix), luminance (sampled from a downscaled canvas) and a blur estimate;
    - drives an animated oval and plain-language hints ("move closer", "find more light", "look straight");
    - waits for about 500 ms of stable, good frames.
4. **Challenge.**
    - Fetch a challenge.
    - **Baseline phase:** capture 3 frontal frames while the screen overlay cycles through the challenge colours. Each colour lasts ≥ 400 ms with eased transitions, keeping well below 3 flashes per second (WCAG 2.3.1). It is disabled when `prefers-reduced-motion`/`prefers-contrast` signals a sensitivity, in which case the light signal is simply not used.
    - **Pose phase:** for each pose (e.g. turn left, look up), show an animated cue. When MediaPipe confirms the pose, capture 1–2 frames.
    - Every frame is recorded with `performance.now()` timestamps and its phase label.
5. **Upload.**
    - Frames are encoded as JPEG (quality 0.85, longest side ≤ 640 px), about 40–80 KB each.
    - The request totals ≤ 1 MB.
    - It is sent with a progress indicator and a retry on network failure (idempotent per `challenge_id`).
6. **Result.**
    - *pass* → a success animation, then return to the RP.
    - *retry* → specific guidance.
    - *step_up* → method choice.
    - *fail* → a respectful message.
    - *reject* → a generic "we couldn't verify" message. **Never reveal which anti-spoofing signal fired.**
7. **Step-up.** The MRZ document capture (guided rectangle, auto-capture when sharp) or the Aadhaar QR scan (QR decoding in the browser with a WASM decoder), each followed by a short selfie capture for the face match.

**Accessibility:**

- every state is announced through an `aria-live` region;
- every action is keyboard-operable;
- instructions are given as text and icons, not colour alone;
- timing is generous;
- a non-camera route always exists.

**Internationalisation:** English and Hindi at launch (next-intl); text lives in message catalogues, never in components.

### 4.3 Client signals (sent, never trusted)
The client sends signals; the server never relies on them. Each is only one input to the fusion step:

- `MediaStreamTrack.getSettings()` — resolution, frame rate, `deviceId` hash;
- the camera label, matched against known virtual-camera names;
- `navigator.webdriver`;
- frame-timing statistics;
- a page-visibility history;
- the MediaPipe pose readings.

---

## 5. Inference service (`services/inference`, package `dwarpal_inference`)

### 5.1 Responsibilities and interface
A **stateless** service, reachable only on the internal network:

- `POST /internal/v1/analyze/face` — multipart frames + challenge spec + client signals → `FaceAnalysis` (a `dwarpal_contracts` model);
- `POST /internal/v1/analyze/document` — MRZ region detection + OCR + portrait crop → `DocumentAnalysis`;
- `POST /internal/v1/compare/faces` — embedding similarity between a selfie and a document/QR portrait → `FaceMatch`;
- `GET /internal/v1/models` — loaded model manifests;
- health and metrics.

**Backends:**

- `onnx` (production): ONNX Runtime CPU; CUDA where available.
- `stub` (CI and local development without weights): deterministic outputs derived from the request, e.g. a magic test pattern → a chosen age. All contract tests run against the stub, so CI needs no model weights.

### 5.2 Face pipeline (per frame, then aggregate)

| Step | Implementation | Output |
| :-- | :-- | :-- |
| 1 Decode | OpenCV `imdecode` from bytes; reject > 1920×1920, non-JPEG/PNG, decode errors | BGR array |
| 2 Detect | YuNet (`cv2.FaceDetectorYN`, MIT), score ≥ 0.8; exactly one face required | box, 5 landmarks, score |
| 3 Pose | MediaPipe Face Landmarker (server-side, Apache-2.0) → yaw/pitch/roll; YuNet geometry as fallback | angles |
| 4 Quality | Laplacian variance on face crop (blur), luminance mean and clipping %, inter-ocular distance, pose, detector score | quality score in [0, 1] + flags |
| 5 Align | similarity transform of 5 landmarks to the canonical template → 224×224 RGB (`dwarpal_vision.align`, shared with training) | aligned crop |
| 6 PAD | MiniFASNet ensemble (Apache-2.0) at its two crop scales | P(live) |
| 7 Age | age model (ONNX), batch of all good frames + horizontal flips | 101-way logits → softmax with calibrated temperature |

**Aggregates:**

- **Age distribution** — a quality-weighted mixture of per-frame distributions. From it: mean, standard deviation, 5th/50th/95th quantiles, and `p_over[N]` for N ∈ {13, 16, 18, 21, 25}.
- **Frame consistency** — the spread of per-frame expected ages; box-trajectory smoothness.
- **Pose challenge** — the per-step pose trajectory checked against the issued sequence:
    - step *k*'s frames must show the requested pose (e.g. yaw ≤ −20° for "turn left");
    - the baseline must be frontal (|yaw| ≤ 12°);
    - order and timing must be monotonic and plausible (no frame earlier than its step's cue, no step completed impossibly fast).
- **Light challenge.**
    - For each baseline frame, mean chromaticity (r/(r+g+b), b/(r+g+b)) is measured over skin patches (cheeks, forehead, from landmarks) and over a background patch.
    - The skin chromaticity shift is correlated with the projected emitted colour sequence, using Pearson *r* with the time alignment from timestamps.
    - Outputs: `r_skin`, `r_background`, and `usable` (false when ambient light swamps the screen's contribution).
- **Injection indicators** — from client signals plus server-side evidence (e.g. identical JPEG quantisation tables and noise across frames that are supposedly from a moving camera).

### 5.3 Memory hygiene — "process, decide, forget"
- Frames are read **into memory only**. Each multipart part is capped below Starlette's 1 MB spool threshold, so no temporary file is ever created. Defence in depth: containers run with a **read-only root filesystem** and `/tmp` mounted as **tmpfs** (RAM). Even a library that spooled to disk would write only to memory.
- No request body, frame, crop or embedding is ever logged, traced or included in error reports. A structlog processor and an OpenTelemetry span processor drop attributes on a deny-list, and a unit test asserts that a request carrying a canary byte pattern never shows it in log output.
- Arrays are released at the end of the request: there is no caching of inputs, and no response contains derived images.
- Core dumps are disabled in the container (`ulimit -c 0`).

### 5.4 Performance
- ONNX Runtime sessions are created once at start-up, with intra-op threads equal to the CPU cores.
- All frames of a request go through each model as **one batch**.
- Blocking inference runs in a bounded thread pool (`anyio.to_thread`) behind a semaphore. Excess load gets `503` + `Retry-After` instead of an unbounded queue — **back-pressure**.
- Target: ≤ 1.5 s p95 for 8 frames on 4 vCPU. INT8 quantisation and a distilled student are the levers if this is missed.

---

## 6. Decision engine (`dwarpal_api.modules.decision`, pure)

### 6.1 Inputs and outputs
`decide(policy, thresholds, analysis, attempt_context) -> Decision`

| Input | Meaning |
| :-- | :-- |
| `policy` | The session's pinned policy version: `min_age` N, `risk_budget` ε, liveness level, step-up methods, maximum attempts |
| `thresholds` | `τ_pass(N, ε)` and `τ_fail(N)` from the **active model's manifest** (computed offline, §8.6) |
| `analysis` | `FaceAnalysis` from the inference service |
| `attempt_context` | The attempt index in this session, the device-budget state, earlier reason codes |

`Decision` = an outcome ∈ {pass, fail, step_up, retry, reject}, plus `reason_codes[]`, `assurance`, `methods[]` and a `trace` — the exact inputs that drove the outcome, stored as `scores`.

### 6.2 Algorithm (ordered; the first rule that fires wins)
1. **Integrity** — missing analysis, an inference error, a malformed challenge response or an expired challenge → `retry` (code `analysis_unavailable` / `challenge_expired`). *Never pass.*
2. **Capture quality** — fewer than K = 4 frames pass the quality gate → `retry` with the dominant flag (`too_dark`, `too_blurry`, `face_too_small`, `multiple_faces`, `no_face`, `not_frontal`).
3. **Liveness:**
    - pose challenge failed → `retry` on the first failure, `reject` on the second;
    - PAD `P(live)` < hard limit → `reject`;
    - between the hard and soft limits, or strong injection indicators → `step_up` (if the policy allows it, else `reject`);
    - the light-challenge evidence adjusts the soft limit: strong correlation lowers the PAD bar slightly, while an absent-but-usable signal raises it.
4. **Consistency** — per-frame age spread above the limit → `retry`, or `step_up` once retries are exhausted.
5. **Age gate:**
    - with s = `p_over[N]` and i = the attempt index (0-based), τ_eff = min(0.999, τ_pass + i·Δ), where Δ = 0.02;
    - s ≥ τ_eff → `pass`;
    - s ≤ τ_fail → `fail`;
    - otherwise → `step_up`.
6. **Attempt budget** — once session or device limits are exhausted, only `step_up` or `fail` remain possible.

All constants (K, limits, Δ) live in the policy or model manifest, never in code. The engine is property-tested:

- **monotonicity** — a higher s never turns a pass into a fail;
- **fail-closed** — any `None` or NaN input → never `pass`;
- **retry hardening** — a later attempt never has a lower bar.

---

## 7. Attestation, webhooks, audit

### 7.1 Signing keys and age tokens
- **Keys.** Ed25519 via `cryptography`. Private keys are encrypted with AES-256-GCM under the deployment master key (`DWARPAL_MASTER_KEY`, 32 bytes, from the environment or a secrets file), with the `kid` as associated data.
- **Rotation.** A new key every 30 days. The old key keeps verifying (it stays in the JWKS) for 7 days after retirement.
- **Token format.** A JWS compact token with header `{alg: "Ed25519", kid, typ: "dwarpal-age+jwt"}` (the fully-specified algorithm name, ADR-0019).
- **Claims:**
    - `iss`, `aud` (the project ID), `iat`, `nbf`, `exp` (policy TTL, default 600 s), `jti`;
    - `sid` (session), `nonce` (an optional RP value passed at session creation);
    - `outcome`, `age_over_N` (a boolean named after the policy's age, e.g. `age_over_18: true`; ADR-0020), `assurance`, `methods`, `policy` (id@version), `model` (version).
- **Verification.** `@dwarpal/node` verifies the signature through a JWKS cache (jose's remote key set: kept for up to 10 minutes, refetched — at most every 30 s — when a token names an unknown `kid`), accepting only `Ed25519`, then checks `typ`, `iss`, `aud`, `exp`, `sid`, and that `age_over_<required>` is exactly `true` (ADR-0020).

### 7.2 Webhooks
- **Events:** `verification_session.completed | expired | canceled`.
- **Delivery:**
    - the worker claims due outbox rows with `FOR UPDATE SKIP LOCKED`, so many workers never double-send;
    - it POSTs JSON with `Dwarpal-Signature: t=<unix>,v1=<hex HMAC-SHA256(secret, "<t>.<body>")>` and `Dwarpal-Event-Id`;
    - receivers reject signatures older than 5 minutes.
- **Retries:** at 1 min, 5 min, 30 min, 2 h, 6 h, 12 h and 24 h, then `dead`. The console can replay a delivery.
- **SSRF guard:**
    - URLs must be `https` in live mode;
    - hostnames are resolved, and every resolved address must be public — not private, loopback, link-local, multicast or reserved (Python `ipaddress`);
    - this is re-checked at delivery time;
    - the worker container's egress is additionally restricted at the network level.

### 7.3 Tamper-evident audit log
- **Hash chain:** `hash_n = SHA-256(hash_{n−1} ‖ canonical_json(entry_n))`, chained per organisation.
- **Appends** run inside the business transaction and lock that organisation's `audit_heads` row, which serialises appends without a global lock.
- **Verification:** a nightly worker job and a console button recompute the chain and report the first broken link, if any.
- **Audited actions:** logins and MFA changes; key creation and revocation; policy versions; webhook changes; member changes; model deployments; data exports.

---

## 8. Machine-learning pipeline (`ml/`, package `dwarpal_ml`)

### 8.1 Data acquisition and licensing
`dwarpal-ml data fetch <dataset>` downloads into `.datasets/raw/<dataset>/` (git-ignored). Where a dataset requires manual acceptance, the script prints the official URL and the expected file names, and **the owner accepts the licence**. A **licence register** (`ml/datasets.yaml`) records the source, licence, permitted use and citation for each dataset. A model's manifest lists exactly which datasets trained it.

First wave (directly obtainable): UTKFace, FairFace, APPA-REAL, FG-NET, AFAD, IMDB-Clean (CSV) + IMDB-WIKI images. Second wave (on request): AgeDB, LAGENDA.

### 8.2 Unified manifest and splits
- One Parquet table: `image_id, path, dataset, subject_id?, age, age_kind ∈ {real, apparent}, sex?, group?, licence, quality, split`.
- **Subject-disjoint splits** where subject IDs exist. **Near-duplicate removal** (perceptual hash) across *all* splits, so the same photo can't sit in both training and test.
- **Four splits:**
    - **train** — fitting;
    - **val** — model selection and temperature scaling;
    - **calib** — risk-control thresholds only;
    - **test** — the final report, opened once per release candidate.
- A **teen-focus** evaluation view (ages 10–25) cuts across the test sets. **Fairness views** use UTKFace's sex and group labels, which come with exact ages.

### 8.3 Pre-processing
`dwarpal_vision` (shared with serving) detects, aligns and crops to 256×256, caching to `.datasets/processed/`. Faces failing detection are dropped and counted per dataset in the data report.

### 8.4 Training recipe (baseline; tuned by experiment)
- **Backbones:** ConvNeXt-V2-T, ViT-B/16 (face-pretrained) and DINOv2-B, all via timm. Head: Linear → 101 logits.
- **Target and loss.**
    - The target is a Gaussian label distribution centred on the age, with σ(a) = 1.0 + 0.04·a (sharper for children, whose faces change faster).
    - Loss = KL(target ‖ softmax) + λ·|E[age] − a|, with λ = 0.1.
    - An optional **safety term** adds μ·Σ_{a′≥N} p(a′) for samples with N−5 ≤ age < N, at N ∈ {13, 16, 18}.
- **Sampling:** balanced over age bins (5-year bins, ages 10–25 up-weighted) and over datasets, so IMDB doesn't dominate.
- **Augmentation:**
    - geometric: random resized crop (0.85–1), horizontal flip, ±10° rotation;
    - colour and exposure: jitter, gamma 0.6–1.4 (low light);
    - **webcam simulation**: Gaussian and motion blur, sensor noise, JPEG quality 30–90, downscale-and-upscale.
- **Optimisation:**
    - AdamW with cosine schedule and warm-up; layer-wise LR decay of 0.75 for ViTs;
    - bf16 autocast, `torch.compile` and EMA of weights;
    - batch size 64–128 at 224 px — fits 8 GB VRAM, with gradient checkpointing for ViT-B.
- **Tracking:** MLflow (local file store), plus config, git commit, data manifest hash and seed for every run.

### 8.5 Evaluation harness (one fixed protocol)
- **MAE** and CS@5, per dataset and per age band.
- **FAR-minor@N** for each exact age N−5…N−1, and averaged over the band — as functions of the threshold, with Clopper–Pearson intervals.
- **Adult step-up rate@N** per adult band (N…N+2, N+3…N+6, N+7…N+11, N+12+).
- **Fairness:**
    - FAR-minor and adult step-up per group;
    - the worst-to-best gap;
    - MAE per group.
- **Calibration:** ECE of the `p_over[N]` probabilities, and reliability diagrams.
- **Release gates** (`ml/gates.yaml`):
    - FAR-minor@18 (band average, upper confidence bound) ≤ 5 %;
    - fairness gap ≤ 2 pp;
    - adult (25+) pass rate ≥ 85 %;
    - CPU latency ≤ budget;
    - ONNX/PyTorch parity within 1e-3.

### 8.6 Risk-controlled thresholds
For each N ∈ {13, 16, 18, 21} and ε ∈ {1 %, 2 %, 5 %}, with δ = 0.05:

1. Score every calib sample with `p_over[N]`, using the exact production aggregation, approximated for single photos by flip TTA plus quality weighting.
2. For each exact age *a* in N−5…N−1, and for each labelled group *g*, find the smallest τ for which the one-sided Clopper–Pearson upper bound of P(s ≥ τ | age = *a*, group = *g*) is ≤ ε. Cells with too few samples are reported and use the pooled-age bound.
3. τ_pass(N, ε) = the maximum across all *a* and *g*.
4. τ_fail(N) = the largest τ for which adults aged N+3 and over fall below it at most 1 % of the time — so adults are almost never hard-failed.
5. Write the thresholds, the per-cell counts and the achieved bounds into the manifest. The model card plots them.

### 8.7 Export, quantisation, registry
- **Export:** ONNX opset 20 with dynamic batch; parity test; `onnxruntime` graph optimisations; INT8 (dynamic for ViT, static QDQ for CNN, calibrated on 512 val images). The quantised model is **re-evaluated against all gates**.
- **Registry:** `models/registry/age/<version>/manifest.json` (committed), containing:
    - SHA-256 of every file;
    - input specification;
    - temperature;
    - thresholds;
    - metrics;
    - datasets and licences;
    - training commit.

  `model_card.md` is generated alongside. Weights live outside git and are fetched by `infra/scripts/fetch-models` (hash-verified).
- **Promotion:** a new version first runs in **shadow** (scored and logged as aggregate statistics only, never deciding), then becomes active. Rollback means switching the active version back.

### 8.8 Third-party models (licence-checked before use)
| Model | Use | Licence |
| :-- | :-- | :-- |
| YuNet (OpenCV Zoo) | face detection + 5 landmarks | MIT |
| MediaPipe Face Landmarker | browser guidance; server pose | Apache-2.0 |
| MiniFASNet V2 / V1SE (Silent-Face) | passive PAD | Apache-2.0 (verify upstream before use) |
| SFace (OpenCV Zoo) | 1:1 face match in step-up | verify before use |
| MiVOLO VOLO-D1 face-only | **benchmark only** (never in the runtime path) | per upstream |

---

## 9. Step-up verifiers (`modules/stepup`)

All verifiers implement:

```python
class StepUpVerifier(Protocol):
    method: str  # "mrz" | "aadhaar_qr"
    assurance: Assurance  # what a success is worth

    async def verify(self, submission, policy) -> StepUpResult: ...  # outcome, dob_year_month?, reason codes
```

### 9.1 ID document (MRZ) — first
1. **Capture.** The client captures the document's data page, auto-capturing when sharp, plus 3 selfie frames.
2. **MRZ location and reading** (inference service `/analyze/document`):
    - MRZ band detection with morphological operations (blackhat → gradient → closing → contour aspect filter);
    - perspective correction;
    - OCR with Tesseract and an OCR-B/MRZ-trained model, restricted to the alphabet `A–Z 0–9 <`.
3. **Parsing** (pure, in the API): our own **ICAO 9303** parser for TD1 (3×30), TD2 (2×36) and TD3 (2×44):
    - fields;
    - **check digits** (weights 7-3-1, values 0–9 / A=10…Z=35 / `<`=0, mod 10) for the document number, date of birth, expiry and the composite;
    - OCR-confusion repair (`0↔O`, `1↔I`, `5↔S`, `8↔B`) applied **only** where it makes a failing check digit pass, and recorded in the reason codes.
4. **Rules:**
    - document not expired;
    - all check digits valid;
    - age from the date of birth ≥ N (two-digit years resolved against the current date and the expiry);
    - selfie ↔ document portrait similarity above the threshold;
    - the selfie passes liveness (pose challenge).
5. **Assurance:** `basic`. Browsers cannot read the passport chip (no BAC/PACE or Active Authentication), and we do not do forensic authenticity checks. The book and the console say so plainly.
6. **Data handling:** only the year and month of birth and the check results are kept. The document number, name and nationality are **discarded** in memory.

### 9.2 Aadhaar Secure QR — second (India)
1. **Capture.** The client scans the Secure QR (from an Aadhaar letter, e-Aadhaar or PVC card) with a WASM QR decoder, sends the **digit string**, and captures 3 selfie frames.
2. **Server processing:**
    - big-integer → bytes → decompress;
    - split the fields at the 0xFF delimiter, following UIDAI's published *Secure QR Code* specification for the version in use;
    - verify the **RSA-2048/SHA-256 signature** against UIDAI's published offline-verification public certificate;
    - extract the date or year of birth, and the embedded photo (JPEG 2000).
3. **Rules:**
    - a valid signature;
    - age ≥ N;
    - selfie ↔ QR-photo similarity above the threshold;
    - a live selfie.
4. **Assurance:** `standard` for date-of-birth authenticity. The binding to the person depends on the face match — the QR photo is low-resolution — so the label is reviewed after evaluation.
5. **Legal and privacy guardrails:**
    - explicit consent screen, with India-only availability by policy;
    - **no Aadhaar data is stored** — not the reference ID, name, address or photo;
    - processing happens in memory only;
    - the feature is labelled "demo / requires legal review before production use";
    - the exact specification version and certificate are verified at implementation time against UIDAI's current publications.

---

## 10. Front-end design system and apps

- **Brand.** *Dwarpal* — the guardian at the gate.
    - Motif: an arch (torana) framing a face formed of light points.
    - Palette (OKLCH): midnight indigo base, saffron/amber accent, teal for success, with tuned dark and light themes.
    - Type: **Inter**-style UI sans paired with a display serif for headlines (decided in Phase 5 with a type specimen).
- **Marketing site.**
    - Hero: a 3D particle face (478 MediaPipe points) inside an arch. It "scans" on scroll, then **disperses into nothing** — *Look. Decide. Forget.*
    - Sections: how it works (3 steps), the privacy promise, the live accuracy table (from the model card), the developer quick-start, compliance mapping (UK/EU/US/AU/IN), FAQ and a demo CTA.
    - Motion respects `prefers-reduced-motion` (falling back to static artwork).
- **Console.**
    - Sidebar layout plus a command palette (⌘K).
    - **Dashboard:** volume and outcome mix over time, median latency, liveness rejects, step-up conversion.
    - **Sessions explorer:** filters, plus a detail drawer with the *decision trace* — scores, thresholds, reason codes, policy and model versions; never images.
    - **Policy editor:** a risk-budget slider with **live projected adult step-up rate** read from the model manifest's curves.
    - **Also:** keys, webhooks (deliveries and replay), members, audit log (with a chain-intact badge), model page (model card and fairness charts) and settings.
- **Demo shop.** A fictional wine shop ("Amber Cellars"): product pages, an age gate at checkout, a server route that creates sessions, and token verification with `@dwarpal/node`. It shows *exactly* the code an RP must write.
- **Quality bars:** Lighthouse ≥ 90 in every category; axe-core clean; Core Web Vitals in the "good" range; no layout shift while the camera loads.

---

## 11. Observability, configuration, operations

- **Logs:** JSON lines with `request_id`, `session_id` (when present), `project_id`, `route`, `status` and `duration_ms`. Redaction deny-list: `frames`, `image`, `authorization`, `client_secret`, `password`, `token`, `secret`, `qr`.
- **Metrics:**
    - `dwarpal_verifications_total{policy,outcome,livemode}`;
    - `dwarpal_attempts_total{kind,result}`;
    - `dwarpal_retry_reasons_total{reason}`;
    - `dwarpal_face_analysis_seconds` (histogram);
    - `dwarpal_inference_inflight`;
    - `dwarpal_p_over_bucket{N}` (drift);
    - `dwarpal_webhook_deliveries_total{status}`;
    - `dwarpal_model_info{name,version,role}`;
    - plus HTTP RED metrics.
- **Traces:** OpenTelemetry across web → API → inference, with frame payloads excluded by the span processor.
- **SLOs:** API availability 99.9 %; face-attempt latency p95 ≤ 1.5 s; webhook delivery p95 ≤ 60 s. Grafana burn-rate alerts.
- **Configuration:** 12-factor — environment variables validated at start-up (the service refuses to start in production with default secrets).
- **Secrets:** generated by `infra/scripts/gen-secrets`; on the VM, a root-only `.env`.

---

## 12. Testing strategy (per layer)

| Layer | Tooling | Examples |
| :-- | :-- | :-- |
| Pure domain | pytest + Hypothesis | decision engine properties; state machine; ICAO check digits; token claims; hash chain |
| Service + DB | pytest-asyncio + **Testcontainers** (PostgreSQL 18, Valkey) | RLS isolation; outbox; idempotency; key rotation; retention purge |
| API contract | **Schemathesis** against OpenAPI | no 5xx on fuzzed input; schema conformance |
| Inference | pytest; golden images (synthetic, CC0); stub backend | decode limits; detector/aligner geometry; ONNX parity; no-disk check (read-only FS in the test container) |
| ML | pytest; small fixtures | metric functions vs hand-computed values; Clopper–Pearson vs reference values; split leakage checks |
| Front end | Vitest + Testing Library | capture state machine; SDK postMessage protocol; policy-editor maths |
| End-to-end | **Playwright** with Chromium's fake camera (`--use-file-for-fake-video-capture`) | demo shop → verify → token verified; step-up flows; accessibility (axe) |
| Load | Locust | 50 concurrent attempts → latency SLO |
| Security | ruff security rules / Semgrep, pip-audit, pnpm audit, Trivy, ZAP baseline | |
| Red team | scripted attacks | print/screen replay videos as fake cameras; payload replay; challenge mismatch; game-render video |
| Docs | `build.py --strict` | 100 % line coverage, no stale walkthroughs |

---

## 13. What could still change

These choices are made, but cheap to revisit once measured: backbone (by experiment), exact quality and liveness constants (from red-team and genuine-attempt data), the light-challenge weight (from field testing), the Aadhaar assurance label (after face-match evaluation), and the display typeface (by specimen review).
