## 5.5 Phase 5 — front-end excellence

Phase 5 gives Dwarpal the faces people see: the console for its customers, a polished verify flow, a marketing site, and documented SDKs. From the roadmap (§3.9):

| Area | Status |
| :-- | :-- |
| **Console** — sign-in, organisations, members, keys, audit log | 🟡 first pages (§5.5.1); a project's sessions, decision traces, counts and policies (§5.5.2); webhooks (§5.5.3); one-time codes and member roles (§5.5.4); a command palette to come |
| Design system — tokens, typography, components, motion | 🟢 first version (§5.5.6): OKLCH tokens (midnight-indigo ink, saffron, teal), Geist Sans and Mono, a type scale, motion presets, shared components and a specimen page, checked in light and dark |
| Marketing site | 🟢 home page with every section and a live accuracy table (§5.5.9), and its 3D hero (§5.5.10) |
| Verify flow in English and Hindi | 🟢 the home page and the verify page in both, with a language switch (§5.5.11); the Hindi needs a native speaker's review |
| Exit tests on three browser engines, accessibility and Lighthouse checks | 🟢 built (§5.5.5): Chromium and WebKit pass here, Firefox can't start on this computer; axe clean on the key pages; Lighthouse ≥ 90 |
| Demo shop and SDKs — `@dwarpal/js`, `@dwarpal/react`, `@dwarpal/node` | 🟢 the check opens in a modal on the website's own page (§5.5.7); the shop uses the React button |
| Policy editor with projected adult step-up rate | 🟢 the model's own lines, with how adults fared at each (§5.5.8) |

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

**The counts as a chart** (added 29 Oct). Beneath the tiles, the 30 days now appear as bars, one per day, each stacked by outcome — the "chart waits for the design system" limitation above, now lifted. The API already sent the counts day by day; the console had only been adding them up. `everyDay` turns its rows into one entry for every day of the window, so a day without checks is a visible gap rather than missing.

!walk apps/web/lib/daily.ts

!walk apps/web/lib/daily.test.ts

!!! key "Key idea — colour is not enough on its own"
    Five outcomes need five colours that stay distinct for people with the common kinds of colour blindness, on both a light and a dark panel. They weren't chosen by eye: a validator measured every neighbouring pair as colour-blind eyes would see it, and the contrast of each against its background. All passed except contrast in light mode, where three colours are paler than 3:1 against white. The rule for that case is that the numbers must also be available as text — so every day's numbers appear on hover *or keyboard focus*, each day's button speaks its total, and the whole series is one click away as a table.

!walk apps/web/app/console/[org]/[project]/daily-chart.tsx

The client (`console-api.ts`) now keeps the daily rows, and its test checks them; the project page orders the totals as the legend does and shows the chart. Each was re-explained.

**The face checks' figures** (added 29 Oct). The design's dashboard also asks for the median time a check takes, how often checks are rejected as likely attacks, and how often they are sent to a stronger check. The outcome counts can't answer these. They count a session when it *finishes*, and a session sent to a stronger check doesn't finish until that check does — or it expires. They also say nothing about time. So each face check that reaches a decision (anything but a retry) now adds one to a second daily count: its outcome, and the band of time from opening the verify page to the decision. A new column, `started_at`, records that opening.

!!! key "Key idea — time in bands, never per person"
    Keeping each check's exact time would be one more fact about a real person, with no use beyond the median. So only counts per band are kept: "10 to 15 seconds", "15 to 20", and so on, finer where most checks should finish. The median is then the band holding the middle check. It's less precise than an exact median, and the page says so by showing a band ("10–15 s"). It counts as within the 15-second target only if the whole band is.

!walk services/api/src/dwarpal_api/migrations/versions/v0009_face_stage_stats.py

!walk services/api/src/dwarpal_api/domain/timing.py

!walk apps/web/lib/figures.ts

!walk apps/web/lib/figures.test.ts

The tables (`tables.py`), the session use cases (`verification.py`, which notes the start and counts each decision), the analytics use case (`analytics.py`, which now also answers with `face_stage`), their tests (`test_domain.py`, `test_api.py`), the client and its test, and the project page changed too; each was re-explained. *Step-up conversion* — how many people sent to a stronger check then finish it — waited for the stronger checks themselves (Phase 6).

**The ID-document checks' figures** (added 9 Nov). With the ID-document check built, a third daily count, `document_stage_stats`, adds one when a session reaches that check — `opened`: sent there by a face check that couldn't decide, or starting there in a live check while no age model is certified (D24) — and one when the check ends, by how it ended: `pass`, `fail`, `reject`, or `age_pass` when a pass ended a live check that started there. The page shows, of the checks reached in the 30 days, the share that ended (the design's **step-up conversion**), the share that passed, and the share that left — or are still on it. The two counts can fall on different days, as a check reached just before the 30 days can end within them, so no share is ever shown over 100 %.

!walk services/api/src/dwarpal_api/migrations/versions/v0013_document_stage_stats.py

The tables, the session and Age Pass use cases (which count each reach and each ending), the analytics use case (which also answers with `document_stage`), the figures (`percent`, now shared, and `documentFigures`), the project page and their tests changed too; each was re-explained.

**The age model's page** (added 29 Oct). The design asks the console for *model information* (FR-10). A new page, *Age model*, linked from the console's front page, shows anyone signed in which model is deciding, whether it may decide live checks, what it learnt from, and its lines for each age with the worst cases measured for them. It is the same for every organisation, so it needs no tenant and no role — only a signed-in person (`GET /console/v1/model`). The API keeps the manifest's whole file at start-up for this page; decisions never read it.

!!! key "Key idea — show the guarantee, and only the guarantee there is"
    A page like this could easily overclaim. So it says *Test checks only* for an uncalibrated model, quotes the manifest's own note on why, and, for the stand-in model, says its lines were "chosen by hand for testing; nothing was measured" rather than showing empty bounds as 0 %. It also leaves out what customers don't need — the file's checksum, the commit it was built from — and a test checks that those never appear.

!walk apps/web/app/console/model/page.tsx

!walk apps/web/app/console/model/model-view.tsx

The manifest's loader (`domain/policy.py`), the console's use cases and routes (`app/console.py`, `http/console.py`), their test (`test_api.py`), the published contract (`docs/api/openapi.json`), the client and its test, the front page's link, and the browser and accessibility tests changed too; each was re-explained.

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
    This is a first version. There is no display serif for headlines, as the design suggested: that would be another download. (The console's sidebar and command palette came later the same night; see the end of this section.) The verify flow's own icons still use Tailwind's emerald, rose and amber, not the tokens. And only the light and dark themes the visitor's system asks for exist — there is no switch on the page.

**A sidebar and a command palette** (added 29 Oct), as the design asks. Once someone is signed in, every console page has a sidebar of places — *Organisations*, *Age model*, *Security* — which on a phone becomes a row above the page; the current one is marked for screen readers as well as by its look. At the top of the sidebar, *Go to…* opens the **command palette**, as does ⌘K (Ctrl+K on Windows and Linux): type part of an organisation's or project's name and press Enter to go there, or use the arrow keys to choose.

!walk apps/web/lib/places.ts

!walk apps/web/lib/places.test.ts

!walk apps/web/components/command-palette.tsx

!!! key "Key idea — build on what the browser already does"
    Command palettes are often a *combobox*: a text box that owns a pop-up list, with the screen-reader wiring that entails. This one is simpler on purpose: a search box and a list of ordinary links, inside the browser's own modal `<dialog>`. The browser then does the hard parts — keeping focus inside, closing on Escape, hiding the page behind from assistive technology — and every result is a real link, which can be opened in a new tab like any other.

The frame (`console-shell.tsx`) now draws the sidebar and the palette when a page says `signedIn`; each signed-in page says so, and the front page's *Age model* and *Security* links moved into the sidebar. A browser test opens the palette from the keyboard, searches, and arrives at a project, and the accessibility test checks the open palette too. Each changed file was re-explained.

### 5.5.7 The check in a modal: the browser SDKs

Until now a website sent its visitor *away* to the verify page and waited for them to come back. The design's first choice is gentler: the check opens in a **modal** over the website's own page, the verify page inside a **frame**. Two packages do that for websites: **`@dwarpal/js`**, for any web page, and **`@dwarpal/react`**, a button and a hook for websites built with React. The demo shop now uses the React button.

Our own security headers stood in the way. The verify page told browsers that no website could frame it (`frame-ancestors 'none'`), against **clickjacking**. Loosening that is a security trade-off, so it went to the owner as decision **D16**, who chose: allow framing **per session**, only by the website the session returns to.

How it fits together:

```
website's server ──(secret key)──► API: new session (return address: shop.example)
website's page: VerifyAgeButton ──► modal + frame ──► verify page
   verify page's web server asks the API: "who may frame vs_…?"  →  https://shop.example
   header: frame-ancestors https://shop.example
verify page ──postMessage("finished", only to shop.example)──► website's page ──► return address ──► server checks the result
```

!!! key "Key idea — two pages, two origins, one narrow channel"
    A page in a frame and the page around it can't touch each other when they come from different websites; the only way through is `postMessage`. Each side keeps one rule. The **sender** names the one origin allowed to receive the message, so it can't leak elsewhere. The **receiver** accepts a message only from the frame it opened and from the verify page's origin, which the browser sets and nobody can fake. And the message carries no result: only "finished, go to your return address", where the website's *server* asks for the result with its key. A message, a callback, anything in the browser can be forged; the token can't.

The rules, one by one:

- **Which website may frame a verify page** — the origin of the session's return address. The website gave it with its secret key, and it had to be one of the project's allowed origins. The verify page's web server asks the API on every page (`/frame-ancestor`), checks the answer is an origin and nothing else, and puts it in the header. Any doubt — no session, an expired one, an API that is slow or down — means no website at all. The page still works full-page.
- **What the website's page accepts** — only our two messages (`finished`, `full_page`), from the frame it opened, at the verify page's origin, about its own session, and a `finished` only with an address on the website's *own* origin. Anything else is ignored.
- **The camera in a frame** — a frame may use the camera only if the page around it allows it (`allow="camera"`). If a browser still refuses, the verify page offers to **open the check in a full page**, and the SDK sends the whole tab there, with the same link.

!walk packages/sdk-js/package.json

!walk packages/sdk-js/tsconfig.json

!walk packages/sdk-js/tsconfig.build.json

!walk packages/sdk-js/src/protocol.ts

!walk packages/sdk-js/src/link.ts

!walk packages/sdk-js/src/open.ts

!walk packages/sdk-js/src/index.ts

!walk packages/sdk-js/test/protocol.test.ts

!walk packages/sdk-react/package.json

!walk packages/sdk-react/tsconfig.json

!walk packages/sdk-react/tsconfig.build.json

!walk packages/sdk-react/src/index.tsx

!walk packages/sdk-react/test/button.test.tsx

!walk apps/demo-shop/app/age-check-button.tsx

**The guides** (added 31 Oct). The roadmap asks for the SDKs *documented*. Websites' developers get guides in `docs/developers/`: how an age check works and a quick start, the browser SDKs, the Node.js SDK, and a checklist to go through before using a live key. Each package has a short `README.md` pointing to them. They are written in Markdown, for developers rather than for this book, so they have no walkthroughs; every code sample in them was type-checked against the real SDKs before it was written down.

!!! real "Real world — what the browser test caught"
    The first run of the new story passed: the check ran inside the frame, camera and all, and the shop let the person in. The *closing* test failed. Pressing the button made it `disabled` while the session was being created, and a disabled button loses the keyboard focus, so when the modal closed there was nothing to give the focus back to. A keyboard user would have been dropped at the top of the page. The button now says it is busy with `aria-disabled` and ignores presses instead, keeping its focus.

The API (the use cases' `frame_ancestor` and the flow's `return_origin`, the new route, and a test), the verify page's proxy and its tests, the flow client and its test, the verify flow, both apps' `package.json`, the shop's action and its two pages, and the browser tests (the shop's story and its accessibility check, now with the modal open) changed too; each was re-explained.

### 5.5.8 The policy editor's projection

The design's policy editor shows a **projected adult step-up rate**: before a website adopts a policy, how many genuine adults it would send to a stronger check. The numbers already existed. When `calibrate` set the age model's lines (§5.2.6), it opened the exact-age **test split** once and measured, for each line, how adults in four bands above the age fared. They sat in a run folder; now the export copies them into the model's manifest (`adults`, on each line), and the console's policy editor shows them for the line chosen.

Building it turned up a real flaw. The editor offered four ages at a fixed 2 % risk budget, but the trained model has lines only at 15 % (13+ and 16+) and 7.5 % (18+ and 21+): a policy must match one of the model's lines exactly, so with the trained model every new version would have been refused. The editor now offers exactly the lines the model in use has, labelled by age and budget.

!!! key "Key idea — the price of keeping minors out"
    A line that lets very few minors through has to be very sure before it says *pass*. The people it is least sure about are those just over the age. At the trained model's 18+ line, 77 % of 18–20-year-olds are sent to a stronger check and 13 % pass, while of adults 30 and over, 94 % pass. The projection puts that trade-off in front of the person choosing a policy, in their visitors' terms, rather than leaving it to be discovered in production.

!!! honest "Honest limitation"
    These are the shares on a dataset's photos, whose ages were estimated rather than documented — about 9,500 faces of adults per line. Real visitors, their cameras and their light will differ, and the editor says so under the table. And it is a table of the lines that exist, not a slider: the model has one budget per age, because the data could certify no stricter one (§5.2.6).

The model's manifest gained only the `adults` lists: `--manifest-only` rewrote it from the same run's files without exporting the model again, so its fingerprint, checks and lines are unchanged.

!walk apps/web/lib/projection.ts

!walk apps/web/lib/projection.test.ts

!walk apps/web/app/console/[org]/[project]/policy-editor.tsx

!walk ml/tests/test_export.py

The export (`export.py`) and the trained model's manifest, the console's model answer and its test, the client and its test, the project page (whose form moved into the editor) and the browser test changed too; each was re-explained.

### 5.5.9 The home page: the marketing site, without its 3D hero

The design's marketing site has a 3D hero — a face of 478 points of light that scans and disperses — and seven sections: how it works, the privacy promise, a **live accuracy table**, the developer quick-start, a compliance map, questions, and a demo. The hero needs a 3D library that hasn't been approved (D1); everything else needed nothing new, so the home page now has all of it, with a still artwork in the hero's place: the same motif, a face of points in a temple doorway, with one line of light passing over it.

The accuracy table is *live*: the page asks the API, as it is made, for the figures of the age model running now. Those figures were behind the console's sign-in, so the API gained one public address, `GET /v1/model`: the console's description of the model without each line's two scores. How well a line works — its bounds, how adults fared — is for anyone to know, as ISO/IEC 27566-1 asks of a provider; the exact scores where it passes and fails would only help someone tuning an attack.

!!! key "Key idea — say only what is measured"
    A marketing page is where systems usually overclaim. This one shows the model's own bounds, measured, with what they rest on (11,301 photos with *estimated* ages) and the plain fact that the model decides test checks only. If the API can't be reached, the table says the figures can't be loaded; it never shows remembered or made-up numbers. The compliance map says what each rule asks and how the design answers it, but no fines or dates (those wait to be checked against primary sources), and calls itself a summary, not legal advice.

!!! honest "Honest limitation"
    The figures are the stand-in model's in the tests ("not measured") and the trained model's on this computer; nothing is hosted yet. The compliance map needs the legal review that the privacy documents need (O5) before it is published anywhere. And the developer guides it points to are in the repository, not on a website.

The accessibility test earned its keep twice while the page was built: grey labels too faint on the dark background, and code boxes and tables that scrolled sideways on a phone but couldn't be reached by keyboard — now they wrap instead. Lighthouse scores the page 95 / 100 / 100 / 100, and, unlike the console and the verify page, it asks search engines to index it.

!walk apps/web/app/page.tsx

!walk apps/web/app/_home/arch.tsx

!walk apps/web/app/_home/accuracy.tsx

!walk apps/web/lib/published-model.ts

!walk apps/web/lib/published-model.test.ts

!walk services/api/src/dwarpal_api/http/model.py

!walk e2e/tests/home.spec.ts

The console's application code (`published_model`), the app's list of routers, the design tokens (the line's animation), the API's tests, the browser tests' servers, the accessibility test and the Lighthouse test changed too; each was re-explained.

### 5.5.10 The 3D hero

The design's hero is a face of 478 points of light that a line of light scans, and that now and then scatters and gathers again: the photos are taken, checked and let go. It needed a 3D library, and the owner approved **three.js** on 1 November (decision D1). Three rules shaped it:

1. **The face is no one's.** The obvious source of 478 face points is a real face run through MediaPipe — but a real person's face shape is biometric data, which Dwarpal never keeps, even of a public-domain portrait. So the face is made from a few smooth rules: points spread evenly over the front of a sphere, pressed into an egg, with a nose, eye hollows and lips (`face-cloud.ts`).
2. **It costs the page nothing it doesn't have to.** The page first shows the still artwork (§5.5.9). Only once the browser is idle, and only if it can draw WebGL and the person hasn't asked for less motion, is the 3D code fetched — as a separate file — and the face swapped in. Off screen or in a hidden tab, it stops drawing. Lighthouse still scores the page 94 for performance.
3. **Failure looks like nothing happened.** No WebGL, reduced motion, a failed download: the still artwork stays.

!!! kid "Explain like I'm six — a face made of stars"
    The computer scatters 478 tiny dots evenly over half a ball, then squeezes the ball into the shape of a face: a bit narrower, a bump for the nose, two little dips for the eyes. It isn't anybody's face — it's what a drawing of "a face" looks like. Then a stripe of light slides up and down over it, like a scanner.

The points are drawn by two small programs that run on the graphics card itself — *shaders* — which place every point, light the ones near the scan line, and make nearer points brighter, so a cloud of dots reads as a face.

!walk apps/web/lib/face-cloud.ts

!walk apps/web/lib/face-cloud.test.ts

!walk apps/web/app/_home/face-scene.ts

!walk apps/web/app/_home/face-hero.tsx

!walk apps/web/types/three.d.ts

The still artwork (it can now be drawn without its face), the home page, the web app's packages and the home page's browser test changed too; each was re-explained.

!!! honest "Honest limitation"
    - **Hand-written types.** three.js ships no type definitions, and the usual ones (`@types/three`) are a separate download not yet approved (D1b). The few parts the hero uses are typed by hand (`types/three.d.ts`); TypeScript trusts them, and can't check them against three.js itself.
    - **Lighthouse's own browser draws no WebGL**, so its score is the page without the 3D face; the browser tests check the face itself in Chromium and WebKit.

### 5.5.11 Hindi

The design asks for the public pages in English and Hindi — India is one of Dwarpal's markets, and its DPDP Act protects every child there. The owner approved **next-intl** on 1 November (decision D2), a library that gives each page its words in the visitor's language. Four decisions shaped the work:

1. **The words leave the code.** Every sentence the home page and the verify page show moved into `messages/en.json` and `messages/hi.json`, under keys such as `Verify.introTitle`. The code asks for keys; next-intl fills in the parts in braces (`Confirm you are {age} or over`) and picks plural forms ("2 tries left", "Last try").
2. **The address doesn't change.** `/` is the home page in either language. The language comes from the person's own choice, remembered in a cookie, else from what their browser asks for (`Accept-Language`), else English. The language switch is a plain form, so it works even without JavaScript.
3. **Only what the browser needs travels.** The home page is drawn on the server in the chosen language, so it sends no translation code at all; the verify page, which runs in the browser, gets only its own groups of words.
4. **The console stays English** — it is an operator's tool — and says so (`lang="en"`), so a screen reader never reads its English as Hindi.

!!! kid "Explain like I'm six — a book with two languages"
    Imagine a picture book where every sentence is a little sticker. The book itself only has empty spaces with labels like "page 3, top". There are two sticker sheets, one in English and one in Hindi. When you open the book, someone sticks on the sheet you can read. The pictures — and the story — stay the same.

!walk apps/web/i18n/locales.ts

!walk apps/web/i18n/locales.test.ts

!walk apps/web/i18n/request.ts

!walk apps/web/i18n/actions.ts

!walk apps/web/components/language-switch.tsx

!walk apps/web/app/console/layout.tsx

!walk apps/web/messages/en.json

!walk apps/web/messages/hi.json

The home page, its accuracy table, the verify page and its camera screen, the tips and problems (`advice.ts`, now only choosing keys), the camera code (it reports the pose, not words), the page frame, the root layout (the page's `lang`), the design system's page, the Next.js configuration, the workspace file (two install scripts declined), the web app's packages and the browser tests changed too; each was re-explained.

**What the tests prove**: the language is chosen in the right order; every tip and problem has its words in both languages, and the Hindi file has exactly the English file's keys; choosing Hindi switches the page — heading, title and `lang` — and is remembered; a browser set to Hindi gets Hindi at once; the Hindi home page breaks no accessibility rule; the verify page speaks Hindi too; and the console stays marked English. Lighthouse still scores the home page above 90.

!!! honest "Honest limitation"
    - **The Hindi is machine-drafted** — by the AI that wrote this code — and needs a native speaker's review before real visitors read it, above all the compliance map and the privacy promises.
    - **The Devanagari typeface**: until 2 November Hindi text used the visitor's system font; since then the site serves Noto Sans Devanagari (decision D2b) — on Hindi pages only since 3 November, so English pages don't fetch it for the one Hindi word in the language switch.
    - **Inside a website's frame the choice may not stick**: browsers often withhold a framed page's cookies, so there the language follows the browser's settings.

### 5.5.12 The console, ready for a launch: projects, keys, accounts and invitations

Looking at what a real customer would need on day one (8 November), four things were missing from the console — and the first made the deployment's own step 7 impossible:

- **Projects and their allowed origins** (decisions D28, D29). Signing up makes a *Default project* with no allowed origins, and nothing could add one; yet a session may only return to an allowed origin, and only that origin may show the verify page in a frame (§5.5.7). Owners and admins can now make projects (at most 20) and set their origins. An origin is written one way — lower case, without the usual port — so `HTTPS://Shop.Example:443/` and `https://shop.example` are the same; `http://` is allowed only for `localhost` while developing.
- **Keys** (D30): a project's keys are listed — never their secrets, which Dwarpal doesn't keep — and can be stopped at once.
- **The account** (D31, D32): a new password ends every other session at once; deleting the account erases the person's address, password, codes and passkeys, closes an organisation where they were alone, and is refused while they are the only owner of one with other members.
- **Invitations** (D44): an address without an account is invited instead of refused; no e-mail is sent (D25), and the person joins when they sign up with that address.

Ending "every other session" needs a trick, because a console session lives in Valkey under the hash of its cookie, with no list of a person's sessions. Each session remembers a **generation** number when it begins; changing the password (or deleting the account) adds one to the person's number, and a session whose number is older stops counting at its next request.

The rule for origins:

!walk services/api/src/dwarpal_api/domain/origins.py

!walk services/api/tests/test_origins.py

The invitations' table, and the function sign-up takes them through:

!walk services/api/src/dwarpal_api/migrations/versions/v0012_invitations.py

On the project's page, the settings and the keys, each in its own panel; and the helper both pages use for the origins box:

!walk apps/web/app/console/[org]/[project]/settings-panel.tsx

!walk apps/web/app/console/[org]/[project]/keys-panel.tsx

!walk apps/web/lib/origins.ts

!walk apps/web/lib/origins.test.ts

The console's use cases and routes, its tables, the Valkey store (a counter that never expires), the role table, the console client and its tests, the organisation's, project's and account's pages, the browser tests, and the API document changed too; each was re-explained.

!!! honest "Honest limitations"
    - **Without e-mail, a forgotten password can't be reset by the person.** Passkeys and one-time codes with their recovery codes remain the ways back in (decision D25); otherwise the operator must help.
    - **Invitations don't expire**, and an invitation is only as private as the address it names: whoever signs up first with that address joins.
    - **Deleting an account leaves its ID in the audit chains** — by design, so they still verify — and a closed organisation's records go only when the usual retention reaches them.

