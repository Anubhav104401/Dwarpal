---
fingerprint: 79f734238364a8db
---
A **software passkey device** for the tests (§5.9.2). The pytest settings put this folder on Python's path, so both `test_webauthn.py` and `test_api.py` import it.

@@ 1-2
The module's docstring: a software stand-in for a phone or a security key, so the tests exercise the real checks.

@@ 4
The project-wide type-hint setting.

@@ 6-12
Base64, hashing, JSON, random bytes, `struct`, dataclasses and `Any`.

@@ 14-16
From `cryptography`: SHA-256, the two kinds of key, and the formats to write a public key out in.

@@ 19-28
**`cbor`** — the writer the server's reader is tested against. `head` writes an item's first byte (major type in the top 3 bits) and, for numbers 24 and above, the 1, 2, 4 or 8 bytes after it.

@@ 30-44
Each kind in turn: `null`, `true` and `false` (checked before whole numbers, since in Python `True` is also an `int`), positive and negative numbers, bytes, text, lists and maps.

@@ 47-48
**`b64url`** — base64url without padding.

@@ 51-60
**`Device`** — one passkey on one device. By default it is for `localhost`, on the console's development origin, signs with Ed25519, reports the person present and verified, starts its counter at 0, and has a random 16-byte ID. A test changes any of these to make a bad answer.

@@ 62-64
It makes both kinds of key at once, and uses the one its `algorithm` names.

@@ 66-71
**`cose_key`** — the public key as a COSE key: Ed25519's 32 raw bytes, or P-256's x and y (the uncompressed point is `04`, then 32 bytes of x, then 32 of y).

@@ 73-75
**`_auth_data`** — the device's data: the site's hash, the flags, the counter, and anything attested.

@@ 77-78
**`_client`** — the client data a browser would write: the kind of request, the challenge, and the origin (another, to imitate a phishing site).

@@ 80-89
**`create`** — a new passkey's answer: the attested credential (16 zero bytes for the device's model, the ID's length, the ID, the key) inside an attestation object with format `none`; all as base64url, as the browser sends them.

@@ 91-103
**`get`** — a sign-in's answer: move the counter on by `step`, and sign the device's data followed by the SHA-256 of the client data, as a real device does.
