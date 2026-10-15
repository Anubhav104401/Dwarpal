# Stage 1 — Problem Analysis

**Project:** AI-Based Age Estimation System for Protecting Minors from Accessing Age-Restricted Online Content
**Working codename:** *Dwarpal* (Sanskrit/Hindi द्वारपाल — "the guardian who stands at the door and decides who may enter"). Rename freely; nothing depends on it yet.
**Document status:** Draft for owner review · 15 Oct 2026
**Audience:** engineers, reviewers, examiners. (The beginner-friendly version of this material lives in the Zero-to-Hero book, Part 1 and Part 3.)

---

## 0. The short version

1. **This is not a "train a model" problem. It is a trust problem with a machine-learning core.** A website must be able to *trust* a yes/no answer ("is this person over 18?") produced from a few seconds of camera video — without learning who the person is, and without the answer being forgeable, replayable, or biased.
2. **The safety-critical number is not accuracy, it is the false-adult rate:** the fraction of minors near the legal threshold who are let through. Mean Absolute Error (MAE), the number most papers report, hides exactly the cases that matter.
3. **Off-the-shelf open models are unfit for this job.** A February 2026 benchmark of 34 models found that most specialised open models classified **39–100 % of minors as adults** at the 18 threshold; even the best general vision-language models did so 16–29 % of the time. The best commercial systems in NIST's ongoing evaluation report around **5 %** of minors passing a "Challenge-25" gate. The gap between those numbers is the engineering work of this project.
4. **Regulators already accept facial age estimation — with conditions:** a buffer above the legal age, a stronger fallback method for people inside the buffer, liveness/anti-spoofing, fairness evidence, and strict privacy (UK Ofcom, Australia eSafety, EU Commission guidance all converge on this).
5. **The hardest risks are:** (a) data — minors are scarce in public datasets and most datasets are research-only licensed; (b) spoofing — in July 2025 users bypassed Discord's UK age checks with video-game characters; (c) privacy — faces are biometric data; (d) fairness — errors are not evenly distributed across skin tones, sexes and ages; (e) friction — every extra second loses users.

---

## 1. Restating the problem precisely

> *"AI Based Age Estimation System For Protecting Minors From Accessing Age Restricted Online Content"*

| Phrase | What it actually demands |
| :-- | :-- |
| **AI based** | A learned model, not rules. It must be trained, evaluated, versioned, monitored and improvable — i.e. an ML *lifecycle*, not a file of weights. |
| **Age estimation** | A *probabilistic* estimate from a biological signal (the face), not verification against a document. Estimation always has error, so the system must quantify *how sure it is*, not just output a number. |
| **System** | End-to-end: capture → quality checks → liveness → estimation → decision → proof to the website → audit → monitoring. A model alone protects no one. |
| **Protecting minors** | The cost of errors is **asymmetric**. Letting a 15-year-old through is a safety failure; stopping a 26-year-old is an inconvenience. The decision rule must encode this asymmetry explicitly. |
| **from accessing** | There is a *gate* at a specific moment in a specific website. The gate lives on someone else's infrastructure (the "relying party"), so the result must be delivered in a form that site can verify and cannot be faked by the user. |
| **age-restricted online content** | Different content has different legal ages (13 social media in many places, 16 in Australia, 18 adult content, 21 alcohol/gambling in some US states). The threshold must be a *policy parameter*, not a constant. |

**Reframed engineering goal:** *Build a privacy-preserving age-assurance service that lets any website ask "is this live person over N?", returns a cryptographically signed, minimal answer with a quantified and policy-controlled risk of letting a minor through, never stores the person's face, and degrades to a stronger check whenever it is unsure.*

---

## 2. Who is involved

| Actor | Wants | Fears | Design consequence |
| :-- | :-- | :-- | :-- |
| **Minor (child/teen)** | Access to age-appropriate content; privacy | Being tracked, profiled, humiliated, or locked out of legitimate services | Minimal data; no identity; no profiling; respectful UX; never store their image |
| **Adult user** | Instant access, no hassle | Being wrongly blocked; handing biometrics to unknown companies | Fast flow (< 15 s); clear privacy promise; a fallback that is not humiliating |
| **Relying party (RP)** — the website/app | Legal compliance, low friction, low cost, easy integration | Fines, bypasses, user drop-off, data-breach liability | SDK + API that take an afternoon to integrate; signed tokens they can verify locally; dashboards for compliance evidence |
| **Parent / guardian** | Children protected; consent where the law requires it (India DPDP Rule 10) | Kids bypassing checks with the parent's face or ID | Liveness; token binding; optional guardian flows later |
| **Regulator** (Ofcom, eSafety, EU Commission/DSCs, India's Data Protection Board, US state AGs) | Checks that are "accurate, robust, reliable, fair" and privacy-preserving | Theatre — checks that look good and are trivially bypassed | Measured, published error rates; fairness reports; DPIA; practice statement; audit logs |
| **Operator** (us) | A system that is safe to run and easy to evolve | Silent model regressions; key compromise; outages that "fail open" | Quality gates in CI; key rotation; **fail closed** on any error; observability |
| **Adversary** | To pass a check they should fail, or to steal data | — | Layered liveness; randomised challenges; retry limits; no biometric storage to steal |

---

## 3. The world this system lives in (as of October 2026)

### 3.1 United Kingdom — Online Safety Act 2023

- Since **25 July 2025** services that allow pornography, and user-to-user services with content harmful to children, must use **"highly effective age assurance" (HEAA)**. Ofcom's four criteria: **technically accurate, robust, reliable, and fair**. Self-declaration and typing a date of birth explicitly **do not** qualify.
- Ofcom lists **facial age estimation** among the methods capable of being highly effective, alongside photo-ID matching, open banking, digital identity, credit-card checks, mobile-network checks and email-based estimation.
- Ofcom sets **no numeric accuracy threshold**, but expects methods with a margin of error to use a **challenge age set well above the legal age**, and to resist circumvention ("fake inputs") and be linked to the person actually present.
- Ofcom's July 2026 statutory report covered **~69 million age checks across 32 services (Jul–Dec 2025)**; facial age estimation and photo-ID matching were the most common methods.
- Enforcement is real: fines have been reported in 2026 (e.g. £730,000 against one adult-site operator announced 4 Sep 2026). Maximum penalty: £18 m or 10 % of global turnover.
- **March 2026:** joint Ofcom–ICO statement — the method must be necessary, proportionate, UK-GDPR-compliant, backed by a **DPIA** and updated privacy notices.

### 3.2 European Union — DSA, AI Act, age-verification blueprint

- **DSA Article 28** guidelines (July 2025) recommend age-assurance methods that are *"accurate, reliable, robust, non-intrusive and non-discriminatory."* The DSA itself does not mandate a specific method.
- **29 April 2026:** Commission Recommendation on protecting children online; **11 May 2026:** the EU age-verification app ("blueprint") declared technically ready. It proves "over N" **without revealing exact age or identity**. Member States are urged to deploy national versions by **31 December 2026**, standalone or inside the **EU Digital Identity Wallet** (also due end-2026). Pilots: Denmark, France, Greece, Italy, Spain.
- **EU AI Act:** facial age estimation is a form of *biometric categorisation*. Whether it is **high-risk** (Annex III 1(b)) is legally unsettled — that point targets *sensitive or protected* attributes, and Recital 54 ties those to GDPR Art. 9 categories, which do not list age. Transparency duties to the person being categorised should be assumed regardless. **→ We design for the stricter reading:** clear notice before capture, documentation (model card, risk management), human-readable decision records.

### 3.3 United States

- **Free Speech Coalition v. Paxton (27 June 2025)** — the Supreme Court upheld Texas's age-verification law for sexual content (6–3, intermediate scrutiny). Roughly 20+ states have similar laws.
- **App-store accountability acts** (Utah, Texas SB 2420, Louisiana HB 570; California's operating-system-level age-signal law) push age signals into app stores and operating systems. Texas's law was enjoined in Dec 2025, then the Fifth Circuit stayed the injunction. Utah's enforcement begins 31 Dec 2026.
- **Consequence:** age assurance is becoming *infrastructure*. A service that emits standard, verifiable "age signals" (signed tokens, later verifiable credentials) fits where the market is heading.

### 3.4 Australia — Social Media Minimum Age (under-16)

- In force since **10 December 2025**; penalties up to AUD 49.5 m; platforms must take "reasonable steps."
- The national **Age Assurance Technology Trial** (60+ technologies, 48 vendors) concluded age assurance *can* be private, robust and effective — but **"no single solution"**, and estimation is highly accurate **outside buffer zones** around thresholds. Reported concerns: false-rejection rates of ~8.5 % for 16-year-olds and ~2.6 % for 17-year-olds at the 16+ gate, and weaker performance for some demographics. The trial recommends a **layered/"waterfall" model**: estimation first, then a more definitive method when uncertain.

### 3.5 India — DPDP Act 2023 and DPDP Rules 2025

- Rules notified **November 2025**, with an ~18-month phase-in (full compliance expected around mid-2027).
- A **"child" is anyone under 18.** Processing a child's personal data requires **verifiable parental consent** (Rule 10). The parent's adulthood and identity can be verified from reliable details already held, or via **virtual tokens from authorised entities such as DigiLocker**.
- Platforms must **not** track, behaviourally monitor or target ads at children, and are expected to stop minors from faking their age.
- **Consequence for us:** in India the age signal decides whether the *data-processing* rules for children apply at all, beyond just gating adult content. A privacy-preserving "is this person an adult?" check that keeps no identity data is directly useful. It also maps onto "verify that the consenting parent is an adult."

### 3.6 Standards and benchmarks we should align to

| Standard / benchmark | What it gives us |
| :-- | :-- |
| **ISO/IEC 27566-1:2025** — Age assurance systems, Part 1: Framework (Dec 2025) | Vocabulary (verification / estimation / inference), five characteristics (functionality, performance, privacy, security, acceptability), *indicators of confidence* (the working draft named asserted → basic → standard → enhanced → strict), and *practice statements* |
| **IEEE 2089.1-2024** — Online age verification | Process requirements for age-verification services; largely aligned with ISO 27566-1 |
| **NIST FATE AEV** (ongoing; page updated 29 Sep 2026) | The reference *method of measurement*: MAE per dataset plus **Challenge-T** metrics (accept if estimate ≥ T; T = 25 is common for a legal age of 18), including a child-online-safety (13–16) set |
| **ISO/IEC 30107-3** | How to test presentation-attack detection (PAD) — metrics APCER/BPCER |
| **CEN/TS 18099** | Injection-attack detection (virtual cameras, stream tampering) |
| **WCAG 2.2 AA** | Accessibility of the capture flow (incl. seizure-safety rules for anything that flashes) |

### 3.7 What all of them agree on — the eight requirements everything else hangs from

1. **Accuracy** measured at the threshold, not on average.
2. **Robustness** against spoofing, injection and circumvention.
3. **Reliability** — it works across devices, cameras and lighting conditions.
4. **Fairness** — errors measured and bounded across demographic groups.
5. **Privacy** — data minimisation; ideally no retention of images; reveal only "over N."
6. **Proportionality / buffers + fallback** — estimation where it is confident, something stronger where it is not.
7. **Accessibility / alternatives** — people without cameras or with facial differences need another route.
8. **Accountability** — DPIA, published performance, practice statement, audit trail.

---

## 4. Vocabulary that shapes the design

| Term | Meaning | Why it matters here |
| :-- | :-- | :-- |
| **Age assurance** | Umbrella term: any method that establishes age with some confidence | What we are building |
| **Age verification** | Age from an authoritative source (ID document, bank, credential) | Our *fallback* tier |
| **Age estimation** | Age inferred from a physical/behavioural characteristic (face) | Our *primary* tier |
| **Age inference** | Age deduced from other verified facts (e.g. holds a credit card) | Out of scope for v1 |
| **Challenge age / buffer** | Pass via estimation only if estimate ≥ legal age + buffer (e.g. 25 for 18) | Converts a noisy regressor into a safe gate |
| **Waterfall / step-up** | If estimation is unsure, escalate to a stronger method | Keeps young adults from being locked out |
| **False adult (minor accepted)** | A minor passes the gate — the **safety** error | Our primary safety metric (we call it **FAR-minor**) |
| **False minor (adult rejected)** | An adult is stopped or forced to step up — the **usability** error | Our primary friction metric |
| **PAD** (presentation-attack detection) | Detecting that what's in front of the camera isn't a live face (photo, screen, mask, render) | Anti-spoofing |
| **Injection attack** | Bypassing the camera entirely (virtual camera, tampered stream, replayed API payload) | Anti-spoofing at the software layer |
| **Relying party (RP)** | The website/app that needs the answer | Our customer |
| **Attestation / age token** | A signed statement "this session's user is over N", verifiable by the RP | How the answer travels without being forgeable |

---

## 5. Why this is genuinely hard

### 5.1 Faces don't carry birth certificates
Models estimate *apparent* age; the law cares about *chronological* age. Genetics, ethnicity, make-up, lighting, camera quality, expression, facial hair and health all move apparent age. Humans themselves misjudge age by several years. Around 13–19 faces change quickly but unevenly, and a mature-looking 16-year-old and a young-looking 20-year-old can be visually indistinguishable. **Consequence:** no amount of modelling removes all error near the threshold, so the *decision procedure* must absorb it (buffers + uncertainty + step-up).

### 5.2 The asymmetric-error problem
For an 18+ gate there are four outcomes. Two are fine (adult passes, minor stopped). The two errors are not equally bad:

| | Predicted "over 18" | Predicted "unsure / under" |
| :-- | :-- | :-- |
| **Actually under 18** | ❌ **Safety failure** (FAR-minor) | ✅ correct |
| **Actually over 18** | ✅ correct | ⚠️ Friction (step-up or block) |

**Consequence:** the operating point is a *policy decision* expressed as "at most ε of minors may pass," and the threshold is then *derived from data* to meet that bound. Picking "25" by hand and hoping is not engineering.

### 5.3 The data problem
| Dataset | Size | Ages | Minors? | Licence (summary — verify before use) |
| :-- | --: | :-- | :-- | :-- |
| IMDB-WIKI | ~524 k | 0–100 (noisy) | few | Academic, non-commercial |
| IMDB-Clean (FP-Age) | ~287 k | mostly adults | few | Inherits IMDB terms |
| UTKFace | ~24 k | 0–116 | **yes** | Non-commercial research |
| AgeDB | ~16.5 k | 1–101 | some | Research (on request) |
| MORPH II | ~55 k | 16–77 | 16–17 only | Academic licence (commercial paid) |
| FG-NET | 1,002 | 0–69 | **many** | Research |
| APPA-REAL | ~7.6 k | 0–95, real + apparent | **yes** | Research (ChaLearn) |
| AFAD | ~160 k | 15–40 (Asian) | 15–17 | Research |
| LAGENDA (MiVOLO) | ~67 k | 0–95 (crowd-labelled, non-celebrity) | **yes** | Check terms |
| FairFace | ~108 k | 9 age *bins*; balanced race/gender | bins only | **CC BY 4.0** |
| Casual Conversations v2 | 26 k videos / 5.5 k people | adults, self-reported, skin-tone labels | no | Evaluation-oriented terms |

Observations:
- **Minors are scarce** and concentrated in small datasets. Celebrity datasets (IMDB) skew adult and photogenic.
- **Most licences are research-only.** A model trained on them is fine for this academic/demo project, but **cannot be sold commercially** without licensed data. The architecture must make the model a swappable artefact.
- **Domain gap:** datasets are photos (often professional); production input is webcam/phone selfies (noise, blur, low light, wide-angle distortion).
- **Synthetic data is not a shortcut:** a 2026 study found that diffusion-generated faces do not reliably depict their intended age, so the labels are wrong. GAN-based child-face sets exist but are research-licensed and identity-focused.
- **We must not collect minors' biometric data ourselves** (consent, ethics, law). Evaluation therefore relies on public data — a limitation we will state, not hide.

### 5.4 The evaluation problem
- MAE averages over everyone. A model can have a great MAE and still pass a third of 16-year-olds.
- What we must report, per NIST practice: **FAR-minor per exact age (13, 14, …, 17) at each policy threshold**, **adult step-up rate per age band (18–20, 21–24, 25–29, 30+)**, per **demographic group**, plus calibration and coverage.
- Cross-paper numbers are not comparable (different splits, crops and protocols). We fix one protocol, publish it, and run every model through it.

### 5.5 The uncertainty problem
A point estimate ("19.3 years") gives no warning when the model is guessing — dark photo, unusual pose, out-of-distribution face. We need (a) a predicted **distribution** over ages, (b) an aggregate across multiple frames, and (c) a **calibrated** statement such as "with 95 % coverage, true age ∈ [17, 24]," whose guarantees we can check on held-out data.

### 5.6 The adversary problem
Real incident: in **July 2025**, days after UK enforcement began, users passed Discord's face-based age check with **video-game characters** (e.g. *Death Stranding*'s photo mode, whose expression controls defeated a "open your mouth" liveness step). Attack classes we must consider:

| Class | Example | Defence direction |
| :-- | :-- | :-- |
| Presentation — print/screen | Photo of an adult held to the camera; video on a phone | Passive PAD (texture/moiré/frequency cues), screen-reflection cues |
| Presentation — rendered/3D | Game character, 3D avatar driven by a controller | Unpredictable challenge + *physical* light-reflection challenge that a renderer can't anticipate |
| Presentation — physical disguise | Make-up, fake beard, masks | PAD + conservative buffer + step-up |
| Injection | Virtual camera (OBS), hooked `getUserMedia`, deepfake stream | Server-issued random challenge schedule that the stream must physically respond to; stream heuristics; nonce binding |
| Replay | Re-submitting a captured successful payload | One-time nonces, session binding, short expiry |
| Proxy | An adult (parent/sibling) does the check | Token bound to the RP session and short-lived; re-checks; *residual risk acknowledged by regulators* |
| Trial-and-error | Retrying with different lighting until it passes | Attempt limits per session/device, cool-downs, stricter gate after failures |
| Model probing / adversarial | Searching for perturbations that raise the estimate | Return only the decision (never the raw age), rate limits, randomised augmentations |
| Token abuse | Sharing or replaying a valid age token | Audience-bound, short TTL, one-time `jti`, RP-side nonce |
| Integration bypass | RP trusts a client-side "passed" flag | Server-side verification is the only documented path; SDK does it by default |
| Data theft | Breach to steal faces | **Nothing to steal**: no images stored; only scores and metadata |

### 5.7 The privacy problem
Faces are biometric data. The privacy design goals:
- **Process, decide, forget:** images live only in memory for the duration of one request; never written to disk, logs, traces or crash dumps.
- **Reveal only the predicate:** the RP learns "over 18: yes", not the estimated age, not an identity.
- **No cross-site linkability:** tokens carry no stable user identifier.
- **Trust boundary:** client-side ML is great for privacy, but a client can lie, so the authoritative decision must be server-side (or cryptographically attested — out of reach in browsers). We use client ML for *guidance* only.

### 5.8 The fairness problem
Age-estimation errors differ by skin tone, sex and age (documented in NIST work and the Australian trial). An unfair gate either endangers some groups of minors (more false adults) or burdens some groups of adults (more step-ups). We will **never predict ethnicity or sex in production**. Those labels are used **offline only**, from datasets that carry them, to *measure and report* disparities, with release gates on the maximum gap.

### 5.9 The integration problem
The protection only works if RPs integrate it correctly. That needs a familiar pattern (create session → hosted flow → signed result, like Stripe Identity or OAuth), a drop-in front-end SDK, local token verification via published keys (JWKS), signed webhooks, test mode, and excellent docs.

### 5.10 The user-experience problem
Each extra step costs users, and failure is embarrassing. The flow needs:
- live guidance ("move closer", "more light") before capture, so bad frames are rare;
- a total time of under 15 s;
- clear, kind copy;
- support for low-end phones and slow networks (relevant in India);
- reduced-motion and seizure-safe visuals;
- a non-camera alternative.

---

## 6. Requirements

### 6.1 Functional requirements

| ID | Requirement |
| :-- | :-- |
| FR-01 | RPs create **verification sessions** via API (policy: minimum age, allowed methods, assurance level; return URL; external reference). |
| FR-02 | A **hosted capture flow**: notice & consent → camera → live guidance → randomised liveness challenge → capture → result → return to RP. |
| FR-03 | **Integration surfaces**: REST API, JS SDK (modal/iframe + redirect), React component, server-side verification helpers, test mode. |
| FR-04 | **Face pipeline**: detection (exactly one face), quality assessment (blur, exposure, size, pose, occlusion), alignment. |
| FR-05 | **Liveness / anti-spoofing**: passive PAD, active randomised challenge, light-reflection challenge, injection heuristics → fused risk score. |
| FR-06 | **Age estimation with uncertainty**: per-frame age distribution, multi-frame aggregation, calibrated interval, P(age ≥ N). |
| FR-07 | **Policy engine**: thresholds per policy; risk-controlled gates; outcomes `pass` / `fail` / `step_up` / `retry` / `reject`; attempt limits; **fail-closed** on any error. |
| FR-08 | **Step-up framework**: pluggable verifiers behind one interface; at least one real verifier in v1 (choice pending — see §9). |
| FR-09 | **Attestation**: signed age token (JWS, EdDSA) with minimal claims; JWKS endpoint; result retrieval API; HMAC-signed webhooks with retries. |
| FR-10 | **Console**: organisations, members & roles, projects, test/live environments, API keys, policies, webhooks, session explorer (no images), analytics, fairness & model reports, audit log. |
| FR-11 | **Model lifecycle**: data preparation, training, evaluation harness, calibration, model registry with manifests, release quality gates, shadow evaluation, rollback. |
| FR-12 | **Privacy controls**: zero image retention, metadata retention windows, privacy notice per RP, no third-party processors for biometrics. |
| FR-13 | **Observability**: metrics, traces, structured logs (biometric-free), health/readiness, dashboards, alerts. |
| FR-14 | **Demo relying party**: a fictional age-restricted site showing a real integration end-to-end. |
| FR-15 | **Developer documentation**: quick-start, API reference (OpenAPI), SDK docs, integration checklist. |
| FR-16 | **Zero-to-Hero book**: single HTML, every line of code explained, grown with the code. |
| *Stretch* | FR-17 reusable "Age Pass" credential (SD-JWT VC, unlinkable batch tokens) · FR-18 guardian/parental-control browser extension · FR-19 parental-consent flow for DPDP. |

### 6.2 Non-functional requirements (targets are provisional until measured)

| ID | Quality | Target |
| :-- | :-- | :-- |
| NFR-01 | **Safety** | 18+ "standard" policy: FAR-minor (ages 13–17, held-out eval) **≤ 2 % target, ≤ 5 % release gate**, reported per age and group |
| NFR-02 | **Usability** | ≥ 85 % of adults aged 25+ pass without step-up; median flow ≤ 15 s |
| NFR-03 | **Accuracy** | Face-only MAE competitive with strongest open specialist (~4.2 y on UTKFace protocol); teen-band MAE reported separately |
| NFR-04 | **Fairness** | FAR-minor gap between best and worst demographic group ≤ 2 percentage points (gate), all groups published |
| NFR-05 | **Latency** | Server processing of one submission (≈ 8 frames) p95 ≤ 1.5 s on 4 vCPU, ≤ 0.5 s on GPU |
| NFR-06 | **Scalability** | Stateless inference; horizontal scaling; back-pressure instead of collapse |
| NFR-07 | **Availability** | 99.9 % design target; **fail closed** — no error path may produce a pass |
| NFR-08 | **Privacy** | No image persisted anywhere; tokens reveal only the predicate; no stable cross-site IDs |
| NFR-09 | **Security** | OWASP ASVS L2 alignment; signed tokens with key rotation; tenant isolation (app + database row-level security); rate limiting; SSRF-safe webhooks; dependency & image scanning |
| NFR-10 | **Accessibility** | WCAG 2.2 AA; keyboard & screen-reader support; reduced motion; seizure-safe light challenge; non-camera route |
| NFR-11 | **Device reach** | Current Chrome/Edge/Firefox/Safari, desktop & mobile; low-end Android; uploads ≤ ~600 KB per attempt |
| NFR-12 | **Accountability** | Every decision traceable to model version, policy version and scores; tamper-evident audit log; model card; practice statement; DPIA template |
| NFR-13 | **Maintainability** | Strict typing (mypy/pyright, TS strict), linting, ≥ 85 % unit coverage of domain code, ADRs for every significant decision |
| NFR-14 | **Deployability** | One command locally; multi-arch container images; 12-factor configuration; CI/CD |
| NFR-15 | **Cost** | Demo traffic on one 4 vCPU / 8–16 GB VM |

### 6.3 Constraints

| ID | Constraint | Effect |
| :-- | :-- | :-- |
| C-01 | Public age datasets are mostly research-only | v1 weights are for research/demonstration. Commercial use needs licensed data; the model is a swappable registry artefact |
| C-02 | We will not collect minors' biometrics | Evaluation is on public data. The webcam domain gap is mitigated (augmentation, conservative gates) and documented |
| C-03 | Compute: RTX 4070 Laptop (8 GB VRAM), i9-14900HX, 32 GB RAM | Fine-tuning ViT-B / ConvNeXt-T class models with mixed precision is feasible locally. No foundation-scale pre-training |
| C-04 | Machine Python is 3.14.6; parts of the ML stack still exclude or lag 3.14 (e.g. torchvision excludes 3.14.1; GPU builds trail) | Services pin **Python 3.13** — supported by every library we need (PyTorch 2.14, ONNX Runtime 1.31, MediaPipe 1.1, NumPy 2.5) — via the `uv` toolchain, independent of the system Python |
| C-05 | Built and maintained by one developer (AI-assisted) | Avoid microservice sprawl; prefer a modular monolith plus one inference service |
| C-06 | No paid third-party AI APIs in the decision path | Self-hosted models only; no faces leave our infrastructure |

### 6.4 Explicit non-goals
- **Identity verification or face recognition** (1:1 / 1:N) — we never answer "who is this?".
- **Storing faces** for any purpose, including "model improvement".
- Content moderation / classifying whether content is adult.
- Claiming legal certification. We say "designed to align with…", and certification is a separate audit.
- Native mobile apps in v1 (the web flow works on mobile browsers).

---

## 7. Success criteria — what "done" means for this project

1. `docker compose up` brings the whole platform up locally; a public deployment serves a working demo over HTTPS.
2. A demo age-restricted site integrates via the SDK, and the token is verified server-side with the published keys.
3. The model card reports, on a fixed public protocol: MAE, **FAR-minor per age at 13/16/18/21 policies**, adult step-up rates, calibration/coverage, and per-group fairness. All release gates pass.
4. Liveness stops, in our own red-team tests: printed photos, screen replays, static game renders, and replayed payloads.
5. Security: automated scans clean (SAST, dependency, image); threat model documented; keys rotate.
6. Load test shows NFR-05 latency at target concurrency.
7. Accessibility audit (axe + manual keyboard/screen reader) passes for the capture flow.
8. **Zero-to-Hero book coverage = 100 % of source lines**, verified mechanically.

---

## 8. Key insights that drive the solution (carried into Stage 2)

1. Optimise and evaluate for **FAR-minor at the threshold**, not MAE.
2. Make the threshold **data-derived from a stated risk budget** (risk-controlled / conformal calibration), not hand-picked.
3. Use **three outcomes** (pass / step-up / fail) with a stronger fallback, never a binary gate on a noisy estimate.
4. Prefer **many good frames over one perfect frame**, and weight them by quality.
5. Liveness must include something **unpredictable and physical** (randomised pose + light-reflection challenge), because static and rendered faces now defeat simple "blink/open mouth" checks.
6. **Privacy by architecture**: no storage path exists for images, so no misconfiguration can leak them.
7. The model is a **versioned, swappable artefact with release gates**, because licensed data or better architectures will replace it.
8. Integration must be **boringly familiar** to web developers (session → hosted flow → signed token → webhook).

---

## 9. Questions for the owner — answered 15 Oct 2026

1. **Product scope:** platform + console + demo shop (no guardian extension in v1).
2. **Step-up methods:** ID-document MRZ first, then Aadhaar Secure QR.
3. **Deployment:** single cloud VM with Docker Compose and Caddy, plus a Helm chart as an artefact.
4. **Name:** Dwarpal.

---

## 10. Sources (consulted 15 Oct 2026)

- Ofcom HEAA overview & enforcement — [RPC: Online Safety: Age Assurance, one year on](https://www.rpclegal.com/thinking/media/online-safety-age-assurance-one-year-on/), [RPC: Ofcom & ICO joint statement](https://www.rpclegal.com/snapshots/data-protection/summer-2026/ofcom-and-ico-joint-statement-on-age-assurance/), [Kaamel: Ofcom Xgroovy penalties](https://www.kaamel.com/blog/en-ofcom-xgroovy-age-assurance-information-penalties/), [AU10TIX: UK OSA](https://www.au10tix.com/blog/uk-online-safety-act/), [VerifyMy: Ofcom guidance](https://verifymy.io/blog/ofcom-releases-official-guidance-on-highly-effective-age-assurance-for-pornography-providers)
- NIST FATE AEV — [NIST results page](https://pages.nist.gov/frvt/html/frvt_age_estimation.html), [Biometric Update: beyond accuracy](https://www.biometricupdate.com/202608/beyond-accuracy-what-nists-latest-age-estimation-results-mean-for-age-assurance), [Regula: interpreting NIST age results](https://regulaforensics.com/blog/nist-age-estimation-results-interpretation/), [Innovatrics NIST AEV results](https://innovatrics.com/awards/innovatrics-results-in-nist-fate-aev)
- VLM vs specialist benchmark — [arXiv 2602.07815](https://arxiv.org/abs/2602.07815)
- MiVOLO — [GitHub](https://github.com/WildChlamydia/MiVOLO), [arXiv 2307.04616](https://arxiv.org/pdf/2307.04616)
- Pre-training effects on age estimation — [Paplham et al., WACV 2026 supplement](https://openaccess.thecvf.com/content/WACV2026/supplemental/Paplham_Photo_Dating_by_WACV_2026_supplemental.pdf)
- Synthetic faces and age labels — [IS&T Electronic Imaging 2026](https://library.imaging.org/ei/articles/38/12/GENAI-182), [Idiap AgeSynth](https://idiap.ch/en/dataset/agesynth)
- Discord bypass (July 2025) — [PinkNews](https://www.thepinknews.com/2025/07/25/discord-video-game-characters-age-verification-checks-uk-online-safety-act), [CO/AI](https://getcoai.com/news/farcical-recognition-uk-users-bypass-face-based-age-verification-with-video-game-characters/)
- EU — [IAPP: EU AV app technically ready](https://www.iapp.org/news/a/european-commission-s-age-verification-app-technically-ready-rollout-to-come), [Inside Privacy: rollout by end-2026](https://www.insideprivacy.com/minors/eu-sets-the-clock-on-age-verification-rollout-urged-by-end%E2%80%912026/), [FPF analysis](https://fpf.org/blog/the-eu-commissions-approach-to-age-verification-mobile-apps-dsa-enforcement-and-challenging-national-social-media-bans/)
- EU AI Act & age estimation — [Facial Age Estimation research roadmap (arXiv 2505.22401)](https://arxiv.org/pdf/2505.22401), [AI Act Recital 54](https://www.artificialintelligenceact.eu/recital/54/), [ICML 2026 position paper (arXiv 2605.17347)](https://arxiv.org/pdf/2605.17347)
- ISO/IEC 27566-1 — [Persona guide](https://withpersona.com/blog/a-guide-to-iso-27566-1-the-new-standard-for-age-assurance-systems), [5Rights](https://5rightsfoundation.com/resource/iso-iec-27566-1-age-assurance-systems-part-1-framework/), [AVPA](https://avpassociation.com/iso-iec-27566-1/)
- US — [FIRE: FSC v. Paxton](https://www.thefire.org/supreme-court/free-speech-coalition-v-paxton), [Orrick: app-store laws](https://www.orrick.com/en/Insights/2025/07/Texas-and-Louisiana-Join-Growing-Trend-of-State-Age-Verification-Laws-for-App-Stores), [ZwillGen: Fifth Circuit stay](https://alerts.zwillgen.com/alerts/update-fifth-circuit-lifts-injunction-for-texas-app-store-accountability-law), [McDermott: app-store acts](https://www.mcdermottlaw.com/insights/app-store-accountability-acts/)
- Australia — [Allens: waterfall model & trial insights](https://www.allens.com.au/insights-news/insights/2025/09/towards-a-waterfall-model-insights-from-esafetys-consultation-and-the-age-assurance-technology-trial/), [hey.paris analysis](https://hey.paris/posts/ageassurance/), [Persona: SMMA prep](https://withpersona.com/blog/how-to-prepare-for-australias-social-media-minimum-age-requirements)
- India — [AMS Shardul: DPDP Rules](https://www.amsshardul.com/insight/enforcement-of-the-dpdp-act-and-notification-of-the-dpdp-rules/), [Seclore: DPDP Rules compliance](https://www.seclore.com/fundamentals/dpdp-rules-2025-compliance-guide/), [Mondaq: DPDP Rules 2025](https://webiis08.mondaq.com/india/data-protection/1708932/the-digital-personal-data-protection-rules-2025-a-new-digital-frontier)
- Anti-spoofing model licence (secondary reports) — [LocalAI commit notes](https://gitea.varghacsongor.hu/GithubMirror/LocalAI/commit/f5eb13d3c21f32d0aad84680f83551c67c36ba57)

*Some regulatory figures come from secondary sources (law-firm and vendor write-ups). Each will be re-checked against the primary source before it appears in any compliance-facing document.*
