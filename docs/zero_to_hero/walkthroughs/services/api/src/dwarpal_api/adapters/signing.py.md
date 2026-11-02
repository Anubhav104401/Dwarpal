---
fingerprint: 9bb0fd577b2b79fc
---
This file makes the API's answers **unforgeable**. When a check ends, the website receives an **age token**: a short text that says "session `vs_…` passed the 18+ check", followed by a **digital signature**. Anyone can check the signature with the API's *public* key; only the API, holding the *private* key, could have made it (§4.12, Choice 9 "the wax seal").

The file has two parts:

1. **`MasterKey`** — **seals** (encrypts) private keys before they go into the database, and opens them again. It uses **AES-256-GCM**.
2. **`KeyRing`** — loads (or, the first time, creates) the signing key, publishes the public keys, and **signs** tokens with **Ed25519**.

!!! kid "Explain like I'm six — the stamp and the safe"
    The API owns a special rubber stamp: anything stamped with it is known to come from the API, and anyone can recognise the stamp by comparing it with a picture the API hangs in the window (the public key). The stamp itself must never be stolen, so at night it goes into a safe (sealing). The code to the safe — the master key — isn't kept in the building at all: it is handed over each morning by whoever opens up (an environment variable).

@@ 1
The docstring states the rule: a private key exists in plain form only in memory, never in the database.

@@ 3
The project-wide type-hint setting.

@@ 5-9
`base64` (decoding the master key from text), `os` (random nonces), `secrets` (random parts of key IDs), `datetime` and `Any`.

@@ 11
`AESGCM` from the **cryptography** library — AES in **GCM** mode, an **AEAD** cipher ("Authenticated Encryption with Associated Data"). It doesn't just hide data; it also *detects any change* to the sealed data, and refuses to open it if a single bit was altered.

@@ 12
`jwt` from **joserfc** — makes and checks **JWTs**: JSON Web Tokens (§4.12).

@@ 13-14
`JoseError` — the error joserfc raises when a token fails to decode or verify. `KeySet` — a collection of keys a token may be checked against, by its `kid`. `OKPKey` — joserfc's class for **Octet Key Pair** keys: the key family that includes Ed25519.

@@ 15-16
SQLAlchemy's `select` (build a query), `text` (raw SQL, used for the lock below) and the async session type.

@@ 18
The `SigningKey` table (`tables.py`).

@@ 20
`ALG = "Ed25519"` — the signature algorithm, written with its fully-specified name from RFC 9864 (ADR-0019). The older name `EdDSA` names a whole family of curves; `Ed25519` names exactly one, so a token's header says precisely how to check it.

@@ 21
`JWT_TYPE = "dwarpal-age+jwt"` — the token's declared **type**. Verifiers check it, so a token made for some other purpose can never be mistaken for an age token, even if it was signed by the same key.

@@ 22
`KEY_CREATION_LOCK` — a number that names a database **lock**, explained at line 46. Any number works, as long as nothing else in the project uses the same one. The underscores in `7_316_001` are only there for readability; Python ignores them.

@@ 25
**`MasterKey`** — the safe for private keys.

@@ 26-27
It is given the master key as Base64 text (from `DWARPAL_MASTER_KEY`) and decodes it. `validate=True` refuses text with characters that don't belong in Base64, instead of silently skipping them.

@@ 28-29
AES-256 needs a key of exactly 32 bytes (256 bits). Anything else stops the API at start-up, with a message saying what is expected.

@@ 30
Create the cipher object once, and keep it. The leading underscore in `_aead` marks it as private to this class.

@@ 32
**`seal`** — encrypt `plaintext`, bound to a `context`.

@@ 33
A fresh 12-byte **nonce** for every seal. GCM's one absolute rule: *never* use the same nonce twice with the same key, or its protection collapses. 96 random bits make an accidental repeat practically impossible for the handful of keys this ever seals.

@@ 34
Encrypt, and store the nonce in front of the result: the nonce isn't secret, but it is needed to open the seal. The result is the nonce (12 bytes), the encrypted key, and a 16-byte **authentication tag** that the library adds at the end.

The `context` is the **associated data**: not encrypted, but part of the seal. We pass the key's ID. If someone swapped two sealed keys between rows in the database, opening one under the wrong ID would fail — a sealed key only opens under the name it was sealed with.

@@ 36-37
**`open`** — the reverse: split off the first 12 bytes as the nonce, and decrypt the rest with the same context. If the data, the tag or the context was changed in any way, the library raises an error instead of returning garbage.

@@ 40
**`KeyRing`** — the signing keys the API currently uses.

@@ 41-44
It starts with the master key, and empty slots: no signing key yet (`None`), and no public keys. `load` fills them.

@@ 46
**`load`** — run once at start-up: make sure an active signing key exists, then load it.

@@ 47
**Take a lock first.** Imagine two copies of the API starting at the same moment, on an empty database: both look, both find no active key, and both create one — now there are two "active" keys. `pg_advisory_xact_lock` is a PostgreSQL lock with a number for a name. The second copy waits at this line until the first copy's transaction ends; by then the key exists, and the second copy simply loads it. `xact` means the lock is released automatically when the transaction ends.

@@ 48-49
Read every key that is `active` or `retiring` — the ones whose public halves must stay published. `scalars(...).all()` returns the matching rows as `SigningKey` objects.

@@ 50
Find the active one, or `None` (the `next(..., None)` pattern from `decision.py`).

@@ 51-54
No active key yet — the very first start: create one, add it to the session (so the commit will save it), and add it to the list of published keys.

@@ 55
Commit: save the new key if there is one, and release the lock.

@@ 56
Open the active key's seal, using its ID as the context. The result is the private key in **PEM** form — a standard text format for keys that starts with `-----BEGIN PRIVATE KEY-----`.

@@ 57
Load it as a key object for signing, labelled with its ID.

@@ 58
Remember the public halves of all published keys.

@@ 60
**`_create`** — make a brand-new signing key. It is private to the class.

@@ 61
Its ID, such as `sig_20261016_3fa9c2e1`: the creation date (`{now:%Y%m%d}` formats the date as year, month, day) plus 4 random bytes in hexadecimal. A person reading a token's header can tell roughly how old its key is.

@@ 62
Generate a fresh Ed25519 key pair, labelled with three standard JWK fields: `kid` (its ID), `use: "sig"` (for signatures only, never encryption) and `alg` (the one algorithm it may be used with).

@@ 63
Seal the private half, in PEM form, with the key's ID as the context.

@@ 64-66
Return the database row: the ID, the public half as a JSON dict (`as_dict(private=False)` leaves the private parts out), the sealed private half, the status `active`, and the creation time.

@@ 68-69
**`jwks`** — the public keys in **JWKS** form ("JSON Web Key Set"): `{"keys": [...]}`. It is published at `/.well-known/jwks.json`, where any website can fetch it.

@@ 71-72
**`sign`** — turn a set of **claims** (the facts in the token) into a signed token. `typ` names what kind of token it is: an age token unless said otherwise; since Phase 9 also an Age Pass (`dc+sd-jwt`, §5.9.3), signed by the same keys.

@@ 73-74
Refuse to sign before `load` has run. That would be a programming mistake, so it is a `RuntimeError` rather than an `ApiError`.

@@ 75
The token's **header**: the algorithm, the type asked for, and which key signed it.

@@ 76
Sign and encode. The result is three Base64url parts joined by dots: `header.claims.signature`. `algorithms=[ALG]` is an **allow-list**: joserfc refuses to use anything but Ed25519, even if a header asked for something else.

@@ 78-81
**`verify`** — the opposite of `sign` (Phase 4, for token introspection; Phase 9, for Age Passes): the claims of a token of the expected type, signed by one of the key ring's current keys, or `None` for anything else. Checking the times is left to the caller, which knows what "now" is.

@@ 82-84
Build a key set from the public keys the ring publishes, and decode the token with it, accepting only Ed25519. The token's `kid` picks the key; a token signed by any other key, or with any other algorithm, fails.

@@ 85-86
Any failure — a bad signature, an unknown key, a token that isn't a JWT at all — becomes `None`: the caller only needs to know "not genuine".

@@ 87-88
A genuine signature on the wrong *type* of token is still refused: an age token is no Age Pass, and an Age Pass no age token.

@@ 89
Return the claims as an ordinary dict.
