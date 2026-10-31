---
fingerprint: f1ab726f494b1173
---
The **manifest of the first trained age model** — its passport in the registry, written by `ml/src/dwarpal_ml/export.py`. The API reads its first fields and its thresholds (§5.1.2); everything else is there so that anyone can see, years later, exactly what this model is, where it came from, what it promises and under which terms it may be used.

The model file itself (`model.onnx`, 110 MB) sits next to this manifest but is never committed to Git (`.gitignore`); the manifest pins it by fingerprint, and the inference service refuses any file that doesn't match (§5.2.7).

@@ 1
The opening brace.

@@ 2
`"name": "age"` — the age estimator.

@@ 3
`"version"` — the model's name: its architecture and the date it was made.

@@ 4
`"serves"` — the model versions this manifest covers: exactly this one. The inference service reports the version with every analysis, and the API refuses to decide if it doesn't match (`model_mismatch`, §5.1.3).

@@ 5
**`"calibrated": false`** — not certified to the release standard, so the API allows only test-mode sessions with it.

@@ 6
The note saying why, in plain words: the thresholds are risk-controlled, but per age only, on estimated ages, at budgets above the 2 % of NFR-01.

@@ 7
`"permitted_use"` — **non-commercial research only**: the terms of the strictest ingredient, the calibration dataset.

@@ 8
The model file's details.

@@ 9-11
Its name, its SHA-256 fingerprint and its size in bytes.

@@ 12
The ONNX operation set it uses.

@@ 13-14
What goes in — pixels, aligned by the shared vision library, in red-green-blue order, 0–255 — and what comes out: 101 probabilities per face.

@@ 15
The temperature (0.884) already built into the file: the service applies nothing further.

@@ 16
End of the model's details.

@@ 17-19
How it was trained: the run's folder name and the backbone.

@@ 20-24
The pretrained weights it started from: their name in the model register, their fingerprint, and their licence, with its recorded caveat.

@@ 25-29
The training data: FairFace, its licence, and where its ages came from.

@@ 30-34
The exact code it was trained with. `uncommitted_changes: true` is the honest truth: this model was trained while step 4 was still being written, before it was committed. Models for a release will be trained from committed code.

@@ 35-40
How it was calibrated: on UTKFace's calibration half (11,301 faces), with its licence and the source of its ages.

@@ 41
The thresholds, one entry per age limit — the part the API acts on.

@@ 42-80
**Age 13**: certified at a 15 % budget, per age. A face passes at P(13 or over) ≥ 0.809 and fails at ≤ 0.708. `minor_bound` is the worst plausible pass rate among 8–12-year-olds that the calibration data showed (13.5 %), and `adult_bound` the worst plausible rate of adults 16 and over failed (just under 1 %).

Then **`adults`** (added in Phase 5, §5.5.8): how people in four age bands above the line fared on the exact-age test split — how many faces each band held, and the shares that passed, were sent to a stronger check, and failed. Each line has the same four kinds of band: 0–2, 3–6 and 7–11 years over the age, and 12 or more. The console's policy editor shows them as its projection.

@@ 81-119
**Age 16**: 15 % per age; pass at ≥ 0.761, fail at ≤ 0.529; and its adults' outcomes.

@@ 120-158
**Age 18**: 7.5 % per age; pass only at P(18 or over) ≥ 0.964, fail at ≤ 0.384. The pass line is high because this model is uncertain about teenagers: it has to be very sure before it lets anyone through.

Its adults' outcomes show the price: of 18–20-year-olds, 77 % are sent to a stronger check and 13 % pass; of those 30 and over, 94 % pass and 6 % are sent on. A line that keeps minors out this firmly asks most young adults for a second check.

@@ 159-197
**Age 21**: 7.5 % per age; pass at ≥ 0.927, fail at ≤ 0.244; and its adults' outcomes.

@@ 198
End of the thresholds.

@@ 199
The checks made when the model was exported.

@@ 200-205
**Parity**: on 512 faces, the ONNX file and PyTorch differed by at most 0.0000008 in any probability, well within the 0.0001 allowed.

@@ 206-211
**The serving path**: aligning faces the service's way instead of the training way changed the estimated age by 0.16 years on average (0.45 years for 95 % of faces) and the probability of being 18 or over by 0.003.

@@ 212-216
**Speed**: one burst of 5 faces on a single processor thread: 668 ms typical, 697 ms in the slow case (p95).

@@ 217-218
The closing braces.
