---
fingerprint: f91aa518ba721ab6
---
The inference service's **settings**, read from environment variables. The same code can then run on a laptop, in CI and in production — only the environment changes (the "12-factor" principle, Stage 4 §9).

@@ 1
The docstring names the environment-variable prefix: `DWARPAL_INFERENCE_`.

@@ 3
The project-wide type-hint setting.

@@ 5-6
`Path` for file locations. `Literal` lets a type allow only certain exact values.

@@ 8
`model_validator` — Pydantic's way of adding a check that looks at **several fields together**, after each has been checked on its own (added in Phase 3).

@@ 9
**pydantic-settings**: `BaseSettings` builds a settings object whose fields are filled from environment variables and checked with Pydantic's rules. `SettingsConfigDict` configures how.

@@ 11
The repository root, found from this file's own location (`parents[4]` climbs `dwarpal_inference → src → inference → services → root`). It gives a sensible default for where model files live during development.

@@ 14-15
**`Settings`.** `env_prefix` means a field such as `stub_age` is read from `DWARPAL_INFERENCE_STUB_AGE`. `extra="ignore"` lets other `DWARPAL_INFERENCE_*` variables exist without causing an error.

@@ 17
`models_dir` — the folder holding model files. In containers this is set to a mounted volume.

@@ 18
`detector_file` — YuNet's file, relative to `models_dir`, exactly as listed in `models/third_party.json`.

@@ 19
`mesh_file` — the MediaPipe face landmarker bundle; the service runs its 478-point face mesh to measure the head's angles (`dwarpal_vision.mesh`).

@@ 20
`hands_file` — the MediaPipe hand landmarker bundle, for finding a hand held next to the face (`dwarpal_vision.hands`).

@@ 21
`antispoof_files` — the two anti-spoofing networks, as ONNX files made from the pinned weights by `python -m dwarpal_ml.antispoof`. If they are missing, the service runs without them and every result says so (`presentation` is empty).

@@ 30
`age_backend` — which age model to use: `"stub"` (the stand-in, still the default) or `"onnx"` (a trained model, added in Phase 2). `Literal` means only these words are accepted, so a typo like `"onx"` is rejected at start-up.

@@ 31-32
The stand-in model's fixed age and spread, in years. Tests and the end-to-end demo choose them, for example 30 for an adult or 15 for a minor.

@@ 33-34
For the ONNX backend: the model's folder inside `models/` (by default the first trained model, `age-convnext-tiny-2026.10.17`), and how many processor threads each request may use.

@@ 35-36
**`age_frames`** (Phase 7, decision P1) — how many of an attempt's flawless frames the age model sees, the sharpest first. 3 was chosen after checking the decisions it makes against the certified safety lines (§5.7.4).

@@ 37
`workers` — how many analyses may run at the same time. The rest wait or are told to retry (back-pressure, Stage 3 §5.4).

@@ 38-39
**`queue_s`** (Phase 7, §5.7.4) — how long a request may wait for a free worker before the answer is "busy": one second. People arrive at random, so now and then a fifth arrives while four analyses are running; waiting a moment serves them, where an instant refusal sent one in five away in the load test.

@@ 40
`liveness` — where the pose check gets its evidence (Phase 3): `"images"`, measured from the photos — the default, and the only safe choice — or `"labels"`, the test mode that believes the photos' labels (§5.3.5).

@@ 42-43
**`labels_only_with_the_stand_in`** — a check across two fields. `mode="after"` runs it once every field is set, so it can compare them. It returns the settings themselves if all is well.

@@ 44-45
**The test mode is allowed only with the stand-in age model.** A service set up with a real age model *and* labels mode would be a real-looking deployment that a photo could pass — so it refuses to start, with a message saying why. This is the first of the three locks on the test mode.

@@ 46
All is well: return the settings.

@@ 22
`matcher_file` (§5.6.2) — SFace, the face recogniser that compares a selfie with a document's photo.

@@ 26-28
`tesseract_command` — how to start Tesseract, the OCR engine, as a list of words. The default, `tesseract`, is for where it is installed (as it will be in the production image). On this project's Windows computers it runs in a container instead (§5.6.2), so the setting becomes `docker exec -i dwarpal-ocr-1 tesseract`, given as a JSON list in an environment variable.

@@ 29
`tesseract_timeout_s` — how long one reading may take before it counts as failed: 10 seconds, far more than the half-second it needs.

@@ 23-25
**`render_model`** — the render detector's ONNX file, inside `models_dir`, once one has been trained and has passed its gates. Empty by default: no detector, and `rendered` stays `None`.
