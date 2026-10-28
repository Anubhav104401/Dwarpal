# Stage 4 — Architecture

**Project:** Dwarpal · **Status:** Baseline architecture v1 · 15 Oct 2026
**Reads with:** [03_implementation_design.md](03_implementation_design.md) (the *how* of each piece) and [`docs/adr/`](../adr/) (the *why* of each decision).

This document describes the system at four zoom levels, following the **C4 model**: context → containers → components → code. It then covers the dynamic behaviour, trust and privacy boundaries, failure behaviour, deployment and quality-attribute scenarios.

---

## 1. System context (C4 level 1)

```
                         ┌──────────────────────────┐
     End user  ─────────►│      Relying party       │  (any website/app with age-restricted content;
   (adult or minor)      │  e.g. the Amber Cellars  │   our demo shop is one)
         │               │       demo shop          │
         │               └─────────┬────────────────┘
         │ hosted verify flow      │ REST API (secret key), JWKS, webhooks
         ▼                         ▼
   ┌─────────────────────────────────────────────────┐        ┌───────────────────────┐
   │                    DWARPAL                      │◄──────►│  RP developer / admin │
   │   privacy-first age-assurance service           │ console│  (manages keys,       │
   │                                                 │        │  policies, webhooks)  │
   └─────────────────────────────────────────────────┘        └───────────────────────┘
         ▲                                   ▲
         │ (offline) training data           │ public keys (UIDAI offline-verification
   Public research datasets                  │ certificate) for Aadhaar Secure QR
   (licence register)                        │
```

**External dependencies at runtime: none.** All inference is self-hosted. The UIDAI certificate is a pinned, versioned file in the repository. Nothing about a user leaves Dwarpal except the signed outcome sent to the RP that asked for it.

---

## 2. Containers (C4 level 2)

| Container | Technology | Responsibility | Talks to | Scales |
| :-- | :-- | :-- | :-- | :-- |
| **Edge** | Caddy 2 | TLS termination (auto-certificates), routing by host/path, security headers, request-size limits, compression | web, api | 1 (VM) |
| **web** | Next.js 16 (Node 24) | Marketing site, docs, **hosted verify flow**, console UI. Server components fetch console data from the API | api (server-side), browser | horizontally (stateless) |
| **api** | FastAPI (Python 3.13), Uvicorn | RP API, flow API, console API, decision engine, tokens, policies, audit | postgres, valkey, inference | horizontally (stateless) |
| **worker** | Same image as api, `arq` command | Webhook delivery (outbox), expiry, retention purge, key rotation, audit-chain verification, stats roll-ups | postgres, valkey, RP webhook URLs (egress) | horizontally (`SKIP LOCKED`) |
| **inference** | FastAPI + ONNX Runtime + OpenCV + MediaPipe | Face analysis, document analysis, face match. **The biometric perimeter** | — (receives only) | horizontally (CPU-bound) |
| **postgres** | PostgreSQL 18 | System of record, RLS-enforced tenancy | — | 1 primary (+ backups) |
| **valkey** | Valkey 9 | Challenges, rate limits, console sessions, job queue, idempotency cache | — | 1 |
| **observability** (optional profile) | OTel Collector, Prometheus, Grafana, Loki | Metrics, logs, traces, dashboards, alerts | scrapes everything | 1 |

**Routing at the edge (one VM):**

| Host / path | Routed to |
| :-- | :-- |
| `dwarpal.<domain>` | web |
| `dwarpal.<domain>/api/*` | api (console API, same-origin) |
| `verify.<domain>` | web (verify flow only — a separate origin with a tight `Permissions-Policy: camera=(self)`) |
| `api.<domain>` | api (RP and flow API, CORS for `verify.<domain>` only) |
| `shop.<domain>` | demo-shop |
| `grafana.<domain>` | Grafana (behind auth) |

> **Why a separate origin for the verify flow?** The page that can use the camera is isolated from the marketing site and console. It runs with a strict Content Security Policy, and no third-party script can ever end up on a page that has camera access.

---

## 3. Components (C4 level 3)

### 3.1 API (modular monolith, hexagonal)

```
              ┌───────────────────────────── HTTP adapters (FastAPI routers) ─────────────────────────────┐
              │  rp_api      flow_api      console_api      well_known (jwks, configuration)             │
              └──────┬────────────┬──────────────┬────────────────────┬─────────────────────────────────┘
                     ▼            ▼              ▼                    ▼
   ┌─────────── application services (use cases; transactions; authorisation) ──────────────┐
   │ SessionsService  FlowService  StepUpService  PoliciesService  KeysService  WebhooksService │
   │ AttestationService  AuditService  AnalyticsService  TenancyService  ModelsService         │
   └──────┬──────────────────────────────┬──────────────────────────────────────┬─────────────┘
          ▼                              ▼                                      ▼
   ┌───── domain (pure) ─────┐   ┌──── ports (Protocols) ────┐        ┌──── adapters ─────────────────┐
   │ decision engine         │   │ SessionRepository         │◄───────│ SQLAlchemy repositories (RLS) │
   │ session state machine   │   │ InferencePort             │◄───────│ HTTP inference client         │
   │ policy & presets        │   │ ChallengeStore, Limiter   │◄───────│ Valkey adapters               │
   │ token claims rules      │   │ KeyStore, Clock, Random   │◄───────│ crypto, system clock, CSPRNG  │
   │ ICAO 9303 / QR parsers  │   │ EventBus (outbox)         │◄───────│ outbox writer                 │
   │ audit hash chain        │   └───────────────────────────┘        └───────────────────────────────┘
   └─────────────────────────┘
```

Rules:

- Arrows point inward only.
- The domain has **no I/O and no clock**. Time and randomness are injected, so tests are deterministic.
- Services own transactions; one use case = one transaction.

### 3.2 Inference service

```
 router ─► FacePipeline ─► [decode] ─► [detect: YuNet] ─► [pose: MediaPipe] ─► [quality] ─► [align]
                                │                                                        │
                                │                       ┌────────────────────────────────┤
                                ▼                       ▼                                ▼
                         ChallengeVerifier        PADModel (MiniFASNet)          AgeModel (ONNX, batched, TTA)
                         (pose trajectory,                │                                │
                          light correlation)              └────────────► Aggregator ◄──────┘
                                                                     (quality-weighted mixture,
                                                                      p_over[N], quantiles, spread)
 ModelRegistry: loads manifests + weights at start-up, verifies SHA-256, exposes versions; active + optional shadow
 Backends: OnnxBackend | StubBackend (deterministic; CI and dev)
```

### 3.3 Web app (Next.js)

- **Route groups:**
    - `(marketing)` — server-rendered, static where possible;
    - `/docs` — MDX, rendered from the repository docs;
    - `/v/[sessionId]` — the client-heavy capture flow, with dynamic imports for MediaPipe so the WASM loads only on this route;
    - `/console/*` — server components plus TanStack Query for interactivity.
- **Shared packages:**
    - `@dwarpal/ui` — tokens, components, motion presets;
    - `@dwarpal/capture` — a pure TypeScript state machine plus camera and MediaPipe adapters, unit-tested without a camera;
    - `@dwarpal/api-types`.

---

## 4. Dynamic view — one verification, end to end

```
RP backend        RP page (SDK)        verify page          API                    Inference         Postgres/Valkey
    │ POST /v1/verification-sessions (dk_live_…, Idempotency-Key)                                        │
    │─────────────────────────────────────────────────────────►│ create session (policy@v, expiry)        │
    │◄──────────────── {id, client_secret, url} ────────────────│──── INSERT session ─────────────────────►│
    │ hand {id, client_secret} to page                          │                                          │
    │──────────────────►│ Dwarpal.open() → iframe verify.<d>/v/id#cs=…                                     │
    │                   │──────────────────►│ POST flow/start (client_secret) ─────►│ verify hash; flow token │
    │                   │                   │ camera + MediaPipe guidance (local)   │                         │
    │                   │                   │ POST flow/challenge ──────────────────►│ SETEX challenge (nonce)│
    │                   │                   │ capture baseline (colours) + poses    │                         │
    │                   │                   │ POST face-attempts (frames+meta) ────►│ rate/attempt limits     │
    │                   │                   │                                       │── analyze/face ───►│    │
    │                   │                   │                                       │◄── FaceAnalysis ───│    │
    │                   │                   │                                       │ decide() (pure)         │
    │                   │                   │                                       │ TX: attempt, outcome,   │
    │                   │                   │                                       │  event+outbox, audit,   │
    │                   │                   │                                       │  token jti ────────────►│
    │                   │                   │◄────────── {outcome: pass} ───────────│                         │
    │                   │◄── postMessage(completed, id) ── (origin-checked)          │                         │
    │◄── page notifies backend (session id only) ─│                                   │                         │
    │ GET /v1/verification-sessions/{id} ─────────────────────────────────────────►│                          │
    │◄──────────── {outcome: pass, age_token: eyJ…} ────────────────────────────────│                          │
    │ verify JWS via cached JWKS; check aud, exp, age_over_18 = true → grant access                          │
    │                                       worker: deliver webhook (HMAC) ◄────────── outbox row ───────────│
```

**Invariants:**

1. The browser never learns the outcome from anything except the API, and the RP **never trusts the browser** about the outcome.
2. The frames exist only in the request memory of the API and inference processes.
3. Every completed session has exactly one outcome event, one audit entry and at most one live token.

---

## 5. Trust boundaries and data classification

| Zone | Contains | Trust |
| :-- | :-- | :-- |
| **Z0 — User device** | Camera stream, MediaPipe outputs, client signals | **Untrusted.** Everything is re-verified server-side |
| **Z1 — Edge** | TLS, routing | Trusted infrastructure; enforces size limits and headers |
| **Z2 — Application** (api, worker, web server) | Sessions, policies, scores, tokens, keys (encrypted) | Trusted; tenant-isolated by RLS |
| **Z3 — Biometric perimeter** (inference + the API request buffer) | Frames, crops, embeddings — **transient** | Trusted; no persistence, no logging, read-only filesystem, tmpfs, no egress |
| **Z4 — Data** (postgres, valkey) | Metadata, scores, audit | Trusted; internal network only; encrypted backups |
| **Z5 — Relying party** | Their session, our token | External. Verifies our signatures; never sees biometrics |

| Data class | Examples | Stored? | Where | Retention |
| :-- | :-- | :-- | :-- | :-- |
| **B — Biometric** | frames, crops, face embeddings, document/QR photos | **Never** | memory only | ≈ request duration |
| **I — Identity documents** | MRZ name/number, Aadhaar fields | **Never** (except year-month of birth) | memory only | request |
| **S — Scores** | quality, P(live), p_over[N], reason codes | Yes | postgres | 90 days (configurable) |
| **M — Metadata** | session status, policy, timestamps, RP external_ref | Yes | postgres | 90 days |
| **C — Credentials** | API key hashes, password hashes, encrypted private keys | Yes | postgres | until revoked |
| **A — Audit** | admin actions | Yes | postgres (hash chain) | 1 year |

---

## 6. Failure behaviour (fail closed, degrade gracefully)

| Failure | Detection | Behaviour | User sees |
| :-- | :-- | :-- | :-- |
| Inference down or slow | client timeout (3 s), circuit breaker | attempt → `retry` (`analysis_unavailable`); **never pass**; `/readyz` fails → removed from rotation | "We're having trouble — please try again" (+ step-up option) |
| Inference overloaded | semaphore full → 503 | API returns `retry` with back-off hint | same |
| Model files corrupt | SHA-256 mismatch at start-up | inference refuses to start; previous container keeps serving | — |
| Postgres down | pool errors | API 503; flow cannot complete; nothing is decided without persistence | "Service unavailable" |
| Valkey down | connection errors | challenge issuance fails → `retry`; rate limiting fails **closed** for flow endpoints | "Please try again" |
| Signing key unavailable | readiness check | no token can be issued → session cannot complete as pass | "Please try again" |
| Webhook receiver down | HTTP errors | retries over 3 days, then dead-letter; console replay | — |
| Clock skew | NTP on the VM; `nbf`/`exp` leeway of 60 s | — | — |
| Partial deploy | health-gated rolling restart in Compose (`depends_on: condition: service_healthy`) | old containers serve until new ones are healthy | — |

---

## 7. Deployment view (owner decision: single VM)

```
             Internet
                │  :443 (:80 → redirect)
        ┌───────▼──────────────────────────────────────────── VM (Ubuntu 24.04 LTS, 4 vCPU / 8–16 GB) ─┐
        │  ufw: allow 22 (key-only SSH), 80, 443 · unattended-upgrades · Docker Engine + Compose        │
        │                                                                                                │
        │  ┌────────┐   edge network   ┌───────┐  ┌──────────┐                                            │
        │  │ caddy  │─────────────────►│  web  │  │ demo-shop│                                            │
        │  └───┬────┘                  └───┬───┘  └─────┬────┘                                            │
        │      │                           │            │                                                 │
        │      └──────────────►┌───────┐◄──┘            │  app network (internal: true)                  │
        │                      │  api  │◄───────────────┘                                                 │
        │                      └─┬──┬──┘                                                                  │
        │          ┌─────────────┘  └───────────┐        ┌──────────┐                                     │
        │          ▼                            ▼        │ worker   │──► egress (webhooks only)           │
        │   ┌─────────────┐  infer network ┌──────────┐  └────┬─────┘                                     │
        │   │  inference  │ (internal, no  │ postgres │◄──────┤                                           │
        │   │ ro rootfs,  │  egress)       │  valkey  │◄──────┘                                           │
        │   │ tmpfs /tmp  │                └──────────┘   volumes: pgdata, valkeydata, caddy_data, models │
        │   └─────────────┘                                                                              │
        │  backups: nightly pg_dump → encrypted (age) → off-site object storage (restic)                  │
        └────────────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Images** are built in GitHub Actions for `linux/amd64` and `linux/arm64`, scanned with Trivy, and pushed to GHCR with SBOMs.
- **Deploy** runs over SSH as a dedicated user: `docker compose pull`, then a `migrate` one-off container (Alembic), then `docker compose up -d --wait`.
- **Rollback** pins the previous image tags.
- **Model weights** are fetched to the `models` volume by a hash-verified script, never baked into public images.
- **Kubernetes path:** `infra/helm/dwarpal` mirrors the same containers. It adds Deployments with probes, HPA for api/inference, NetworkPolicies equivalent to the Compose networks, and Secrets. It is shipped and linted in CI, and used only if the deployment target changes.

---

## 8. Quality-attribute scenarios (how the architecture meets the NFRs)

| Attribute | Scenario | Architectural response |
| :-- | :-- | :-- |
| **Safety** | A minor near the threshold tries 5 times with different lighting | Session attempt limit → device budget → rising τ_eff → step-up only. Risk-controlled τ bounds the per-attempt pass rate |
| **Privacy** | An attacker gets a full database dump | Contains no images, names, document numbers or stable user IDs — only scores and metadata. Keys are encrypted with a master key not stored in the DB |
| **Privacy** | A developer adds `logger.info(request)` by mistake | The redaction processor drops payload fields. The canary test fails CI if frames reach logs |
| **Security** | A tenant's API key leaks | Scoped, revocable keys. RLS confines damage to that project. Audit log shows usage. Rotation without downtime (two keys active) |
| **Security** | A forged "pass" in the RP's front end | RP verifies an EdDSA signature with our JWKS. `aud` binds the token to their project; `exp`/`jti` limit replay |
| **Availability** | Inference node crashes mid-attempt | API timeout → `retry`, nothing decided. Compose restarts it; readiness gates traffic |
| **Performance** | 50 people in a check at once on 4 vCPU (an attempt every ~20 s each; decision P2) | Batched ONNX inference, bounded concurrency, 503 back-pressure instead of collapse. Scale inference replicas horizontally |
| **Modifiability** | Replace the age model with a licensed commercial-grade one | Drop a new registry version with a manifest. Gates run in CI, shadow-compare, promote. No API change |
| **Modifiability** | Add a new step-up method (EU wallet / OpenID4VP) | Implement `StepUpVerifier`; add to policy method list and the flow UI |
| **Testability** | Verify the whole camera flow in CI without a camera or weights | Playwright fake camera + stub inference backend + test-mode magic inputs |
| **Auditability** | A regulator asks how a session was decided | Decision trace (scores, thresholds, policy@version, model@version) and the hash-chained audit log |

---

## 9. Cross-cutting conventions

- **Configuration:** environment variables only; one typed settings object per service, validated at start-up.
- **Time:** UTC everywhere; the server clock is the authority; the domain receives time via a `Clock` port.
- **IDs:** prefixed UUIDv7. **Money:** none.
- **Errors:** problem+json with stable codes; no stack traces to clients; correlation via `request_id`.
- **API versioning:** `/v1` path; additive changes only within a version; deprecations announced via the `Deprecation` header.
- **Security headers (edge + app):** HSTS (preload-ready), CSP with nonces, `Permissions-Policy` (camera only on the verify origin), `Referrer-Policy: strict-origin-when-cross-origin`, `X-Content-Type-Options: nosniff`. The embeddable verify page sets `frame-ancestors` **per session**, from the RP project's registered allowed origins — so only that RP's own pages can frame it, which blocks clickjacking by arbitrary sites. `postMessage` is origin-checked in both directions.
- **Dependency policy:** see [ADR-0018](../adr/0018-licence-policy.md). Permissive licences only in the runtime path; every model and dataset recorded in a licence register.

---

## 10. Architecture decision records

See [`docs/adr/README.md`](../adr/README.md) for the index of all decisions (ADR-0001 … ADR-0018).
