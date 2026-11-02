---
fingerprint: a4ddd31914a72467
---
Tests for the **Age Pass's rules** (§5.9.3), with real signatures from a software holder.

@@ 1
The module's docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-18
Helpers, pytest, the software holder, Hypothesis, joserfc, and the rules under test.

@@ 20-24
A test issuer with its own Ed25519 key, a fixed "now", a session ID as the audience, and today's date.

@@ 27-37
**`issue`** — passes as the API issues them: one per holder key, each signed with the test key as a `dc+sd-jwt` and joined to its disclosures; the holder keeps them.

@@ 40-54
**`verify`** — what the API does with a presentation, every check in order, returning the line it proves.

@@ 57-62
Two helpers: a kept pass's signed claims, and "now" in seconds.

@@ 65-70
**Test — a pass states its own line and every standard line below**, and only those.

@@ 73-80
**Test — a pass shown with one disclosure proves that line**: 18 for an 18+ check, 16 for a 16+ one — and the website learns that one fact, not the pass's other lines.

@@ 83-87
**Test — a pass proves no more than it states**: a 16+ pass has no 18 line to show.

@@ 90-101
**Test — passes from one check share nothing that could link them**: the only claims all five share are those everyone issued that day shares; every digest and every salt is different; and the issue time is the day, not the second.

@@ 104-107
**Test — every pass lists six digests**, whatever lines it states.

@@ 110-134
**Test — tampered presentations are refused**: another pass's disclosure, a disclosure dropped after signing; and proofs signed with another key, for another nonce, for another session, an hour old, or of the wrong type.

@@ 137-154
**Test — a pass must be ours, of the session's mode, and unexpired**: another issuer or type, a live pass in a test session, the moment it expires, and malformed times — while a second before expiry it still counts.

@@ 157-173
**Test — only a public P-256 key on the curve can hold a pass**: extra fields are dropped; a private part, another curve or key type, a point off the curve, a short coordinate, missing coordinates or a non-key are refused.

@@ 176-179
**Test — malformed presentations are refused**: empty, one part, an empty part, a trailing `~`, too long, and non-ASCII text.

@@ 180-192
And malformed disclosures, each listed by digest so only its shape is wrong: an object, one overwriting `iss`, two items, a number for a salt — and the same disclosure twice.

@@ 195-200
**Test — the lowest true line at or above the policy's age is the one proved**; names that aren't lines and values that aren't `true` count for nothing.

@@ 203-207
**Test — any text at all either splits into a presentation that puts it back together exactly, or is refused with our error** — never another exception.

@@ 210-213
**Test — base64url is read strictly**: anything decoded encodes back to itself.
