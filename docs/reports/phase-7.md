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
4. ~~Privacy documents~~ — **drafted 26 Oct**; need legal review (O5) and the operator's contact details (O6). The final model card waits for a calibrated model.
5. ~~Threat-model review~~ — **done 26 Oct**; its top residual risks are the Next.js advisory (D12), the owner-login role switch (Phase 8), and untested presentation attacks.
