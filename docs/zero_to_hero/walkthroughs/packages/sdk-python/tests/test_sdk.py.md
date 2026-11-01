---
fingerprint: 46192508a7c99fa6
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

@@ 61-68
**Test — a refusal carries the API's stable code and request ID.**

@@ 71-75
**Test — bad keys and session IDs are refused before anything is sent** — including a "session ID" that tries to climb the address (`../admin`).

@@ 78-81
**Test — a malformed answer is reported, not trusted**: a status Dwarpal never gives.

@@ 84-95
**Test — the async client reads a completed session.** (`# fmt: skip` keeps the long answer on few lines.)

@@ 98-100
**Age tokens.** A signing key made for the tests, with key ID `k1`.

@@ 103-110
**`token`** — a signed age token, valid unless a test overrides a claim, the type or the key.

@@ 113-123
**`keys`** — an issuer's keys served by a fake address that counts its calls, with no refresh limit.

@@ 126-127
**`check`** — verify a token for an 18+ door.

@@ 130-133
**Test — a genuine pass allows entry at its age only**: at 18 yes; at 21, which the token doesn't state, no.

@@ 136-149
**Test — forged, foreign, expired or odd tokens are refused**: another issuer, another project, expired, the wrong type, an unknown outcome — and a forgery signed with a different key that claims the real key's ID.

@@ 152-154
**Test — a token for another session is refused.**

@@ 157-162
**Test — a new signing key is fetched once when a token needs it**: the keys kept predate a rotation; a token signed with the new key still verifies, after exactly one fetch.

@@ 165-169
**Webhooks.** A test secret, and an event's body.

@@ 171-174
**`signed`** — a `Dwarpal-Signature` header for a body, at a time, with a secret — as Dwarpal makes them.

@@ 177-178
**Test — a genuine webhook gives its event.**

@@ 181-193
**Test — missing, forged, stale or mismatched webhooks are refused**: no header, a garbled one, the wrong secret, an hour old, and a signature for a different body.
