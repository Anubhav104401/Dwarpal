---
fingerprint: 0782ca76da876dd0
---
Tests for **which words** the verify page shows (§5.5.11), and for the words themselves: that every tip and problem has its words in both languages, and that the Hindi file has exactly the English file's keys.

@@ 1-5
Vitest's tools; both languages' words, read straight from their JSON files; and the code under test.

@@ 7-11
**Test — the tip is the first reason that has one**: `too_dark` has its own; an unknown reason before `no_face` is skipped.

@@ 13-17
**Test — unknown or missing reasons get the general tip**: no reasons at all, or a rejection's deliberately vague `verification_failed`.

@@ 20-24
**Test — known problems keep their name, and nothing else passes a raw code on**: an internal error becomes the general problem.

@@ 26-32
For the next tests: the tip keys of a few reasons from each family (photos, liveness, the document check, the service), and the general one.

@@ 34-43
**Test — the words exist in every language**: each of those tips, and a problem's title, in English and in Hindi. (`as keyof typeof …` tells TypeScript the key is one the file has.)

@@ 45-52
**Test — Hindi has the same keys as English, everywhere**: every path through both files (`Verify.ending.pass.title`, …), listed by a function that walks into each object, must be the same. A word added to one language and forgotten in the other fails here.

@@ 19
The `problemFor` tests.
