---
fingerprint: 6cac80b800cafd7a
---
**Idempotency** (Phase 4, §5.4.2). Networks fail in an awkward way: a website's server sends "create a session", Dwarpal creates it, and the *answer* is lost on the way back. The website can't tell whether its request arrived, so it sends it again — and without help, the person now has two sessions, the first one forgotten.

The standard cure, used by payment APIs everywhere, is the **`Idempotency-Key`** header. The website makes up a unique key for each thing it means to do (for example `order-1234-age-check`) and sends it with the request. If the same key arrives again, Dwarpal doesn't do the work a second time: it answers with the **first** answer. An operation that gives the same result however often it is repeated is called **idempotent**.

!!! kid "Explain like I'm six — the cloakroom ticket"
    You hand in your coat and get ticket 42. If you come back and show ticket 42 again, you get the same coat back — not a second coat. The key is the ticket; the stored answer is the coat.

Two dangers shape this file:

- **A key reused for something else.** If the same key comes with a *different* request, that's a bug in the website, and quietly returning the old answer would hide it. So the request's **fingerprint** is stored with it, and a mismatch is refused;
- **A secret kept in a cache.** The first answer contains the session's one-time client secret. Kept in Valkey as plain text, anyone with a copy of Valkey's memory could use it. So the answer is **sealed** (encrypted) with a key derived from the website's idempotency key *and* Dwarpal's master key. Valkey alone holds only an unreadable blob, and only a request carrying the same idempotency key can open it.

@@ 1-2
The docstring: what idempotency is for.

@@ 4
The project-wide type-hint setting.

@@ 6-11
Standard-library tools: `base64` (bytes as text), `hashlib` (SHA-256), `hmac` (keyed digests, explained at line 30), `json`, `re` (to check the key's shape) and `secrets` (unpredictable random bytes).

@@ 12-13
Types: `Awaitable` and `Callable` describe the work function `make`; `Any`.

@@ 15
`AESGCM` — the AES-GCM cipher from the `cryptography` library, the same one that seals the signing keys (`adapters/signing.py`). It encrypts *and* detects tampering: a sealed reply that has been altered by even one bit fails to open.

@@ 17-18
The Valkey store and our error class.

@@ 20
`KEY_SHAPE` — an acceptable idempotency key: 8 to 255 **printable** characters (codes 0x21 to 0x7E: letters, digits and punctuation, but no spaces or control characters). Short keys are refused because a short key is easy to repeat by accident.

@@ 21
`NONCE_BYTES` — AES-GCM needs a fresh 12-byte **nonce** (a "number used once") every time it encrypts.

@@ 24-25
**`fingerprint`** — a digest of *what* the request asks for: the operation and its body.

@@ 26
Write them as JSON in a **canonical** form: keys sorted, no spaces. The same request always gives exactly the same text, so the same digest, whatever order its fields arrived in.

@@ 27
The SHA-256 digest of that text, written as hexadecimal.

@@ 30-31
**`server_secret`** — Dwarpal's own secret for idempotency, made from the master key. An **HMAC** is a digest computed *with a key*: without the key, nobody can compute it or work backwards from it. Using the master key with a fixed label (`"dwarpal idempotency"`) gives a new secret for this one purpose, so the master key itself is never used directly here.

@@ 34-35
**`_derive`** — make a key for one purpose from the server secret and the website's idempotency key. Two purposes are used below: `slot` (where the reply is stored) and `seal` (the encryption key). The `\x00` between them is a separator that can't appear in either part, so different pairs can never produce the same text.

@@ 38-46
**`once`** — the heart of the file. It takes the store, the server secret, the **scope** (whose keys these are), the website's key, the request's fingerprint, how long to remember, and `make`, the function that does the actual work. It returns the reply and whether it was a replay.

@@ 47
Its docstring.

@@ 48-49
Refuse a badly shaped key with `422 invalid_idempotency_key`.

@@ 50
The **slot** — the Valkey key where this reply lives: the scope plus a derived digest. The website's idempotency key itself never appears in Valkey, so a copy of Valkey's memory doesn't reveal which keys were used.

@@ 51-52
**Claim** the slot with a "pending" record holding the fingerprint (`store.claim`: write only if empty, in one step). If two copies of a request arrive at the same moment, exactly one of them wins.

@@ 53-54
If something was already there, this is a repeat: answer from the stored record (`_replay`, below) and report it as replayed.

@@ 55-59
We claimed the slot, so do the work. If it fails in any way, delete the claim before letting the error continue (`raise` with nothing after it passes the same error on). Nothing was made, so the website may safely try again with the same key.

@@ 60-61
**Seal** the reply: a fresh nonce, then AES-GCM with the `seal` key. The slot's name goes in as **associated data**: it isn't secret, but it is checked when opening, so a sealed reply moved to another slot won't open.

@@ 62-63
Replace the pending record with the finished one — the fingerprint and the sealed reply, nonce first, as Base64 text — for the same lifetime.

@@ 64
Return the fresh reply: not a replay.

@@ 67
**`_replay`** — answer a repeat from the stored record.

@@ 68-69
A different request under the same key: refuse with `422 idempotency_key_reused`.

@@ 70-71
The first request is still running (the record is only "pending"): refuse with `409 idempotency_in_progress`, and the website retries a moment later.

@@ 72-73
Unpack the nonce and the sealed reply, and open it with the `seal` key derived from the same idempotency key. A wrong key, a moved record or a tampered one all fail here.

@@ 74-75
Turn the JSON back into a dict and return it — exactly the first answer.
