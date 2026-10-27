# Phase 5 report — front-end excellence

**Dates:** from 26 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Status:** 🟡 in progress — the console's first pages are built and tested; the design system, marketing site, Hindi and the exit tests wait for decisions and downloads ([pending decisions](pending-decisions.md)).

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

## What was measured

| Check | Result |
| :-- | :-- |
| Web unit tests | 23 passed (7 new for the console client) |
| API tests | a new test: an analyst reads sessions, a trace (numbers, no token) and counts, may not add a policy; an owner may; another organisation's project is 404; and a webhook test: an owner adds, tests, replays and removes an endpoint, an analyst can neither add nor list, the audit log names the person; and a members test: the owner rules, the last owner, and an audit entry for each change |
| End-to-end (Chromium) | **7 passed**: the age-check story, plus console sign-up → key (shown once) → intact audit log, then a website's server creates a session with that key, it appears on the project's page with an empty trace, and an owner adds a policy version and a webhook endpoint (secret shown, test event pending); a wrong password refused like an unknown account; and one-time codes turned on, then required at sign-in |
| Lint / typecheck | clean |
| Visual check | screenshot of the organisation page reviewed: layout, key box and audit badge as intended |

## Findings

- **Next.js 16.4.0 reported known security vulnerabilities** during `next build` (two critical, one high). **Fixed 27 Oct**: upgraded to 16.4.2 (decision D12); `pnpm audit` clean; builds no longer stop with `SecurityFatalError`.
- Next.js's route announcer is also `role="alert"`, so tests must pick the alert with text.
- **Contract tests found a 500**: a NUL character in a text field (an e-mail address) reached PostgreSQL, which can't store it. Fixed for every route in `http/problems.py` (`422 invalid_text`), with a regression test. It appeared on one random run only.

## Open items

1. Design system and typeface (C1); marketing site (D1); Hindi (D2); three-engine, axe and Lighthouse exit tests (D3–D5).
2. Console pages still to build without new packages: search and filters for sessions; switching a webhook endpoint off; switching one-time codes off or resetting them, recovery codes; a browser test for member controls. QR code for one-time codes needs a library (download). (Sessions, traces, counts, policies, webhooks, one-time-code set-up, member roles: done.)
