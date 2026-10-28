---
fingerprint: 424a7bc7d6727222
---
**The age model's page** (§5.5.2): which model is deciding, whether it may decide live checks, what it learnt from, and its lines for each age with what was measured about them. A website's team can see what stands behind each decision without asking.

@@ 1
It loads its data in the browser, after the page arrives (§5.5.1).

@@ 3-4
Links between pages, and React's state and effect hooks.

@@ 6-7
The console's frame, alert, panel and quiet button; and the design system's badge.

@@ 8
The console client, and the shapes of the model's details and of a source of faces.

@@ 10
One client for the page.

@@ 12-13
**`percent`** — a share as a percentage with one decimal: 0.0705 becomes "7.1 %". A share that was never measured (`null`) says so in words, rather than showing a misleading 0.

@@ 15-16
**`Source`** — one sentence about a set of faces.

@@ 17-24
Its name in medium weight; then, when known, how many faces (`toLocaleString("en-GB")` writes 11301 as "11,301"); its licence; and how the ages were known — read from photos, or checked by a person. `<>…</>` is a **fragment**: a group of pieces with no element around them.

@@ 26-28
**`ModelView`** — the model's details once loaded (`null` while loading, `"signed-out"` when the API says so), and an error message, if any.

@@ 30-35
When the page first appears, ask for the model; no answer means signed out. A failed request becomes a polite message.

@@ 37-54
Not loaded yet, failed, or signed out: the frame alone, with the error, *Loading…*, or a link to sign in — as on the *Security* page.

@@ 56-64
Loaded: the frame, with its sidebar (`signedIn`) and a way back to all organisations.

@@ 65
The heading.

@@ 66-73
Under it, the model's version in code font and a badge: green *Decides live checks* for a calibrated model, amber *Test checks only* otherwise — the same rule the API applies to every session.

@@ 74
The manifest's own note, when it has one: why the model is or isn't allowed to decide live checks, in its makers' words.

@@ 76-79
**What it learnt from** — a panel.

@@ 80
A list of terms and their descriptions (`dl`), as two columns on wider screens and one on phones.

@@ 81-82
The use its licences permit, such as "non-commercial research only".

@@ 83-90
The network it started from (its *backbone*), in code font — or, for the stub, plain words saying there is none.

@@ 91-94
The faces it was trained on, or none for the stub.

@@ 95-96
The faces its lines were set on, or "not measured".

@@ 97-98
The end of the list and the panel.

@@ 100-103
**Its lines for each age** — a panel.

@@ 104-107
How to read the lines, in plain words: the model gives a chance; above the pass line, pass; below the fail line, fail; between them, another way to prove one's age.

@@ 108-111
And where they came from: for a calibrated model, set on faces of known age within the risk budget; for the stub, chosen by hand, with nothing measured — so the page never claims a guarantee the model doesn't have.

@@ 112
The table may be wider than a phone, so it scrolls sideways inside its own box rather than making the whole page scroll.

@@ 113-123
The table and its header row: the age, the risk budget, the two lines, and the two measured worst cases.

@@ 124-126
One row per age.

@@ 127-128
The age, such as "18+", and its risk budget as a percentage.

@@ 129-130
The two lines, to three decimals, with ≥ and ≤ to say which side of each line counts. `whitespace-nowrap` keeps each sign beside its number.

@@ 131-132
The measured worst cases: the share of younger people who could pass, and of older people who could fail — or "not measured".

@@ 133-141
The end of the row, the table, its box, the panel, the frame and the function.
