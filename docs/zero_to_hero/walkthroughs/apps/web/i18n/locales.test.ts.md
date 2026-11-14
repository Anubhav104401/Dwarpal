---
fingerprint: 64be208dd2da4d98
---
Tests for **choosing the language** (§5.5.11).

@@ 1-3
Vitest's tools, and the code under test.

@@ 5-9
**Test — the person's own choice beats everything**, even a browser asking for the other language.

@@ 11-16
**Test — otherwise the browser's languages decide, most wanted first**: Hindi first; English first with Hindi lower; French (not offered) then Hindi; and qualities out of order, where the higher one wins.

@@ 25-31
**Test — English for anything else**: no header, only languages the pages aren't written in, a made-up choice, or Hindi marked unwanted (`q=0`).

@@ 33-38
**Test — only the pages' languages are languages**: seven of the ten are (`every`), and none of these is (`some` is false) — `HI` in capitals, French, Urdu, Odia (two of India's languages not yet translated), a number, nothing.

@@ 18-23
**Test — the eight new languages are found by the codes browsers send** (14 Nov): a Tamil browser gets Tamil, a Bengali one Bengali; a browser that prefers French, then Punjabi, gets Punjabi; and a person's own choice (Malayalam) still beats the browser (Kannada).
