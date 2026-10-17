---
fingerprint: 63383dc3418828f1
---
The **release gates**: the minimum a model must achieve before it may serve real people. They turn "is this model good enough?" from a judgement made while looking at the results — when it's tempting to be generous — into rules written down *beforehand* (§2.16).

The design calls this file `gates.yaml`; it is TOML for the same reasons as the licence register (`ml/datasets.toml`).

@@ 1-3
What the file is, and how a gate works: `metric` is a path into a model's evaluation results (`dwarpal_ml/evaluate.py`), checked against a `max` or a `min`.

@@ 4-7
**Provisional**, and why. The design's real gates (NFR-01 and NFR-04 in the problem analysis) are about children of each exact age from 13 to 17, under the final risk-controlled thresholds. FairFace's age bands can't measure that, so these gates measure what it *can*. Every value is the project owner's decision; these are proposals.

@@ 9-13
**Accuracy**: overall band-MAE at most 2.0 years. Each gate has a `name`, a `metric`, its limit, and a `why` in plain words.

@@ 15-19
**Children rated adult**: of the children under 10, the share rated more likely than not 18 or over, with 95 % confidence, at most 5 % — the release-gate level of NFR-01. It uses the *upper* end of the interval, so the gate holds even with bad luck in the sample.

@@ 21-25
**The same in every group**, at most 10 %. It is looser only because each group has a few hundred children, and a small sample's upper bound is wide: with zero mistakes in 160 children, the upper end is still 2.3 %.

@@ 27-31
**Accuracy gap**: the worst group's band-MAE at most 25 % above the best group's.

@@ 33-37
**Calibration**: the probabilities of being over an age match reality to within 5 percentage points, on average (§2.13).
