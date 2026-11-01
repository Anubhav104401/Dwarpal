---
fingerprint: 5cba0401defb0a60
---
**Passkeys** in the console (Phase 9, §5.9.2): adding, listing and removing them, and signing in with one. The checks are in `domain/webauthn.py`; this module handles challenges, storage and sessions around them.

@@ 1-6
The module's docstring: the passkey use cases, what this module does around the checks in `domain/webauthn.py`, and why a passkey sign-in needs no one-time code — the device has already verified the person.

@@ 8
The project-wide type-hint setting.

@@ 10-13
JSON, secure random bytes, type helpers, and `urlsplit` to read a host name out of an origin.

@@ 15-16
SQLAlchemy's `select` and `count`, and the error a unique column raises on a duplicate.

@@ 18-23
The passkey lookup and the unit of work; password checking; the users, memberships and passkeys tables; the audit log and the console's own helpers; identifiers, one-time codes and the passkey checks; our error class.

@@ 25-27
Types needed only by the type checker: the console session and the toolbox.

@@ 29-31
Five minutes to answer the device's prompt; at most ten passkeys per account; and **one** refusal for every way a passkey can fail to be found — an unknown passkey, or one whose account doesn't match — so the answer reveals nothing.

@@ 34-36
**`rp_id`** — the *relying party ID*: the site name passkeys are bound to. The setting if given, else the host of the console's first origin (`localhost` in development). A passkey made for one name can't be used on another.

@@ 39-43
**`_decoded`** — base64url from the browser, or a `422` if it isn't valid.

@@ 46-48
**`_reauthenticate`** — adding a passkey adds a way into the account, so a signed-in browser left open isn't enough: the password is needed, and a current one-time code too if those are on. Attempts count against the sign-in limits.

@@ 49-58
Spend a sign-in token; check the password; if one-time codes are on, check the code and, if it is good, mark it used (each code works once). Either one wrong: `403`. Both are checked before answering, so the answer doesn't say which was wrong.

@@ 61-69
**`registration_options`** — what the browser's `navigator.credentials.create` needs. A fresh 32-byte challenge; the person's existing passkeys (so the same device isn't registered twice); and the challenge kept in Valkey under this person's name, for five minutes. A newer request replaces an older one.

@@ 70-83
The options, in WebAuthn's own field names: the challenge; our site's name; the person — their handle is their account's random ID, which names no one, and their address as the label their device shows; the two algorithms we accept, Ed25519 first; a passkey that lives on the device (`residentKey`, so it can sign in without typing an address) and that verifies the person; no attestation; the passkeys to leave out; and the time limit in milliseconds.

@@ 86-95
**`register`** — the person's chosen name for the passkey, the device's two answers, and the password (and code) to confirm it's them.

@@ 96-105
Lock the person's row, confirm it's them, then **take** the challenge — read and delete in one step, so an answer can be used once. None left (expired, or used): `409`.

@@ 106-115
Check the device's answer (`domain/webauthn.py`). A failure becomes a `422` whose code names the check — `passkey_wrong_origin`, say.

@@ 116-118
At most ten passkeys: a cap on how much one account can store.

@@ 119-132
Keep the passkey. The `flush` sends it to the database now, so a duplicate — this device's passkey, already registered — is caught here as a `409`, rather than later as an unexpected error (the API test found that).

@@ 133-135
Record it in the audit log of every organisation the person belongs to, commit, and answer with the passkey as the console shows it.

@@ 138-144
**`_shown`** — a passkey as the console sees it: an ID with the `pk_` prefix, its name, and when it was added and last used. Never its key.

@@ 147-152
**`list_passkeys`** — the person's passkeys, oldest first. Row-level security would hide anyone else's anyway.

@@ 155-159
**`remove`** — a passkey's ID, or `404` if it isn't one.

@@ 160-168
Find it, and the person; if it isn't theirs, the same `404`. Delete it, record that in the audit log, and commit. Removing needs no password: it takes a way in away rather than adding one.

@@ 171-173
**`sign_in_options`** — signing in with a passkey names no account: the browser shows the person their passkeys for this site and they pick one. Each request counts against the address's sign-in limit, so nobody can fill Valkey with challenges.

@@ 174-182
A fresh challenge, kept for five minutes under its own value (any one person may hold several, in several tabs), and the options: the challenge, our site's name, the person verified, and the time limit.

@@ 185-192
**`_spend_address`** — take a token from the address's sign-in bucket (shared with password sign-in); none left: `429`, with how many seconds to wait.

@@ 195-204
**`_challenge_in`** — the challenge the browser says it signed, read out of the client data. It is only used to look up the challenge in Valkey; the full check comes later. Anything malformed, or implausibly long, is the one refusal.

@@ 207-216
**`sign_in`** — the passkey's ID, the device's three answers, the account's handle if the device gave one, and the network address.

@@ 217-221
Spend a token, read the challenge, and take it from Valkey. If it isn't there — never given, expired, or used already — refuse: an answer can't be replayed.

@@ 222-225
Find the passkey by its ID through the lookup function. Not found, or the device's account handle doesn't match its owner: the one refusal.

@@ 226-231
In the owner's unit of work, lock the passkey (two sign-ins at once must not both read the same counter) and load the person.

@@ 232-244
Check the signature, the site, the origin, the challenge and the counter; keep the new counter. A failure becomes a `401` naming the check.

@@ 245-250
Note when the passkey and the account were last used, record the sign-in — with how — in each organisation's audit log, and commit.

@@ 251
Open a console session, exactly as a password sign-in does.
