---
fingerprint: d165839c517ca4a3
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

@@ 6-8
`dependencies = [ "pydantic==2.14.0" ]` — the one library the contracts need: **Pydantic** (§4.8). It turns plain class definitions into data models that *check* every value they are given. The contracts deliberately depend on nothing else, so both services can install them cheaply.

@@ 10-12
**The build system** — `uv_build`, exactly as for the API package (§5.0.2).
