---
fingerprint: bd2969b45a2d197a
---
**The dashboard's face-check figures, in words** (§5.5.2): the median time as a band people can read, whether it meets the target, and an outcome's share as a percentage. Plain functions, tested without a browser.

@@ 1
What the module is for.

@@ 3
The shape of the face-check counts the console client reads (`console-api.ts`). `import type` brings only the type, not any code.

@@ 5-6
**`MEDIAN_TARGET_S`** — the design's target: half of all checks decided within 15 seconds (NFR-02).

@@ 8-9
**`bandText`** — a band of seconds as people say it.

@@ 10
A helper: seconds as minutes, to at most one decimal place; `Number(...)` drops a trailing ".0", so 60 seconds reads "1", not "1.0".

@@ 11-12
The last band has no end: "5 min or more" (or, for a band under a minute, "… s or more").

@@ 13
Bands that end within a minute, in seconds: "10–15 s".

@@ 14-15
Longer ones in minutes: "1–1.5 min". End of the function.

@@ 17-19
**`withinTarget`** — the median meets the target only if the *whole* band does: "10–15 s" does; "15–20 s" might not, so it doesn't count. The open-ended last band never does.

@@ 21-23
**`share`** — one outcome's share of the decided checks, as a whole percentage.

@@ 24
Nothing decided yet: a dash, rather than a misleading "0 %".

@@ 25-26
How many had that outcome (none if it isn't listed — `?? 0`), as a percentage rounded to a whole number.

@@ 27-28
A rare outcome that rounds to 0 % — one rejection in 400 checks — reads "under 1 %", so it isn't hidden. End of the function.
