# Decisions waiting for the owner

Work that needs your answer — a download, a design choice, an account, or something only you can do — is collected here instead of stopping the work. Everything else carries on. Each item says what it unblocks.

**Started:** 26 Oct 2026, overnight run. **Phase 4 is complete** (commits `450bfba`, `7d730ee`, `95f3e91`).

## Morning summary — 2 Nov, 10 am (overnight work on Phases 8 and 9)

**Still waiting for you** — steps only you can take (each says what it unblocks):

| # | Step | Unblocks |
| :-: | :-- | :-- |
| O2c | **Create the server** from `infra/vm/cloud-init.yaml` (Always Free Ampere, 2 cores / 12 GB, Ubuntu 24.04), open ports 80 and 443 in its security list, and send me its public IP address | the first deploy |
| O10 | **Choose and point a domain** at that address (an `A` record for the domain, `www.`, `api.` and `shop.`) | HTTPS, and the first deploy |
| O8 | **Create the backup storage**: in Oracle, an Object Storage bucket `dwarpal-backups` (Always Free: 20 GB) and a *customer secret key*; choose a restic password and keep it offline too (`infra/deploy/README.md`, step 8) | backups, and Phase 8's restore drill |
| O9 | **GitHub settings for deploys**: a separate deploy SSH key, the `production` environment (ideally with your approval required), and the variables listed in `infra/deploy/README.md`, step 5 | automatic deploys; after the first image build, set each `dwarpal-*` package on GitHub to **Public** (D18) |

**Done overnight** (no decision needed; all checks green):

- **Phase 8** — Dockerfiles, Compose with Caddy, deploy/backup/restore scripts, the manual GHCR deploy workflow, runbooks, and the Helm chart (`6b6a1da`). Waiting only on the server, the domain, O8 and O9 (D17–D19 approved 2 Nov).
- **Phase 9** — the Python SDK (`9ca1bfd`); **passkeys** for console sign-in (§5.9.2), with a software test device and a Chromium end-to-end test; and on 2 Nov, after the owner's answers, the **Age Pass** itself (D21, §5.9.3) and Helm's check of the chart in CI (D19).
- **CI is fully green on GitHub** (`03f3f5b`) for the first time since Phase 6: Lighthouse now starts its browser on GitHub's Linux machines, and the Python job's 30-minute timeouts were one ML test hanging (forked worker processes); it now takes 2 minutes.

**Blocked, and why** (nothing for you to do yet):

- **CGI-render detector** (liveness level 6) — needs examples of computer-rendered faces to train and measure against, and none are licensed for this project. It waits for a dataset decision, which I will bring with options when the rest is done.
- **Kubernetes deployment** — the Helm chart exists; trying it needs a local cluster tool (kind, a further download; Helm itself was approved 2 Nov, D19), and the Always Free server (O2b) is a single machine, where Compose is the better fit. Left optional, as the roadmap says.

## Decided on 2 Nov 2026

The owner answered the overnight decisions in the morning, each with the recommended option.

| # | Decision |
| :-: | :-- |
| D17 | **Approved**: the five base images — `python:3.13.17-slim-bookworm` (44 MB), `node:24.22.1-bookworm-slim` (81 MB), `caddy:2.11.6-alpine` (24 MB), `restic/restic:0.19.1` (17 MB) from Docker Hub, and `ghcr.io/astral-sh/uv:0.13.1` (18 MB) from GitHub (sizes for arm64) — pulled only on GitHub's build machines and the server |
| D18 | **Approved, public**: Dwarpal's images go to GitHub's container registry under the owner's account and are made public, so the server pulls them without a token |
| D19 | **Approved**: Helm **4.3.1** (`helm-v4.3.1-linux-amd64.tar.gz`, 20.4 MB, get.helm.sh, Apache-2.0) on CI's machines only, checked against its SHA-256, to lint and render the chart. Helm 3, first proposed, stops getting security fixes on 11 Nov 2026 |
| D20 | **Kept**: signing in with a passkey needs no one-time code; the device's own check of the person is the second factor |
| D21 | **Build the Age Pass now**, with the suggested defaults: passes last 90 days, are issued 20 at a time, each is used once, and websites opt in through their policy (off by default) |

## Decided on 1 Nov 2026

The owner answered every waiting decision at once, and asked for the decided work to be done before the project moves on.

| # | Decision |
| :-: | :-- |
| D15 | **Approved**: `pillow` 13.0.0, `certifi` 2026.10.19, `filelock` 4.2.1, `setuptools` 84.1.0 (pypi.org, through uv's `override-dependencies`); re-run the ML tests after |
| D14b | **Approved**: `tmp` 0.2.7 (40 KB, registry.npmjs.org) in place of 0.2.6 |
| D1 | **Approved**: `three` **0.186.1** (20.4 MB, npm, MIT); 0.187.0 is still inside the cooldown. The home page's 3D hero, with the still artwork as its fallback |
| D2 | **Approved**: `next-intl` 4.14.9 (0.4 MB, npm, MIT; brings `@swc/core`). English and Hindi; the Hindi is machine-drafted and marked for review by a native speaker |
| D6b | **Docker**: Tesseract from Debian's `tesseract-ocr` in a `debian:bookworm-slim` image (~75 MB), plus `pytesseract` 0.3.13; `eng` model limited to MRZ characters first (D6c) |
| D7b | **Accept SFace, int8** (`face_recognition_sface_2021dec_int8.onnx`, 9.9 MB, OpenCV Zoo, Apache-2.0). Its training data (web-scraped, without consent) is stated in the model card; faces are compared in memory only |
| D8, O7 | **Aadhaar deferred**: finish the MRZ route first; Aadhaar waits for UIDAI's material or OVSE registration |
| O1 | **Repository**: https://github.com/Anubhav104401/Dwarpal — **public**; push now (history checked for secrets first) |
| Licence | **Apache-2.0** for the repository |
| O6 | Placeholder stays; publishing the practice statement stays blocked |
| O5 | The DPIA, practice statement and compliance map are labelled **draft, not legally reviewed** |
| O2 | **Oracle free tier** for Phase 8 when it starts (the owner creates the account and domain) |
| O2b | **Decided 1 Nov: stay on Always Free.** Oracle tenancy in India South (Hyderabad); the server is sized to the Always Free allowance, **2 Ampere cores / 12 GB** (1,500 OCPU-h, 9,000 GB-h a month), from the start, so nothing is disabled when the 30-day trial (16 cores / 96 GB) ends. Consequences: NFR-05 (50 people in a check) was met on 4 cores, so the capacity on 2 must be measured again in Phase 8; Always Free servers idle for 7 days (A1: memory under 20 %) can be reclaimed, which the running stack's memory use keeps clear of |
| D2b | *Optional, not blocking*: a Devanagari typeface for the Hindi pages (e.g. Noto Sans Devanagari, SIL OFL), which Geist lacks; today the visitor's system font is used. Not downloaded; ask when convenient |
| D2c | *Not a download*: a native Hindi speaker to review `apps/web/messages/hi.json`, machine-drafted on 1 Nov |
| D1b | *Optional, not blocking*: `@types/three` (TypeScript types for three.js, npm, 0.186.x) would replace the hand-written `apps/web/types/three.d.ts`. Not downloaded; ask when convenient |

## Decided on 27 Oct 2026

| # | Decision |
| :-: | :-- |
| D12 | **Approved**: Next.js 16.4.0 → 16.4.2 (`next`, `@next/swc-win32-x64-msvc`, `@next/env`) in both apps; done first |
| C1 | **Keep Geist**; the design system builds on it |
| D13 | **Done** (QR code on the Security page). **Approved**: `qrcode` 1.5.4 (+ `pngjs`, `yargs`, `dijkstrajs`) and `@types/qrcode` 1.5.6 |
| D4 | **Done** (axe tests, clean). **Approved**: `@axe-core/playwright` 4.14.0 (+ `axe-core` 4.14.0) |
| D3 | **Done**: WebKit passes; Firefox installed but **can't start on this Windows build** (side-by-side error; runs on CI). **Approved**: Playwright 1.64.0's Firefox and WebKit browsers (~200 MB, Playwright's CDN) |
| D5 | **Done** (Lighthouse ≥ 90; uses Playwright's headless shell). **Approved**: `@lhci/cli` 0.15.1 (+ `lighthouse` 13.5.0 and its dependencies) |
| D1, D2 | Not approved yet (`three` 0.186.1, 20.4 MB; `next-intl` 4.14.9 with `@swc/core`) — marketing hero and Hindi wait |
| D6–D11 | **Approved 27 Oct** ("approved", after the details below were listed), with the recommendations as written: Tesseract's own `eng` model limited to MRZ characters before any OCR-B model (D6c); SFace's training data checked before it is used (D7); UIDAI material from uidai.gov.in only (D8) |
| D7 | **Condition not met — not downloaded.** The SFace paper trains on CASIA-WebFace, VGGFace2 and MS-Celeb-1M ([arXiv 2205.12010](https://arxiv.org/pdf/2205.12010)); OpenCV Zoo's file doesn't say which ([model folder](https://github.com/opencv/opencv_zoo/blob/main/models/face_recognition_sface/README.md)). All three are web-scraped celebrity photos without consent; MS-Celeb-1M was withdrawn for that. **Needs a decision (D7b)**: accept SFace anyway, look for a face-match model trained on consented data, or drop selfie ↔ document matching from Phase 6 |
| D6 | **Install route needed (D6b)**: Tesseract on this Windows computer means running the UB Mannheim *installer* (an `.exe`, system-wide install), or I can run Tesseract inside a Docker container instead (Debian's `tesseract-ocr` 5.x package in a `debian:bookworm-slim` image, ~75 MB pulled), which is also how the API's production image would get it. I recommend Docker |
| D8 | **Blocked on material**: UIDAI's technical Secure QR specification and current certificate weren't found on uidai.gov.in; the 2021 regulations require OVSE registration (O7). Nothing downloaded |
| D9 | **Done 27–28 Oct**: pip-audit, Trivy, ZAP and Semgrep run and triaged (`docs/reports/phase-7.md`); Semgrep now reports 0 |
| D10, D11 | **Done 27 Oct**: Locust load test (result → **P1**); OpenTelemetry traces with collector, Tempo, Grafana (Prometheus approved, not pulled: no metrics yet) |
| D14 | **Done 27 Oct** for `tmp` 0.2.6, `uuid` 11.1.1, `basic-ftp` 6.2.1, `zod` 4.6.6 (`pnpm-workspace.yaml` overrides; Lighthouse test still passes): `pnpm audit` 8 → 4 findings. `body-parser` 1.20.9 **done 30 Oct** (after its cooldown; Lighthouse test passes; `pnpm audit` → 3). Left: `extract-zip` has no fix; and a **new** advisory (GHSA-7c78-jf6q-g5cm) says `tmp` 0.2.6 is affected too — fixed in **0.2.7** (40 KB, registry.npmjs.org, 27 May 2026): **needs approval** (D14b) |
| O1 | The owner creates an empty private GitHub repository and gives its URL; push only after the owner confirms |
| O6 | Placeholder stays in the practice statement; publishing it stays blocked |

## Downloads (each needs your explicit approval: file, source, size)

| # | What | Unblocks | Notes |
| :-: | :-- | :-- | :-- |
| D1 | `three` (npm) | Phase 5 marketing hero (3D face mesh) | exact version and size to be confirmed when asked |
| D2 | `next-intl` (npm) | Phase 5 English/Hindi | |
| D3 | Playwright Firefox and WebKit browsers (~200 MB) | Phase 5 exit: e2e on three engines | |
| D4 | `@axe-core/playwright` (npm) | Phase 5 exit: "axe clean" | |
| D5 | Lighthouse CI (npm) | Phase 5 exit: Lighthouse ≥ 90 | |
| D6 | **Reading the MRZ from a photo.** (a) Tesseract OCR **5.5.3** (Apache-2.0, released 24 Jul 2026): on Linux from Debian's `tesseract-ocr` package inside the API's Docker image; on Windows the UB Mannheim installer is only at 5.4.0 (`tesseract-ocr-w64-setup-5.4.0.20240606.exe`, 50.2 MB, github.com/UB-Mannheim/tesseract). (b) `pytesseract` 0.3.13 (Apache-2.0, 0.01 MB, PyPI; needs Pillow). (c) An **OCR-B model**: the usual one, `ocrb.traineddata` (11.4 MB, github.com/Shreeshrii/tessdata_ocrb), has **no licence**, so it can't be used. The alternatives are Tesseract's own `eng` model limited to MRZ characters (no extra download), or training our own OCR-B model | Phase 6 MRZ reading from photos (the MRZ *parser* is already built) | **choose (c)**: I recommend trying `eng` first and measuring it on the ICAO specimens |
| D7 | **Face match** (selfie ↔ document photo): OpenCV Zoo's **SFace** (Apache-2.0), `face_recognition_sface_2021dec.onnx` **38.7 MB** (or the int8 version, 9.9 MB), from github.com/opencv/opencv_zoo (`models/face_recognition_sface`, Git LFS); run by OpenCV, already installed | Phase 6 selfie ↔ document match | the files are Apache-2.0, but the **training data** behind them (face datasets like MS-Celeb-1M were withdrawn over consent) must be checked before use; the model never stores faces, only compares two in memory |
| D8 | **Aadhaar Secure QR**: UIDAI's signing certificate for Secure QR and its QR format, **from uidai.gov.in only**. My search didn't find the technical specification on the site, only the [Secure QR reader FAQ](https://uidai.gov.in/en/306-faqs/aadhaar-online-services/secure-qr-code-reader-beta.html), the [data and downloads page](https://uidai.gov.in/en/data-and-download) and the [Authentication and Offline Verification Regulations, 2021](https://old.uidai.gov.in/images/The_Aadhaar_Authentication_and_Offline_Verifications_Regulations_2021-_Clean_copy-30122025.pdf). The certificate listed there expired in 2021: the current one must be found | Phase 6 Aadhaar | the regulations require an **Offline Verification Seeking Entity** to verify UIDAI's digital signature before accepting an Aadhaar QR, so registration may be needed first (O7) |
| D9 | **Security scanners**, development only: `pip-audit` **2.10.1** (Apache-2.0, 0.06 MB + ~20 small deps, PyPI); **Semgrep** 1.182.0 (LGPL-2.1, **59–72 MB** wheel + 27 deps, PyPI; its rule registry is fetched at run time); **Trivy** 0.76.0 (Apache-2.0, Docker image `aquasec/trivy`, **63 MB** compressed; downloads its vulnerability database, ~0.5 GB, on first run); **OWASP ZAP** (Apache-2.0, Docker image `zaproxy/zap-stable:20261016`, **1.2 GB** compressed) | Phase 7 scans | could approve pip-audit alone first: smallest, and it covers the Python dependencies |
| D10 | **Load testing**: **Locust** 2.46.7 (MIT, 1.5 MB, PyPI, released 4 Oct) + 15 deps (Flask, gevent, pyzmq, psutil and others, roughly 30 MB together) | Phase 7 load tests (p95 latency targets) | development only |
| D11 | **Observability**: in the API, `opentelemetry-sdk` **1.45.1**, `opentelemetry-exporter-otlp-proto-http` 1.45.1, `opentelemetry-instrumentation-fastapi` **0.66b1** (a *beta*, as all its versions are) — Apache-2.0, all under 1 MB, PyPI; for local viewing, Docker images `otel/opentelemetry-collector-contrib:0.163.1` (116 MB), `grafana/grafana:13.0.11` (358 MB, AGPL-3.0), `grafana/tempo:2.10.9` (38 MB, AGPL-3.0), `prom/prometheus:v3.13.4` (107 MB, Apache-2.0); sizes compressed, linux/amd64 | Phase 7 observability | the libraries go into the API itself; the images only run locally. Grafana and Tempo are AGPL, which is fine to *run* but matters if modified and offered as a service |
| ~~D12~~ | ~~Upgrade Next.js 16.4.0 → 16.4.2~~ | **done 27 Oct** — both apps on 16.4.2; `pnpm audit`: no known vulnerabilities; all checks and the 7 browser tests pass | |
| D13 | A QR-code library for the web app (e.g. `qrcode`, npm; version and size to be confirmed when asked) | Phase 5: a QR code on the console's *Security* page, so phones can scan the one-time-code secret (today: text and an `otpauth://` link) | |
| **D15** | **Python security fixes** (from pip-audit and Trivy, 27 Oct), forced with uv's `override-dependencies`, from pypi.org: `pillow` **13.0.0** (7.3 MB wheel, 16 Oct; a *major* version, comes in through torchvision — training only), `certifi` 2026.10.19 (0.14 MB), `filelock` 4.2.1 (0.16 MB), `setuptools` 84.1.0 (0.8 MB) — all past the cooldown | clears 47 known flaws (6 critical) | I'd re-run the ML tests after: Pillow 13 may change image decoding |
| D14b | `tmp` **0.2.7** (40 KB, registry.npmjs.org, 27 May 2026) replacing the approved 0.2.6, which a new advisory (GHSA-7c78-jf6q-g5cm) also covers | the last fixable `tmp` finding | development only |
| D14 | Patched versions of Lighthouse CI's dependencies, forced with `pnpm.overrides`, from registry.npmjs.org: `tmp` 0.2.6 (40 KB), `uuid` 11.1.1 (134 KB), `basic-ftp` 6.2.1 (155 KB), `zod` 4.6.6 (6.1 MB); and `body-parser` 1.20.9 (62 KB), released 22 Oct, so only after 29 Oct (cooldown). `extract-zip` has **no** fixed version | clears 7 of `pnpm audit`'s 8 findings (1 low, 1 moderate, 6 high), all in development-only tools run against local servers; nothing ships in the apps | overriding may break Lighthouse CI: re-run its test after |

## Design choices

| # | Question | Unblocks |
| :-: | :-- | :-- |
| ~~P1~~ | **Decided 28 Oct: (a), then (b) if needed.** Done: the age model sees the 3 sharpest frames (safety lines re-checked, unchanged within chance); dynamic INT8 tried — slower, not adopted; a 1 s queue for workers. Result: server processing p95 1.21 s for 50 people at a realistic pace | |
| ~~P2~~ | **Decided 29 Oct: 50 people in a check** — each sending an attempt every ~20 s; 4 cores kept. Met on the laptop (analysis p95 1.21 s, throttled); to be measured again on the Phase 8 server. Design documents reworded (NFR-05, §10/§13 of the implementation design, architecture quality table) | |
| C1 | The console/marketing **typeface** (the design says: chosen from a type specimen). The web app already uses **Geist** (installed in Phase 1): keep it, or choose another? | Phase 5 design system |
| ~~D16~~ | **Decided 30 Oct: (a)**, framing per session by the return address's origin, COOP kept — **done** (§5.5.7 of the book; `@dwarpal/js`, `@dwarpal/react`, the shop uses the modal). Was: **How the browser SDK opens the check** (`@dwarpal/js`, `@dwarpal/react`, roadmap Phase 5). The design's first choice is a **modal with an iframe**, then a **popup**, then a full **redirect** (§4.1 of the implementation design). Our own security headers forbid the first two today: `frame-ancestors 'none'` stops any site framing the verify page, and `Cross-Origin-Opener-Policy: same-origin` cuts a popup off from the page that opened it. Options: (a) allow framing *per session*, only by the origin of the session's `return_url` (which the website registered with its secret key), and keep COOP for everything else — I recommend this; (b) also relax COOP on `/v/*` to allow the popup fallback; (c) redirect only for now — the SDK still saves websites the plumbing, and the shop already works this way | the JS and React SDKs; their tests |

## Things only you can do

| # | What | Unblocks |
| :-: | :-- | :-- |
| O1 | Push to GitHub and let remote CI run (nothing has been pushed since Phase 3) | CI evidence for every phase report |
| O2 | Choose a VM provider and create the account; choose a domain and add DNS records | Phase 8 deployment |
| O3 | Your own Aadhaar QR for testing (never anyone else's) | Phase 6 Aadhaar end-to-end |
| O4 | More people for genuine liveness and age attempts (ages, skin tones, glasses) | Phase 3 exit criterion; fairness of the anti-spoofing model |
| O5 | Legal review of the DPIA and practice statement (drafts in `docs/privacy/`) for your launch markets | production launch |
| O6 | The operator's name and contact details for data-protection requests (practice statement §8) | publishing the practice statement |
| O7 | Register Dwarpal with UIDAI as an **Offline Verification Seeking Entity** ([OVSE registration](https://uidai.gov.in/en/ovse)), if the Aadhaar route goes ahead; check what the 2021 regulations require of it | Phase 6 Aadhaar in production (testing with your own QR is unaffected) |

## Morning summary — night of 28–29 Oct

**Waiting for you** (each row above has the details):
- **D15** — Python security fixes (`pillow` 13.0.0 and three small ones): approve the downloads?
- **D14b** — `tmp` 0.2.7 (40 KB) in place of the approved 0.2.6, which a newer advisory also covers. `body-parser` 1.20.9 (already approved) can go in from 11:38 UTC today.
- **D7b** — SFace's training data failed your condition; not downloaded. Accept anyway, look for a consented model, or drop selfie ↔ document matching?
- **D6b** — Tesseract via Docker (recommended) or the Windows installer?
- **D8 / O7** — Aadhaar is blocked on UIDAI material, and probably on OVSE registration.
- **O1** — the GitHub repository's URL, so CI (and Firefox) can run.

**Done tonight** (all committed; every check, the browser tests and the book at 100 %):
- `22d2b2f` P2 recorded: NFR-05 means 50 people in a check, on 4 cores; the design documents now say so.
- `dd14d78` Webhook endpoints can be switched off and on (API, console, tests).
- `e081571` Sessions can be searched by outcome and by the website's reference.
- `8587058` A browser test of the member controls.
- `7a61996` Recovery codes (10, single-use, stored as HMACs) and switching one-time codes off (password + code).
- `c25ac7f` The web app's script policy uses a per-page nonce — ZAP's remaining warning fixed.
- `8cad67a` Valkey, PostgreSQL and inference stopped during a load test: nothing passed, all recovered; one 500 found and fixed.
- `ce9a191` Metrics, a Grafana dashboard and burn-rate alerts (Prometheus, approved under D11): request totals labelled by route pattern only; alerts on the 99.9 % promise and on NFR-05. Checked end to end on this laptop. Alerts aren't delivered anywhere yet — that needs Alertmanager and a destination, in Phase 8.
- `c64dbe0` The console's 30-day counts as a daily stacked chart (colours checked for colour-blind readers, numbers on hover or keyboard focus, and as a table).
- `d0bb90d` The age model's page in the console: which model decides, whether it may decide live checks, what it learnt from, and its lines with their measured worst cases — and nothing of its build.
- `946565f` The console's sidebar and ⌘K/Ctrl+K command palette, as the design asks. Lighthouse and axe still pass.
- Added later (29 Oct, after you said to leave deployment for now): the dashboard's face-check figures — median time to a decision, share rejected as a likely attack, share sent to a stronger check — from new daily counts by band of time (migration 0009; no exact times kept).
- Not done, because each needs something from you or doesn't exist yet: step-up conversion (needs the Phase 6 verifiers), the policy editor's projected step-up rate, and fairness charts on the model page (no fairness results are published yet).

## Done overnight (no decision needed)

Kept up to date as work lands; see the commit log for details.

- `95f3e91` — **Phase 4 complete**: console accounts, Argon2id, TOTP, CSRF, roles; published OpenAPI document; Schemathesis contract tests (which found and fixed a missing `Allow` header).
- **Phase 6 begun**: the MRZ (passport/ID) parser and age rule, proved against ICAO's specimens and generated documents (`docs/reports/phase-6.md`).
- **Phase 7 begun**: `503` with `Retry-After` when the database or Valkey is down; inference failures never pass; security headers on every API answer (`docs/reports/phase-7.md`).
- **Phase 5 begun**: the console's first pages — sign-in/sign-up, organisations, members, keys (shown once), audit log with chain badge — tested in Chromium (`docs/reports/phase-5.md`).
- `478bddb`, `653d67f` and the next commit — **console pages**: a project's sessions with decision traces, counts and policies; webhooks (secret once, test, deliveries, replay); one-time-code set-up; members' roles and removal, with an owner always kept.
- **Phase 7 documents**: threat model (`docs/security/threat-model.md`), DPIA and practice statement drafts (`docs/privacy/`).
