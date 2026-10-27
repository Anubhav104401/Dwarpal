# Decisions waiting for the owner

Work that needs your answer — a download, a design choice, an account, or something only you can do — is collected here instead of stopping the work. Everything else carries on. Each item says what it unblocks.

**Started:** 26 Oct 2026, overnight run. **Phase 4 is complete** (commits `450bfba`, `7d730ee`, `95f3e91`).

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
| D6–D11 | **Details ready** (27 Oct): exact versions, sources, sizes and licences are in the Downloads table below, for approval item by item. All versions passed the 7-day cooldown |
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
| D14 | Patched versions of Lighthouse CI's dependencies, forced with `pnpm.overrides`, from registry.npmjs.org: `tmp` 0.2.6 (40 KB), `uuid` 11.1.1 (134 KB), `basic-ftp` 6.2.1 (155 KB), `zod` 4.6.6 (6.1 MB); and `body-parser` 1.20.9 (62 KB), released 22 Oct, so only after 29 Oct (cooldown). `extract-zip` has **no** fixed version | clears 7 of `pnpm audit`'s 8 findings (1 low, 1 moderate, 6 high), all in development-only tools run against local servers; nothing ships in the apps | overriding may break Lighthouse CI: re-run its test after |

## Design choices

| # | Question | Unblocks |
| :-: | :-- | :-- |
| C1 | The console/marketing **typeface** (the design says: chosen from a type specimen). The web app already uses **Geist** (installed in Phase 1): keep it, or choose another? | Phase 5 design system |

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

## Done overnight (no decision needed)

Kept up to date as work lands; see the commit log for details.

- `95f3e91` — **Phase 4 complete**: console accounts, Argon2id, TOTP, CSRF, roles; published OpenAPI document; Schemathesis contract tests (which found and fixed a missing `Allow` header).
- **Phase 6 begun**: the MRZ (passport/ID) parser and age rule, proved against ICAO's specimens and generated documents (`docs/reports/phase-6.md`).
- **Phase 7 begun**: `503` with `Retry-After` when the database or Valkey is down; inference failures never pass; security headers on every API answer (`docs/reports/phase-7.md`).
- **Phase 5 begun**: the console's first pages — sign-in/sign-up, organisations, members, keys (shown once), audit log with chain badge — tested in Chromium (`docs/reports/phase-5.md`).
- `478bddb`, `653d67f` and the next commit — **console pages**: a project's sessions with decision traces, counts and policies; webhooks (secret once, test, deliveries, replay); one-time-code set-up; members' roles and removal, with an owner always kept.
- **Phase 7 documents**: threat model (`docs/security/threat-model.md`), DPIA and practice statement drafts (`docs/privacy/`).
