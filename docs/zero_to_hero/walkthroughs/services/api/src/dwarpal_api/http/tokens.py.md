---
fingerprint: d6456c1341ad490a
---
**Token introspection** (Phase 4) — one endpoint, `POST /v1/tokens/introspect`, for a website's server that would rather ask Dwarpal whether an age token is genuine than check the signature itself. The work is in `app/verification.py`, `introspect`.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5
`Annotated` and `Any`.

@@ 7-8
FastAPI's router and dependency marker; Pydantic's model, settings and field limits.

@@ 10-12
The use cases, the toolbox type, and the gate pieces.

@@ 14
The router: paths under `/v1/tokens`.

@@ 17-20
**`Introspection`** — the body: one field, the token, between 1 and 4,000 characters (an age token is a few hundred).

@@ 23-28
**`introspect`** — any key that may read sessions may ask about its own project's tokens.

@@ 29
Ask the use case, for the caller's project.
