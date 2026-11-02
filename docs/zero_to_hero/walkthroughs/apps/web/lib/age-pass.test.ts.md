---
fingerprint: a7766422042dc75f
---
Tests for **the Age Pass in the browser** (§5.9.3), with real WebCrypto keys (Node has the same WebCrypto as browsers). Keeping passes in IndexedDB is tested end to end (§5.9.3's browser test).

@@ 1-4
Vitest's functions, the functions under test, and base64url.

@@ 6-8
Helpers: JSON into base64url, and back.

@@ 10-14
**`pass`** — a kept pass as the API would send it: a JWT (its signature is never checked in the browser — the server checks it) and one disclosure per line.

@@ 16-30
**A kept pass** lists its disclosures by name, and shows the lowest line that is enough — or none.

@@ 32-42
**Keys**: the private half can't be exported (the attempt is refused), and the public key goes out as exactly four fields, with 43-character coordinates.

@@ 44-50
**A presentation**: a real key pair, a pass stating 13, 16 and 18, a fixed time, and a presentation for the 18 line.

@@ 52-54
Three parts — the pass, one disclosure, the proof — and the disclosure is the 18 line's.

@@ 56-65
The proof's header and claims: ES256 and `kb+jwt`; the time in seconds, the audience, the nonce, and the hash of exactly the signed part.

@@ 66-73
And its signature checks out with the public key — as the server will check it.

@@ 75-80
A pass that doesn't state the line asked for can't be presented.
