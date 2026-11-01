---
fingerprint: 7720b2a1e793c8bc
---
**The live accuracy table** (§5.5.9): the design's "live accuracy table (from the model card)", drawn from the figures the age model now running publishes.

@@ 3-4
The projection's wording for age bands and shares (`lib/projection.ts`, §5.5.8), and the published model's type.

@@ 6
The classes of a figure's cell: `tabular-nums` gives every digit the same width, so figures line up down a column.

@@ 8-15
What it shows, and its one input: the model's figures, or null when they couldn't be had. It is now an `async` server component — it waits for its words and the page's language before drawing.

@@ 16-18
Without figures, say so in a sentence, rather than draw an empty table.

@@ 20-30
A table, whose column headings say exactly what each figure is: the share of people under the age who pass, at most; of adults 3 or more years over it who are turned away, at most; and of adults just over it who are sent to a stronger check.

@@ 31-35
One row per line. `youngest` is the band of adults just over the age — the first band, the one most often sent on.

@@ 36-38
The row's heading, the age line ("18+"), marked `scope="row"` so a screen reader announces it with each figure in its row.

@@ 39-40
The two bounds (§5.2.6), or "not measured" for a model whose lines were never measured — the stand-in that the tests use.

@@ 41-45
The share of the youngest adults sent to a stronger check, with their ages ("77 % of 18–20", or in Hindi "18–20 में से 77 %": each language puts the parts in its own order).

@@ 46-50
The end of the row and the table.

@@ 60-63
The end.

@@ 1
From next-intl, on the server: the request's language, and a translator for this table's words (`Accuracy` in `messages/`, §5.5.11).

@@ 19
"not measured", in the page's language, used in three columns.

@@ 51-59
What the figures rest on: the model's version, and how many photos from which dataset — with ages estimated rather than documented — the number written as the page's language writes numbers; what "at most" means: a 95 % upper bound for any one age; and, while the model isn't calibrated to the release standard, that it decides test checks only. The page never presents these as better than they are.
