---
fingerprint: 7a0a4c49b78f2d84
---
Tests for **which words** the verify page shows (§5.5.11), and for the words themselves: that every tip and problem has its words in both languages, and that the Hindi file has exactly the English file's keys.

@@ 1-5
Vitest's tools; both languages' words, read straight from their JSON files; and the code under test.

@@ 7-11
**Test — the tip is the first reason that has one**: `too_dark` has its own; an unknown reason before `no_face` is skipped.

@@ 13-17
**Test — unknown or missing reasons get the general tip**: no reasons at all, or a rejection's deliberately vague `verification_failed`.

@@ 20-25
**Test — known problems keep their name, and nothing else passes a raw code on**: `session_not_open` and (since 9 Nov) `rate_limited` keep theirs; an internal error becomes the general problem.

@@ 27-40
For the next tests: the tip keys of a few reasons from each family (photos, liveness, the document check, the service), and the general one. Since Part 7 the list is written one code per line, and has the three Aadhaar ones too — so the test fails if any of them lacks its words in English or Hindi.

@@ 42-51
**Test — the words exist in every language**: each of those tips, and a problem's title, in English and in Hindi. (`as keyof typeof …` tells TypeScript the key is one the file has.)

@@ 53-60
**Test — Hindi has the same keys as English, everywhere**: every path through both files (`Verify.ending.pass.title`, …), listed by a function that walks into each object, must be the same. A word added to one language and forgotten in the other fails here.

@@ 19
The `problemFor` tests.
