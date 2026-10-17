---
fingerprint: 640b319cc3a35e29
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

@@ 6-19
`dependencies = [...]` — the libraries this package needs in order to run, added in Phase 1. Each one is pinned to an exact version with `==`, for the reason given above: a service is tested and deployed with exactly one set of versions.

| Library | Version | What the API uses it for |
| :-- | :-- | :-- |
| `alembic` | 1.20.0 | database **migrations**: step-by-step, versioned changes to the tables (§4.10) |
| `asyncpg` | 0.32.0 | the **driver** for PostgreSQL — the low-level code that speaks the database's own network language, without blocking while it waits (§4.8, §4.10) |
| `cryptography` | 50.0.2 | AES-GCM, which seals the private signing keys before they are stored (§4.12) |
| `dwarpal-contracts` | — | our own shared message shapes; it has no version because it lives in this repository (see below) |
| `fastapi` | 0.143.0 | the web framework: turns Python functions into HTTP endpoints (§4.8) |
| `httpx` | 0.28.1 | an HTTP client, used to call the inference service |
| `joserfc` | 1.7.5 | JOSE: signs age tokens (JWS/JWT) and publishes the public keys (JWK) (§4.12) |
| `pydantic-settings` | 2.15.0 | reads the service's settings from environment variables, with type checks |
| `python-multipart` | 0.0.32 | parses **multipart** uploads — the format a browser uses to send files such as camera frames |
| `redis` | 8.1.0 | the client library for Valkey, which speaks the same language as Redis (§4.11) |
| `sqlalchemy[asyncio]` | 2.1.4 | talks to the database through Python classes (§4.10). `[asyncio]` is an **extra**: an optional bundle of additional libraries, here the ones needed for `async` use |
| `uvicorn` | 0.54.0 | the server program that listens on a network port and hands each request to FastAPI (§4.8) |

Only these direct dependencies are listed here. The libraries *they* need in turn are pinned in the workspace lockfile, `uv.lock` (§0.17).

@@ 21-22
`[tool.uv.sources]` tells uv *where* to get a dependency when that isn't the public package index (PyPI). `dwarpal-contracts = { workspace = true }` means "use the workspace member of that name" — the folder `libs/contracts` in this repository. The curly brackets are an **inline table**: TOML's way of writing a small table on one line.

Because the contracts come from the same repository, the API always uses them exactly as they are in the same commit. That is why they need no version number.

@@ 24
`[build-system]` — how to turn this folder into an installable package. Every installer, including uv and pip, reads this table first.

@@ 25
`requires = ["uv_build>=0.13.1,<0.14"]` — the **build backend** needed to build it: `uv_build`, made by the uv team. It is small, fast, and fits the `src/` layout (§4.2). The range allows bug-fix releases of 0.13 but not 0.14, which could change behaviour.

@@ 26
`build-backend = "uv_build"` — the Python module that installers should call to perform the build.
