# Phase 7 report — hardening

**Dates:** from 26 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Status:** 🟡 in progress — fail-closed behaviour and API security headers are built and tested; the threat model, DPIA and practice statement are drafted; scanners, load tests and observability wait for approved downloads ([pending decisions](pending-decisions.md)).

**Exit (from the roadmap):** scans clean (or every finding triaged); SLOs met under load; fail-closed tests green.

## What is built

| Area | Delivered |
| :-- | :-- |
| Fail closed | database or Valkey unreachable → `503 service_unavailable` with `Retry-After: 5` (was a generic `500`); inference down or returning nonsense → `retry`, never `pass` |
| API headers (`http/headers.py`) | `nosniff`, `no-referrer`, `X-Frame-Options: DENY`, `default-src 'none'; frame-ancestors 'none'`, `no-store` unless a route sets its own caching; HSTS (2 years) in production only |
| Documentation pages | `/docs` only outside production (it needs scripts the content policy forbids); `/openapi.json` always published |
| Threat model | `docs/security/threat-model.md`: assets, trust boundaries, STRIDE per component with the test proving each mitigation, age-assurance-specific attacks, eight ranked residual risks |
| Privacy | `docs/privacy/dpia.md` (reference deployment, every data item with its retention and code) and `docs/privacy/practice-statement.md` (ISO/IEC 27566-1 style) — both drafts for legal review |
| Book | §5.7, §5.7.1–5.7.2; one new walkthrough, three re-explained |

| Scans (`tasks.py scan`, `zap`) | pip-audit 2.10.1, Trivy 0.76.0 (on a copy of tracked files), ZAP `zap-stable:20261016` baseline (web) and API scan; Semgrep 1.182.0 wired, waits for its cooldown |
| Traces (`adapters/telemetry.py`) | OpenTelemetry SDK 1.45.1 + FastAPI instrumentation 0.66b1; on only with `DWARPAL_OTEL_ENDPOINT`; query string, caller address and browser blanked; compose profile `observability`: collector 0.163.1 → Tempo 2.10.9 → Grafana 13.0.11 (port 3300) |
| Load test (`infra/load/locustfile.py`) | Locust 2.46.7: 50 users, create → start → challenge → 8-frame attempt; unanalysed attempts count as failures |
| API header | `Cross-Origin-Resource-Policy: same-origin` (from ZAP) |

## What was measured

| Check | Result |
| :-- | :-- |
| Valkey unreachable | `503` + `Retry-After: 5`; `/readyz` → `{"database": "ok", "valkey": "unavailable"}` |
| Inference unreachable / nonsense | two attempts with a passing face: none passes; first is `retry` |
| Headers | present on refusals and successes; JWKS keeps `public, max-age=300`; no CSP on `/docs` |
| Production | HSTS sent; `/docs` → 404; `/openapi.json` → 200 |
| pip-audit (27 Oct) | 47 known flaws in 4 packages: `pillow` 12.3.0 (38, via torchvision), `filelock` 4.1.0 (6), `certifi` 2026.7.22 (2), `setuptools` 84.0.0 (1); `torch`/`torchvision` (CUDA builds) can't be audited — not on PyPI → **D15** |
| Trivy (27 Oct) | `uv.lock`: 30 (24 high, 6 critical) — the same packages; `pnpm-lock.yaml`: none high/critical; **no secrets**, no misconfigurations |
| `pnpm audit` | 8 → 4 after D14: `extract-zip` ×2 (no fix), `body-parser` (fix after 29 Oct), `tmp` 0.2.6 (new advisory; 0.2.7 → **D14b**) — all inside Lighthouse CI, development only |
| ZAP web (27 Oct) | **0 fail**, 64 pass; warnings triaged: CSP `script-src 'unsafe-inline'` (open: needs per-request nonces), COEP missing (not needed: no cross-origin isolation features used), non-storable content and "modern web app" (informational) |
| ZAP API (27 Oct) | **0 fail**, 119 pass; one warning — CORP missing → **fixed** |
| Traces through Tempo | 6 traces stored for 6 requests; span attributes hold route, status, timing; no query string, caller address or browser |
| Load, first run (50 users, 3 min) | 9,256 requests, 0 HTTP failures — **misleading**: inference answered 2,136 "busy", analysed 84 |
| Load, one user (60 s) | face attempt **4.3–4.7 s**; analysis 4.27–4.53 s, of which the age model ≈ 4.0 s (profiled); detection, mesh, hands, anti-spoofing < 0.6 s together |
| Age model threads (one analysis) | 1 thread 4.1–4.5 s · 2 threads 2.3–2.4 s · 4 threads 1.43–1.45 s |
| Frame-count check (28 Oct, `dwarpal_ml.frames`, UTKFace calib, 11,301 faces × 8 simulated webcam frames) | minors passed — 13+: clean 6, best-1 11, best-3 9, all-8 10 (of 373); 16+: 10/13/15/13 (of 274); 18+: 3/4/4/2 (of 383); 21+: 4/3/3/2 (of 503); adults' step-up unchanged; every upper bound within budget → **3 frames adopted** |
| INT8 (dynamic, ONNX Runtime) | 28.2 MB vs 112.5 MB, but 3 faces 793 ms vs 391 ms (1 thread) → **not adopted** |
| Throttling (28 Oct) | laptop on battery, Balanced plan: the same 8-frame script 1.40 s in the foreground, 3.21 s as a background task — all server timings were throttled; comparisons below are like-for-like |
| Load, 3 frames (28 Oct, throttled) | 1 person: analysis 0.93 s (8 frames: 3.33 s); 50 at stress pace: 531 analysed, 83 % busy, analysis p95 1.58 s; 50 at 15–25 s pace: 20 % busy → with a 1 s queue **6 % busy, analysis p95 1.21 s**, whole attempt p95 1.9 s |
| Semgrep 1.182.0 (28 Oct) | 67 findings → 0: actions pinned to commits; pnpm `blockExoticSubdeps`, `trustPolicy: no-downgrade` (two old `semver` versions exempted); `SET ROLE` and `torch.load` reviewed as safe; migrations, memory-pinning advice and a mis-firing cooldown rule excluded with reasons |

## Open items

1. **Scanners** — run and triaged (27–28 Oct); Semgrep clean. Left: Python fixes (D15); `tmp` 0.2.7 (D14b); a nonce-based CSP for the web app.
2. **Performance** — P1 (a) done: 3 frames, a 1 s queue; server processing p95 1.21 s for 50 people at a realistic pace (throttled laptop). **P2 decided (29 Oct)**: NFR-05 means 50 people in a check (an attempt every ~20 s each) — met on the laptop. Open: measuring on the real 4-core server (Phase 8); static INT8; certifying the lines on webcam-degraded images; failures mid-flow under load.
3. **Observability** — traces done; dashboards, metrics (Prometheus, approved, not yet needed) and burn-rate alerts to come.
6. **Process slip**: a local test API key was printed in tool output while preparing the load test; revoked at once.
4. ~~Privacy documents~~ — **drafted 26 Oct**; need legal review (O5) and the operator's contact details (O6). The final model card waits for a calibrated model.
5. ~~Threat-model review~~ — **done 26 Oct**; its top residual risks are the Next.js advisory (D12), the owner-login role switch (Phase 8), and untested presentation attacks.
