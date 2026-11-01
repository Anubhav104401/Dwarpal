---
fingerprint: 26b4b892b51be7ab
---
Tests for **choosing the language** (§5.5.11).

@@ 1-3
Vitest's tools, and the code under test.

@@ 5-9
**Test — the person's own choice beats everything**, even a browser asking for the other language.

@@ 11-16
**Test — otherwise the browser's languages decide, most wanted first**: Hindi first; English first with Hindi lower; French (not offered) then Hindi; and qualities out of order, where the higher one wins.

@@ 18-24
**Test — English for anything else**: no header, only languages the pages aren't written in, a made-up choice, or Hindi marked unwanted (`q=0`).

@@ 26-37
**Test — only the pages' languages are languages**: `en` and `hi` — not `HI` in capitals, not French, not a number, not nothing.
