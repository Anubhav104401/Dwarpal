## 5.7 Phase 7 — hardening

Phases 1–6 make Dwarpal work. Phase 7 makes it hold up: under attack, under load, and when the things it depends on fail. From the roadmap (§3.9):

| Area | What | Status |
| :-- | :-- | :-- |
| Resilience | **Fail closed**: kill a dependency mid-flow, and nothing may pass | ✅ §5.7.1 |
| Security | Headers and content policy verified; scanners (Semgrep, pip-audit, Trivy, ZAP); threat-model review | 🟡 headers ✅ (§5.7.1); scanners wait for approved downloads |
| Observability | OpenTelemetry end to end, dashboards, alerts | 🗓 waits for approved downloads |
| Performance | Load tests against the service levels (Locust) | 🗓 waits for an approved download |
| Privacy | A filled DPIA template, a practice statement, the final model card | 🗓 |

### 5.7.1 Failing closed, and telling browsers what not to do

**Failing closed** means that when something goes wrong, the system refuses rather than allows. For an age gate this matters more than anything: a broken component must never become an open door.

- **When the inference service is down, or answers nonsense,** the API has no analysis, and "no analysis" can only become *retry* — never *pass* (Phase 1's rule, now tested against a dead service and a garbled one).
- **When the database or Valkey can't be reached,** the API now answers `503 service_unavailable` with `Retry-After: 5`, as its published contract promises, instead of a generic `500`. `/readyz` says exactly which dependency is missing.

**Security headers.** The web pages already had a strict content policy. The API, which serves only JSON, now tells browsers on every answer: never guess its type (`nosniff`), never frame it, never load or run anything from it, never cache it unless a route allows it, never tell other sites where a request came from — and, in production, to use only HTTPS for two years (HSTS). The interactive documentation pages, which need scripts, exist only outside production; the API document itself is always published.

!walk services/api/src/dwarpal_api/http/headers.py

The rest changed existing files, each re-explained in its walkthrough: `http/problems.py` (the `503` handler), `main.py` (the headers, documentation only outside production) and `test_api.py` (the fail-closed and header tests).

**What the tests prove**: with Valkey unreachable, creating a session gets `503` with `Retry-After` and readiness names Valkey; with the inference service down, or answering nonsense, two attempts with a real adult face are both refused passage, the first as `retry`; every answer carries the headers, while the public key set keeps its own caching rule; production sends HSTS and serves no interactive documentation.

!!! honest "Honest limitation"
    These tests break one dependency before a request starts. The roadmap also asks for failures **mid-flow** — a dependency dying between two steps of one attempt — under load; that needs the load-testing tools awaiting approval.
