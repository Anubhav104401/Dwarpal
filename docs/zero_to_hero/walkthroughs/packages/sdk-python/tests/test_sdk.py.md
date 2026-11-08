---
fingerprint: e3a960073e2889c2
---
Tests for the **Python SDK** (§5.9.1), mirroring the Node SDK's. A further test in the API's suite runs the SDK against the real API.

@@ 1
The module's docstring: the API is faked by httpx's own mock transport — no network, no server.

@@ 3
The project-wide type-hint setting.

@@ 5-25
Hashing, HMAC, JSON, the clock, dates, httpx, pytest, the SDK's public names, and joserfc to sign test tokens with keys made here.

@@ 27-40
An API address, a test key, a session ID, a project ID, and the API's answer to creating a session.

@@ 43-44
**`api`** — an httpx client whose every request goes to the given function instead of a network.

@@ 47-58
**Test — a session is created with the key, and only the fields given**: the request carries the key, and a body without the fields left out; the answer is read into a `CreatedSession`.

@@ 79-86
**Test — a refusal carries the API's stable code and request ID.**

@@ 89-93
**Test — bad keys and session IDs are refused before anything is sent** — including a "session ID" that tries to climb the address (`../admin`).

@@ 96-99
**Test — a malformed answer is reported, not trusted**: a status Dwarpal never gives.

@@ 102-113
**Test — the async client reads a completed session.** (`# fmt: skip` keeps the long answer on few lines.)

@@ 116-118
**Age tokens.** A signing key made for the tests, with key ID `k1`.

@@ 121-128
**`token`** — a signed age token, valid unless a test overrides a claim, the type or the key.

@@ 131-141
**`keys`** — an issuer's keys served by a fake address that counts its calls, with no refresh limit.

@@ 144-145
**`check`** — verify a token for an 18+ door.

@@ 148-151
**Test — a genuine pass allows entry at its age only**: at 18 yes; at 21, which the token doesn't state, no.

@@ 154-167
**Test — forged, foreign, expired or odd tokens are refused**: another issuer, another project, expired, the wrong type, an unknown outcome — and a forgery signed with a different key that claims the real key's ID.

@@ 170-172
**Test — a token for another session is refused.**

@@ 175-180
**Test — a new signing key is fetched once when a token needs it**: the keys kept predate a rotation; a token signed with the new key still verifies, after exactly one fetch.

@@ 183-187
**Webhooks.** A test secret, and an event's body.

@@ 189-192
**`signed`** — a `Dwarpal-Signature` header for a body, at a time, with a secret — as Dwarpal makes them.

@@ 195-196
**Test — a genuine webhook gives its event.**

@@ 199-211
**Test — missing, forged, stale or mismatched webhooks are refused**: no header, a garbled one, the wrong secret, an hour old, and a signature for a different body.

@@ 61-66
**Test — idempotency keys** (9 Nov): a stand-in API notes each request and answers with a new session.

@@ 68-70
A session created with a key, then one without.

@@ 71-72
The first request carried the `Idempotency-Key` header, the second none; and the key isn't in the body.

@@ 73-75
Four malformed keys — too short, with spaces, too long, and one ending in a line break — are each refused with a `ValueError` naming `idempotency_key`…

@@ 76
…and nothing more was sent.
