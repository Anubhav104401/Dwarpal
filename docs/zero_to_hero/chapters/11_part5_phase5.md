## 5.5 Phase 5 — front-end excellence

Phase 5 gives Dwarpal the faces people see: the console for its customers, a polished verify flow, a marketing site, and documented SDKs. From the roadmap (§3.9):

| Area | Status |
| :-- | :-- |
| **Console** — sign-in, organisations, members, keys, audit log | 🟡 first pages (§5.5.1); a project's sessions, decision traces, counts and policies (§5.5.2); webhooks (§5.5.3); one-time-code set-up and a command palette to come |
| Design system — tokens, typography, components, motion | 🗓 waits for the typeface decision; the brand colours in `globals.css` are already used |
| Marketing site (3D face-mesh hero) | 🗓 waits for an approved 3D library |
| Verify flow in English and Hindi | 🗓 waits for an approved translation library |
| Exit tests on three browser engines, accessibility and Lighthouse checks | 🗓 wait for approved downloads |

### 5.5.1 The console's first pages

Phase 4 built the console's API — accounts, sessions, one-time codes, roles, members, keys, the audit log. These are its first pages, in the same web app as the verify page, under `/console`:

- **`/console`** — sign in or create an account (and, if switched on, enter a one-time code); once signed in, your organisations;
- **`/console/org_…`** — an organisation's members (and, for owners and admins, a form to add one), its projects and API keys (and a form to create a key, shown **once**), and for owners and admins the audit log, with a badge saying whether its chain is intact.

!!! key "Key idea — the page hides, the API decides"
    Each form appears only for roles allowed to use it, using a copy of the role matrix (`CAN`). That copy only spares people buttons that would fail. Anyone can change a page in their own browser, so the API checks every request again (`domain/roles.py`) and refuses what the role doesn't allow.

**One origin.** The pages call `/console-api/…` on their own site, and Next.js passes those requests on to the API (`next.config.ts`), as Caddy will in production. So the session cookie, its `SameSite` rule and the `__Host-` prefix all work as designed, and the API's `Origin` check sees the console's own address.

**Accessible by construction.** Every field has a label tied to it (`htmlFor` and `id`); errors are announced with `role="alert"`, a new key with `role="status"`; every section is named by its heading. The browser test finds everything the way a screen reader would — by role and by label — so a page that loses its labels fails its test.

!walk apps/web/lib/console-api.ts

!walk apps/web/lib/console-api.test.ts

!walk apps/web/components/console-shell.tsx

!walk apps/web/app/console/page.tsx

!walk apps/web/app/console/console-home.tsx

!walk apps/web/app/console/[org]/page.tsx

!walk apps/web/app/console/[org]/organisation-view.tsx

!walk e2e/tests/console.spec.ts

The rest changed existing files, each re-explained in its walkthrough: `next.config.ts` (the `/console-api` passage), and the console API's new list of an organisation's projects (`app/console.py`, `http/console.py`, `test_api.py`).

**What the tests prove**:
- the client sends the CSRF token on every change and never on a read, treats "nobody signed in" as an answer rather than an error, and reads the audit log's verdict;
- in a real browser, a new customer signs up, opens their organisation, creates a key that is shown once (and gone after a reload), and sees an intact audit log listing it;
- a wrong password is refused with the same words as an unknown account.

!!! honest "Honest limitation"
    These pages are deliberately plain: the design system, with its type, motion and components, waits for the typeface decision. The console doesn't yet show webhooks, which their API already provides, and it has no pages for switching on one-time codes. (Sessions, analytics and policies came next, in §5.5.2.)

### 5.5.2 A project's page: sessions, decision traces, counts, policies

The organisation page now links each project to its own page, `/console/org_…/prj_…`. It shows, for test or live data (a switch at the top, test by default):

- **the last 30 days' counts**, one tile per outcome;
- **the sessions**, newest first, twenty at a time, with *Show older sessions*;
- **the decision trace** of any session: each attempt's outcome, its reasons, and the numbers it rested on — the probability of being over the age, the line it was compared with, the liveness evidence. These are the numbers Dwarpal already stores; the trace stores nothing new, and it never mints a token;
- **the policies**, presets and the project's own versions, with a form — for owners, admins and developers — to add the next version of a policy.

The console API gained five routes under `/console/v1/orgs/{org}/projects/{project}/…`: `sessions`, `sessions/{id}`, `analytics`, and `policies` (read and add). They reuse the website API's use cases, so a page and a website see the same sessions, counts and policies.

!!! key "Key idea — the project must belong to the organisation in the address"
    The console's tenant is the **organisation**: row-level security lets a member see their organisation's rows. A project page's address names an organisation *and* a project. If the API checked only the organisation, a member of A could write A's ID beside a project of B's. So `project_in` reads the project as the organisation and refuses — "not found" — unless it belongs to it. A test tries exactly that.

!walk apps/web/app/console/[org]/[project]/page.tsx

!walk apps/web/app/console/[org]/[project]/project-view.tsx

The rest changed existing files, each re-explained in its walkthrough: the console API (`app/console.py`, `http/console.py`), its test (`test_api.py`), the published contract (`docs/api/openapi.json`), the client and its test (`console-api.ts`, `console-api.test.ts`), the organisation page's project links (`organisation-view.tsx`), and the browser test (`console.spec.ts`).

**What the tests prove**:
- an analyst reads a project's sessions, a passed session's trace with its numbers (and no token), and its counts, but may not add a policy version; an owner may;
- a project of another organisation, named under this organisation's address, is not found;
- the client builds the sessions address with the mode and cursor exactly, and reads a trace's scores unchanged;
- in a real browser, a website's server creates a session with the console's new key; the session appears on the project's page; its trace says it has no attempts; and an owner's new policy version is listed at once.

!!! honest "Honest limitation"
    The counts are totals, not a chart: the chart waits for the design system. Sessions can't yet be searched or filtered by outcome, and the trace shows numbers, not explanations of them; the reasons' meanings are in §5.3.

### 5.5.3 Webhooks in the console

A project's page now ends with a **Webhooks** panel, for the chosen mode: its endpoints, a form to add one, and for each one *Send test*, *Deliveries* (with *Replay* for a finished delivery) and *Remove*. A new endpoint's signing secret is shown once, exactly like a new API key.

The console API gained six routes under `…/projects/{project}/`: `webhooks` (list and add), `webhooks/{id}` (remove), `webhooks/{id}/test`, `webhooks/{id}/deliveries`, and `webhook-deliveries/{id}/replay`. They call the **same use cases** as the website API (§5.4.3) — the same allowed events, the same SSRF guard, the same limit of 16 endpoints. To make that possible, those use cases no longer take the website API's `Caller` (a key, with its project and mode); they take the project, organisation, mode and **actor** — whoever the audit log should name. A key names itself `api_key:…`; a person, `user:…`.

!!! key "Key idea — some things only the people who change them may see"
    Analysts may read sessions, traces and counts, but not webhooks: the API refuses even to *list* endpoints to them (`403`), and the page doesn't show the panel. An endpoint's address says where a project's events go — useful to an attacker, and of no use to someone reading reports.

!walk apps/web/app/console/[org]/[project]/webhooks-panel.tsx

The rest changed existing files, each re-explained in its walkthrough: the webhook use cases and routes (`app/webhooks.py`, `http/webhooks.py`), the console API (`app/console.py`, `http/console.py`), its test (`test_api.py`), the client and its test (`console-api.ts`, `console-api.test.ts`), the project page (`project-view.tsx`), the browser test (`console.spec.ts`) and its servers (`playwright.config.ts`, which now lets the test API accept a webhook on this computer).

**What the tests prove**:
- an owner adds an endpoint (with its secret), sends a test event, sees it pending, replays it and removes the endpoint; an analyst may neither add nor list one; the other mode sees none; the audit log names the person each time;
- the client sends the mode with every webhook request, and reads a dead delivery's last answer;
- in a real browser, an owner adds an endpoint, sees its secret, and sees the test event waiting.

!!! honest "Honest limitation"
    The console shows the last 100 deliveries of one endpoint at a time, with no filter, and can't yet switch an endpoint off without removing it. During the browser test nothing is actually delivered: no delivery worker runs there (the worker has its own tests, §5.4.3).
