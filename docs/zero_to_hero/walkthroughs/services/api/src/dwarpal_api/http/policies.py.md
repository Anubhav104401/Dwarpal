---
fingerprint: 0f7ef08fc4c671f8
---
The **policies API** (Phase 4) — two endpoints for a website's server:

| Method and path | Scope | What it does |
| :-- | :-- | :-- |
| `GET /v1/policies` | `sessions:read` | list the presets and every version of the project's own policies |
| `POST /v1/policies` | `policies:write` | add the next version of one of the project's own policies |

Like `rp.py`, the file is thin: it checks the input's shape and calls the use cases in `app/policies.py`.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5
`Annotated` and `Any`.

@@ 7-8
FastAPI's router and dependency marker; Pydantic's model, settings and field limits.

@@ 10-13
The policy use cases, the toolbox type, the `Policy` type, and the gate pieces from `deps.py`.

@@ 15
The router: every path here starts with `/v1/policies`.

@@ 18-19
**`NewVersion`** — the body of `POST /v1/policies`. Unknown fields are refused.

@@ 21
`name` — 3 to 40 characters (the use case checks the exact shape).

@@ 22
`min_age` — between 13 and 25. Whether the age model can actually serve that age is checked by the use case, against the manifest.

@@ 23
`risk_budget` — how often, at most, a minor may wrongly pass: above 0 and at most 10 % (`le=0.1`), 2 % if not given.

@@ 24
`max_face_attempts` — 1 to 5, 3 if not given.

@@ 25
`token_ttl_s` — how long the age token lasts: one minute to one hour, 10 minutes if not given.

@@ 28-32
**`list_policies`** — `GET`, for any key that may read sessions: list everything the project can choose from.

@@ 35-40
**`add_version`** — `POST`, answering `201 Created`; it needs the `policies:write` scope.

@@ 41
The draft: the requested rules as a `Policy` (its version is filled in by the use case).

@@ 42-45
Add it, in the caller's project, with the time and a new ID from the toolbox, the project's organisation and the caller as the audit log's actor; answer with the new version.
