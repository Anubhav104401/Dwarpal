---
fingerprint: f4a646c6d4d79137
---
A **software Age Pass holder** for tests (§5.9.3), shared by the rules' tests and the API's.

@@ 1-2
The module's docstring: a software stand-in for the browser's side of the Age Pass.

@@ 4
The project-wide type-hint setting.

@@ 6-8
Hashing, JSON, and the clock.

@@ 10-13
joserfc for JWTs and P-256 keys, and the batch size and base64url helpers from the rules.

@@ 16-19
**`disclosures_of`** — a kept pass's disclosures, by the claim each reveals.

@@ 22-30
**`present`** — a presentation of a kept pass, as the verify page makes one; a test may set the time or the type, to make a bad one.

@@ 31-34
The signed pass, the chosen disclosures, and the signed part they make together.

@@ 35-41
The key-binding JWT: when, for whom, which nonce, and the hash of the signed part — signed with the pass's own key.

@@ 44-49
**`Holder`** — a browser with one P-256 key per pass.

@@ 51-52
**`public_keys`** — the public halves, in exactly the four fields the API takes.

@@ 54-55
**`keep`** — the passes the API gave, in the order of the keys.

@@ 57-58
**`present`** — pass `index`, shown with its own key.
