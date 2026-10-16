---
fingerprint: baaf9df5d28bc22d
---
The **manifest of the stand-in age model** used throughout Phase 1. It has the same shape as a real model's certificate (`domain/policy.py` reads it), but its numbers are placeholders, and it says so twice: in `calibrated: false`, and in a plain-language note.

The folder path is part of the design: `models/registry/<model name>/<version>/manifest.json`. Phase 2 adds real, calibrated versions next to this one, and switching the API to one is a single setting (`DWARPAL_AGE_MANIFEST`).

@@ 1
The opening brace of the JSON object.

@@ 2
`"name": "age"` — which kind of model: the age estimator.

@@ 3
`"version": "stub"` — this manifest's own version.

@@ 4
`"serves": "stub-age-*"` — the pattern of model versions it covers. The stand-in model in the inference service reports versions such as `stub-age-30`, which match.

@@ 5
`"calibrated": false` — the thresholds below were **not** produced by risk calibration. Because of this one line, the API refuses to create **live** sessions (error `model_not_calibrated`); test sessions still work, so the whole system can be built and tested before a real model exists.

@@ 6
`"note"` — the same warning in plain words, for any person who opens the file.

@@ 7
The list of thresholds begins.

@@ 8-11
One row per supported minimum age — 13, 16, 18 and 21 — each at a 2 % risk budget, with:

- `tau_pass: 0.95` — pass only when the model gives at least a 95 % probability of being old enough;
- `tau_fail: 0.05` — fail at 5 % or less.

These round numbers were chosen for testing, not measured. Phase 2 replaces them with values computed from real photos.

@@ 12
The list ends.

@@ 13
The object ends.
