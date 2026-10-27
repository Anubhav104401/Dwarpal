# Decisions waiting for the owner

Work that needs your answer — a download, a design choice, an account, or something only you can do — is collected here instead of stopping the work. Everything else carries on. Each item says what it unblocks.

**Started:** 26 Oct 2026, overnight run. **Phase 4 is complete** (commits `450bfba`, `7d730ee`, `95f3e91`).

## Decided on 27 Oct 2026

| # | Decision |
| :-: | :-- |
| D12 | **Approved**: Next.js 16.4.0 → 16.4.2 (`next`, `@next/swc-win32-x64-msvc`, `@next/env`) in both apps; done first |
| C1 | **Keep Geist**; the design system builds on it |
| D13 | **Approved**: `qrcode` 1.5.4 (+ `pngjs`, `yargs`, `dijkstrajs`) and `@types/qrcode` 1.5.6 |
| D4 | **Approved**: `@axe-core/playwright` 4.14.0 (+ `axe-core` 4.14.0) |
| D3 | **Approved**: Playwright 1.64.0's Firefox and WebKit browsers (~200 MB, Playwright's CDN) |
| D5 | **Approved**: `@lhci/cli` 0.15.1 (+ `lighthouse` 13.5.0 and its dependencies) |
| D1, D2 | Not approved yet (`three` 0.186.1, 20.4 MB; `next-intl` 4.14.9 with `@swc/core`) — marketing hero and Hindi wait |
| D6–D11 | To prepare next: exact files, sources and sizes will be brought back for approval before any download |
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
| D6 | Tesseract OCR + an MRZ (OCR-B) model | Phase 6 MRZ reading from photos | the MRZ *parser* is built without it |
| D7 | A face-match model (e.g. SFace, licence to verify) | Phase 6 selfie ↔ document match | |
| D8 | UIDAI Secure QR specification + offline-verification certificate | Phase 6 Aadhaar | official sources only |
| D9 | Security scanners: Semgrep, pip-audit, Trivy, OWASP ZAP | Phase 7 scans | |
| D10 | Locust | Phase 7 load tests | |
| D11 | OpenTelemetry SDK + collector, Grafana | Phase 7 observability | |
| ~~D12~~ | ~~Upgrade Next.js 16.4.0 → 16.4.2~~ | **done 27 Oct** — both apps on 16.4.2; `pnpm audit`: no known vulnerabilities; all checks and the 7 browser tests pass | |
| D13 | A QR-code library for the web app (e.g. `qrcode`, npm; version and size to be confirmed when asked) | Phase 5: a QR code on the console's *Security* page, so phones can scan the one-time-code secret (today: text and an `otpauth://` link) | |

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

## Done overnight (no decision needed)

Kept up to date as work lands; see the commit log for details.

- `95f3e91` — **Phase 4 complete**: console accounts, Argon2id, TOTP, CSRF, roles; published OpenAPI document; Schemathesis contract tests (which found and fixed a missing `Allow` header).
- **Phase 6 begun**: the MRZ (passport/ID) parser and age rule, proved against ICAO's specimens and generated documents (`docs/reports/phase-6.md`).
- **Phase 7 begun**: `503` with `Retry-After` when the database or Valkey is down; inference failures never pass; security headers on every API answer (`docs/reports/phase-7.md`).
- **Phase 5 begun**: the console's first pages — sign-in/sign-up, organisations, members, keys (shown once), audit log with chain badge — tested in Chromium (`docs/reports/phase-5.md`).
- `478bddb`, `653d67f` and the next commit — **console pages**: a project's sessions with decision traces, counts and policies; webhooks (secret once, test, deliveries, replay); one-time-code set-up; members' roles and removal, with an owner always kept.
- **Phase 7 documents**: threat model (`docs/security/threat-model.md`), DPIA and practice statement drafts (`docs/privacy/`).
