# Stage 2 — Solution Options & Recommendation

**Project:** Dwarpal — AI age assurance for protecting minors (working name)
**Document status:** Draft for owner confirmation · 15 Oct 2026
**Builds on:** [01_problem_analysis.md](01_problem_analysis.md) — read §5 ("why this is hard") first; every decision below answers one of those problems.

**How to read this.** Each decision area lists the realistic options, scores them against the same criteria, and ends with a **verdict**. §19 assembles the verdicts into one blueprint. §23 lists the four decisions that are yours to make.

**Criteria used throughout:** 🛡 *Safety* (keeps minors out) · 🔒 *Privacy* · ⚙️ *Feasibility* (one developer, an RTX 4070 Laptop, public data) · 🏢 *Enterprise-readiness* (secure, operable, scalable) · 💰 *Cost* · 🎓 *Explainability* (can every line be taught in the Zero-to-Hero book?).

---

## D1. What shape is the product?

| Option | Description | 🛡 | 🔒 | ⚙️ | 🏢 | Verdict |
| :-- | :-- | :-: | :-: | :-: | :-: | :-- |
| A. Client-side age-gate widget | JS widget estimates age in the browser and tells the page "ok" | ❌ trivially bypassed (edit the JS) | ✅ | ✅ | ❌ | Rejected — a gate the user controls is not a gate |
| **B. Hosted age-assurance platform (B2B)** | Websites create a verification session; users complete a hosted flow; the site receives a **signed** result | ✅ | ✅ (by design) | ✅ | ✅ | **Core of the solution** — this is how Yoti, Persona, Stripe Identity and k-ID work, and what regulators audit |
| C. Device-side guardian (parental control) | Browser extension/desktop agent that checks who is at the keyboard and blocks categories | ⚠️ bypassable by the device owner | ⚠️ camera on the home device | ✅ | ⚠️ | **Optional add-on** (stretch); reuses B's models |
| D. Content classifier | Detect whether *content* is adult | n/a | — | — | — | Out of scope — different problem (content moderation) |

**Verdict:** **B**, plus a **demo relying-party site** that proves the integration end-to-end. C is a stretch goal (owner's choice, §23).

---

## D2. Which signal tells us age?

| Signal | Accuracy near 13–18 | Friction | Privacy | Spoof resistance | Verdict |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **Face, multi-frame video (≈ 2–4 s)** | Good outside buffer zones; best-studied | Low | Medium (biometric, but not identification) | Good with liveness | **Primary** |
| Face, single photo | Lower (no averaging, no liveness) | Lowest | Medium | Poor | Rejected as primary (used only inside multi-frame) |
| Voice | Weaker, scarce data | Medium | Medium | Poor (TTS/voice cloning) | Rejected |
| Hand image | Research-stage | Medium | Medium | Unknown | Rejected |
| Behaviour / text inference | Probabilistic, slow to accumulate | None | **Poor** (profiling — DPDP bans profiling children) | Medium | Rejected for v1 |
| ID document | Exact DOB (if authentic) | High | **Poor** (full identity) | Depends on forensics | **Fallback** |
| Digital credential (EU wallet, DigiLocker token) | Exact | Low once available | **Excellent** (selective disclosure) | Strong (cryptographic) | **Future fallback** (ecosystems still rolling out) |
| Email/financial signals | Indirect | Low | Poor (third-party data) | Medium | Rejected (needs commercial data deals) |

**Verdict:** a **waterfall** — *multi-frame facial estimation* first; a *stronger verifier* only when estimation is unsure. This is the Australian trial's "layered" model, and it is how Ofcom expects buffers to work.

---

## D3. Where does the AI run?

| Option | 🛡 Trust | 🔒 Privacy | Notes | Verdict |
| :-- | :-- | :-- | :-- | :-- |
| Client only (browser ML) | ❌ result forgeable — no hardware attestation exists for browser JS | ✅ face never leaves device | Fine for parental-control mode, not for a regulated gate | Rejected for the gate |
| Server only | ✅ | ⚠️ face travels to server (encrypted) and is processed in memory | No real-time guidance → more bad captures | Partial |
| **Hybrid** | ✅ server decides | ✅ minimised: only a short burst of frames is sent, held in RAM, never stored | Browser ML (MediaPipe Face Landmarker) gives *real-time guidance* (framing, light, pose challenge tracking); the server re-checks everything | **Chosen** |

**Principle:** *the client guides, the server decides.* Nothing the browser says is trusted. Every check the browser does is repeated on the server from the raw frames.

---

## D4. The age model — the heart of the system

### D4.1 Approach

| Option | Description | Reported quality | Problems | Verdict |
| :-- | :-- | :-- | :-- | :-- |
| a. Off-the-shelf open libraries (DeepFace, InsightFace `genderage`, OpenCV `age_net`, HF ViT on FairFace) | Download and call | MAE often 5–10 y; age *bins* for some; **39–100 % of minors classified adult** in the 2026 benchmark | Unsafe for a gate; several are non-commercial | Rejected (kept as benchmark baselines only) |
| b. Commercial cloud APIs (AWS Rekognition age range, etc.) | Send faces to a vendor | Wide ranges, not tuned for gates | Faces leave our infrastructure; cost; lock-in; not "our AI" | Rejected |
| c. Zero-shot vision-language models (e.g. Gemini 3 Flash) | Prompt a large multimodal model | Best generalist MAE (~4.3 y in 2026 benchmark) but **16–29 % minors → adult** | Privacy (third-party), latency (seconds), cost per check, non-determinism, prompt-injection surface | Rejected for production. Noted as a future *distillation teacher* idea |
| **d. Our own specialist, fine-tuned from a strong pre-trained backbone** | Train on combined public datasets with a gate-aware objective, uncertainty and calibration | Target: competitive MAE, and above all low **FAR-minor** | Data licences (research-only → demo weights); training work | **Chosen** |
| e. MiVOLO (face+body ViT, strongest open specialist) | Use published checkpoints | Face-only VOLO-D1 ≈ 4.2 y MAE (UTKFace protocol) | Body branch irrelevant for selfies; its bundled YOLOv8 detector is AGPL; weight terms need checking; not trained for gates | **Benchmark baseline** we must beat |

### D4.2 Backbone — decided by experiment, not opinion
We will run the *same* recipe on a short list and pick by **FAR-minor at the policy gate**, then by latency:

| Candidate | Why it's on the list | Licence (verify at download) |
| :-- | :-- | :-- |
| ConvNeXt-V2-Tiny | Fast and CPU-friendly; strong ImageNet-22k pre-training; exports cleanly to ONNX/INT8 | Apache-2.0 / timm |
| ViT-B/16 with face pre-training (FaRL) | Evidence (WACV 2026) that **face-specific pre-training beats generic pre-training** for age (UTKFace MAE 4.84 → ~4.1 with large face pre-training) | Check |
| DINOv2 / SigLIP-2 ViT-B | Strongest general self-supervised/contrastive features | Apache-2.0 |
| EfficientNet/MobileNetV4 (student) | Tiny distilled student for CPU and browser | Apache-2.0 |

### D4.3 Output head and loss
- **Predict a full probability distribution over ages 0–100** (label-distribution learning; targets are Gaussians centred on the true age). Why: the distribution gives the expected age, the uncertainty (its width) and **P(age ≥ N) for any N** — one model serves 13/16/18/21 policies.
- Loss = KL divergence to the label distribution + L1 on the expected age. This is the DLDL-v2 family. A careful 2024 study (Paplham & Franc, CVPR) found specialised age losses matter far less than backbone and data, so we pick the one that gives us **distributions**, not the one with the fanciest name.
- **Safety-weighted term (experiment):** extra penalty on probability mass above N for training samples just below N (ages 13–17). This measures whether we can buy FAR-minor cheaply at the training stage.
- **Temperature scaling** after training, so probabilities mean what they say (calibration).

### D4.4 From many frames to one answer
- Each accepted frame → age distribution, plus a horizontally-flipped view (test-time augmentation).
- **Quality-weighted mixture** of the frame distributions (sharper, frontal, well-lit frames count more).
- Disagreement between frames is itself a signal. High spread → `retry` or `step_up`.

### D4.5 The decision rule — risk-controlled, not hand-picked (key idea)
Instead of "pass if estimate ≥ 25" with a magic 25, we state a **risk budget** and let calibration data choose the threshold:

1. Score every session with `s = P(age ≥ N)` from the aggregated distribution.
2. On a held-out **calibration set of minors in the hard band** (e.g. ages 13–17 for N = 18), count how many would pass at each candidate threshold τ.
3. Choose the **smallest τ whose one-sided Clopper–Pearson upper confidence bound on FAR-minor is ≤ ε** (e.g. ε = 2 %, confidence 1 − δ = 95 %), **for every exact age in the band and every demographic group with labels**, and take the most conservative.
4. A second, lower threshold τ_fail is chosen so that **adults are almost never hard-failed** (they get `step_up` instead).

Result: **"With 95 % confidence, at most 2 % of 13–17-year-olds in the calibration distribution pass this gate."** That is a statistical guarantee in the family of conformal risk control / learn-then-test, rather than a vibe. *Honest caveat:* it holds for the calibration distribution (dataset photos), not automatically for webcam selfies. We add an extra margin, gate on capture quality, and monitor pass-rate drift. The book explains all of this.

### D4.6 Deployment form
- Export to **ONNX**, run with **ONNX Runtime** (CPU by default, CUDA optional). Optimise with **INT8 quantisation**, which ships only if the gate metrics do not regress.
- A distilled **student model** for CPU latency.

---

## D5. Finding and aligning the face

| Option | Where | Licence | Verdict |
| :-- | :-- | :-- | :-- |
| **YuNet** (`cv2.FaceDetectorYN`) | Server | MIT (OpenCV Zoo) | **Server detector** — tiny, fast, gives 5 landmarks for alignment |
| **MediaPipe Face Landmarker** (478 landmarks + head pose) | Browser (WASM/GPU) and optionally server | Apache-2.0 | **Browser guidance + challenge tracking**; server re-verification of pose |
| RetinaFace / SCRFD | Server | Code permissive; *InsightFace weights non-commercial* | Rejected (licence) |
| YOLOv8-face | Server | AGPL-3.0 | Rejected (licence contagion) |
| MTCNN | Server | Old, slow | Rejected |

Alignment: a similarity transform from the 5 landmarks to a canonical template, then a fixed crop with margin. The exact same function is used in training and serving to avoid **train/serve skew**.

---

## D6. Liveness and anti-spoofing — layered defence

No single check survives modern attacks: Discord's "open your mouth" check fell to a game's photo mode. We fuse **independent** signals:

| Layer | What it catches | Implementation | Verdict |
| :-- | :-- | :-- | :-- |
| L1 **Capture-quality gate** | Garbage-in (blur, darkness, tiny faces, multiple faces) | Laplacian variance, exposure stats, face size, pose angles | ✅ |
| L2 **Passive PAD** | Prints, screens, some masks | MiniFASNet ensemble (Apache-2.0, ~4 MB, < 10 ms CPU), evaluated on public PAD sets | ✅ |
| L3 **Randomised active challenge** | Static photos, pre-recorded video | Server issues a random sequence (e.g. "turn left → look up → closer") with a one-time nonce. The server verifies the head-pose trajectory from the frames' landmarks, time-aligned to the schedule | ✅ |
| L4 **Screen-light reflection challenge** *(novel for an open project)* | Replays, virtual-camera injection, game renders that can't predict the colours | The screen shows a **random, gentle colour sequence** (seizure-safe, < 3 changes/s). The server checks that the face skin's chroma shifts correlate with that secret sequence in time | ✅ as a *soft* signal (weak in bright sunlight) |
| L5 **Injection heuristics** | Virtual cameras, automation | Track settings, known virtual-camera labels, `navigator.webdriver`, frame-timing jitter, nonce binding | ✅ (weak alone; useful in the fusion) |
| L6 **CGI/render detector** | Game characters, 3D avatars | Small classifier trained on openly-licensed renders (e.g. Blender + CC0 assets) vs real faces | Stretch |
| L7 Deepfake detector | Real-time face swaps | Research-grade; generalises poorly | Deferred (pluggable slot) |

The outputs are fused into a **liveness risk score**, which the policy engine maps to `continue` / `step_up` / `reject`. Raw scores are recorded (never the frames), so thresholds can be tuned from aggregate statistics.

---

## D7. Decision policy

| Option | 🛡 | Usability | Verdict |
| :-- | :-- | :-- | :-- |
| Fixed threshold on point estimate ("≥ 18") | ❌ ~half of 17-year-olds near the line pass | ✅ | Rejected |
| Hand-picked Challenge-T buffer ("≥ 25") | ✅ (industry baseline) | ⚠️ many 18–24s blocked | Baseline / comparison |
| **Risk-controlled three-outcome gate** (D4.5) + attempt limits + step-up | ✅ provable budget | ✅ adults in the buffer get a route | **Chosen** |

Outcomes: `pass` · `step_up` (estimation unsure → stronger method) · `fail` (confidently under) · `retry` (quality problem, with guidance) · `reject` (suspected attack). The policy is **versioned**, with presets per regime: UK OSA 18+, EU DSA, US state 18+/21+, Australia 16+, India DPDP 18+. Attempt limits stop "retry until it passes": every retry raises the bar.

**Fail-closed rule:** any exception, timeout or missing signal resolves to `retry`/`step_up`, **never** `pass`.

---

## D8. Step-up (fallback) verification

| Option | Assurance | Effort | Notes | Verdict |
| :-- | :-- | :-- | :-- | :-- |
| **Pluggable verifier interface** | — | Low | Every verifier (document, credential, …) implements one contract; the policy chooses which are allowed | ✅ Always |
| ID document — MRZ (passports/ID cards) | Basic–Standard | Medium | OCR the machine-readable zone, validate ICAO 9303 check digits, read DOB; optional selfie↔portrait match. *Without chip reading (impossible in browsers) or forensics, a printed fake MRZ can pass*, so we label the assurance honestly | Owner's choice (§23) |
| Aadhaar Secure QR (India) | Strong DOB authenticity (UIDAI digital signature) | Medium | Verify UIDAI's signature offline, read DOB/YoB, discard the rest. Legally sensitive: never store, explicit consent, Aadhaar rules apply. Needs a selfie↔QR-photo match to stop using a parent's card | Owner's choice (§23) |
| Digital credentials (OpenID4VP + SD-JWT VC / ISO mdoc "age_over_18") | Strong, privacy-preserving | Medium-High | Matches the EU blueprint and wallets; ecosystem still rolling out (end-2026). Natural v2 alongside our own reusable "Age Pass" | v2 |
| Mock verifier only | — | Lowest | Lets us finish the core first | Owner's choice (§23) |

---

## D9. Delivering the answer to the website

| Option | 🛡 | 🔒 | Verdict |
| :-- | :-- | :-- | :-- |
| Redirect with `?result=pass` | ❌ forgeable | — | Rejected |
| Unsigned webhook | ❌ spoofable | — | Rejected |
| **Signed age token** (JWS, **EdDSA/Ed25519**) + **JWKS** + server-side result API + **HMAC-signed webhooks** | ✅ verifiable offline; key rotation via `kid` | ✅ minimal claims | **Chosen** |
| Reusable credential in the user's browser (SD-JWT VC, batch-issued for unlinkability) | ✅ | ✅✅ | v2 "Age Pass" |
| Zero-knowledge proofs (e.g. Google's open-sourced longfellow-zk) | ✅ | ✅✅✅ | Research watch-list |

**Token claims (minimal):** `iss`, `aud` (the RP project), `iat`/`exp` (short), `jti` (one-time), `nonce` (from the RP), `sid` (session), `age_over_18: true` (ADR-0020), `outcome: "pass"`, `assurance`, `methods`, `policy_version`, `model_version`. **Never:** estimated age, image data, any stable user identifier.

**Integration flow (the Stripe Identity / OAuth-code pattern):**
1. RP backend `POST /v1/verification-sessions` (secret API key) → `{id, client_secret, url}`.
2. RP front end opens the flow — SDK modal (iframe/popup) or full redirect.
3. User completes the hosted flow.
4. RP is notified three ways: browser event / redirect (carries **only the session id**), signed webhook, or result-API fetch. It trusts **only** the server-side result or the signature-verified token.

---

## D10. Backend architecture

| Option | Pros | Cons | Verdict |
| :-- | :-- | :-- | :-- |
| Single monolith (one FastAPI app incl. ML) | Simplest | CPU-heavy inference starves the API; one blast radius; images and business data share a process | Rejected |
| **Modular monolith API + dedicated inference service + background worker** | Clear domain modules; inference scales separately (CPU/GPU); a smaller "biometric perimeter"; a one-person team can operate it | Two deployables to version together | **Chosen** |
| Full microservices (auth, sessions, billing, webhooks, inference each separate) | Independent scaling | Ops overhead, distributed transactions, overkill for one developer | Rejected |
| Event-driven backbone (Kafka) | Decoupling at scale | Heavy infrastructure for our load | Rejected (a Valkey-backed job queue + transactional outbox is enough) |

**Inside the API:** *hexagonal / ports-and-adapters* layering — `domain` (pure rules: policy engine, risk control, token claims) ← `application` (use cases: create session, submit capture, issue token) ← `adapters` (FastAPI routers, SQLAlchemy repositories, inference HTTP client, Valkey). Pure domain code can be unit-tested in milliseconds without any server.

**Language: Python 3.13 for both services.** The ML ecosystem lives there, both services share typed contracts, and the book teaches one language for the whole backend. Throughput is bound by inference, not by the HTTP layer, so Go or Rust would buy little here.

| Concern | Choice (current version) | Why / alternatives |
| :-- | :-- | :-- |
| Web framework | **FastAPI 0.143** + **Pydantic 2.14** | Async, typed, auto OpenAPI 3.1. *Alt:* Litestar (good, smaller ecosystem), Django (heavier, sync-first) |
| ASGI server | **Uvicorn 0.54** | Standard. *Alt:* Granian (Rust, faster; worth a benchmark later) |
| ORM / migrations | **SQLAlchemy 2.1** (async, asyncpg) + **Alembic 1.20** | Mature, explicit. *Alt:* SQLModel (thin layer), Tortoise (less mature) |
| Jobs | **arq 0.28** (asyncio, Valkey) + transactional **outbox** for webhooks | *Alt:* Celery (heavy, sync-first), Dramatiq, Taskiq |
| Tokens / keys | **joserfc 1.7** (JWS/JWK/JWKS, EdDSA) + **cryptography 50** | *Alt:* PyJWT (fine, less JWK-set ergonomic) |
| Passwords / 2FA | **argon2-cffi** (Argon2id), **pyotp** TOTP; passkeys via **webauthn 3** (stretch) | Industry-standard primitives, no home-made crypto |
| Logging | **structlog 26** (JSON), biometric-free by construction | |
| Telemetry | **OpenTelemetry 1.45** + Prometheus client | Vendor-neutral |
| Quality | **uv 0.13** workspace, **ruff 0.17**, **mypy 2.4 (strict)**, **pytest 9** | |

---

## D11. Data stores

| Need | Choice | Why |
| :-- | :-- | :-- |
| System of record (tenants, sessions, policies, audit, outbox) | **PostgreSQL 18** | Transactions, JSONB, **row-level security** for tenant isolation, native `uuidv7()` for time-ordered IDs |
| Ephemeral state (challenge nonces, rate limits, job queue, console sessions) | **Valkey 9** (BSD-licensed Redis fork) | Speed + TTLs. Chosen over Redis 8 (AGPL/RSAL) to keep licensing clean |
| Model artefacts | Local registry volume (`models/registry/<name>/<version>/` + signed manifest); S3-compatible later | Hash-pinned, rollback-able |
| **Biometric images** | **None — by design** | There is no table, bucket or log sink where a frame could land |

---

## D12. Front end — "exceptionally beautiful", and fast

| Layer | Choice (current) | Why / alternatives considered |
| :-- | :-- | :-- |
| Framework | **Next.js 16.4** (App Router, React **19.3**, Server Components, Turbopack) | Largest ecosystem, first-class with shadcn/ui and Vercel. *Alt:* SvelteKit 2 (lovely, smaller ecosystem), React Router 7 framework mode, Nuxt 4, Astro 5 (great for marketing pages only) |
| Language | **TypeScript** (strict) | |
| Styling | **Tailwind CSS 4.3** (CSS-first config, OKLCH colours) | |
| Components | **shadcn/ui** (Radix primitives, copy-in components) + a custom design system; selected **Magic UI / Aceternity-style** effects for marketing only | Accessible primitives; we own the code |
| Motion | **Motion 14** (formerly Framer Motion) for UI; **GSAP 3.15** (now free incl. plugins) + **Lenis** for scroll storytelling | |
| 3D | **three.js 0.186** + **React Three Fiber 9.8** + drei — a hero built from a **478-point face-mesh particle field** (on-theme with MediaPipe) | Honours `prefers-reduced-motion`; GPU-cheap |
| Camera ML | **MediaPipe Tasks Vision 1.1** (Face Landmarker); **ONNX Runtime Web 1.30** (WebGPU) for optional on-device pre-checks | |
| Data | **TanStack Query 5**, **Zod 4**, React Hook Form; **Recharts 3** (shadcn charts) for the console | |
| i18n | **next-intl 4** (English + Hindi as stretch) | India-first audience |
| Monorepo | **pnpm** workspaces + **Turborepo 2.11** | Shared UI, SDK, types |
| Lint/format | **Biome 2.5** | One fast tool. *Alt:* ESLint 10 + Prettier |
| Tests | **Vitest 5**, Testing Library, **Playwright 1.64** with **Chromium's fake camera** (feeds a video file as the webcam — the capture flow runs end-to-end in CI) | |

**Apps:** `web` (marketing + docs + hosted verify flow + console), `demo-rp` (fictional age-restricted shop). **Packages:** `sdk-js` (`@dwarpal/js`), `sdk-react`, `ui` (design system), `api-types` (generated from OpenAPI).

---

## D13. Infrastructure and deployment

| Option | Cost | Realism | Ops load | Verdict |
| :-- | :-- | :-- | :-- | :-- |
| **Single cloud VM + Docker Compose + Caddy (auto-HTTPS)** | €0 (Oracle Always-Free ARM, if capacity) – ~€8–15/mo (Hetzner) | ✅ real public HTTPS deployment | Low | **Recommended primary** |
| Free-tier PaaS mix (Vercel + Render/Fly + Neon + Upstash) | ~$0 | ✅ | Low | Inference RAM limits and cold starts; many moving vendors |
| Kubernetes (k3s or managed) + Helm + GitOps | €€ | ✅✅ enterprise path | High | Ship a **Helm chart as an artefact**; deploy on k8s only if wanted |
| Local only | €0 | ❌ not "deployable" | — | Interim |

Built container-first either way: multi-stage, non-root, multi-arch (amd64/arm64) images. **GitHub Actions** CI (lint, type-check, tests, model gates, build, scan with Trivy, SBOM with Syft) → GHCR → deploy. Backups (`pg_dump` + offsite), runbooks.

---

## D14. Observability
OpenTelemetry traces + metrics + logs → Collector → **Prometheus + Grafana** (+ Loki for logs, Tempo for traces) as an optional Compose profile.

Dashboards:
- **service** — RED metrics (rate, errors, duration), SLO burn;
- **ML** — pass/step-up/fail mix per policy, liveness-reject rate, frame-quality distribution, predicted-age histogram drift;
- **security** — rate-limit hits, attempt-limit triggers.

Health: `/livez`, `/readyz` (readiness checks the DB, Valkey and that the model is loaded). **Logs never contain images, tokens or secrets** — enforced by a log-redaction processor and a unit test.

---

## D15. Security engineering (highlights)

- **Tenancy:** org → project → environment (test/live), enforced in the repository layer **and** by PostgreSQL row-level security as defence in depth.
- **API keys:** Stripe-style prefixed keys (`dk_live_…`), shown once. We store a SHA-256 hash, which is sufficient for 256-bit random secrets, and keys have scopes and rotation.
- **Console auth:** Argon2id passwords + TOTP (passkeys stretch); server-side sessions, `HttpOnly`/`Secure`/`SameSite` cookies; CSRF protection.
- **Signing keys:** Ed25519, encrypted at rest (envelope encryption), JWKS publication, scheduled rotation with overlap.
- **Webhooks:** HMAC-SHA256 with timestamp (replay window), retries with exponential back-off, dead-letter. **SSRF guard** — webhook URLs are resolved and rejected if they point at private/loopback ranges.
- **Abuse:** token-bucket rate limits (Valkey + Lua) per key/IP/session, attempt limits per session/device, idempotency keys on mutating endpoints.
- **Input hardening:** upload size caps, image-dimension caps (decompression-bomb guard), EXIF stripped, strict content types.
- **HTTP:** CSP, HSTS, `Permissions-Policy` (camera only on the verify origin), CORS allow-lists.
- **Audit:** append-only, **hash-chained** audit log (each entry commits to the previous hash), so tampering is evident.
- **Supply chain:** lockfiles, Renovate, pip-audit / pnpm audit, Trivy, SBOM; signed images (cosign) as stretch.

---

## D16. MLOps

| Concern | Choice |
| :-- | :-- |
| Data | Scripted preparation per dataset with **checksummed manifests**. The owner accepts each dataset licence. No raw data in git |
| Configs | Typed Pydantic + YAML experiment configs |
| Training | **PyTorch 2.14**, **timm 1.0**, torchvision v2 transforms, bf16 mixed precision, `torch.compile`, deterministic seeds. Augmentations that simulate webcams (blur, noise, JPEG, low light, colour casts) |
| Tracking | **MLflow 3** (self-hosted file store — no data leaves the machine) |
| Evaluation harness | One fixed, published protocol: MAE/CS@5; **FAR-minor per age at 13/16/18/21**; adult step-up per band; per-group fairness; calibration (ECE); risk-control verification |
| Release gates | CI fails the model release if FAR-minor, fairness gap or latency regress — **the model is code-reviewed by numbers** |
| Registry | Versioned dir + manifest (sha256, metrics, thresholds τ/τ_fail per policy, licence notes, training-data lineage) |
| Serving | ONNX + ONNX Runtime; INT8 only if gates hold; **shadow mode** (new model scores in parallel, does not decide) before promotion; instant rollback |
| Documentation | Auto-generated **model card** per release |

---

## D17. Testing strategy

- **Unit:** domain rules (policy engine, risk control math, token claims, MRZ check digits), with **property-based tests** (Hypothesis).
- **Integration:** real PostgreSQL/Valkey via **Testcontainers**; API contract fuzzing from OpenAPI (**Schemathesis**).
- **ML:** deterministic golden tests on fixed inputs; metric-function tests on synthetic predictions; ONNX-vs-PyTorch parity tests.
- **E2E:** Playwright with fake-camera video through the whole flow (SDK → hosted flow → token → demo site).
- **Accessibility:** axe-core in Playwright + manual keyboard/screen-reader passes.
- **Load:** Locust/k6 scenarios against the NFR-05 latency target.
- **Security:** SAST (ruff-bandit rules / Semgrep), dependency and image scans, red-team scripts for print/replay/render/payload-replay attacks.

---

## D18. Documentation

- **Zero-to-Hero book** (`docs/zero_to_hero/zero_to_hero.html`) — single HTML file, every source line explained. It is built from Markdown chapters plus per-file *walkthroughs*. The builder **hashes each source file**, flags stale explanations and **computes line coverage**, so "every line is explained" is *checked*, not promised.
- **ADRs** (architecture decision records) for every significant choice.
- **API reference** (OpenAPI → rendered docs), SDK guides, integration checklist.
- **Model card, DPIA template, practice statement** (ISO/IEC 27566-1 style), threat model, runbooks.

---

## 19. The recommended blueprint — one picture

```
                    ┌────────────────────────────── Relying party (any website) ───────────────────────────────┐
                    │  RP backend ──(secret key)──► POST /v1/verification-sessions ──► {id, client_secret, url}│
                    │  RP frontend ──@dwarpal/js──► opens hosted flow (modal or redirect)                      │
                    │  RP backend ◄── signed webhook / GET result / verify JWS via JWKS                         │
                    └───────────────────────────────────────────────────────────────────────────────────────────┘
                                                        │
 User's browser ────────────────────────────────────────┼──────────────────────────────────────────────────────────
  web app (Next.js)  /verify/{session}                  │
   • consent & notice                                   │  HTTPS (frames held in memory only)
   • MediaPipe live guidance (framing, light, pose)     ▼
   • random pose + colour challenge from server  ┌──────────────────────────┐   HTTP (internal)   ┌───────────────────────────┐
   • burst of ~8 frames + timing ───────────────►│  API  (FastAPI, modular  │ ──────────────────► │ Inference service         │
                                                 │  monolith, hexagonal)    │ ◄────────────────── │ (FastAPI + ONNX Runtime)  │
  console (Next.js) /console ── cookie session ─►│  sessions · policies ·   │  scores only        │ decode → detect (YuNet) → │
                                                 │  risk-controlled gate ·  │                     │ quality → align → PAD →   │
                                                 │  tokens (EdDSA) · keys · │                     │ challenge verify → age    │
                                                 │  webhooks · audit        │                     │ distribution → aggregate  │
                                                 └───┬──────────┬───────────┘                     └───────────────────────────┘
                                                     │          │                                   (stateless, scales out;
                                          PostgreSQL 18    Valkey 9 ◄── worker (arq):                images never persisted)
                                          (RLS, audit      (nonces,     webhooks outbox,
                                           hash chain)      limits,     retention cleanup,
                                                            queue)      reports
  Offline: ml/ (PyTorch training → evaluation harness → risk-control calibration → ONNX → registry + model card)
  Edge:    Caddy (TLS) · Prometheus/Grafana/Loki/Tempo · GitHub Actions CI/CD
```

**Life of one verification (happy path):**
1. RP creates a session with policy `uk_osa_18_standard`.
2. User opens the flow and sees the plain-language notice.
3. The camera starts and MediaPipe guides framing.
4. The server issues a challenge `{nonce, pose_sequence, colour_sequence}`.
5. The browser captures about 8 frames while the user follows the prompts and the screen tints softly.
6. The API forwards the frames to inference.
7. Inference returns per-frame quality, PAD, pose-trajectory and chroma-correlation scores, and age distributions. The frames are dropped.
8. The API's domain layer fuses liveness, aggregates the age distribution, applies the policy's risk-controlled thresholds → `pass`.
9. The API signs an age token, writes the session outcome plus scores to PostgreSQL, appends an audit event, and enqueues a webhook.
10. The browser returns to the RP with the session id only. The RP verifies the result server-side.

---

## 20. What makes this better than a typical implementation

| # | Typical project | This design |
| :-: | :-- | :-- |
| 1 | Reports MAE; threshold hand-picked | **FAR-minor per age is the headline metric**; threshold **derived from a stated risk budget** with a confidence bound |
| 2 | Binary yes/no on one photo | Multi-frame, quality-weighted **distributions** → **three outcomes** + step-up |
| 3 | Blink/smile liveness | **Layered** liveness incl. randomised pose + **screen-light reflection** challenge |
| 4 | Stores uploaded selfies "for training" | **No storage path for images exists** |
| 5 | Returns `{"age": 23}` to the website | Returns a **signed, minimal, audience-bound** predicate token |
| 6 | One script, no tests | Hexagonal modular monolith, typed, tested at every layer, **model release gates in CI** |
| 7 | Fairness ignored | Per-group metrics with **release gates**; no demographic inference in production |
| 8 | README | **Zero-to-Hero book with mechanically-verified line coverage**, ADRs, model card, DPIA |

---

## 21. Rejected ideas (consolidated)

| Idea | Why rejected |
| :-- | :-- |
| Trusting a browser-side result | Forgeable — the user controls the browser |
| Using a VLM API (Gemini/GPT) per check | Faces leave our control; cost/latency; 16–29 % minors → adult |
| Training on scraped social-media selfies | Unlawful/unethical; licence violations |
| Generating synthetic minors with diffusion for labels | 2026 evidence: generated faces don't match the intended age |
| Predicting ethnicity/sex in production "for fairness" | Unnecessary sensitive inference; fairness is measured offline instead |
| AGPL/non-commercial components in the runtime path (YOLOv8, InsightFace weights) | Licence contagion / commercial restriction |
| Microservices + Kafka | Operational cost far beyond the benefit at our scale |
| Storing frames encrypted "just in case" | Creates the breach we promise cannot happen |

---

## 22. Top risks and how the plan absorbs them

| Risk | Likelihood | Impact | Mitigation |
| :-- | :-: | :-: | :-- |
| Public data can't reach the FAR-minor gate at acceptable adult step-up rates | Med | High | The risk-controlled gate keeps **safety fixed** and lets the step-up rate absorb weakness. Backbone/face pre-training experiments; teacher→student distillation; publish honest numbers |
| Dataset access friction (registration, dead links) | High | Med | Start with directly downloadable sets. Bootstrap a quick **v0 model** so platform work isn't blocked |
| Webcam domain gap | High | Med | Webcam-style augmentation, quality gate, extra margin, drift monitoring |
| Sophisticated liveness bypass | Med | High | Layering; honest assurance labels; render detector (stretch); step-up on medium risk |
| Browser/camera variability | Med | Med | Live guidance, Playwright fake-camera tests, device matrix |
| Scope creep | High | Med | Walking skeleton first; phases with exit criteria; stretch items fenced off |
| Licence mistakes | Med | High | A licence register for every model/dataset/package in the runtime path |
| CPU latency | Med | Med | ONNX + INT8 + distilled student; measure early |
| Security bugs in auth/crypto | Med | High | Vetted libraries only; threat model; tests; scanners |
| Book drifts from code | High | Med | Hash-checked walkthroughs; coverage gate in CI |

---

## 23. Owner decisions — confirmed 15 Oct 2026

| # | Question | Decision |
| :-: | :-- | :-- |
| 1 | Scope | **Platform + console + demo shop.** The guardian extension is out of scope for v1 |
| 2 | v1 step-up verifier | **Both: ID-document MRZ first, then Aadhaar Secure QR** as a second plug-in |
| 3 | Deployment target | **Single VM + Docker Compose + Caddy**, with a Helm chart shipped as an artefact |
| 4 | Name | **Dwarpal** |

All other recommendations in this document are accepted as proposed. They are recorded as Architecture Decision Records in [`docs/adr/`](../adr/).
