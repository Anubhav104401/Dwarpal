---
fingerprint: 818595810d72373a
---
**Passkeys in the browser** (Phase 9, §5.9.2): translating WebAuthn's options and answers between the API's JSON and the browser's bytes.

@@ 1-5
The module's comment: the API speaks JSON, with bytes written as base64url; the browser's passkey functions want real bytes and answer in bytes. These functions translate, and decide nothing — the server checks everything.

@@ 7
A JSON object of unknown shape.

@@ 9-14
**`fromBase64Url`** — turn `-` and `_` back into `+` and `/`, put back the `=` padding that makes the length a multiple of 4, decode with the browser's `atob` (which gives one character per byte), and copy the character codes into bytes. The return type says the bytes sit in an ordinary `ArrayBuffer`, which is what the browser's functions accept.

@@ 16-22
**`toBase64Url`** — the reverse: one character per byte, `btoa`, then swap to the URL-safe characters and drop the padding.

@@ 24-25
Small readers for answers of unknown shape: text or empty, an object or empty.

@@ 27-30
**`passkeysSupported`** — the browser has `PublicKeyCredential` (and this code isn't running on the server, where there is no `window`).

@@ 32-38
**`creationOptions`** — the registration options from the API, read field by field.

@@ 39-53
Built in the shape `navigator.credentials.create` takes: the challenge and the person's handle as bytes; the site; the algorithms; a passkey kept on the device (`requireResidentKey` is the older spelling, for older browsers) that verifies the person; no attestation; the passkeys already registered, as bytes, so the device won't make a second; and the time limit, five minutes unless the API says otherwise.

@@ 55-64
**`requestOptions`** — the sign-in options: the challenge, our site's name, the person verified. No `allowCredentials`: by not naming any passkeys, the browser offers every passkey it holds for this site, so nobody types an e-mail address.

@@ 66-76
**`registrationAnswer`** — a new passkey's two answers, as base64url, for `POST /passkeys`.

@@ 78-86
**`signInAnswer`** — a sign-in's answers: the passkey's ID, the client data, the device's data and the signature.

@@ 87-91
The account's handle too, if the device gave one, so the server can check it belongs to the passkey's owner.

@@ 93-96
**`cancelled`** — the browser reports a closed prompt, or one left to time out, as `NotAllowedError` (or `AbortError`). That isn't an error worth showing: the person changed their mind.
