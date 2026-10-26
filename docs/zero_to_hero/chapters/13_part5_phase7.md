## 5.7 Phase 7 — hardening

Phases 1–6 make Dwarpal work. Phase 7 makes it hold up: under attack, under load, and when the things it depends on fail. From the roadmap (§3.9):

| Area | What | Status |
| :-- | :-- | :-- |
| Resilience | **Fail closed**: kill a dependency mid-flow, and nothing may pass | ✅ §5.7.1 |
| Security | Headers and content policy verified; scanners (Semgrep, pip-audit, Trivy, ZAP); threat-model review | 🟡 headers ✅ (§5.7.1); scanners wait for approved downloads |
| Observability | OpenTelemetry end to end, dashboards, alerts | 🗓 waits for approved downloads |
| Performance | Load tests against the service levels (Locust) | 🗓 waits for an approved download |
| Privacy | A filled DPIA template, a practice statement, the final model card | 🟡 drafts (§5.7.2); model card waits for a calibrated model |

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

### 5.7.2 Writing down the threats, and the promises

Two kinds of document matter as much as code for an age-assurance service.

**The threat model** (`docs/security/threat-model.md`) lists what must be protected — the age decision above all, then faces, keys, tenant data and audit history — and where the trust boundaries lie. It then walks through each component with **STRIDE**, a checklist of six kinds of threat: **S**poofing, **T**ampering, **R**epudiation, **I**nformation disclosure, **D**enial of service and **E**levation of privilege. Every mitigation names the test that proves it. A mitigation with no proof is listed as a gap, and the gaps are ranked: first the Next.js advisory, then the database login's role switch, then the presentation attacks nobody has tried yet.

**The privacy documents** (`docs/privacy/`) are a **DPIA** — the data-protection impact assessment that UK and EU law require before processing like this, and that Ofcom and the ICO jointly asked age-assurance providers for — and a **practice statement** in the style of ISO/IEC 27566-1, which tells websites and regulators how the system decides, how well it performs, and what it does with data. Each data item in the DPIA names its retention period and the code that enforces it. Both are drafts: the legal roles, the lawful basis and the wording need a lawyer's review for each country.

!!! honest "Honest limitation"
    Documents can be wrong in ways tests can't catch. They are kept honest by pointing at code and tests, and by review triggers in the threat model, but a legal review is still essential before any real launch.
