---
fingerprint: c8f2707afda9c597
---
Tests for the safety lines. The calculation in `risk.py` is the promise the whole system makes to parents and regulators, so it is tested three ways:

- **known values** worked out independently — the 149-person minimum;
- **properties** that must hold for *every* input, checked by Hypothesis on hundreds of invented ones — including the central claim, "the pass line is safe, and is the lowest safe line";
- **refusals** — every way the data can be too thin, each one checked to be refused with a clear reason.

The tests use made-up populations: people with ages, groups and scores, but no faces.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5
`random` — to make up test populations.

@@ 7-9
`pytest`, and Hypothesis's `given` and strategies.

@@ 11-21
The parts of `risk.py` under test.

@@ 24
**The known values.**

@@ 25
149 people are needed to prove 2 % (§2.14).

@@ 26
Checked directly: with 149 people and nobody passing, the bound is within 2 % (1.990 %); with 148 it is just over (2.004 %).

@@ 27
When everyone passes, the bound is 100 %.

@@ 30
**A property.** The strategy first picks a number of trials from 1 to 2,000, then (`flatmap`) a number of successes from 0 up to that number — so the pair always makes sense.

@@ 31-33
The worst plausible rate is never lower than the rate actually seen. A bound below the evidence would be absurd.

@@ 36-37
**Two more properties**, from two invented numbers.

@@ 38
Make sure there are fewer successes than trials, so one more success still fits.

@@ 39
One more person passing never *lowers* the bound.

@@ 40
One more person tested, with the same passes, never *raises* it. More evidence of the same kind can only make the promise easier to keep.

@@ 43
**`population`** — a made-up population for the tests: `per_cell` people for every age from 8 to 39 in every group.

@@ 44
A random-number generator started from a **seed**, so the same seed always gives the same population, and any failure can be replayed. The `noqa` note tells the security linter (which warns about `random` because it's unsuitable for secrets) that this use is deliberate, and why.

@@ 45
Start with nobody.

@@ 46-47
For every age and group…

@@ 48
…a typical score that rises with age: low for children, about 0.5 at 18, high for adults (kept between 0.02 and 0.98).

@@ 49
Each person's score is that typical score plus random noise (`gauss` draws from a bell curve with a spread of 0.15), kept between 0.001 and 0.999. Exactly 0 or 1 is left out on purpose: those are the cases `risk.py` refuses, and they have their own tests.

@@ 50
Return everyone.

@@ 53
**The central property**, checked on a hundred different random populations: the pass line is *safe*, and it is the *lowest* safe line.

@@ 54-56
Make a population and find its pass line for minimum age 18 and a 2 % budget.

@@ 57
Independently sort the 13–17-year-olds into cells.

@@ 58
**Safe:** at the chosen line, the worst cell's bound is the one reported, and it is within 2 %.

@@ 59
The highest score that lies below the line — the next line down that would let one more person through.

@@ 60-61
**Lowest:** at that lower line, the bound is over budget. So no lower line would have been safe, and the search didn't settle for a stricter line than needed.

@@ 64-68
**Both lines, in order:** the fail line is below the pass line, both on the 0–1 scale, and both bounds within their budgets.

@@ 71-75
**A cell too small.** Replace the 15-year-olds of group `b` with only 100 people. The calculation is refused, and the message names the cell and its size: `age 15 · b (100)`.

@@ 78-80
**A missing age.** With no 16-year-olds at all, the calculation is refused, naming the age.

@@ 83
**A model that can't tell ages apart.** This test began as a mistaken expectation: it was written to check that a model giving everyone the same score is refused. It isn't — and rightly so.

@@ 84
Everyone, child or adult, scores 0.5.

@@ 85-86
The pass line ends up above 0.5 and the fail line below it, so this model passes no one and fails no one: **everyone is sent to step-up**. That is useless, but *safe* — exactly what the rules should produce. The test now checks that.

@@ 89-91
**A model that separates perfectly.** Every child scores 0.9 and every adult 0.95.

@@ 92-95
Calibration succeeds, and puts both lines in the gap between the two groups: children are failed, adults pass, and both bounds are within budget. An earlier version of `calibrate` wrongly refused this model; this test, rewritten when the mistake was found, makes sure it can't come back.
