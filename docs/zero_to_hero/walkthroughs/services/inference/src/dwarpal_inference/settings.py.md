---
fingerprint: 83f8cdd81731e5c1
---
The inference service's **settings**, read from environment variables. The same code can then run on a laptop, in CI and in production — only the environment changes (the "12-factor" principle, Stage 4 §9).

@@ 1
The docstring names the environment-variable prefix: `DWARPAL_INFERENCE_`.

@@ 3
The project-wide type-hint setting.

@@ 5-6
`Path` for file locations. `Literal` lets a type allow only certain exact values.

@@ 8
**pydantic-settings**: `BaseSettings` builds a settings object whose fields are filled from environment variables and checked with Pydantic's rules. `SettingsConfigDict` configures how.

@@ 10
The repository root, found from this file's own location (`parents[4]` climbs `dwarpal_inference → src → inference → services → root`). It gives a sensible default for where model files live during development.

@@ 13-14
**`Settings`.** `env_prefix` means a field such as `stub_age` is read from `DWARPAL_INFERENCE_STUB_AGE`. `extra="ignore"` lets other `DWARPAL_INFERENCE_*` variables exist without causing an error.

@@ 16
`models_dir` — the folder holding model files. In containers this is set to a mounted volume.

@@ 17
`detector_file` — YuNet's file, relative to `models_dir`, exactly as listed in `models/third_party.json`.

@@ 18
`age_backend` — which age model to use. Today only `"stub"` is allowed (`Literal`), so a typo like `"stubb"` is rejected at start-up. Phase 2 adds `"onnx"`.

@@ 19-20
The stand-in model's fixed age and spread, in years. Tests and the end-to-end demo choose them, for example 30 for an adult or 15 for a minor.

@@ 21
`workers` — how many analyses may run at the same time. The rest wait or are told to retry (back-pressure, Stage 3 §5.4).
