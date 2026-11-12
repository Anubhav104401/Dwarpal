---
fingerprint: 26cc1fc7b2bf1d03
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

@@ 6-16
`dependencies = [ … ]` — the libraries the service needs at run time, filled in during Phase 1. Each outside library is pinned with `==`:

| Library | Why the inference service needs it |
| :-- | :-- |
| `anyio` 4.15.1 | Runs the heavy, blocking image work on a limited pool of worker threads, so the server stays responsive (§4.8) |
| `dwarpal-contracts` | Our shared message shapes (`FaceAnalysis`, …) — the API uses the very same definitions |
| `dwarpal-vision` | Our shared face code: decode, detect, align, check quality |
| `fastapi` 0.143.0 | The web framework that turns Python functions into HTTP endpoints (§4.8) |
| `onnxruntime` 1.31.0 | Runs trained age models exported to ONNX, on the processor, without PyTorch (added in Phase 2) |
| `pydantic-settings` 2.15.0 | Reads the service's settings from environment variables, with types (§4.8) |
| `python-multipart` 0.0.32 | Lets FastAPI read `multipart/form-data` uploads — how the frames arrive |
| `uvicorn` 0.54.0 | The server program that actually listens on a port and hands requests to FastAPI |

Our own packages carry no version pin, because they are part of the same workspace and always move together. Their source is declared on the next lines. Since Part 7 also **`cryptography`**, the library that checks UIDAI's RSA signature on an Aadhaar Secure QR. The API already used the same version, so nothing new was downloaded.

@@ 18-20
`[tool.uv.sources]` — tells uv *where* to find two of the dependencies: `{ workspace = true }` means "use the copy that is a member of this workspace", not a package from the internet. A change to `dwarpal-vision` is therefore immediately visible to the inference service, with no publishing step in between.

@@ 22-24
**The build system**: `uv_build`, within the 0.13 series, called through the `uv_build` module — exactly as for the API package.
