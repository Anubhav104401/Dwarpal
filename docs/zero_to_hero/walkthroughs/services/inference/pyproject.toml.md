---
fingerprint: 34bd4c3a8692ab59
---
The `pyproject.toml` of the **inference service** — the "clean room" where faces are analysed in memory and never stored (§3.8). Its structure is identical to the API's (see §5.0.2, `services/api/pyproject.toml`); only the name and description differ.

@@ 1
`[project]` — the standard package description table.

@@ 2
`name = "dwarpal-inference"` — imported in code as `dwarpal_inference`.

@@ 3
`version = "0.1.0"` — early development.

@@ 4
`description` — face analysis, liveness signals and age distributions, **in memory only**. Even the one-line description repeats the privacy promise, so nobody can forget it.

@@ 5
`requires-python = ">=3.13,<3.14"` — tested and deployed on Python 3.13 only.

@@ 6
`dependencies = []` — empty for now. ONNX Runtime, OpenCV, NumPy and FastAPI arrive in Phases 1–2.

@@ 8-10
**The build system**: `uv_build`, within the 0.13 series, called through the `uv_build` module — exactly as for the API package.
