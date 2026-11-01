---
fingerprint: ac0e509fed0e8c05
---
**Checking a webhook** (§5.9.1): proof that Dwarpal sent this very body, recently, before the website acts on it.

@@ 1
The module's docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-12
Hashing, HMAC, JSON, regular expressions, the clock, a type helper, and the SDK's webhook error.

@@ 14-16
How old a signature may be (five minutes), and the shape of its digest: 64 hexadecimal characters.

@@ 19-30
**`verify_webhook`** — the body exactly as it arrived (parsing and re-serialising JSON would change the bytes), the `Dwarpal-Signature` header, the endpoint's secret, and two options for tests.

@@ 31-34
Read the header's `t=` (when it was signed) and `v1=` (the signature). Missing or malformed: refused.

@@ 35-36
Too old, or from the future: refused — it may be a recorded webhook played again.

@@ 37-38
The signature it should have: an HMAC-SHA256, with the secret, of the time, a dot, and the body.

@@ 39-41
Compared in **constant time** (`compare_digest`), so the time taken reveals nothing about how much of a forgery was right.

@@ 42-43
Genuine: return the event.
