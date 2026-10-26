# Phase 5 report — front-end excellence

**Dates:** from 26 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Status:** 🟡 in progress — the console's first pages are built and tested; the design system, marketing site, Hindi and the exit tests wait for decisions and downloads ([pending decisions](pending-decisions.md)).

**Exit (from the roadmap):** Lighthouse ≥ 90 in all categories on key pages; axe clean; Playwright passes on Chromium, Firefox and WebKit.

## What is built

| Area | Delivered |
| :-- | :-- |
| Console client (`lib/console-api.ts`) | typed client for the console API via `/console-api`; CSRF token on every change, never on reads; problem answers as `ConsoleError` |
| Pages | `/console` (sign in, one-time code when asked, create account, organisations); `/console/org_…` (members and add-member, projects and create-key shown once, audit log with chain badge); `/console/org_…/prj_…` (test/live switch, 30-day counts, sessions with *Show older*, each session's decision trace, policies and add-version) |
| Proxy | `next.config.ts` rewrites `/console-api/*` → API `/console/v1/*` (one origin, like Caddy in production) |
| API | `GET /console/v1/orgs/{org}/projects` (any member); under `…/projects/{project}/`: `GET sessions`, `GET sessions/{id}` (decision trace, no token), `GET analytics` (analytics roles), `GET`/`POST policies` (adding: policy managers). Every project route checks the project belongs to the organisation named (`project_in`) |
| Accessibility | labels tied to controls; `role="alert"` errors; `role="status"` for the new key; sections named by headings; tests locate by role and label |
| Book | §5.5, §5.5.1, §5.5.2; ten new walkthroughs; twelve re-explained |

## What was measured

| Check | Result |
| :-- | :-- |
| Web unit tests | 21 passed (5 new for the console client) |
| API tests | a new test: an analyst reads sessions, a trace (numbers, no token) and counts, may not add a policy; an owner may; another organisation's project is 404 |
| End-to-end (Chromium) | **6 passed**: the age-check story, plus console sign-up → key (shown once) → intact audit log, then a website's server creates a session with that key, it appears on the project's page with an empty trace, and an owner adds a policy version; and a wrong password refused like an unknown account |
| Lint / typecheck | clean |
| Visual check | screenshot of the organisation page reviewed: layout, key box and audit badge as intended |

## Findings

- **Next.js 16.4.0 reports a known security vulnerability** during `next build` (an advisory fetched from the npm registry); upgrading is a download → pending decision D12.
- Next.js's route announcer is also `role="alert"`, so tests must pick the alert with text.

## Open items

1. Design system and typeface (C1); marketing site (D1); Hindi (D2); three-engine, axe and Lighthouse exit tests (D3–D5).
2. Console pages still to build without new packages: webhooks and deliveries, one-time-code enrolment, members' role changes; search and filters for sessions. (Sessions, traces, counts and policies: done.)
