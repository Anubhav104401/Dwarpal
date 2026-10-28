## 5.5 Phase 5 — front-end excellence

Phase 5 gives Dwarpal the faces people see: the console for its customers, a polished verify flow, a marketing site, and documented SDKs. From the roadmap (§3.9):

| Area | Status |
| :-- | :-- |
| **Console** — sign-in, organisations, members, keys, audit log | 🟡 first pages (§5.5.1); a project's sessions, decision traces, counts and policies (§5.5.2); webhooks (§5.5.3); one-time codes and member roles (§5.5.4); a command palette to come |
| Design system — tokens, typography, components, motion | 🟢 first version (§5.5.6): OKLCH tokens (midnight-indigo ink, saffron, teal), Geist Sans and Mono, a type scale, motion presets, shared components and a specimen page, checked in light and dark |
| Marketing site (3D face-mesh hero) | 🗓 waits for an approved 3D library |
| Verify flow in English and Hindi | 🗓 waits for an approved translation library |
| Exit tests on three browser engines, accessibility and Lighthouse checks | 🟢 built (§5.5.5): Chromium and WebKit pass here, Firefox can't start on this computer; axe clean on the key pages; Lighthouse ≥ 90 |

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
    The counts are totals, not a chart: the chart waits for the design system. The trace shows numbers, not explanations of them; the reasons' meanings are in §5.3.

**Searching sessions** (added 29 Oct). The list can be narrowed to one **outcome**, one **reference** of the website's own (such as an order number), or both — in the console's search form, and in the website API (`?outcome=pass`, `?external_ref=order-1`). There is no status filter, on purpose: "expired" is worked out when a session is read, not stored, so filtering the stored status would show expired sessions as still waiting.

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
    The console shows the last 100 deliveries of one endpoint at a time, with no filter. (Switching an endpoint off came later — see below.) During the browser test nothing is actually delivered: no delivery worker runs there (the worker has its own tests, §5.4.3).

**Switching an endpoint off** (added 29 Oct). A website whose receiver is down for maintenance can now switch its endpoint off instead of deleting it, which would lose the secret: `PATCH /v1/webhook-endpoints/{id}` with `{"enabled": false}`, or *Switch off* in the console. Off, it keeps its address, events and secret but gets nothing: new events skip it, and deliveries still pending are closed unsent. Each switch is in the audit log; a test proves a switched-off endpoint is sent nothing until switched back on.

### 5.5.4 One-time codes and members' roles

Two pieces of the console's API from §5.4.5 had no pages: switching on one-time codes, and managing people beyond adding them.

- **Security** (`/console/account`, linked from the organisations page): if one-time codes are off, *Set up one-time codes* shows a new secret (in groups of four, and as an `otpauth://` link for an app on the same device); the person enters the code their app shows, and only then are codes required at sign-in.
- **Members**: owners and admins now see, on each member's row, a role menu and a *Remove* button. The API gained `PATCH` and `DELETE` on `/orgs/{org}/members/{user}`.

!!! key "Key idea — an organisation always has an owner"
    Two rules guard the owners. Only an owner may make, change or remove an owner. And the **last** owner can't step down or be removed: the API answers `409 last_owner` — make someone else an owner first. The second rule needs care when two requests arrive together: if two owners each demote the other at the same moment, each could see "two owners" and both succeed. So every change first **locks** the owners' rows (`SELECT … FOR UPDATE`); the second request waits, then sees only one owner left, and is refused.

!walk apps/web/app/console/account/page.tsx

!walk apps/web/app/console/account/account-view.tsx

The rest changed existing files, each re-explained in its walkthrough: the console API (`app/console.py`, `http/console.py`) and its test (`test_api.py`), the client and its test (`console-api.ts`, `console-api.test.ts`), the organisation page (`organisation-view.tsx`), the console's home (`console-home.tsx`), and the error answers (`problems.py`), the browser test (`console.spec.ts`), which now computes one-time codes itself, exactly as an authenticator app does.

**What the tests prove**:
- an admin may change an analyst's role, but may not make, change or remove an owner; the last owner may not step down, and may once there are two; an owner may remove an admin; the audit log holds exactly the changes that happened;
- the client uses `PATCH` and `DELETE` on the right addresses, and sends the code to confirm;
- in a real browser, a new member turns on one-time codes; signing out and in again then asks for a code, and the next code lets them in.

**A bug the contract tests found.** Running the new routes through Schemathesis (§5.4.6), one random request carried the NUL character inside an e-mail address. PostgreSQL can't store NUL in text, the error went unhandled, and the API answered `500`. The request was at fault, so `http/problems.py` now turns that one database refusal into `422 invalid_text`, for every route at once, and a test sends such an address on purpose. (The failure appeared on one run and not the next: random testing finds rare inputs only sometimes, which is why it runs on every check.)

!!! honest "Honest limitation"
    (The QR code came next, in §5.5.5.) (Switching codes off, and recovery codes, came later — see below.) (A browser test of the member controls came later: an owner adds a colleague, changes their role, reloads to see it kept, and removes them.)

**Recovery codes, and switching codes off** (added 29 Oct). A lost phone used to mean a locked account. Now switching one-time codes on also gives **ten recovery codes**, shown once: each signs the person in once, typed where the code goes. Only an HMAC of each is stored, under a key made from the master key, so a copy of the database can't reveal them (migration `0008`). The *Security* page shows how many are left, makes a fresh set on request, and can **switch codes off** — but only with the password *and* a current code, so someone who found a signed-in browser left open can't remove the protection. Every use is in each organisation's audit log.

!walk services/api/src/dwarpal_api/migrations/versions/v0008_recovery_codes.py

### 5.5.5 The exit tests: three engines, accessibility, Lighthouse — and a QR code

Phase 5 ends when three checks pass (§3.9): the browser tests on **Chromium, Firefox and WebKit**; **axe** finding nothing on the key pages; and **Lighthouse** scoring at least 90. The owner approved the four downloads they needed (decisions D3, D4, D5 and D13), and each is now wired in:

- **Three engines.** `playwright.config.ts` has a project per engine. Firefox and WebKit run everything that doesn't need a camera — only Chromium can play a video file as one, so the age-check story stays there. `E2E_ENGINES` can name fewer engines.
- **axe** (`tests/accessibility.spec.ts`) checks the shop, the verify page, and every console page against WCAG 2.2 A and AA, on each engine.
- **Lighthouse** (`tests/lighthouse.spec.ts`, `lighthouserc.json`) scores the shop, the console's sign-in and the verify page.
- **A QR code** on the *Security* page, drawn in the browser by `qrcode`, so phones can scan the one-time-code secret.

!walk e2e/tests/accessibility.spec.ts

!walk e2e/tests/lighthouse.spec.ts

!walk e2e/lighthouserc.json

The rest changed existing files, each re-explained in its walkthrough: the Security page (`account-view.tsx`), the colours and controls the tests found wanting (`globals.css`, `console-shell.tsx`, `verify-flow.tsx`, `webhooks-panel.tsx`), the browser tests and their servers (`console.spec.ts`, `playwright.config.ts`), the packages (`apps/web/package.json`, `e2e/package.json`), `turbo.json`, `.gitignore`, the book's own `book.toml` (which now skips Lighthouse CI's scratch folder), and a new API test of the production session cookie (`test_api.py`).

**What the new tests found** — each fixed, or explained:

1. **Text too faint.** The *Console* badge and the verify page's step numbers used `brand-600` saffron text on a pale saffron circle: 2.8:1, where WCAG AA asks 4.5:1. A darker `brand-700` measures at least 5.3:1.
2. **Checkboxes too close.** WCAG 2.2 asks that small controls have room around them for a finger. The webhook form's two event checkboxes didn't; their rows are taller now.
3. **A false alarm.** axe first reported a faint button on the verify page. It had measured the card while it was still fading in, so the colours were halfway blends. The test now waits for one-off animations to finish.
4. **WebKit and secure cookies.** WebKit drops a `Secure` cookie on plain `http://localhost`, so every console page after sign-in looked signed out. The test servers now use a plain session cookie, and an API test checks the production one (`__Host-`, `Secure`, `HttpOnly`) instead. Production refuses to start without it.
5. **A limiter with a memory.** Three engines signing in from one computer ran into the sign-in limit, which remembers earlier runs in Valkey. The test API gets a larger allowance that refills fast.
6. **Private pages and search engines.** Lighthouse gave the console and the verify page 60 for search engines, because both ask not to be indexed — on purpose. So the rule for them is the opposite: the test fails if they ever *stop* asking.

!!! real "Real world — browsers that won't start"
    On the owner's Windows 11 computer (build 26200), Playwright's Firefox and its full Chromium both fail to start, with Windows reporting an incorrect "side-by-side configuration": it can't find the private parts each program declares, although the files are there. Reinstalling didn't help, and an older Chromium fails the same way, so the cause is in this Windows installation, not the downloads. Two workarounds keep the checks honest. Lighthouse uses Playwright's **headless shell**, a windowless Chromium that does start. And Firefox is left out here (`E2E_ENGINES=chromium,webkit`), to run on the Linux CI machine once the code is on GitHub. Until then, "passes on Firefox" is not proven.

!!! honest "Honest limitation"
    Lighthouse CI brought 262 packages, and `pnpm audit` reports known flaws in eight of them (one low, one moderate, six high: `tmp`, `uuid`, `extract-zip`, `basic-ftp`, `zod`, `body-parser`). All are tools that run only on a developer's or CI machine, against local test servers, and none ships in the apps. Fixed versions exist for all but `extract-zip`, and installing them is a new download, so it waits for the owner (decision D14). Lighthouse scores also vary a few points from run to run.

### 5.5.6 The design system

The roadmap asks for a design system: tokens, typography, components, motion presets, light and dark. The owner kept **Geist** as the typeface (decision C1). The design also names shadcn/ui and the Motion library, but both are downloads nobody has approved, so this first version uses only what was already installed: Tailwind, and Geist's two families.

- **Tokens** (`globals.css`). The colours are in OKLCH:
    - **ink**, a midnight-indigo neutral scale;
    - **saffron**, the accent;
    - **teal**, for success.

    Alongside them: a display type size that grows with the window, Geist Mono for code, and motion presets (one easing curve, three durations).
- **Components** (`components/ui.tsx`): buttons in three tones and three sizes, panel and card, input and field, alert and notice, and badges in four tones. The console's and the verify page's shells pass them on under their old names, so the pages didn't have to change.
- **A specimen** (`/design`) shows every token and component. The accessibility test checks it in **both** themes.

!!! key "Key idea — change the tint, not the lightness"
    Contrast — what the accessibility rules measure — depends almost entirely on **lightness**. The new ink scale keeps the lightness of every step of Tailwind's grey `zinc`, which the pages used before, and changes only the hue and a little chroma. So moving every page from grey to midnight indigo was a mechanical rename (`zinc-` → `ink-`), and every contrast the tests had measured stayed where it was. OKLCH makes this possible: in older colour models such as HSL, two colours with the same "lightness" number can look very different in brightness.

!walk apps/web/components/ui.tsx

!walk apps/web/app/design/page.tsx

The rest changed existing files, each re-explained in its walkthrough:
- the tokens (`globals.css`);
- the two fonts and theme colours (`layout.tsx`);
- the shells (`shell.tsx`, `console-shell.tsx`);
- the renamed colours on every page;
- the accessibility test.

**Reduced motion, decided twice.** The first attempt switched off *all* animation for people who ask their system for less. Then the light challenge came to mind. It eases between colours on purpose, to stay far below three flashes a second, and forcing it to snap would make it harsher for exactly the people the setting protects. So the rule is narrower: decorative motion is written `motion-safe:…`, and that one protective fade always runs.

**What the tests prove**: the specimen breaks no WCAG 2.2 A or AA rule in the light or the dark theme, on Chromium and WebKit; and every earlier page still passes axe and Lighthouse after the change of palette.

!!! honest "Honest limitation"
    This is a first version. There is no display serif for headlines, as the design suggested: that would be another download. The console has no sidebar or command palette yet. The verify flow's own icons still use Tailwind's emerald, rose and amber, not the tokens. And only the light and dark themes the visitor's system asks for exist — there is no switch on the page.
