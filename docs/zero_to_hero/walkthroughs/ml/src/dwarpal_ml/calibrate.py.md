---
fingerprint: 0bf9dc4771d33d16
---
**Exact-age calibration**: where the safety lines of §2.14 are finally set, on real faces with exact ages, and then checked on faces nobody has looked at.

```
UTKFace calib half (11,301 faces) ─► model ─► P(age ≥ N) for every face
                                  ─► for N = 13, 16, 18, 21: try budgets 2 %, 3 %, 5 %, … with cells per age and group,
                                     then per age; keep the strictest that the data can certify     ─► calibration-utkface.json
UTKFace test half (11,637 faces)  ─► the same model and lines ─► pass / step-up / fail for every face
                                  ─► children passed at each exact age; adults' outcomes; per group  ─► evaluation-utkface-test.json
```

Two rules make it honest:

- **The lines are certified on one half and checked on the other.** Clopper–Pearson already gives a guarantee on the calibration half; the test half shows whether it holds on faces that played no part in choosing the lines.
- **The strictest budget the data supports is used, and every stricter one that failed is recorded with the reason.** Nobody can quietly pick a comfortable number.

@@ 1-5
The docstring: what it does, and the command.

@@ 7
The project-wide type-hint setting.

@@ 9-14
`argparse`, `json`, `sys`, `asdict` (to turn the thresholds into a dictionary for JSON), `Path` and `Any`.

@@ 16-17
NumPy, and its array type.

@@ 19-22
From the evaluation protocol: probabilities, bands, the temperature, predictions and rates with intervals. The row type and the register. From risk control: the span of minor ages (5), the refusal, the scored-person type and `calibrate` itself.

@@ 24
The age limits to calibrate.

@@ 25-27
**`BUDGETS`** — the risk budgets to try, from the design's 2 % target to 20 %, and the comment saying how they are used.

@@ 28-29
**`ADULT_BANDS`** — adults are reported in four groups by how far above the limit they are, as the problem analysis asks (§1): just over (N to N+2), then N+3 to N+6, N+7 to N+11, and N+12 and over. Being sent to step-up is most likely just over the limit, and that is the cost the system's users feel.

@@ 30
`AGE_RANGES` — age ranges for reporting the exact-age error.

@@ 33-34
**`over`** — each face's probability of being at least the limit: the sum of the probabilities from that age to 100.

@@ 37-38
**`cells`** — the name of a kind of cell, for the records.

@@ 41
**`certify`** — find the strictest budget the data can certify for one limit.

@@ 42-44
For each budget, strictest first, and for each kind of cell — per age and group first, then per age only…

@@ 45-49
…try risk control. If it refuses — too few people in some cell, a missing age — record the budget, the kind of cell and the reason, and try the next.

@@ 50
The first success is the answer: its thresholds, its kind of cell, and every refusal before it.

@@ 51
If even 20 % can't be certified, say so: no thresholds.

@@ 54-55
**`decide`** — what the system would do with each face: **pass** at or above the pass line, **fail** at or below the fail line, and **step-up** in between. `np.where` picks, for each face, the first value where the condition holds and the second where it doesn't; nested, it chooses among three.

@@ 58-59
**`outcomes`** — the share of pass, step-up and fail among some faces, each with its interval.

@@ 62
**`decisions_view`** — everything the test half shows about one limit.

@@ 63-65
Each face's exact age, group and decision.

@@ 66
The **minors** the guarantee is about: ages N−5 to N−1.

@@ 67-70
**Children passed, at each exact age** — the number the design's safety requirement (NFR-01) is written in.

@@ 71
All those minors together.

@@ 72-74
The same, **per group**. These are measurements, not guarantees: when the lines could only be certified per age, nothing promises each group's rate, so the report must show it.

@@ 75
Children **younger** than N−5 who passed. They are further from the line, so they should almost never pass; this checks it.

@@ 76-81
**Adults**, in the four bands: the share passed, sent to step-up, and failed. `200` stands for "no upper age" in the last band.

@@ 82
Return the view.

@@ 85
**`exact_accuracy`** — with exact ages, the true **mean absolute error** in years (§2.12), overall and per age range.

@@ 86-87
Each face's error: the distance between its expected age and its labelled age.

@@ 88-91
The average error in each age range; `None` for a range with no faces, since an average of nothing is not a number (the tests found the first version producing exactly that).

@@ 92
Return the overall error and the ranges.

@@ 95
**`summary`** — the printout: the error, then one line per limit.

@@ 96
The first line: how many test faces, and the error in years.

@@ 97-101
For each limit: if nothing could be certified, say so.

@@ 102-107
Otherwise: the budget, the kind of cell, both lines, and the share of minors passed at each exact age.

@@ 108
Join the lines.

@@ 111-116
**`main`** — the run, the exact-age dataset, and the number of loader processes.

@@ 117-120
Refuse a dataset without exact ages: calibration per exact age needs them.

@@ 121-124
**The lock**: each run is checked on a dataset's test half only once.

@@ 125-126
The temperature, fitted on the training dataset's **validation** split — the same one the service will apply (§2.13).

@@ 127-128
The model's probabilities for the calibration half.

@@ 129-136
The calibration record: which run, which dataset, **where its ages came from** (for UTKFace: estimated by an algorithm and checked by a person), the temperature, and how many faces.

@@ 137-142
For each limit: every face as a `Scored` person — exact age, group, probability of being at least the limit — and certify. (`or 0` only satisfies the type checker: an exact-age dataset has an age for every row.)

@@ 143
Save it as `calibration-<dataset>.json` in the run's folder. These are the thresholds the model's manifest will carry (Phase 2, step 7).

@@ 144-145
Now the test half, with the same temperature.

@@ 146-158
The test results: the exact-age error, and the decisions view for every limit that has thresholds.

@@ 159-161
Save them — which also locks the test half for this run — print the summary, and finish.

@@ 164-165
Run `main` when the module is started as a program.
