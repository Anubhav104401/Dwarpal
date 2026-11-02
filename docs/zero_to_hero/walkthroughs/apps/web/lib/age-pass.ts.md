---
fingerprint: ff69d8a7297a19da
---
**The Age Pass in the browser** (Phase 9, §5.9.3): making keys, keeping passes, and making a presentation.

@@ 1-7
The module's comment: what the browser does for the Age Pass — makes one key pair per pass, whose private half can't be read out even by this page; keeps the passes in IndexedDB; and later shows one pass, with only the line needed, signed over the server's nonce.

@@ 9
Base64url, shared with the passkey code (§5.9.2).

@@ 11-17
**`HolderKey`** — a public key exactly as the API takes it: four fields, no more.

@@ 19-26
**`KeptPass`** — a pass as this browser keeps it: the pass's text, its private key (a `CryptoKey` that can sign but never be exported), the lines it states, when it expires, and test or live.

@@ 28-33
**`Usable`** — a kept pass that can answer the check at hand: where it is stored, the pass, and the line it will show.

@@ 35
One text encoder, reused: text to UTF-8 bytes.

@@ 37-48
**`disclosuresOf`** — a pass's disclosures by the claim each reveals: everything after the signed JWT, decoded from base64url JSON (`[salt, name, value]`), keyed by the name.

@@ 50-54
**`lineFor`** — the lowest line the pass states that is still enough: an 18+ pass shown to a 16+ website shows `age_over_16`, the least it needs to reveal.

@@ 56-62
**`newKeys`** — new ECDSA key pairs on P-256, one per pass. `false` makes the private halves *non-extractable*: the browser will sign with them, and never hand them over — not to this page, not to anything injected into it.

@@ 64-68
**`holderKey`** — export a public key as a JWK and keep only its four fields: the browser's export adds `ext` and `key_ops`, which the API's schema refuses.

@@ 70-82
**`presentation`** — a presentation of one pass, for one line, this session's nonce and audience, at a time (now unless a test says otherwise).

@@ 83-87
The signed JWT, and the disclosure for the line asked for — which the pass must have.

@@ 88-89
The signed part, and its SHA-256 in base64url: the `sd_hash` that ties the proof to exactly what is shown.

@@ 90-92
The key-binding JWT's two halves, each JSON in base64url: the header (ES256, `kb+jwt`), and the claims — when (in seconds), for whom, which nonce, and the hash.

@@ 102
The second part: keeping passes. **IndexedDB** is the browser's database for a website: it can hold a `CryptoKey` as an object, still non-extractable — `localStorage` could only hold text, which would mean exporting the key.

@@ 104-107
The database's and the store's names; and a minute's margin, so a pass that would expire during the check isn't offered.

@@ 109-116
**`open`** — open the database, creating its store the first time (each pass gets an automatic number as its key). IndexedDB answers through events, so the promise is settled from them.

@@ 118-132
**`withStore`** — run some work in one transaction on the store, and wait for the transaction to finish — not just for the requests to be sent — so a promise that resolves means the change is saved. The database is closed afterwards in every case.

@@ 134-141
**`keep`** — add a batch of passes in one transaction.

@@ 143-157
**`everything`** — every kept pass with its key, read with a cursor: one result at a time, each pushed to the list, until there are no more.

@@ 159-164
**`usable`** — a pass for this check, or `null`.

@@ 165-173
Read everything; delete the passes that have expired (or will within the minute).

@@ 174-181
The first — oldest — pass that is still good, of the session's mode, and states a line high enough.

@@ 183-188
**`forget`** — remove one pass: used, or refused for good.

@@ 93-100
Sign them with the pass's private key. WebCrypto's ECDSA gives the 64-byte r||s form that JWTs' ES256 uses, so the signature goes on as it is. The presentation: the signed part, then the JWT. The end of `presentation`.
