---
fingerprint: fc41ab6386a4ebc7
---
The `pyproject.toml` of the **API service** package: its name, version, purpose, supported Python versions, libraries it needs, and how to build it. The other four packages follow exactly the same pattern, so this one is explained in the most detail.

@@ 1
`[project]` — the standard table (defined in PEP 621) that every Python package uses to describe itself.

@@ 2
`name = "dwarpal-api"` — the **distribution name** that installers use. Inside Python code, the package is imported as `dwarpal_api`, with an underscore, because a dash isn't allowed in a Python name (§4.2).

@@ 3
`version = "0.1.0"` — **semantic versioning** (*major.minor.patch*, §0.17). A major version of `0` signals "early development; anything may still change".

@@ 4
`description` — one line saying what the package is for: the relying-party, flow and console APIs, the decision engine, and signed age tokens (Stage 3 §3).

@@ 5
`requires-python = ">=3.13,<3.14"` — this package runs on Python 3.13 only.

!!! why "Why an upper limit?"
    Libraries usually avoid upper limits, so their users can upgrade freely. A **service** is different: we test it on exactly one Python version and deploy exactly that version, so declaring anything wider would be a promise we haven't checked.

@@ 6
`dependencies = []` — the libraries this package needs to run. It is empty for now. Phase 1 adds FastAPI, Pydantic, SQLAlchemy and others here, each pinned.

@@ 8
`[build-system]` — how to turn this folder into an installable package. Every installer, including uv and pip, reads this table first.

@@ 9
`requires = ["uv_build>=0.13.1,<0.14"]` — the **build backend** needed to build it: `uv_build`, made by the uv team. It is small, fast, and fits the `src/` layout (§4.2). The range allows bug-fix releases of 0.13 but not 0.14, which could change behaviour.

@@ 10
`build-backend = "uv_build"` — the Python module that installers should call to perform the build.
