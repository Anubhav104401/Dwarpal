---
fingerprint: d7fb645ec802001c
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

@@ 48-55
**`attempt`** — run one piece of work, showing the API's words if it is refused.

@@ 57-61
**`start`** — ask for a new secret, then draw its `otpauth://` address as a QR code: a PNG image, 200 pixels square, as a `data:` URL. It is drawn **in the browser**, so the secret never goes to any other service.

@@ 63-65
**`confirm`** — the form was sent: read the code, without any spaces the person typed between the digits.

@@ 66-88
Confirm it; on success, show the recovery codes, hide the secret and reload — the page now says "On". **`replaceCodes`** — ask for a fresh set and show it. **`turnOff`** — the turn-off form was sent: read the password and the code (spaces removed), and switch codes off; hide any codes shown.

@@ 141-158
Loading, a failure, or nobody signed in — with a way back to the console.

@@ 160-168
The page, framed by the console with its sidebar (`signedIn`), and a link back to the organisations.

@@ 169-175
The heading, the person's address, and the error, if any.

@@ 177-180
**One-time codes** — a panel.

@@ 181-196
**The recovery codes**, when there are some to show — just after switching codes on, or after asking for a fresh set: announced (`role="status"`), with what they are for and a warning that they won't be shown again, in two columns of fixed-width type so each letter is easy to copy.

@@ 197-232
**Already on**: say so, announced, with how many recovery codes are left. A button for a fresh set. And the **turn-off form**: the password (`autoComplete="current-password"`, so a password manager can fill it) and a code from the app, then *Turn off*.

@@ 233-242
Off, and nothing on offer: what one-time codes are for, and a button to set them up.

@@ 243-246
**Step 1** — scan the QR code with the authenticator app,

@@ 247-254
the picture itself. Next.js prefers its `<Image>`, which resizes and caches images from a server; a picture made in the browser gains nothing from that, so a plain `<img>` is used and the lint rule is told why (`biome-ignore`). Its `alt` text tells a screen-reader user what it is.

@@ 255
Or type the key in by hand:

@@ 256-261
shown in groups of four;

@@ 262-265
or, on a phone with an authenticator app, a link that opens it there (`otpauth://`). A QR code would need a new library (a download), so it waits.

@@ 266-277
**Step 2** — the code the app shows: a numeric keyboard on phones (`inputMode`), filled in by the phone itself where it can (`autoComplete="one-time-code"`), and six digits, spaces allowed (`pattern`).

@@ 278-283
The button, and the end of the steps.

@@ 32-33
Since Phase 9 also the person's passkeys, and whether this browser can make them.

@@ 36-40
**`load`** — who is signed in, and, if anyone is, their passkeys.

@@ 42
Whether the browser supports passkeys is asked once the page is in the browser. Asking while the server draws the page would give a different answer there than in the browser, and React would complain that the two don't match.

@@ 44-46
Load on arrival, with a message if it fails.

@@ 90-95
**`addPasskey`** (Phase 9) — the form was sent: read its fields, with spaces taken out of the code.

@@ 96-103
Get the options; ask the browser to make a passkey, which asks the device to verify the person; if one was made, send its answer with the name and the password (and code); then clear the form and load the list again.

@@ 104-108
The person closing the prompt isn't an error; anything else is shown.

@@ 110-114
**`removePasskey`** — remove one, then load the list again.

@@ 284
End of the one-time codes panel.

@@ 286-293
**Passkeys** — a panel, with a sentence saying what a passkey is and why it can't be phished.

@@ 294-318
The passkeys, if any: each with its name, when it was added, and when it was last used — and a **Remove** button whose accessible name says which passkey it removes.

@@ 319-330
Where the browser can make passkeys: a form, first with a name for the new one.

@@ 331-340
The password, to confirm it's the person. The label differs from the one-time-codes panel's, so each field has a name of its own.

@@ 341-353
A code, only when one-time codes are on.

@@ 354-357
**Add a passkey**.

@@ 358-360
Where the browser can't: a sentence saying so.

@@ 34
**`passwordChanged`** — whether to say that the password was changed.

@@ 116-117
**`changePassword`** (decision D31) — the form's three fields go to the API, which ends every other session and gives this browser a new one (the client keeps its new CSRF token).

@@ 118-122
The form, its fields, the code without spaces, and any earlier notice cleared.

@@ 123-128
On success the form is emptied and the notice shown; a refusal (a wrong password, a weak new one) is shown by `attempt`.

@@ 130-131
**`deleteAccount`** (decision D32) — erase the account, then leave for the console's front page.

@@ 132-134
The form's password, and the code without spaces.

@@ 135-139
On success the page moves to `/console`, now signed out; a refusal (a wrong password, or an only owner with others in the organisation) is shown instead.

@@ 361
End of the passkeys panel.

@@ 363-369
**The password panel** (decision D31): what changing it does, said first.

@@ 370-374
After a change, the notice — `role="status"` makes screen readers announce it.

@@ 375-385
The form: the current password (`current-password` lets a password manager fill it in)…

@@ 386-397
…the new one — at least 12 characters, as the API requires (the browser checks too) — which a password manager may offer to make (`new-password`)…

@@ 398-410
…and a one-time code when codes are on: six digits, spaces allowed.

@@ 411-414
The button, and the form's end.

@@ 415
End of the panel.

@@ 417-425
**Deleting the account** (decision D32): what it does is said before anything is asked — what is erased, what happens to an organisation where they are alone, and what to do first if they are an only owner.

@@ 426-436
The form: the password…

@@ 437-449
…a code when codes are on…

@@ 450-453
…and a tick that they understand it can't be undone: `required`, so the browser won't send the form without it.

@@ 454-459
A red button: the one thing on this page that can't be reversed.

@@ 460-461
The form's end, and the panel's.

@@ 462-464
The end of the page, and of `AccountView`.
