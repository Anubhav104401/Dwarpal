## 5.5 Phase 5 — front-end excellence

Phase 5 gives Dwarpal the faces people see: the console for its customers, a polished verify flow, a marketing site, and documented SDKs. From the roadmap (§3.9):

| Area | Status |
| :-- | :-- |
| **Console** — sign-in, organisations, members, keys, audit log | 🟡 first pages (§5.5.1); dashboard, sessions explorer, policy editor, webhooks and a command palette to come |
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
    These pages are deliberately plain: the design system, with its type, motion and components, waits for the typeface decision. The console doesn't yet show sessions, analytics, policies or webhooks, which their APIs already provide, and it has no pages for switching on one-time codes.
