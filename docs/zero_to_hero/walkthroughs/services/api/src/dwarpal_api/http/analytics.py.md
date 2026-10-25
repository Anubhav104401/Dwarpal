---
fingerprint: 6b983dc7c5ef5c86
---
The **analytics API** (Phase 4): `GET /v1/analytics/sessions?days=30` — a website's counts of finished checks, for any key that may read sessions.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5
`Annotated` and `Any`.

@@ 7
FastAPI's router, dependency marker and `Query`.

@@ 9-11
The analytics use case, the toolbox type, and the gate pieces.

@@ 13
The router: paths under `/v1/analytics`.

@@ 16-21
**`session_counts`** — needs `sessions:read`; `days` is 30 unless given, and must be 1 to 365.

@@ 22
Read the caller's project's counts, in the caller's mode.
