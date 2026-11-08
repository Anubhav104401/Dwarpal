# Stage 5 — Roadmap

**Project:** Dwarpal · **Status:** Active · **Started:** 15 Oct 2026
**Principle:** build a **walking skeleton** first — a thin slice through every layer working end to end with a stub model — then thicken each layer. Every phase ends in something that *runs*, is *tested*, and is *explained in the book*.

---

## Progress

| Phase | Name | Status |
| :-: | :-- | :-- |
| 0 | Foundations — repository, toolchains, quality gates, CI | ✅ complete — [report](../reports/phase-0.md); CI green on GitHub since 2 Nov (`03f3f5b`) |
| 1 | Walking skeleton — end to end with a stub model | ✅ complete — [report](../reports/phase-1.md) |
| 2 | ML core — data, training, evaluation, risk control, v1 model | ✅ steps 1–7 done — [report](../reports/phase-2.md); open: exact-age data for NFR-01 (owner) |
| 3 | Liveness and anti-spoofing | 🟡 built, red-teamed by the owner — [report](../reports/phase-3.md); open: broader measurement (more people, cameras, rooms) |
| 4 | Platform — tenancy, auth, policies, webhooks, audit | ✅ complete — [report](../reports/phase-4.md) |
| 5 | Front-end excellence — design system, site, flow, console, SDKs | ✅ exit met on CI (Lighthouse ≥ 90, axe, Chromium/Firefox/WebKit) — [report](../reports/phase-5.md); open: Hindi and legal reviews |
| 6 | Step-up verifiers — MRZ, then Aadhaar Secure QR | 🟡 MRZ done end to end — [report](../reports/phase-6.md); Aadhaar deferred by the owner (D8, O7) |
| 7 | Hardening — security, observability, load, privacy docs | 🟡 nearly all done — [report](../reports/phase-7.md); open: SLOs measured on the real server, alert delivery |
| 8 | Deployment — VM, TLS, CI/CD, backups, runbooks, Helm | 🟡 everything written and checked — [report](../reports/phase-8.md); the domain is a free DuckDNS name (D40) and an outside uptime check is ready (D33); waits on the owner's server, the name's creation and backups storage |
| 9 | Stretch — Age Pass credential, passkeys, render detector, Python SDK | 🟡 SDK, passkeys, Age Pass built — [report](../reports/phase-9.md); render detector's code built, its data being made (D22; filming waits for D23) |

Each phase ends with a **phase report** in `docs/reports/`: what was built, what was measured, what changed from the plan and why, and the known limitations. The book's changelog links to it.

---

## Definition of Done (applies to every task)

A change is done only when **all** of the following hold:

1. The code is formatted and lint-clean (ruff / Biome) and type-checks strictly (mypy `--strict` / `tsc --strict`).
2. Tests exist at the right layer and pass. Domain logic has property tests where invariants exist.
3. There are no secrets, frames or personal data in code, logs or fixtures.
4. Its **walkthrough** is written and stamped, so `build.py --strict` passes at 100 % coverage with no stale files. New concepts get book prose.
5. Significant decisions have an ADR; design documents are updated if a design changed.
6. CI is green.

---

## Phase 0 — Foundations

**Goal:** a professional monorepo that every later phase builds on.

| Deliverable | Detail |
| :-- | :-- |
| Version control | `git init`; `.gitignore`, `.gitattributes` (LF everywhere), `.editorconfig`; first commit |
| Python toolchain | `uv` installed; uv workspace (root `pyproject.toml`) pinned to **Python 3.13**; members: `services/api`, `services/inference`, `libs/contracts`, `libs/vision`, `ml` (skeleton packages); ruff + mypy + pytest configured at the root |
| Node toolchain | Corepack-pinned **pnpm**; `pnpm-workspace.yaml`; Turborepo; shared `tsconfig` and Biome configuration in `packages/config` |
| Developer commands | A small, dependency-free Python script `tasks.py`, run as `uv run tasks.py <command>`: `check` (everything CI runs), `lint`, `format`, `typecheck`, `test`, `book`. It works identically on Windows, macOS and Linux, unlike Makefiles |
| Local infrastructure | `infra/compose/compose.yaml` with PostgreSQL 18 and Valkey, health checks, named volumes |
| Book tooling | The book builder moves into the uv workspace; `build.py --strict` becomes a CI step |
| CI | GitHub Actions workflow: Python lint, types and tests; JS lint and types; book strict build |
| Docs | README (what, why, quick start); `CONTRIBUTING.md` (Definition of Done, commit style); `SECURITY.md` |
| **Book** | Part 4 begins (Git, uv, pnpm, Turborepo, Docker Compose, CI); Part 5.0 walks every Phase 0 file |

**Exit criteria:**

- On a fresh clone, `uv sync`, `pnpm install` and `uv run tasks.py check` succeed.
- `docker compose up` brings PostgreSQL and Valkey up healthy.
- `build.py --strict` passes at 100 %.
- The CI workflow file is valid.

**Owner actions:** none required. (Optional: create an empty GitHub repository so CI can run remotely.)

---

## Phase 1 — Walking skeleton

**Goal:** demo shop → hosted flow → API → inference (stub) → decision → signed token → demo shop verifies it.

| Area | Deliverables |
| :-- | :-- |
| Contracts | `dwarpal_contracts`: `FaceAnalysis`, `FrameMeta`, `ChallengeSpec`, … |
| API | settings, logging, problem+json, IDs; sessions create/get; flow start/challenge/face-attempts/finish; **decision engine v0** (pure, property-tested); signing keys + JWKS + token issuance; Alembic migrations for sessions, attempts, keys and tokens |
| Inference | FastAPI app, `StubBackend`; real decode + YuNet detection + quality gates (`dwarpal_vision`) |
| Front end | `apps/web` minimal verify flow (camera → capture → upload → result); `apps/demo-shop` minimal; `@dwarpal/js` + `@dwarpal/node` v0 |
| Tests | Unit, integration (Testcontainers) and **Playwright e2e with fake camera** across the whole slice |
| **Book** | Part 5.1: the life of a request, with every new file walked through |

**Exit:** the e2e test passes locally and in CI; a token issued by the API verifies in the demo shop with JWKS.

---

## Phase 2 — ML core

**Goal:** a v1 age model that passes the release gates, served from the registry.

| Area | Deliverables |
| :-- | :-- |
| Data | `ml/datasets.yaml` licence register; fetch and prepare scripts (UTKFace, FairFace, APPA-REAL, FG-NET, AFAD, IMDB-Clean; then AgeDB and LAGENDA); unified manifest; dedup; subject-disjoint train/val/calib/test splits; data report |
| Training | Backbone bake-off (ConvNeXt-V2-T, face-pretrained ViT-B, DINOv2-B); label-distribution loss with safety term; webcam augmentations; MLflow tracking |
| Evaluation | Fixed protocol; FAR-minor per age; adult step-up; fairness; calibration; **MiVOLO baseline comparison** |
| Risk control | Per-(N, ε) thresholds via Clopper–Pearson; manifest output |
| Serving | ONNX export + parity; INT8 evaluation; registry + model card; `OnnxBackend`; shadow mode |
| **Book** | Part 2 written in full (AI from zero, with our real numbers); Part 5.2 walkthroughs |

**Exit:** all gates in `ml/gates.yaml` pass on the test split; model card published; inference p95 within budget on CPU.

**Owner actions:** accept dataset licences and download any that require registration (scripts will print exact instructions).

---

## Phase 3 — Liveness and anti-spoofing

| Area | Deliverables |
| :-- | :-- |
| Client | MediaPipe guidance loop; pose-challenge runner; seizure-safe light sequence; client signals |
| Server | Pose-trajectory verification; light-correlation analysis; MiniFASNet PAD (licence verified, ONNX); injection heuristics; fusion; session and device attempt budgets |
| Red team | Scripted attack suite: printed photo, screen replay, game-render video, payload replay, challenge mismatch, all via fake-camera videos |
| **Book** | Liveness chapters + walkthroughs |

**Exit:** every red-team case is blocked; genuine-attempt false-reject rate measured and documented.

**Owner actions (optional, consented):** record a few attack samples *of yourself* (photo on a phone, printed photo) to enrich the red-team set.

---

## Phase 4 — Platform

| Area | Deliverables |
| :-- | :-- |
| Tenancy and auth | Organisations, users (Argon2id), TOTP, members and roles, console sessions, CSRF |
| Data safety | **RLS** on all tenant tables, with tests proving isolation |
| RP features | API keys (prefixed, hashed, scoped, rotation); policies (versioned, presets); idempotency; rate limits; cursor pagination |
| Events | Outbox + webhook worker (HMAC, retries, SSRF guard, replay); events; token introspection |
| Accountability | Hash-chained audit log + verification job; retention purge; analytics aggregates |
| Contract | Published OpenAPI document; Schemathesis contract tests |
| **Book** | Platform chapters + walkthroughs |

**Exit:** contract and integration suites green; RLS isolation tests green; audit-chain verification green.

---

## Phase 5 — Front-end excellence

| Area | Deliverables |
| :-- | :-- |
| Design system | Tokens (OKLCH), typography, components, motion presets, dark/light |
| Marketing site | 3D face-mesh hero (*Look. Decide. Forget.*), how-it-works, privacy, live accuracy table, developer quick-start, compliance map, FAQ |
| Verify flow | Polished guidance, animations, accessibility, English/Hindi |
| Console | Dashboard, sessions explorer with decision trace, policy editor with projected step-up rate, keys, webhooks, members, audit, model page, command palette |
| Demo shop and SDKs | Polished "Amber Cellars"; `@dwarpal/js`, `@dwarpal/react`, `@dwarpal/node` documented |
| **Book** | Front-end chapters + walkthroughs |

**Exit:** Lighthouse ≥ 90 in all categories on key pages; axe clean; Playwright passes on Chromium, Firefox and WebKit.

---

## Phase 6 — Step-up verifiers

| Order | Deliverables |
| :-: | :-- |
| 1 | **MRZ:** capture UI; MRZ detection + OCR; ICAO 9303 parser (property-tested with ICAO specimen data); face-match model (licence verified); rules; assurance labelling |
| 2 | **Aadhaar Secure QR:** WASM QR decoding; UIDAI specification and certificate verified from official sources; decompression + field parsing + RSA-SHA256 verification; DOB rule; face match; consent screen; India-only policy flag |
| — | **Book:** step-up chapters + walkthroughs |

**Exit:** parsers pass specimen and test vectors; end-to-end step-up flows pass with fake-camera inputs.

**Owner actions:** for Aadhaar testing, use only your own Aadhaar QR (or UIDAI sample data, if published) — never other people's.

---

## Phase 7 — Hardening

| Area | Deliverables |
| :-- | :-- |
| Security | Threat-model review; ZAP baseline scan; Semgrep; pip-audit / pnpm audit; Trivy; secret scanning; CSP/headers verification |
| Observability | OTel end to end; Grafana dashboards (service, ML, security); SLO burn-rate alerts |
| Performance | Locust load tests against the SLOs; tuning (batching, threads, INT8) |
| Privacy | DPIA template filled for the reference deployment; practice statement (ISO/IEC 27566-1 style); final model card |
| Resilience | Fail-closed chaos tests (kill inference/Valkey mid-flow) |

**Exit:** scans clean (or every finding triaged); SLOs met under load; fail-closed tests green.

---

## Phase 8 — Deployment

| Area | Deliverables |
| :-- | :-- |
| Server | VM provisioning script (cloud-init); hardened SSH; ufw; unattended upgrades |
| Running services | Production Compose + Caddy; domains/DNS; GHCR images; CD over SSH with health-gated rollout and rollback |
| Data safety | Backups (restic, encrypted, off-site) and a **restore drill** |
| Operations | Runbooks: deploy, rollback, rotate keys, restore, incident |
| Kubernetes | Helm chart linted in CI |

**Exit:** public HTTPS URL serving the demo shop, verify flow and console; a successful restore drill on record.

**Owner actions:** choose and create the VM account (Oracle free tier or a paid provider), buy or choose a domain, and add DNS records. I prepare everything else and walk you through each click.

---

## Phase 9 — Stretch (only after Phases 0–8)

- **Age Pass:** reusable SD-JWT VC credential stored in the browser, batch-issued for unlinkability.
- **Passkeys** for console login.
- **CGI-render detector** (liveness L6).
- **Python SDK.**
- An optional Kubernetes deployment using the Helm chart.

---

## How the roadmap is followed

1. Each phase starts by refining its task list in the session plan, and ends with a phase report.
2. Work proceeds in small, reviewable commits that each meet the Definition of Done.
3. When reality disagrees with the plan — a measurement, a licence, a library limitation — the plan changes **in writing**: the roadmap, an ADR where needed, and the phase report. It is never silently ignored.
