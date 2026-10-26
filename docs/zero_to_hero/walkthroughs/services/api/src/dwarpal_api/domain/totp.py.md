---
fingerprint: 7b0681954c469d99
---
**One-time codes** (Phase 4, §5.4.5): the six digits an authenticator app shows, changing every 30 seconds. This is **TOTP**, *Time-based One-Time Password* (RFC 6238), built on HOTP (RFC 4226). With codes switched on, a stolen password alone is no longer enough to sign in: the thief also needs the person's phone.

How it works: when codes are switched on, Dwarpal and the phone agree on a random **secret**, usually by scanning a QR code. From then on, both sides compute the same code independently: an HMAC of the secret and the current 30-second **step** (the time divided by 30), cut down to six digits. Nothing is sent between them; they agree because they share the secret and roughly agree on the time.

The file is pure arithmetic, and its output is checked against the standard's own published examples (`test_console_rules.py`).

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-9
`base64` (secrets are written in Base32), `hashlib` and `hmac` (the code), `secrets` (randomness), and `quote` (to make text safe inside an address).

@@ 11-13
A step is 30 seconds; a code has 6 digits; and codes from one step either side of now are accepted too, because a phone's clock may be a little off.

@@ 16-18
**`new_secret`** — 20 random bytes, the length RFC 4226 recommends, written in **Base32** (letters A–Z and digits 2–7), the form authenticator apps expect. The `=` padding at the end is removed, as apps do.

@@ 21-22
**`code_at`** — the code for one step.

@@ 23
Turn the Base32 secret back into bytes, first putting back the padding Base32 needs (to a multiple of 8 characters).

@@ 24
The HMAC-SHA1 of the step number, written as 8 bytes, keyed with the secret. (SHA-1 is weak for other uses, but inside HMAC it is still safe, and it is what every authenticator app uses.)

@@ 25-26
**Dynamic truncation** (RFC 4226): the last 4 bits of the digest choose a position; the 4 bytes there become a number, with the top bit cleared (`& 0x7FFF_FFFF`) so it is never negative.

@@ 27
Its last six decimal digits, with leading zeros kept (`zfill`), so `81804` shows as `081804`.

@@ 30-32
**`accepted_step`** — is this code right now? It returns the step it belongs to, or `None`.

@@ 33-34
Anything other than six digits is wrong at once.

@@ 35
The current step.

@@ 36-38
Try the step before, now, and the step after. A code is accepted only if it matches (compared in constant time) **and** its step is later than the last code used. Remembering that step (`users.totp_last_step`) makes every code single-use: someone who sees a code over your shoulder can't sign in with it after you.

@@ 39
No step matched.

@@ 42-43
**`provisioning_uri`** — the `otpauth://` address an authenticator app reads, usually shown as a QR code.

@@ 44
The label the app displays, `Dwarpal:ana@shop.example`, made safe for an address.

@@ 45-47
The address: the label, the secret, the issuer, and the settings — SHA-1, 6 digits, 30 seconds — so any standard app computes the same codes.
