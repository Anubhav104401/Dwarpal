---
fingerprint: 961599e561de3a49
---
The `pyproject.toml` of **`dwarpal-ml`** — everything for teaching and evaluating the AI: datasets, training, evaluation, the risk-control calculations, export to ONNX, and model cards (Stage 3 §8). It never runs inside a deployed service. It produces model files and their manifests, which the services then load.

@@ 1
`[project]` — the standard package description table.

@@ 2
`name = "dwarpal-ml"` — imported as `dwarpal_ml`.

@@ 3
`version = "0.1.0"` — early development.

@@ 4
`description` — datasets, training, evaluation, risk control, export and model cards.

@@ 5
`requires-python = ">=3.13,<3.14"` — the same Python as serving, so the shared vision code behaves identically in both.

@@ 6
`dependencies = []` — empty for now. PyTorch, timm, MLflow and others arrive in Phase 2, pinned.

@@ 8-10
**The build system** — `uv_build`, as for every package in the workspace.
