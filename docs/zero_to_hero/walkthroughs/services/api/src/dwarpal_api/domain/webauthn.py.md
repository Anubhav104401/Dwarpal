---
fingerprint: 6ced0d8c40c8f486
---
The **passkey checks** (Phase 9, §5.9.2): pure functions, with no database or network, that decide whether a device's answer can be trusted. The rest of the API stores and fetches; this module only judges.

@@ 1-10
The module's docstring: what a passkey is — a key pair whose private half never leaves the person's device — and the small part of WebAuthn the console uses: no attestation (the console doesn't need to know the device's make), the person always verified by the device, and the two signature algorithms passkeys use in practice.

@@ 12
The project-wide type-hint setting.

@@ 14-19
Base64, hashing, JSON, `struct` (for reading fixed-size numbers out of bytes), dataclasses, and `Any` for decoded CBOR, whose shape isn't known in advance.

@@ 21-23
From the `cryptography` library, already used for the API's signing keys: the error a bad signature raises, SHA-256, and the two kinds of public key — elliptic-curve (P-256) and Ed25519.

@@ 25-28
The flags byte in the device's answer. Bit 0 (`0x01`): the person was **present** (touched the key, or confirmed). Bit 2 (`0x04`): the device **verified** them (PIN, fingerprint or face). Bit 6 (`0x40`): the answer carries a new **credential**, as when a passkey is made.

@@ 29
How deeply CBOR may nest. WebAuthn's structures go three or four levels deep; a deeper one is an attack (a stack of nested lists to exhaust memory or recursion), so it is refused.

@@ 30
The two algorithms, by their COSE numbers: −8 is EdDSA (Ed25519), −7 is ES256 (ECDSA on P-256 with SHA-256).

@@ 33-38
**`WebAuthnError`** — the device's answer can't be trusted. It carries a stable `code` (such as `wrong_origin`), which the API turns into its own error code, and a message saying which check failed. It is a `ValueError`, so code that catches bad values catches it too.

@@ 41-46
**`b64url_decode`** — WebAuthn sends binary values as *base64url*: base64 with `-` and `_` instead of `+` and `/`, and without the `=` padding. The padding is put back (`-len(text) % 4` is how many `=` are missing), and anything that isn't valid becomes a `WebAuthnError` rather than a crash.

@@ 49-50
**`b64url_encode`** — the reverse: encode, and strip the padding.

@@ 53
**CBOR** (RFC 8949) is a compact binary cousin of JSON. A device writes its answers in it. Rather than add a library, this module reads the few kinds WebAuthn uses — about forty lines, all tested.

@@ 56-64
**`_length`** — every CBOR item starts with one byte: the top 3 bits are its *major type* (number, string, list…), the low 5 bits its *argument* (a length, or the number itself). Below 24 the argument is those bits; 24, 25, 26 and 27 mean it follows in the next 1, 2, 4 or 8 bytes. Anything else (or a length that runs past the end) is refused.

@@ 67-72
**`cbor_decode`** — one item starting at position `at`: its value and where the next item starts. Too deep, or nothing left: refused. Split the first byte into its major type and argument. Type 7 (simple values) keeps the raw argument; every other type reads its length.

@@ 73-76
Types 0 and 1: a whole number, and a negative one (CBOR stores −1 − n, so −1 is stored as 0).

@@ 77-86
Types 2 and 3: bytes and text, `value` bytes long — refused if that runs past the end. Text must be valid UTF-8 (the tests found that a broken string escaped as the wrong kind of error, so it is caught here).

@@ 87-92
Type 4: a list of `value` items, each read in turn, one level deeper.

@@ 93-100
Type 5: a map of `value` key–value pairs. WebAuthn's keys are numbers or text; any other kind of key (a list, say — which Python couldn't even use as a key), or the same key twice, is refused. A repeated key matters: two readers could otherwise disagree on which value counts.

@@ 101-104
Type 7: `false`, `true` and `null` (20, 21, 22). Anything else — floating-point numbers, tags — WebAuthn doesn't use here, so it is refused.

@@ 107
The second part: the device's own data.

@@ 110-116
**`AuthenticatorData`** — what the device signs: a hash of the site's name, the flags, a signature counter, and — only when a passkey is made — its ID and public key (kept as the CBOR bytes the device sent, which is what gets stored).

@@ 119-121
**`parse_authenticator_data`** — its docstring gives the layout, byte by byte.

@@ 122-127
At least 37 bytes: 32 of the site's hash, 1 of flags (byte 32), and a 4-byte counter (bytes 33–36; `>I` means a big-endian unsigned 32-bit number). Without the credential flag, that's all.

@@ 128-133
With it: 16 bytes naming the device's model (bytes 37–52, unused here), a 2-byte length (`>H`, bytes 53–54), the credential's ID, and then the public key — a CBOR item, read to find where it ends.

@@ 136-141
**`public_key_of`** — a COSE key (RFC 9053), CBOR with numbered fields: 1 is the key type, 3 the algorithm, −1 the curve, −2 and −3 the key's coordinates.

@@ 142-147
Ed25519 (key type 1, "OKP"; curve 6) is 32 raw bytes. P-256 (key type 2, "EC2"; curve 1) is a point — x and y, joined after the byte `04` that means "uncompressed". Both are handed to `cryptography`.

@@ 148-150
A key of the right type can still be broken — the wrong length, or a point that isn't on the curve; `cryptography` raises `ValueError`, which becomes our error. Any other algorithm (RSA, for one) is refused: the console accepts only what it can check.

@@ 153
The third part: the two *ceremonies*, as WebAuthn calls them — making a passkey, and signing in with one.

@@ 156-167
**`_client_data`** — the browser's own record of the request, as JSON: its `type` (`webauthn.create` or `webauthn.get`), the challenge, and the **origin** — the site the page was on. The origin is written by the browser, not the page, so a phishing site can't fake it. All three must match.

@@ 170-174
**`_checked`** — the site's hash must be the hash of our name (a passkey made for another site doesn't count), and the person must be both present and verified.

@@ 177-181
**`NewPasskey`** — what a registration leaves to store: the ID, the public key, and the starting counter.

@@ 184-190
**`verify_registration`** — check the client data, read the *attestation object* (CBOR with the device's data in `authData`), and check that data.

@@ 191-197
It must carry a credential, with a key this module can check later; then return what to store. (The attestation's own signature isn't checked: with `"none"` attestation there is none to check, and the console doesn't need to know who made the device.)

@@ 200-210
**`verify_assertion`** — a sign-in: the stored key and counter, the browser's answer, the challenge we gave, our origins and our site's name. It returns the counter to store.

@@ 211-213
The same checks of the client data (now `webauthn.get`) and of the device's data.

@@ 214-222
The device signed its data followed by the SHA-256 of the client data. Check that signature with the stored key — plain Ed25519, or ECDSA with SHA-256 — and refuse if it doesn't match.

@@ 223-227
The counter: a device that counts signs with a higher number each time. A number that doesn't go up means a second copy of the key is in use, so it is refused. Passkeys that sync between devices send 0 always, which proves nothing either way, so 0 is let through.
