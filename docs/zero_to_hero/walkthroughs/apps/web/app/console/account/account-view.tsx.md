---
fingerprint: 1621e9bdfeedf5ee
---
The *Security* page (Phase 5, §5.5.4): whether one-time codes are on, and, if not, setting them up — show a new secret, then confirm a code from the person's authenticator app. Until a code is confirmed, nothing changes: a secret typed in wrongly can't lock anyone out.

@@ 1
`"use client"` — it runs in the browser.

@@ 3-5
Next.js's `Link`; `qrcode`, which draws a QR code (approved as D13); and React's tools.

@@ 7-15
The console's shared pieces.

@@ 16
The client, its error, and the shapes of the signed-in person and of a new secret.

@@ 18
One client for the page.

@@ 20-21
**`grouped`** — the secret in groups of four letters, as apps show it and people type it. `match(/.{1,4}/g)` cuts it into pieces of up to four characters.

@@ 23-24
**`Offer`** — a secret on offer, plus its QR code as a `data:` URL (the page's security policy allows `data:` images).

@@ 26
**`AccountView`**.

@@ 27-30
Its state: who is signed in (or `"signed-out"`, or `null` while loading), a secret on offer with its picture, recovery codes to show, and an error.

@@ 32-38
**`load`** — who is signed in; run on arrival, with a message if it fails.

@@ 40-47
**`attempt`** — run one piece of work, showing the API's words if it is refused.

@@ 49-53
**`start`** — ask for a new secret, then draw its `otpauth://` address as a QR code: a PNG image, 200 pixels square, as a `data:` URL. It is drawn **in the browser**, so the secret never goes to any other service.

@@ 55-57
**`confirm`** — the form was sent: read the code, without any spaces the person typed between the digits.

@@ 58-80
Confirm it; on success, show the recovery codes, hide the secret and reload — the page now says "On". **`replaceCodes`** — ask for a fresh set and show it. **`turnOff`** — the turn-off form was sent: read the password and the code (spaces removed), and switch codes off; hide any codes shown.

@@ 82-99
Loading, a failure, or nobody signed in — with a way back to the console.

@@ 101-108
The page, framed by the console, with a link back to the organisations.

@@ 109-115
The heading, the person's address, and the error, if any.

@@ 117-120
**One-time codes** — a panel.

@@ 121-136
**The recovery codes**, when there are some to show — just after switching codes on, or after asking for a fresh set: announced (`role="status"`), with what they are for and a warning that they won't be shown again, in two columns of fixed-width type so each letter is easy to copy.

@@ 137-172
**Already on**: say so, announced, with how many recovery codes are left. A button for a fresh set. And the **turn-off form**: the password (`autoComplete="current-password"`, so a password manager can fill it) and a code from the app, then *Turn off*.

@@ 173-182
Off, and nothing on offer: what one-time codes are for, and a button to set them up.

@@ 183-186
**Step 1** — scan the QR code with the authenticator app,

@@ 187-194
the picture itself. Next.js prefers its `<Image>`, which resizes and caches images from a server; a picture made in the browser gains nothing from that, so a plain `<img>` is used and the lint rule is told why (`biome-ignore`). Its `alt` text tells a screen-reader user what it is.

@@ 195
Or type the key in by hand:

@@ 196-201
shown in groups of four;

@@ 202-205
or, on a phone with an authenticator app, a link that opens it there (`otpauth://`). A QR code would need a new library (a download), so it waits.

@@ 206-217
**Step 2** — the code the app shows: a numeric keyboard on phones (`inputMode`), filled in by the phone itself where it can (`autoComplete="one-time-code"`), and six digits, spaces allowed (`pattern`).

@@ 218-223
The button, and the end of the steps.

@@ 224-227
End of the panel, the page and `AccountView`.
