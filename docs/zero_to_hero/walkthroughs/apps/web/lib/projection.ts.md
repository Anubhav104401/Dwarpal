---
fingerprint: c0a6e5d67d2a1fcb
---
The policy editor's **projection, in words** (§5.5.8): small functions that name an age line, pick the one to offer first, and write age bands and shares the way people read them.

@@ 1
What the file is for.

@@ 3
The type of one of the model's lines (`console-api.ts`).

@@ 5-6
**`lineKey`** — a line's key in the editor's menu: its age and risk budget, as in `18@0.075`. Together they pick exactly one of the model's lines; that's also how the API looks a policy's line up (`thresholds_for`).

@@ 8-10
**`lineLabel`** — a line as a person reads it: "18+ · risk budget 7.5 %". The budget is turned into a percentage with one decimal place, and `Number(…)` drops a useless `.0` ("15 %", not "15.0 %").

@@ 12-15
**`defaultLine`** — the line chosen first: the 18+ line, which most websites need, or else the model's first line; `undefined` for a model with none.

@@ 17-18
**`agesText`** — an age band as people write it: the hyphen in "18-20" becomes an en dash ("18–20"); "30+" has none and stays.

@@ 20-24
**`percent`** — a share as a whole percentage. A share that rounds to 0 but isn't nothing says "under 1 %", so a rare outcome is never shown as if it couldn't happen.
