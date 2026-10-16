---
fingerprint: 4414bc222a118730
---
Tests for the shop's signed pass: valid until it expires, and impossible to forge, extend, or move to another session.

@@ 1
Vitest's building blocks.

@@ 3
The code under test.

@@ 5-6
A test secret (long enough to be accepted) and a session ID.

@@ 7
A fixed "now": noon UTC on 16 October 2026. `Date.UTC(2026, 9, 16, …)` uses month **9** for October, because JavaScript counts months from 0 — a classic trap. A fixed time makes the test give the same result whenever it runs.

@@ 9
All the tests below are about the pass.

@@ 10-11
**Valid until it expires.** Issue a pass at "now".

@@ 12-15
Read at "now", it gives back the session, with an expiry exactly 30 minutes later.

@@ 16
Read at the expiry moment itself, it is no longer valid: `null`.

@@ 17
The end of the test.

@@ 19-21
**Can't be forged, extended or moved.** Issue a pass, and split it into its three parts.

@@ 22
Signed with a different secret — as a forger would have to — it is refused.

@@ 23
With the expiry pushed an hour later but the old signature kept, it is refused: changing the time breaks the signature.

@@ 24
With another session's ID but the old signature, it is refused.

@@ 25
The end of the test.

@@ 27-31
**Missing and malformed cookies are simply not passes**: no cookie at all, an empty one, and one with four parts.

@@ 32
The end of the group.
