## 5.7 Phase 7 — hardening

Phases 1–6 make Dwarpal work. Phase 7 makes it hold up: under attack, under load, and when the things it depends on fail. From the roadmap (§3.9):

| Area | What | Status |
| :-- | :-- | :-- |
| Resilience | **Fail closed**: kill a dependency mid-flow, and nothing may pass | ✅ §5.7.1 |
| Security | Headers and content policy verified; scanners (Semgrep, pip-audit, Trivy, ZAP); threat-model review | 🟡 headers ✅ (§5.7.1); every scanner run and triaged (§5.7.3–5.7.4); Python fixes wait for D15 |
| Observability | OpenTelemetry end to end, dashboards, alerts | 🟡 traces from the API to Tempo and Grafana, with nothing about the person (§5.7.3); dashboards and alerts to come |
| Performance | Load tests against the service levels (Locust) | 🟡 analysis p95 1.2 s at a realistic load (§5.7.4); 50 *simultaneous* attempts on 4 cores still out of reach |
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

### 5.7.3 Scanning, tracing, and a load test that failed

The owner approved the Phase 7 tools (decisions D9–D11). Each now runs from `tasks.py`, as a tool in a throwaway environment of its own, still under the 7-day cooldown:

- `scan` runs pip-audit, Semgrep and Trivy;
- `zap` runs OWASP ZAP against running servers;
- `load` runs Locust.

**The scans.**

- **pip-audit** and **Trivy** agree: four locked Python packages have known flaws (`pillow`, `certifi`, `filelock`, `setuptools`).
    - Most come in through PyTorch, which is used for training, not by the services.
    - Fixed versions exist and pass the cooldown, but installing them is a new download (decision D15).
- **Trivy** found no committed secrets and no unsafe container settings.
- **ZAP** found **no failures**: 64 checks passed on the web app, 119 on the API.
- **Semgrep** waits: the approved version (1.182.0) came out on 20 Oct at 20:32 UTC, and the cooldown counts to the minute.

Every ZAP warning was weighed:

- the API now sends `Cross-Origin-Resource-Policy`;
- the web app's content policy still allows inline scripts, which Next.js needs unless each page gets a per-request *nonce* — an open item;
- the rest are informational.

**Traces.** With `DWARPAL_OTEL_ENDPOINT` set, the API sends one trace per request to an OpenTelemetry collector, which passes it to **Tempo**; **Grafana** shows them (`--profile observability` in the compose file). By default the instrumentation records the full address *with its query string*, the caller's network address and their browser. Each of those identifies a person or could carry a secret. The module overwrites them. A test proves none of them survives; a real run through Tempo showed the same.

!!! key "Key idea — measure the right thing"
    The first load test looked healthy: 9,256 requests, none failed, a median face attempt of 0.69 seconds. But the inference service had answered *2,136* requests with "busy" and analysed only *84*. Each "busy" became a quick, safe *try again* — and Locust counted it as a fast success. The test now marks an attempt that wasn't analysed as a failure. A load test that measures how quickly a system refuses work says nothing about how quickly it does it.

**The result.** Alone, with nothing else running, **one face attempt takes about 4.5 seconds**: the age model alone takes about 4 s of it, eight faces through ConvNeXt-Tiny on one CPU thread. The design's target is 1.5 seconds at the 95th percentile, with 50 people at once, on 4 cores. With 4 threads one attempt takes 1.4 s, but 50 people would then share those 4 cores, so threads alone can't meet the target. The work per attempt has to shrink:

- age only the best few frontal frames instead of all eight;
- a smaller or quantised (INT8) model, re-checked against the release gates;
- or a GPU.

Each changes accuracy or cost, so it is the owner's decision (P1).

!walk infra/load/locustfile.py

!walk services/api/src/dwarpal_api/adapters/telemetry.py

!walk services/api/tests/test_telemetry.py

!walk infra/scripts/committed_copy.py

!walk infra/observability/collector.yaml

!walk infra/observability/tempo.yaml

!walk infra/observability/grafana-datasources.yaml

The rest changed existing files, each re-explained in its walkthrough:

- the tasks (`tasks.py`);
- the API's dependencies, settings, start-up and headers;
- its header test;
- the compose file;
- `.gitignore`;
- the book's `book.toml`, which now skips the scans' output folder.

One slip, recorded honestly: while preparing the load test, a local *test* API key was printed in a tool's output. It was revoked at once (`cli revoke-key`), and the load test used a fresh key that was never shown.

!!! honest "Honest limitation"
    The load test ran on a 32-thread computer, not the 4-core machine the target names. The inference service limits itself to 4 analyses at a time, so the comparison is fair for one person but not exact. There are no dashboards or alerts yet. Semgrep hasn't run. And the scans' Python findings stay open until D15 is decided.

### 5.7.4 Making an attempt fast enough — and learning to measure it

The owner chose how to attack the 4.5 seconds (decision P1): first let the age model see fewer frames, check that the safety lines still hold, then try INT8 if needed.

**Fewer frames.** The age model now sees only the **3 sharpest** of an attempt's flawless frames (`age_frames`); liveness still sees every frame, and every flawless frame still counts as usable.

The safety lines were certified on one clean photo per person, so `dwarpal_ml.frames` checked the change on the calibration split's 11,301 exact-age faces. Each face became a burst of 8 webcam-like frames (the training augmentations), and the decisions were compared:

| Age line (risk budget) | clean photo | sharpest 1 | sharpest 3 | all 8 |
| :-- | :-: | :-: | :-: | :-: |
| 13+ (0.15) — minors passed, of 373 | 6 | 11 | 9 | 10 |
| 16+ (0.15) — of 274 | 10 | 13 | 15 | 13 |
| 18+ (0.075) — of 383 | 3 | 4 | 4 | 2 |
| 21+ (0.075) — of 503 | 4 | 3 | 3 | 2 |

Three frames and eight differ by one or two people per line — chance, at these numbers. Adults asked to step up were unchanged, and every upper bound stayed within its budget. One thing the table shows that nobody had measured: webcam-like damage itself passes a few more minors at 13+ and 16+ than clean photos. The lines were certified on clean photos; certifying them on degraded ones would be more honest, and is now an open item.

**INT8.** ONNX Runtime's *dynamic* quantisation made the model four times smaller but **twice as slow** (0.79 s against 0.39 s for 3 faces). It stores the weights in 8 bits but converts every input at run time, and it leaves ConvNeXt's depthwise convolutions alone. So it was not adopted. *Static* quantisation might do better, but it needs calibration data and a full pass through the release gates.

!!! real "Real world — the laptop was slowing its own work down"
    Measured as a plain script, 8 frames took 1.4 seconds — but 3.3 seconds inside the server, and 4.5 the evening before. The same script, started as a *background* task, took 3.2 seconds. The owner's laptop was on battery, with Windows' balanced power plan, and Windows runs background work on its slower, power-saving cores. Every server measurement had been taken that way. The lesson: compare settings only under identical conditions — which the numbers below are — and measure the real target on the real machine (Phase 8's 4-core server).

**A short queue.** Under load, the inference service turned work away the instant its 4 workers were busy. People arrive at random, so even at a gentle pace one in five attempts arrived at a busy moment and was refused. It now waits up to `queue_s` (1 second) for a free worker before saying "busy".

**The results**, all on the same throttled laptop, one face attempt at a time per simulated person:

| Load | analysed | refused as busy | analysis p50 / p95 | whole attempt p95 |
| :-- | :-: | :-: | :-: | :-: |
| 1 person, 8 frames | all | — | 3.3 s | 3.7 s |
| 1 person, 3 frames | all | — | 0.93 s | 1.05 s |
| 50 people, 1–3 s apart (stress), 3 frames | 531 | **83 %** | 1.31 / 1.58 s | — |
| 50 people, 15–25 s apart, 3 frames, no queue | 351 | 20 % | 0.97 / 1.23 s | 1.4 s |
| 50 people, 15–25 s apart, 3 frames, 1 s queue | 407 | **6 %** | 1.01 / **1.21 s** | 1.9 s |

!!! key "Key idea — a target needs its load spelled out"
    "50 concurrent attempts" can mean 50 people in the middle of a check — each sending one attempt every 20 seconds or so — or 50 attempts arriving in the same instant. The first is now met for the server's processing (p95 1.21 s, under 1.5 s), on a throttled laptop. The second would need about 50 × 1 s of computing within 1.5 s: some 30 cores, not 4. No setting closes that gap; only a GPU, or more machines, could. The design's sentence has to say which it means — a decision for the owner.

**Semgrep** could finally run (its approved version was past the cooldown). Of its 67 findings:

- **Hardened**:
    - the CI actions are pinned to exact commits, not movable tags;
    - pnpm refuses packages from outside the registry and versions that drop their provenance.
- **False alarms, reviewed and marked**:
    - `SET ROLE` with a checked role name;
    - a PyTorch load that already refuses pickled code.
- **Left out of the scan on purpose, with the reason in `tasks.py`**:
    - the migrations' fixed SQL;
    - memory-pinning advice;
    - a cooldown rule that missed ours.

It now reports **0 findings**.

!walk ml/src/dwarpal_ml/frames.py

The rest changed existing files, each re-explained in its walkthrough: the pipeline and its settings, the inference service's queue and its test, the load test's pace, the scan task, the CI workflow, `pnpm-workspace.yaml`, the database adapter and the anti-spoofing loader.

!!! honest "Honest limitation"
    Every timing here comes from a laptop on battery, throttling background work; they compare settings fairly, but say little about the 4-core server the target names. The frame check used simulated webcam damage on the calibration split, not real webcam bursts, and its counts are small. The whole attempt — including the wait for a worker — reached p95 1.9 s at a realistic pace; only the server's processing is under 1.5 s.
