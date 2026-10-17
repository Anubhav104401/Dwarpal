---
fingerprint: 10cb06247fa95468
---
What happens when a visitor presses **"Verify my age to enter"**. It is a **server action** (§4.17): a function that runs on the shop's *server*, although it is triggered by a button in the visitor's browser. That is essential here — it uses the shop's secret API key, which must never reach a browser.

@@ 1
`"use server"` — every function exported from this file is a server action. Next.js turns a call to it from a page into a request to the server, and runs it there.

@@ 3-4
From Next.js: `cookies` (read and write the visitor's cookies) and `redirect` (send the visitor elsewhere).

@@ 6-7
The shop's settings helpers, and the cookie names and lifetime — `PASS_COOKIE`, the pass itself, is needed by `leaveCellar` below.

@@ 9-10
**`startAgeCheck`** — the action.

@@ 11
Read the settings.

@@ 12-15
Ask Dwarpal for a new session, through the SDK: the shop's policy, and the address to come back to afterwards.

@@ 16-22
Before sending the visitor away, **remember which session this browser started**, in the `amber_pending` cookie:

- `httpOnly` — the page's own scripts can't read it; only the browser and the server see it;
- `sameSite: "lax"` — the browser sends it back when the visitor *returns* to the shop by following a link or a redirect, but not with requests that other websites try to make in the background;
- `secure` — sent only over HTTPS, when the shop runs on HTTPS;
- `path: "/age-check"` — sent only to the return address, nowhere else in the shop;
- `maxAge` — forgotten after 30 minutes, the same as an age check's own life.

!!! real "Real world — why this cookie exists"
    Without it, the return link `…/age-check/complete?session_id=vs_…` would work in *any* browser. An adult could finish a check and send that link to a child, and the child's browser would receive the shop's pass. With the cookie, the shop only accepts a return in the browser that started the check. Websites that sign people in with another service use the same trick, which OAuth calls the `state` parameter.

@@ 23
Send the visitor to the verify page, using the link from the session.

@@ 24
The closing brace.

@@ 26-27
**`leaveCellar`** (added in Phase 3, for repeated testing) — forget this browser's pass and go back to the front door, as its comment says. Like `startAgeCheck`, it is a **server action**: the cellar's button calls it, and it runs on the shop's server, where the cookie can be changed.

@@ 28
Delete the pass cookie. The browser is told to forget it at once, so the next visit to the cellar needs a new age check.

@@ 29-30
Send the visitor to the front page.
