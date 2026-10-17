---
fingerprint: 40960f2bb78a2f60
---
**The safety lines** — the most important calculation in the project (ADR-0006, §2.14). The age model gives each face a score `p_over`: how likely the person is to be at least the minimum age `N`, from 0 to 1. This file chooses the two lines that turn the score into a decision:

```
p_over:   0 ─────────────── τ_fail ════════ step-up ════════ τ_pass ─────────────── 1
               fail (clearly under N)                            pass (clearly N or over)
```

- **`tau_pass`** (τ is the Greek letter *tau*, a traditional name for a threshold) is the *lowest* line at which, for **every exact age** from N−5 to N−1 and **every group**, the worst plausible share of those children who would pass is within the **risk budget** ε (*epsilon*) — with 95 % confidence.
- **`tau_fail`** is the *highest* line at which the worst plausible share of clear adults (N+3 and over) who would be failed outright is within 1 %, in every group.

Everyone between the two lines gets step-up (a document check), never a rejection.

Why "every age and every group", and not just "all children together"? Because an average hides danger. A model could let in 0.5 % of 13-year-olds and 6 % of 17-year-olds and still average under 2 %. Checking every **cell** — one age in one group — separately means the promise holds for each of them.

@@ 1-7
The docstring: the rule above, in one paragraph.

@@ 9
The project-wide type-hint setting.

@@ 11-15
`bisect` (fast searching in sorted lists), `math`, `defaultdict` (a dictionary that creates missing entries automatically), the types for functions and sequences, and `dataclass`.

@@ 17
**`beta`** — the beta distribution, from **SciPy**, Python's standard library of scientific maths. The Clopper–Pearson bound is a value read off this distribution (§2.14). The formula is famous and short, but computing it accurately for any input is not: SciPy's code for it has been tested for decades, so we use it rather than write our own.

@@ 19
`DELTA` (δ, *delta*) — the chance we accept of the bound itself being wrong: 5 %, so the guarantee holds with 95 % confidence.

@@ 20
`MINOR_SPAN` — how many years under N are checked: for N = 18, ages 13 to 17. Younger children are further from the line, so they are even safer.

@@ 21
`ADULT_MARGIN` — the fail line protects adults from N+3 upwards (21 and over, for N = 18). People aged 18–20 may land in step-up more often, which is the price of keeping children out.

@@ 22
`ADULT_FAIL_BUDGET` — at most 1 % of those adults may be failed outright, in any group.

@@ 24
**`Cells`** — the scores sorted into cells: a cell's name (such as `age 15 · Indian`) mapped to its list of scores. `type … = …` names a type, so long types can be written once.

@@ 25
**`Count`** — a function that counts, in one cell's sorted scores, how many would pass (or fail) at some line.

@@ 28-32
**`Scored`** — one calibration image after the model has looked at it: the person's real age, their group, and the model's score.

@@ 35-43
**`Thresholds`** — the result: the minimum age and risk budget it was made for, both lines, the worst bound each line achieved (`minor_bound` for children passing, `adult_bound` for adults failing), and whether the promise holds for every group or only for every age (`by_group`, below). These numbers go into the model's manifest, so anyone can see what was promised.

@@ 46-47
**`CalibrationError`** — the data can't support the promise. The docstring states the rule: refusing, with a reason, is safer than handing back a line that only *looks* safe.

@@ 50-51
**`cell_name`** — the name of a person's cell. Normally one cell per age *and* group (`age 15 · Indian`); when the data is too thin for that, one cell per age, all groups together (`age 15`). The second is a weaker promise — it holds on average across groups, not for each — and the results always record which one was made.

@@ 54-55
**`clopper_pearson_upper`** — the bound itself. Out of `trials` people, `successes` passed; how high could the true pass rate plausibly be? (For 6 out of 600: 1.96 %.)

@@ 56-57
Refuse impossible inputs — no people, or more passes than people.

@@ 58-59
If *everyone* passed, the true rate could be anything up to 100 %: the bound is 1. (The formula below would divide by zero here.)

@@ 60
The Clopper–Pearson upper bound: the value below which the beta distribution with parameters `successes + 1` and `trials − successes` holds 1 − δ of its weight (`ppf` reads the distribution "backwards", from a share to a value). `float(...)` turns SciPy's number type into an ordinary Python number.

@@ 63-65
**`minimum_cell_size`** — the fewest people a cell needs before the promise is even *possible*. With zero passes the bound is 1 − δ^(1/n), and requiring that to be at most ε gives n ≥ log δ ÷ log(1 − ε). For ε = 2 %: **149 people**. With 148, even a perfect result can't prove 2 %. `math.ceil` rounds up to a whole person.

@@ 68
**`cells_of`** — sort labelled scores into cells.

@@ 69-71
Add each score to its cell's list; `defaultdict(list)` creates an empty list the first time a cell is seen.

@@ 72
Return each cell's scores **sorted**, so counting how many lie above a line becomes a fast search (`passes_at`, below).

@@ 75
**`check_size`** — refuse any cell too small to certify the budget.

@@ 76-77
Work out the minimum, and list every cell that falls short, with its size.

@@ 78-79
If any do, refuse, naming them all — such as `too few minors to certify 2% (need 149 per cell): age 15 · b (100)`. The message says exactly which data is missing.

@@ 82-83
**`worst_bound`** — the highest bound across all cells, for a given way of counting. The promise is only as good as its weakest cell.

@@ 86
**`first_safe`** — find the first safe value in a list, given that the list is in order: once one candidate is safe, every candidate after it is safe too. It uses **binary search**: the guessing game where someone thinks of a number from 1 to 100, you guess 50, they say "higher" or "lower", and each guess throws away half of what's left — so seven guesses are always enough.

@@ 87
The docstring states that condition, because the search is only correct when it holds. It does here: raising the pass line can only make fewer people pass.

@@ 88
Search between the first and the last candidate.

@@ 89-94
Look at the middle one. If it is safe, the first safe one is here or earlier: keep the left half. If not, it's later: keep the right half. Each step halves the range, so even 100,000 candidates take about 17 steps.

@@ 95
When the range has shrunk to one, that's the answer. (If no candidate were safe, this would return the last one; the callers check for that.)

@@ 98-99
**`passes_at`** — make a counting function for a pass line τ: how many scores are **at or above** τ. In a sorted list, `bisect_left` finds where τ would go; everything from there on is at least τ.

@@ 102-103
**`fails_at`** — the same for a fail line: how many scores are **at or below** τ. `bisect_right` finds the position just after any scores equal to τ.

@@ 106-109
**`tau_pass_for`** — the lowest safe pass line, and the bound it achieves. `by_group` chooses the kind of cell.

@@ 110-111
The ages checked (`range(13, 18)` is 13 to 17 — the end is not included), and the people of those ages.

@@ 112-114
If any of those ages has no data at all, refuse: a promise about 13–17-year-olds can't be made without 16-year-olds.

@@ 115
The cells: one per age and group, or one per age.

@@ 116
Refuse any cell under the minimum size.

@@ 117
Every distinct score seen, in order.

@@ 118
The **candidate lines**. A line only matters where it crosses a score, so the candidates are 0 (everyone passes) and, for each score, the smallest number just above it (`math.nextafter(score, math.inf)` — the next number a computer can represent, heading towards infinity). A line just above a score makes that person, and everyone below them, fail. Trying only these lines covers every possible outcome, with nothing missed.

@@ 119
Find the first — so the lowest — candidate at which the worst cell's pass bound is within the budget. A lower line lets more adults pass straight away, so the lowest *safe* line is the best one.

@@ 120-121
If the only safe line is above 1, some child scored exactly 1.0 ("certainly an adult"), and no line on the 0–1 scale keeps them out: refuse.

@@ 122
Return the line and its bound.

@@ 125-136
**`tau_fail_for`** — the highest safe fail line for clear adults, and its bound. The extra setting `below` caps the line under a given value — the pass line, when `calibrate` calls it (`math.inf`, "infinity", means no cap). The docstring records why capping is always allowed: lowering a fail line can only fail *fewer* adults, so a safe line stays safe.

@@ 137-138
One cell per group holding everyone N+3 and over — or, without groups, a single cell of all those adults.

@@ 139-140
No adults at all: refuse.

@@ 141
Refuse any group under the minimum size (299 people for 1 %).

@@ 142-143
The candidates run the other way: every distinct score, **highest first**, and finally a value just below the lowest score (a line that fails no one). Lowering the fail line can only fail fewer adults, so once a candidate is safe, every later one is too — the condition `first_safe` needs.

@@ 144
Find the highest safe line.

@@ 145
Then cap it: no higher than just below `below`, and no lower than 0, to stay on the 0–1 scale.

@@ 146-148
Measure the bound at the final line, and check it again: if an adult scored exactly 0.0, even the line at 0 fails them, so no fail line is safe — refuse.

@@ 149
Return the line and its bound.

@@ 152-155
**`calibrate`** — both lines for one minimum age and budget, with either kind of cell.

@@ 156
First the pass line, which protects children — it is never moved to suit anything else.

@@ 157
Then the fail line, capped just below the pass line, so the two can never cross and no score can mean both "pass" and "fail".

A first version of this function refused to answer when the highest safe fail line came out *above* the pass line, calling it a model that "can't separate" the ages. Writing this book's explanation of its test showed that was wrong: in that test the children all scored 0.9 and the adults 0.95 — a model that separates the ages *perfectly*. A fail line chosen without looking at the pass line can drift up past it, but it can always be lowered again safely. Now it is.

@@ 158
Return the result, recording the kind of cell.
