---
fingerprint: feedf1c20ad4ea22
---
**Evaluation**: one fixed set of measurements for every model (§2.12, §2.13, §2.16), so that models can be compared fairly and nobody can pick, after the fact, the numbers that flatter one. It answers four questions:

| Question | Measured as |
| :-- | :-- |
| How accurate? | band-MAE and in-band share — overall, per age band, per group, per sex |
| How often would it get a clear case dangerously wrong? | for each age limit (13, 16, 18, 21): clear minors rated more likely than not *over* the limit, and clear adults rated *under* it, each with a 95 % interval |
| Can its probabilities be trusted? | calibration error of "at least *b* years old", for every band edge *b*, before and after a temperature correction |
| Is it fair? | the worst group against the best |

The results go to `evaluation-<split>.json` in the run's folder and are checked against the **release gates** (`ml/gates.toml`).

**The test split is opened once.** While developing, everything is measured on validation. The test split is evaluated a single time per model, and a second attempt is refused: if people could look at test results, change something and look again, the test would slowly turn into one more validation set, and stop being an honest exam (§2.2).

@@ 1-5
The docstring, with the two commands.

@@ 7
The project-wide type-hint setting.

@@ 9-16
Standard-library tools: `argparse`, `json`, `sys`, `tomllib` (for the gates), `defaultdict`, `partial` (below), `Path` and `Any`.

@@ 18-24
NumPy; PyTorch; NumPy's array type; `load_file` to read a trained model's weights; SciPy's `minimize_scalar` (find the best value of one number) and `beta` (for intervals, as in `risk.py`); and PyTorch's data loader.

@@ 26-31
From the ML package: the data and bands, the row type, the model, the prepared faces, the root folder, and from risk control the adult margin (adults are those N+3 and over) and the confidence level.

@@ 33
`GATES` — the release gates file.

@@ 34
`LIMITS` — the age limits websites use, which every model is measured at.

@@ 35-36
**`EDGES`** — FairFace's band edges. The comment gives the reason they matter: "is this person at least 20?" has a known answer for *every* face, because no FairFace band straddles 20. At these ages, calibration can be measured exactly, even without exact ages.

@@ 37
`BINS = 10` — calibration groups forecasts into ten bins: 0–10 %, 10–20 %, …

@@ 39
`Floats` — a name for "an array of decimal numbers".

@@ 42
**`softmax`** — turn logits into probabilities (§2.11), with a **temperature**.

@@ 43
Divide the logits by the temperature. Above 1, the differences shrink and the probabilities spread out (less confident); below 1, they sharpen (more confident).

@@ 44
Subtract each row's largest logit first. It changes nothing about the result, but keeps `exp` from overflowing on large numbers — a standard precaution.

@@ 45-46
Raise *e* to each, and divide by the row's total.

@@ 49-51
**`bands`** — every row's band as two arrays: lower ends and upper ends. `reshape(-1, 2)` keeps the shape right even for an empty list.

@@ 54-57
**`band_probability`** — how much probability the model gave to the labelled band: for each row, add up the probabilities of the ages inside it. `low[:, None]` turns the list of lower ends into a column, so that comparing it with the row of 101 ages gives a table: one row per face, one column per age, true inside the band.

@@ 60
**`fit_temperature`** — find the temperature that makes the model's probabilities most honest (§2.13).

@@ 61-63
For a candidate temperature: the average **surprise**, `−log(probability given to the true band)`. A model that gives the true band 90 % is barely surprised (0.1); one that gave it 1 % is very surprised (4.6). The smallest average surprise is the most honest temperature. `clip` avoids `log(0)`.

@@ 65
Search temperatures between 0.25 and 4 for the smallest surprise. It is fitted on **validation** only, never on test.

@@ 68-71
**`interval`** — the **two-sided Clopper–Pearson 95 % interval** for a rate (§2.14): the range the true rate plausibly lies in, given *k* out of *n*. The lower end uses `δ/2`, the upper end `1 − δ/2`, so that each end is wrong at most 2.5 % of the time. At 0 out of *n* the lower end is exactly 0, and at *n* out of *n* the upper end is exactly 1.

@@ 74-79
**`rate`** — a share of yes-or-no flags with its interval, how many, and out of how many. With no faces at all, every number is `None` ("not measurable"), never a misleading 0.

@@ 82-84
**`accuracy`** — band-MAE (average years outside the band) and the share inside the band (§2.12).

@@ 87
**`calibration_error`** — the **expected calibration error** (ECE): how far stated probabilities are from what actually happens (§2.13).

@@ 88
Put each forecast into one of ten bins by its probability: 0.37 goes into bin 3. `minimum(…, 9)` puts a forecast of exactly 1.0 into the last bin.

@@ 89-94
For each bin: the gap between the average forecast and the share that actually came true, weighted by the share of forecasts in that bin. If the model says "about 35 %" for some faces and 35 % of them really are over the age, that bin adds nothing.

@@ 97
**`calibration`** — the calibration error of "at least *edge*", for every band edge.

@@ 98-103
For each edge: the faces whose answer is known (all of them, for FairFace); the model's probability of being at least that age (the sum of the probabilities from `edge` upwards); and whether they truly are (`low >= edge`). Then the average over all edges.

@@ 106
**`limit_view`** — the dangerous mistakes at one age limit.

@@ 107
Each face's probability of being at least the limit.

@@ 108
**Clear minors**: faces whose whole band lies below the limit (for 18, the bands 0–2 and 3–9; FairFace's 10–19 can't be called either way). How many were rated *more likely than not* to be over it.

@@ 109
**Clear adults**: faces whose whole band starts at least 3 years above the limit (for 18, bands from 30 up). How many were rated more likely than not to be under it.

@@ 110
Both rates, and the minors' upper bound on its own, for the gates. These are measured at the plain 50 % line. The system's real decisions use the risk-controlled lines of §2.14, set on exact-age data, which will be stricter; these numbers describe the model, not the final system.

@@ 113-117
**`gap`** — the worst value divided by the best. If the best is perfectly 0, the ratio is 1 when everything is 0, and otherwise undefined (`None`), which fails any gate. The tests found the first version dividing by zero here.

@@ 120-121
**`order`** — the order to list a view's entries in: age bands by their lower age (so "3-9" comes before "10-19"), everything else alphabetically.

@@ 124
**`evaluate`** — the whole protocol, on one model's logits for one split.

@@ 125-127
The calibrated probabilities, each face's expected age, and the bands.

@@ 128-136
Sort the faces into **views**: by band, by group and by sex. For each, a list of row positions.

@@ 137-138
Start the results, and the overall accuracy.

@@ 139-148
For every entry in every view: its accuracy, and how many of its clear minors were rated 18 or over. `partial(order, view)` makes a one-argument version of `order` with the view filled in, as `sorted` requires.

@@ 149
The dangerous-mistake rates at every limit.

@@ 150-153
Calibration with the raw probabilities and with the temperature-corrected ones.

@@ 154-160
**Fairness**: the ratio of the worst group's band-MAE to the best group's, and the highest upper bound, across groups, of children rated 18 or over.

@@ 161
Return everything.

@@ 164-168
**`lookup`** — follow a dotted path such as `limits.18.minor_rate_upper` into the results.

@@ 171-177
**`check`** — read every gate from `ml/gates.toml`, look up its value, and pass it only if the value exists and is within its `max` and `min` (a missing limit is infinitely far away).

@@ 180
**`predict`** — the model's logits for every face of a split.

@@ 181-182
Read the run's record, to know its dataset and backbone, and the split's faces.

@@ 183-185
Logits already computed for this run and split are saved next to it, and reused: evaluating again (on validation) costs nothing, and gives exactly the same numbers.

@@ 186-189
Otherwise: build the backbone without any pretrained weights, then fill it with the trained weights, and switch it to evaluation behaviour.

@@ 190-194
Run every batch through the model, on the GPU if there is one, keeping the logits at full precision.

@@ 195-197
Join the batches, save them, and return them with the rows.

@@ 200
**`summary`** — the short printout.

@@ 201-211
Overall accuracy, the rates at 18, the calibration error before and after the temperature correction, and each group's band-MAE.

@@ 212-213
One line per gate, PASS or FAIL.

@@ 216-221
**`main`** — the run folder, the split (validation unless told otherwise), and the number of loader processes.

@@ 222-225
**The lock**: if this run has already been evaluated on the test split, refuse.

@@ 226-227
Always fit the temperature on validation.

@@ 228
Then take validation's logits, or compute the test split's.

@@ 229-233
Evaluate, check the gates, save the results, print the summary, and exit with `1` if any gate failed.

@@ 236-237
Run `main` when the module is started as a program.
