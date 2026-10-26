# Phase 7 report — hardening

**Dates:** from 26 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Status:** 🟡 in progress — fail-closed behaviour and API security headers are built and tested; scanners, load tests and observability wait for approved downloads ([pending decisions](pending-decisions.md)).

**Exit (from the roadmap):** scans clean (or every finding triaged); SLOs met under load; fail-closed tests green.

## What is built

| Area | Delivered |
| :-- | :-- |
| Fail closed | database or Valkey unreachable → `503 service_unavailable` with `Retry-After: 5` (was a generic `500`); inference down or returning nonsense → `retry`, never `pass` |
| API headers (`http/headers.py`) | `nosniff`, `no-referrer`, `X-Frame-Options: DENY`, `default-src 'none'; frame-ancestors 'none'`, `no-store` unless a route sets its own caching; HSTS (2 years) in production only |
| Documentation pages | `/docs` only outside production (it needs scripts the content policy forbids); `/openapi.json` always published |
| Book | §5.7, §5.7.1; one new walkthrough, three re-explained |

## What was measured

| Check | Result |
| :-- | :-- |
| Valkey unreachable | `503` + `Retry-After: 5`; `/readyz` → `{"database": "ok", "valkey": "unavailable"}` |
| Inference unreachable / nonsense | two attempts with a passing face: none passes; first is `retry` |
| Headers | present on refusals and successes; JWKS keeps `public, max-age=300`; no CSP on `/docs` |
| Production | HSTS sent; `/docs` → 404; `/openapi.json` → 200 |

## Open items

1. **Scanners** (Semgrep, pip-audit, pnpm audit, Trivy, ZAP) — D9.
2. **Load tests against the SLOs**, and failures **mid-flow under load** — D10.
3. **Observability** (OpenTelemetry, Grafana, burn-rate alerts) — D11.
4. **Privacy documents**: DPIA template, practice statement, final model card — can be drafted without downloads; scheduled next.
5. **Threat-model review** of everything since Phase 3 — can be done without downloads; scheduled next.
