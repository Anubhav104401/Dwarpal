---
fingerprint: 2b2a0e121181b538
---
Tests for exact-age calibration, on made-up populations whose answers are known: when the data is plentiful, thin, or far too thin; how decisions are counted; and the two refusals that keep it honest.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-8
`Path`, NumPy and pytest.

@@ 10-12
The code under test, the row type, and the scored-person type.

@@ 15-16
**`row`** — a helper: a face with an exact age and a group.

@@ 19-28
**`people`** — a made-up population like the one in `test_risk.py`: `per_cell` people of every age from 8 to 39 in each group, with a probability of being 18 or over that rises with age, plus noise.

@@ 31-35
**Plenty of data**: 400 people per cell. The strictest budget, 2 %, is certified per age *and* group, with nothing refused.

@@ 38-45
**Thin data**: 100 people per cell. Per age and group, 2 % needs 149 per cell, so it is refused — and the refusal is recorded with its budget, its kind of cell and its reason. Per age, the two groups together make 200, so the lines are certified that way, and the result says `age`.

@@ 48-51
**Far too little**: 3 people per cell. Nothing can be certified, and every one of the 14 attempts (7 budgets, 2 kinds of cell) is recorded as refused.

@@ 54-56
**Decisions**: with a pass line of 0.9 and a fail line of 0.1, scores of 0.95 and 0.9 pass (the line itself passes), 0.05 fails, and 0.5 goes to step-up.

@@ 59-64
**Counting decisions.** Six faces at the limit 18 — two 16-year-olds in different groups, a 17-year-old, a 5-year-old, a 19-year-old and a 30-year-old — each given a chosen probability of being 18 or over.

@@ 65-71
At age 16, one passed; three minors in all; none of group `b`; one younger child; the 19-year-old went to step-up; the 30-year-old passed.

@@ 74-80
**Exact accuracy**: guessing 20 for a 22-year-old and 50 for a 50-year-old is an error of 1 year on average, 2 in the 18–24 range, and *not measured* (`None`) for children, of whom there are none.

@@ 83-91
**The refusals**: FairFace, which has no exact ages, is refused; and a run that has already been checked on UTKFace's test half is refused a second time.
