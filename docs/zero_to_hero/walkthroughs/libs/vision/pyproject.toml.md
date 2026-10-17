---
fingerprint: 1b563b6f31652c23
---
The `pyproject.toml` of **`dwarpal-vision`** — the face-handling code shared by **training** (in `ml/`) and **serving** (in the inference service).

!!! key "Key idea — one function for training and serving"
    An AI model learns from faces that were found, straightened and cropped in a particular way. If the live system prepared faces even slightly differently, the model would see images unlike anything it was trained on, and its accuracy would quietly drop. Engineers call this **train/serve skew**. Putting that code in one shared package makes skew impossible: training and serving literally call the same function.

@@ 1
`[project]` — the standard package description table.

@@ 2
`name = "dwarpal-vision"` — imported as `dwarpal_vision`.

@@ 3
`version = "0.1.0"` — early development.

@@ 4
`description` — decoding, detection, alignment and quality checks, shared by training and serving.

@@ 5
`requires-python = ">=3.13,<3.14"` — Python 3.13 only, like everything else.

@@ 6-9
`dependencies = [ … ]` — the two libraries everything in computer vision stands on (§4.9):

- `numpy` 2.5.3 — fast arrays of numbers. A picture is a NumPy array of shape *height × width × 3*;
- `opencv-python-headless` 5.0.0.93 — **OpenCV**, the classic open-source computer-vision library (Apache-2.0). *Headless* means the build without windowing and GUI parts, which a server never needs, so it is smaller and has fewer system requirements.

@@ 11-13
**The build system** — `uv_build`, as for every package in the workspace.
