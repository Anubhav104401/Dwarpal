# Phase 5 report — front-end excellence

**Dates:** from 26 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Status:** 🟡 in progress — the console is built and tested; the exit tests are built and pass on Chromium and WebKit (Firefox can't start on this computer, so it waits for CI); the design system's first version is built (Geist kept); the marketing site is built, with its 3D hero (1 Nov, D1); Hindi is next (D2) ([pending decisions](pending-decisions.md)).

**Exit (from the roadmap):** Lighthouse ≥ 90 in all categories on key pages; axe clean; Playwright passes on Chromium, Firefox and WebKit.

## What is built

| Area | Delivered |
| :-- | :-- |
| Console client (`lib/console-api.ts`) | typed client for the console API via `/console-api`; CSRF token on every change, never on reads; problem answers as `ConsoleError` |
| Pages | `/console` (sign in, one-time code when asked, create account, organisations); `/console/org_…` (members and add-member, projects and create-key shown once, audit log with chain badge); `/console/org_…/prj_…` (test/live switch, 30-day counts, sessions with *Show older*, each session's decision trace, policies and add-version, webhooks: add (secret shown once), test, deliveries, replay, remove); `/console/account` (one-time codes: secret, confirm); members' role menu and Remove for owners and admins |
| Proxy | `next.config.ts` rewrites `/console-api/*` → API `/console/v1/*` (one origin, like Caddy in production) |
| API | `GET /console/v1/orgs/{org}/projects` (any member); under `…/projects/{project}/`: `GET sessions`, `GET sessions/{id}` (decision trace, no token), `GET analytics` (analytics roles), `GET`/`POST policies` (adding: policy managers). `GET`/`POST webhooks`, `DELETE webhooks/{id}`, `POST webhooks/{id}/test`, `GET webhooks/{id}/deliveries`, `POST webhook-deliveries/{id}/replay` (all: webhook managers; analysts can't list them). `PATCH`/`DELETE /orgs/{org}/members/{user}` (only owners touch owners; the last owner stays; owner rows locked against races). Every project route checks the project belongs to the organisation named (`project_in`) |
| Accessibility | labels tied to controls; `role="alert"` errors; `role="status"` for the new key; sections named by headings; tests locate by role and label |
| Book | §5.5, §5.5.1–§5.5.4; thirteen new walkthroughs; seventeen re-explained |

| Design system | OKLCH tokens in `globals.css` (ink, saffron, teal; display size; Geist Sans and Mono; motion presets); `components/ui.tsx` (button tones and sizes, panel, card, input, field, alert, notice, badge); specimen at `/design`, axe-checked in light and dark; every page moved from zinc to ink |
| SDKs (30 Oct, D16) | `@dwarpal/js` (modal with an iframe, or redirect; `postMessage` protocol with origin checks; link check) and `@dwarpal/react` (`VerifyAgeButton`, `useDwarpal`); the verify page may be framed only by its session's return origin (`GET /v1/flow/sessions/{id}/frame-ancestor`, read by `proxy.ts`), and offers *open in a full page* when the frame can't go on; the demo shop opens the check in the modal |
| Developer guides (31 Oct) | `docs/developers/`: integration overview and quick start, browser SDKs, Node.js SDK, integration checklist (FR-15); a README per SDK; every code sample type-checked against the SDKs |
| Policy editor (31 Oct) | offers the model's own lines (age + risk budget; the old fixed 2 % matched none of the trained model's lines, so every version would have been refused); shows the projected adult step-up rate per band from the test split (`adults` in the manifest, via `export --manifest-only`) |
| Home page (1 Nov) | the marketing site's sections: how it works, privacy promise, live accuracy table (public `GET /v1/model`: the model's description without its scores), developer quick-start, compliance map, questions, demo; a still artwork in place of the 3D hero (D1); axe clean in both themes; Lighthouse 95 / 100 / 100 / 100 and indexable |
| Exit tests | Playwright projects for Chromium, Firefox, WebKit (`E2E_ENGINES` picks); axe on shop, verify page and every console page (WCAG 2.2 A/AA); Lighthouse CI on the shop, console sign-in and verify page (≥ 0.9 in each category; private pages must stay `noindex`); QR code on the Security page |

## What was measured

| Check | Result |
| :-- | :-- |
| Web unit tests | 23 passed (7 new for the console client) |
| API tests | a new test: an analyst reads sessions, a trace (numbers, no token) and counts, may not add a policy; an owner may; another organisation's project is 404; and a webhook test: an owner adds, tests, replays and removes an endpoint, an analyst can neither add nor list, the audit log names the person; and a members test: the owner rules, the last owner, and an audit entry for each change |
| Exit criteria (27 Oct) | **15 passed** with `E2E_ENGINES=chromium,webkit`: axe clean on all key pages in both engines; Lighthouse — shop 98/100/100/100, console sign-in 97/100/96 (search: noindex by design), verify page 98/100/100 (performance/accessibility/best practices/search). **Firefox not run**: it can't start on this computer |
| End-to-end (Chromium) | **7 passed**: the age-check story, plus console sign-up → key (shown once) → intact audit log, then a website's server creates a session with that key, it appears on the project's page with an empty trace, and an owner adds a policy version and a webhook endpoint (secret shown, test event pending); a wrong password refused like an unknown account; and one-time codes turned on, then required at sign-in |
| Lint / typecheck | clean |
| Visual check | screenshot of the organisation page reviewed: layout, key box and audit badge as intended |

## Findings

- **Next.js 16.4.0 reported known security vulnerabilities** during `next build` (two critical, one high). **Fixed 27 Oct**: upgraded to 16.4.2 (decision D12); `pnpm audit` clean; builds no longer stop with `SecurityFatalError`.
- Next.js's route announcer is also `role="alert"`, so tests must pick the alert with text.
- **Firefox and full Chromium can't start on this Windows 11 build (26200)**: "side-by-side configuration is incorrect" — Windows can't resolve the private assemblies they declare (`mozglue`; Chrome's `156.0.8078.4`), though the files are present; reinstalling and an older Chromium fail the same way. Not changed (system settings). Workarounds: Lighthouse uses Playwright's headless shell; Firefox runs on CI. Playwright fetched the browsers from `cdn.playwright.dev`, its current CDN, not the `playwright.azureedge.net` named when approval was asked.
- **axe found two real failures**: `brand-600` text on a saffron tint at 2.8:1 (fixed with `brand-700`, ≥ 5.3:1), and webhook checkboxes too close together (WCAG 2.2 target size; rows made taller). A third was a false alarm (colours measured mid-fade); the test now waits for animations.
- **WebKit drops `Secure` cookies on plain-HTTP localhost**: test servers use a plain cookie; a new API test checks the production `__Host-` cookie.
- **Lighthouse CI's dependencies carry 8 known flaws** (dev-only, never shipped): decision D14.
- **Contract tests found a 500**: a NUL character in a text field (an e-mail address) reached PostgreSQL, which can't store it. Fixed for every route in `http/problems.py` (`422 invalid_text`), with a regression test. It appeared on one random run only.

- **A timing flake under load (30 Oct)**: in a 22-minute run of every browser test in two engines, the age-check story timed out once in Chromium at the first pose ("turn your head to your left"): the face tracker in the browser never confirmed the pose from the fake camera in time, so nothing was uploaded. Run alone it passed. To watch: if it recurs, the pose step's wait (or the test's 90 s limit) needs room on a busy machine.

## Open items

1. Design system: a display serif and token colours for the verify flow's icons; Hindi (D2, approved 1 Nov) in progress; three.js typed by hand until `@types/three` is approved (D1b); the compliance map needs the legal review (O5) before publishing; Firefox proof on CI (O1); Lighthouse CI dependency fixes (D14).
2. Console pages: the planned set is done — sessions (with search), traces, counts, policies, webhooks (with an on/off switch), one-time codes (with a QR code, recovery codes, and switching off), member roles (with a browser test). The rest of the design's list was added on 29 Oct: a daily chart of the counts, the age model's page, and the sidebar with a command palette (⌘K). Later on 29 Oct, the dashboard's face-check figures followed: the median time to a decision (a band of seconds, against the 15 s target), and the shares rejected as likely attacks and sent to a stronger check, from new daily counts by band of time (migration 0009). The policy editor's projected step-up rate followed on 31 Oct. Still not built: step-up conversion (needs the Phase 6 verifiers), and the model page's fairness charts (no fairness results are published yet).
