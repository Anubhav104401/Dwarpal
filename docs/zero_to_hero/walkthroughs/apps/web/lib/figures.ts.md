---
fingerprint: 97838400c6723316
---
**The dashboard's face-check figures, in words** (§5.5.2): the median time as a band people can read, whether it meets the target, and an outcome's share as a percentage. Plain functions, tested without a browser.

@@ 1-2
What the module is for: the dashboard's headline figures, as words — the face checks', and since 9 Nov the ID-document checks'.

@@ 4
The shapes of the counts the console client reads (`console-api.ts`): the face checks', and the ID-document checks'. `import type` brings only the types, not any code.

@@ 6-7
**`MEDIAN_TARGET_S`** — the design's target: half of all checks decided within 15 seconds (NFR-02).

@@ 9-10
**`bandText`** — a band of seconds as people say it.

@@ 11
A helper: seconds as minutes, to at most one decimal place; `Number(...)` drops a trailing ".0", so 60 seconds reads "1", not "1.0".

@@ 12-13
The last band has no end: "5 min or more" (or, for a band under a minute, "… s or more").

@@ 14
Bands that end within a minute, in seconds: "10–15 s".

@@ 15-16
Longer ones in minutes: "1–1.5 min". End of the function.

@@ 18-20
**`withinTarget`** — the median meets the target only if the *whole* band does: "10–15 s" does; "15–20 s" might not, so it doesn't count. The open-ended last band never does.

@@ 22-25
**`percent`** (9 Nov, taken out of `share` so both kinds of figure use it) — a count as a whole percentage of a whole.

@@ 26
Nothing to divide by: a dash, rather than a misleading "0 %".

@@ 27
The share, rounded to a whole number — and never over 100: a check reached just before the 30 days shown can end within them, so the endings can outnumber the checks reached.

@@ 28-29
A rare outcome that rounds to 0 % — one rejection in 400 checks — reads "under 1 %", so it isn't hidden. End of the function.

@@ 31-33
**`share`** — one outcome's share of the decided face checks (none if it isn't listed — `?? 0`).

@@ 35-37
**`documentFigures`** (9 Nov) — the ID-document checks' three figures, from the counts: the share of the checks reached that ended (the design's **step-up conversion**), the share that passed, and the share that left — or are still on it.

@@ 38-39
How many ended, any way at all (`reduce` adds up every ending's count); and how many passed — by the document, or by an Age Pass in a live check that starts at the document.

@@ 40-45
The three, each a share of the checks reached. Those that left are the ones reached with no ending, never fewer than none (`Math.max`).
