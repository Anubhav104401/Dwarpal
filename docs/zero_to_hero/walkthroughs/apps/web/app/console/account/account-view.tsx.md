---
fingerprint: 0e6370aacc0ec35c
---
The *Security* page (Phase 5, §5.5.4): whether one-time codes are on, and, if not, setting them up — show a new secret, then confirm a code from the person's authenticator app. Until a code is confirmed, nothing changes: a secret typed in wrongly can't lock anyone out.

@@ 1
`"use client"` — it runs in the browser.

@@ 3-4
Next.js's `Link`, and React's tools.

@@ 6-14
The console's shared pieces.

@@ 15
The client, its error, and the shapes of the signed-in person and of a new secret.

@@ 17
One client for the page.

@@ 19-20
**`grouped`** — the secret in groups of four letters, as apps show it and people type it. `match(/.{1,4}/g)` cuts it into pieces of up to four characters.

@@ 22
**`AccountView`**.

@@ 23-25
Its state: who is signed in (or `"signed-out"`, or `null` while loading), a secret on offer, and an error.

@@ 27-33
**`load`** — who is signed in; run on arrival, with a message if it fails.

@@ 35-42
**`attempt`** — run one piece of work, showing the API's words if it is refused.

@@ 44
**`start`** — ask for a new secret, and show it.

@@ 46-48
**`confirm`** — the form was sent: read the code, without any spaces the person typed between the digits.

@@ 49-54
Confirm it; on success, hide the secret and reload — the page now says "On".

@@ 56-73
Loading, a failure, or nobody signed in — with a way back to the console.

@@ 75-82
The page, framed by the console, with a link back to the organisations.

@@ 83-89
The heading, the person's address, and the error, if any.

@@ 91-94
**One-time codes** — a panel.

@@ 95-99
Already on: say so, announced (`role="status"`), and what it means at sign-in.

@@ 100-109
Off, and nothing on offer: what one-time codes are for, and a button to set them up.

@@ 110-113
**Step 1** — the secret to add to the app,

@@ 114-119
shown in groups of four;

@@ 120-123
or, on a phone with an authenticator app, a link that opens it there (`otpauth://`). A QR code would need a new library (a download), so it waits.

@@ 124-135
**Step 2** — the code the app shows: a numeric keyboard on phones (`inputMode`), filled in by the phone itself where it can (`autoComplete="one-time-code"`), and six digits, spaces allowed (`pattern`).

@@ 136-141
The button, and the end of the steps.

@@ 142-145
End of the panel, the page and `AccountView`.
