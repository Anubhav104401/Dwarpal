---
fingerprint: 41edff6f11f2ecb0
---
The `pyproject.toml` of **`dwarpal-contracts`** — the shared data models. When the API asks the inference service to analyse frames, both sides must agree on exactly what the request and the answer look like. Defining those shapes **once**, in a package both services install, means they can never drift apart.

@@ 1
`[project]` — the standard package description table.

@@ 2
`name = "dwarpal-contracts"` — imported as `dwarpal_contracts`.

@@ 3
`version = "0.1.0"` — early development.

@@ 4
`description` — the purpose in one line: shared data models, so services' messages can never drift apart.

@@ 5
`requires-python = ">=3.13,<3.14"` — the same single, tested Python version as the services that use it.

@@ 6
`dependencies = []` — empty for now. Pydantic (the data-validation library) arrives in Phase 1.

@@ 8-10
**The build system** — `uv_build`, exactly as for the API package (§5.0.2).
