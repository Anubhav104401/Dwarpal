---
fingerprint: 0dfa7cf21c7d5711
---
The *Security* page (Phase 5, §5.5.4): whether one-time codes are on, and, if not, setting them up — show a new secret, then confirm a code from the person's authenticator app. Until a code is confirmed, nothing changes: a secret typed in wrongly can't lock anyone out.

@@ 1
`"use client"` — it runs in the browser.

@@ 3-5
Next.js's `Link`; `qrcode`, which draws a QR code (approved as D13); and React's tools.

@@ 7-15
The console's shared pieces.

@@ 16-17
The client, its error, and the shapes of the signed-in person, a passkey and a new secret; and the passkey helpers (Phase 9).

@@ 19
One client for the page.

@@ 21-22
**`grouped`** — the secret in groups of four letters, as apps show it and people type it. `match(/.{1,4}/g)` cuts it into pieces of up to four characters.

@@ 24-25
**`Offer`** — a secret on offer, plus its QR code as a `data:` URL (the page's security policy allows `data:` images).

@@ 27
**`AccountView`**.

@@ 28-31
Its state: who is signed in (or `"signed-out"`, or `null` while loading), a secret on offer with its picture, recovery codes to show, and an error.

@@ 47-54
**`attempt`** — run one piece of work, showing the API's words if it is refused.

@@ 56-60
**`start`** — ask for a new secret, then draw its `otpauth://` address as a QR code: a PNG image, 200 pixels square, as a `data:` URL. It is drawn **in the browser**, so the secret never goes to any other service.

@@ 62-64
**`confirm`** — the form was sent: read the code, without any spaces the person typed between the digits.

@@ 65-87
Confirm it; on success, show the recovery codes, hide the secret and reload — the page now says "On". **`replaceCodes`** — ask for a fresh set and show it. **`turnOff`** — the turn-off form was sent: read the password and the code (spaces removed), and switch codes off; hide any codes shown.

@@ 115-132
Loading, a failure, or nobody signed in — with a way back to the console.

@@ 134-142
The page, framed by the console with its sidebar (`signedIn`), and a link back to the organisations.

@@ 143-149
The heading, the person's address, and the error, if any.

@@ 151-154
**One-time codes** — a panel.

@@ 155-170
**The recovery codes**, when there are some to show — just after switching codes on, or after asking for a fresh set: announced (`role="status"`), with what they are for and a warning that they won't be shown again, in two columns of fixed-width type so each letter is easy to copy.

@@ 171-206
**Already on**: say so, announced, with how many recovery codes are left. A button for a fresh set. And the **turn-off form**: the password (`autoComplete="current-password"`, so a password manager can fill it) and a code from the app, then *Turn off*.

@@ 207-216
Off, and nothing on offer: what one-time codes are for, and a button to set them up.

@@ 217-220
**Step 1** — scan the QR code with the authenticator app,

@@ 221-228
the picture itself. Next.js prefers its `<Image>`, which resizes and caches images from a server; a picture made in the browser gains nothing from that, so a plain `<img>` is used and the lint rule is told why (`biome-ignore`). Its `alt` text tells a screen-reader user what it is.

@@ 229
Or type the key in by hand:

@@ 230-235
shown in groups of four;

@@ 236-239
or, on a phone with an authenticator app, a link that opens it there (`otpauth://`). A QR code would need a new library (a download), so it waits.

@@ 240-251
**Step 2** — the code the app shows: a numeric keyboard on phones (`inputMode`), filled in by the phone itself where it can (`autoComplete="one-time-code"`), and six digits, spaces allowed (`pattern`).

@@ 252-257
The button, and the end of the steps.

@@ 32-33
Since Phase 9 also the person's passkeys, and whether this browser can make them.

@@ 35-39
**`load`** — who is signed in, and, if anyone is, their passkeys.

@@ 41
Whether the browser supports passkeys is asked once the page is in the browser. Asking while the server draws the page would give a different answer there than in the browser, and React would complain that the two don't match.

@@ 43-45
Load on arrival, with a message if it fails.

@@ 89-94
**`addPasskey`** (Phase 9) — the form was sent: read its fields, with spaces taken out of the code.

@@ 95-102
Get the options; ask the browser to make a passkey, which asks the device to verify the person; if one was made, send its answer with the name and the password (and code); then clear the form and load the list again.

@@ 103-107
The person closing the prompt isn't an error; anything else is shown.

@@ 109-113
**`removePasskey`** — remove one, then load the list again.

@@ 258
End of the one-time codes panel.

@@ 260-267
**Passkeys** — a panel, with a sentence saying what a passkey is and why it can't be phished.

@@ 268-292
The passkeys, if any: each with its name, when it was added, and when it was last used — and a **Remove** button whose accessible name says which passkey it removes.

@@ 293-304
Where the browser can make passkeys: a form, first with a name for the new one.

@@ 305-314
The password, to confirm it's the person. The label differs from the one-time-codes panel's, so each field has a name of its own.

@@ 315-327
A code, only when one-time codes are on.

@@ 328-331
**Add a passkey**.

@@ 332-334
Where the browser can't: a sentence saying so.

@@ 335-338
End of the panel, the page and `AccountView`.
