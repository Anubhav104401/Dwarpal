---
fingerprint: 5cd5ebdc3b5db0b2
---
Tests of `adult_outcomes`, the part of the export that copies how adults fared at each line into the manifest (§5.5.8). The export itself needs a trained model and a GPU's worth of time; this part needs only a file.

@@ 1-6
The type-hint setting; JSON and `Path`; and the function under test.

@@ 9-10
**`measured`** — one measured share, shaped as the evaluation writes it: the rate, the count, out of how many, and its confidence interval.

@@ 13-16
**Test — one line's adults, rounded.** A made-up evaluation: at 18, one band of 330 adults with three shares; at 21, a limit with no adult bands at all. Written where the export looks for it.

@@ 17-20
Each share is rounded to four places, the band keeps its name and its number of faces, and a limit without bands gets an empty list.

@@ 23-24
**Test — nothing measured.** With no evaluation file, there is nothing to show — an empty answer, not an error.
