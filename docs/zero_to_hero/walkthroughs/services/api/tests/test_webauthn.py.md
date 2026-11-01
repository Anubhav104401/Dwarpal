---
fingerprint: 0ba77d15fd1e1dbc
---
Tests for the **passkey checks** (§5.9.2), against a software device making real signatures.

@@ 1
The module's docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-23
Base64, `contextlib` (to ignore one kind of error), JSON, random bytes, pytest, Hypothesis, the test device, and the functions under test.

@@ 25-26
The console's development origin and site name.

@@ 29-38
**`register`** — make a passkey on a device for a challenge, and check it; return what the server would store.

@@ 41-52
**`sign_in`** — sign a challenge with the device and check it against the stored key and counter; return the new counter.

@@ 55-62
**Test — the reader reads back whatever the writer writes.** Hypothesis builds values from `null`, booleans, numbers across the full 64-bit range, bytes, text, lists and maps, nested; each must come back unchanged, using exactly all its bytes. (`# fmt: skip` keeps the generator readable.)

@@ 65-68
**Test — garbage gives our error and nothing else.** Random bytes either decode or raise `WebAuthnError`; anything else fails the test. This test found the two bugs the reader now guards against: invalid UTF-8, and a list as a map key.

@@ 71-75
**Test — specific bad inputs are refused**: lists nested 20 deep, a 5-byte string with 2 bytes left, a reserved length code, nothing at all, a map keyed by a list, a map with a key twice, and text that isn't UTF-8.

@@ 78-85
**Test — a passkey registers and then signs in**, with each algorithm: the ID and key come back, and the counter goes 1, then 2.

@@ 88-106
**Test — registration refuses** the wrong challenge, another site's origin, a passkey made for another site's name, and a person the device didn't verify — each with its own code.

@@ 107-110
And a sign-in's client data offered as a registration: the wrong kind of request.

@@ 113-120
**Test — keys that can't be checked are refused**: RSA, an Ed25519 key of the wrong length, a P-256 point that isn't on the curve, and something that isn't a map.

@@ 123-129
**Test — a forged sign-in is refused**: another passkey's key doesn't verify this device's signature.

@@ 130-143
Nor does this device's own signature with one bit flipped.

@@ 146-152
**Test — a counter that goes backwards** means a copy: the server has seen 9, so a 6 is refused as `cloned`.

@@ 153-156
But a passkey that always sends 0 — one that syncs between devices — keeps working.

@@ 159-174
**Test — an answer can't be reused for a new challenge**: the challenge the browser signed must be the one the server is expecting.

@@ 177-187
**Test — malformed answers give our error**: client data that isn't JSON or isn't an object, device data too short, attested data too short, and base64url of an impossible length; and well-formed base64url decodes.
