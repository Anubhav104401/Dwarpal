---
fingerprint: 5cd6681ece3e51a6
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
`age_backend` — which age model to use: `"stub"` (the stand-in, still the default) or `"onnx"` (a trained model, added in Phase 2). `Literal` means only these words are accepted, so a typo like `"onx"` is rejected at start-up.

@@ 20-21
The stand-in model's fixed age and spread, in years. Tests and the end-to-end demo choose them, for example 30 for an adult or 15 for a minor.

@@ 22-23
For the ONNX backend: the model's folder inside `models/` (by default the first trained model, `age-convnext-tiny-2026.10.17`), and how many processor threads each request may use.

@@ 24
`workers` — how many analyses may run at the same time. The rest wait or are told to retry (back-pressure, Stage 3 §5.4).

@@ 25
`liveness` — where the pose check gets its evidence (Phase 3): `"images"`, measured from the photos — the default, and the only safe choice — or `"labels"`, the test mode that believes the photos' labels (§5.3.5).

@@ 27-28
**`labels_only_with_the_stand_in`** — a check across two fields. `mode="after"` runs it once every field is set, so it can compare them. It returns the settings themselves if all is well.

@@ 29-30
**The test mode is allowed only with the stand-in age model.** A service set up with a real age model *and* labels mode would be a real-looking deployment that a photo could pass — so it refuses to start, with a message saying why. This is the first of the three locks on the test mode.

@@ 31
All is well: return the settings.
