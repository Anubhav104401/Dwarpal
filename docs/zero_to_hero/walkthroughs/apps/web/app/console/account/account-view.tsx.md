---
fingerprint: 97774f883d73a016
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

@@ 27-29
Its state: who is signed in (or `"signed-out"`, or `null` while loading), a secret on offer with its picture, and an error.

@@ 31-37
**`load`** — who is signed in; run on arrival, with a message if it fails.

@@ 39-46
**`attempt`** — run one piece of work, showing the API's words if it is refused.

@@ 48-52
**`start`** — ask for a new secret, then draw its `otpauth://` address as a QR code: a PNG image, 200 pixels square, as a `data:` URL. It is drawn **in the browser**, so the secret never goes to any other service.

@@ 54-56
**`confirm`** — the form was sent: read the code, without any spaces the person typed between the digits.

@@ 57-62
Confirm it; on success, hide the secret and reload — the page now says "On".

@@ 64-81
Loading, a failure, or nobody signed in — with a way back to the console.

@@ 83-90
The page, framed by the console, with a link back to the organisations.

@@ 91-97
The heading, the person's address, and the error, if any.

@@ 99-102
**One-time codes** — a panel.

@@ 103-107
Already on: say so, announced (`role="status"`), and what it means at sign-in.

@@ 108-117
Off, and nothing on offer: what one-time codes are for, and a button to set them up.

@@ 118-121
**Step 1** — scan the QR code with the authenticator app,

@@ 122-129
the picture itself. Next.js prefers its `<Image>`, which resizes and caches images from a server; a picture made in the browser gains nothing from that, so a plain `<img>` is used and the lint rule is told why (`biome-ignore`). Its `alt` text tells a screen-reader user what it is.

@@ 130
Or type the key in by hand:

@@ 131-136
shown in groups of four;

@@ 137-140
or, on a phone with an authenticator app, a link that opens it there (`otpauth://`). A QR code would need a new library (a download), so it waits.

@@ 141-152
**Step 2** — the code the app shows: a numeric keyboard on phones (`inputMode`), filled in by the phone itself where it can (`autoComplete="one-time-code"`), and six digits, spaces allowed (`pattern`).

@@ 153-158
The button, and the end of the steps.

@@ 159-162
End of the panel, the page and `AccountView`.
