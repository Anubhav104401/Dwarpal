---
fingerprint: 39d56bfcd6e557df
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

@@ 6-13
`dependencies` — what the ML package needs, each pinned exactly (added in Phase 2):

- `dwarpal-vision` — the project's own vision library (§5.1.1), so that training prepares faces with exactly the code that serving uses (`prepare.py`). It has no version number, because it comes from this workspace (below);
- `httpx` 0.28.1 — downloads approved datasets (`fetch.py`);
- `scipy` 1.18.1 — the scientific-computing library; the risk-control code uses its **Beta distribution** to compute exact Clopper–Pearson bounds (`risk.py`);
- `timm` 1.0.30 — PyTorch Image Models: hundreds of tested network designs (`model.py`);
- `torch` 2.14.1 — **PyTorch**, the deep-learning library (§2.6): tensors, automatic gradients, the GPU;
- `torchvision` 0.29.1 — PyTorch's vision companion. Our code doesn't use it directly, but timm needs it, and it must be built for the same PyTorch, so it is pinned and sourced alongside `torch` (below).

@@ 15-16
`[tool.uv.sources]` — tells uv where to find `dwarpal-vision`: in this workspace, not on the internet (as for the inference service, §5.1.1).

@@ 17-24
**Where PyTorch comes from.** PyTorch is published in several builds: for NVIDIA GPUs (one per CUDA version) and for processors only. The ordinary package index has just one of them. These lines choose by operating system, using **markers**:

- on Windows (`sys_platform == 'win32'`) — this project's development laptop, with its NVIDIA RTX 4070 — the build for **CUDA 13.0**, about 2 GB;
- on Linux — CI and servers — the **CPU** build, about a tenth the size. CI has no GPU, and the service won't run PyTorch at all: the trained model is exported to ONNX (Phase 2, step 6).

@@ 26-34
The two **package indexes** those lines name: PyTorch's own download servers for each build. `explicit = true` means uv uses them only for the packages that name them, never for anything else — a safeguard against another package being quietly fetched from an unexpected place.

@@ 36-38
**The build system** — `uv_build`, as for every package in the workspace.
