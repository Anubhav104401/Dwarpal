---
fingerprint: 9a334d5ee5cdf085
---
**The live accuracy table** (§5.5.9): the design's "live accuracy table (from the model card)", drawn from the figures the age model now running publishes.

@@ 1-2
The projection's wording for age bands and shares (`lib/projection.ts`, §5.5.8), and the published model's type.

@@ 4
The classes of a figure's cell: `tabular-nums` gives every digit the same width, so figures line up down a column.

@@ 6-11
What it shows, and its one input: the model's figures, or null when they couldn't be had.

@@ 12-14
Without figures, say so in a sentence, rather than draw an empty table.

@@ 15-25
A table, whose column headings say exactly what each figure is: the share of people under the age who pass, at most; of adults 3 or more years over it who are turned away, at most; and of adults just over it who are sent to a stronger check.

@@ 26-30
One row per line. `youngest` is the band of adults just over the age — the first band, the one most often sent on.

@@ 31-33
The row's heading, the age line ("18+"), marked `scope="row"` so a screen reader announces it with each figure in its row.

@@ 34-39
The two bounds (§5.2.6), or "not measured" for a model whose lines were never measured — the stand-in that the tests use.

@@ 40-44
The share of the youngest adults sent to a stronger check, with their ages ("77 % of 18–20").

@@ 45-49
The end of the row and the table.

@@ 50-55
What the figures rest on: the model's version, and how many photos from which dataset — with ages estimated rather than documented — and what "at most" means: a 95 % upper bound, for any single age in the five years under the line.

@@ 56-58
And, while the model isn't calibrated to the release standard, that it decides test checks only. The page never presents these as better than they are.

@@ 59-62
The end.
