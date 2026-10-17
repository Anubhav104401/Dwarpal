---
fingerprint: d1d256b17512beec
---
Tests for the evaluation protocol. They use made-up model outputs whose right answers are known, so every measure can be checked exactly — including the one that matters most for honesty: that the test split can't be evaluated twice.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-10
`Path`, NumPy, pytest and Hypothesis.

@@ 12-14
The code under test, the row type, and the number of ages.

@@ 17-18
**`row`** — a helper: a row with a band, a group and a sex.

@@ 21-25
**`peaked`** — made-up logits that peak at chosen ages: each age's score falls in a straight line with its distance from the peak, so after softmax most of the probability sits near it. `sharpness` sets how confident the "model" is.

@@ 28-31
**Probabilities add up to 1** at every temperature.

@@ 32-36
**Temperature sharpens or softens**: the probability at the peak is highest at temperature 0.5, lower at 1, lower still at 2.

@@ 39-43
**The fitted temperature undoes overconfidence.** Make an honest "model" for 3,000 faces, and draw each face's true age *from that model's own probabilities* — so the model is, by construction, perfectly calibrated.

@@ 44-46
Then make it overconfident by multiplying its logits by 3 (the same as a temperature of ⅓). Fitting should find a temperature close to 3, which exactly cancels it — and it does, within 15 %.

@@ 49-53
**The interval always contains what was observed**, for any count out of up to 400 that Hypothesis invents, and stays between 0 and 1.

@@ 56-59
**A perfectly calibrated forecast scores 0**: forecasts of 5 %, 35 % and 75 %, each for 100 faces, of which exactly 5, 35 and 75 come true.

@@ 60
**A badly calibrated one scores its gap**: saying 90 % about 100 faces, none of which come true, scores 0.9.

@@ 63-69
**Clear minors and adults are chosen by their whole band.** Four faces: 3–9, 10–19, 20–29 and 30–39. At the limit 18, only the 3–9 face is a clear minor (and, predicted as 25, it is rated over 18), and only the 30–39 face is a clear adult (and, predicted as 35, it is not doubted). The 10–19 and 20–29 faces are neither.

@@ 72-77
**Every view is reported**: bands in age order (`70-100` for the open band), both groups, both sexes.

@@ 78-79
And the fairness ratio is the worst group's band-MAE over the best's.

@@ 82-85
**The gap is defined even when a group is perfect**: 2.0 against 1.6 is 1.25; two perfect groups are equal (1.0); one perfect group against an imperfect one has no meaningful ratio (`None`). This test was added after the first version divided by zero.

@@ 88-97
**Gates pass and fail by their limits**: a value under its maximum passes, a value under its minimum fails, and a value that couldn't be measured (`None`) fails — never passes by default.

@@ 100-103
**The project's real gates all name real results**: every metric path in `ml/gates.toml` leads to a value. A typo in the gates file would be caught here, not on release day.

@@ 106-109
**The test split is evaluated only once.** A run folder that already has `evaluation-test.json` is refused, before any data is even read.
