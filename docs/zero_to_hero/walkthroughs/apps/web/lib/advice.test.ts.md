---
fingerprint: de11d04c2285211e
---
Tests for the friendly messages in `advice.ts`: the right tip for a reason, safe fallbacks for codes the page doesn't know, and no raw codes ever reaching the screen.

@@ 1
Vitest's building blocks.

@@ 3
The code under test. A test file sits right next to the file it tests, and imports it with `./`.

@@ 5
The tests of `tipFor`.

@@ 6-9
**The first known reason wins.** One reason gives its tip. When the list starts with a code the page doesn't know (`something_new`), it is skipped, and the next one's tip is used. `toMatch(/…/)` checks that the text *contains* the pattern, so a later rewording of the rest of the sentence won't break the test.

@@ 11-14
**Unknown or missing reasons get the general tip** — including `verification_failed`, the deliberately vague reason given for a rejection (§5.1.3, `flow.py`).

@@ 15
The end of the group.

@@ 17-22
**Problems**: a known code gets its own title or explanation, and an unknown one — here `internal_error` — the default message.

@@ 23
The end of the group.
