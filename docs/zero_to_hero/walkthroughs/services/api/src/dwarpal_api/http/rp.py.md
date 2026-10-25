---
fingerprint: 6779615d2b197a78
---
The **relying-party API** — the two endpoints a website's *server* calls. ("Relying party" is the standard name for a service that relies on someone else's check; here, any website that uses Dwarpal.)

| Method and path | Scope | What it does |
| :-- | :-- | :-- |
| `POST /v1/verification-sessions` | `sessions:write` | create a session; returns its ID and the link to send the person to. Accepts an `Idempotency-Key` |
| `GET /v1/verification-sessions` | `sessions:read` | list the project's sessions, newest first, a page at a time (Phase 4) |
| `GET /v1/verification-sessions/{id}` | `sessions:read` | read a session's result, with a freshly signed age token if it is finished |

All three require the website's secret API key, with the scope shown. Notice how thin the file is: each endpoint checks its input, calls one use case, and returns the answer. The rules live in `app/verification.py`.

@@ 1-2
The docstring: websites create sessions, list them and read their results, with their secret key.

@@ 4
The project-wide type-hint setting.

@@ 6
`Annotated` (see `deps.py`) and `Any`.

@@ 8
From FastAPI: `APIRouter` — a group of endpoints that share a path prefix; `main.py` adds the group to the app. `Depends` marks dependencies; `Header` and `Query` read a parameter from a request header or from the address's query (`?limit=20`); `Response` lets an endpoint add headers to its answer.

@@ 9
From Pydantic: `AnyHttpUrl` — a type that only accepts a well-formed `http://` or `https://` address; `BaseModel`, `ConfigDict` and `Field`.

@@ 11-13
The use cases and the idempotency helper (imported as modules, so calls read `verification.create_session` and `idempotency.once`), the toolbox type, the `Caller` type, the scope gate `needs`, and the toolbox dependency.

@@ 15
The router: every path in this file starts with `/v1/verification-sessions`. The `v1` is the API's **version**. If a future change ever has to break existing integrations, it goes under `v2`, and websites built against `v1` keep working. `tags` groups these endpoints in the API's automatic documentation.

@@ 18-19
**`CreateSession`** — the shape of the request body, checked by Pydantic before the endpoint runs. `extra="forbid"` refuses unknown fields, so a typo such as `polcy` is reported instead of silently ignored.

@@ 21
`policy` — which policy to check: a preset's name, or the name of one of the project's own policies (`/v1/policies`), at most 40 characters. If left out, it is `uk_osa_18`.

@@ 22
`return_url` — where to send the person afterwards. Optional, but if given it must be a real web address; the use case then checks that it belongs to the project.

@@ 23
`external_ref` — the website's own reference, such as an order number: optional, at most 200 characters.

@@ 26
`@router.post("", status_code=201)` makes the function below an endpoint for `POST` on the router's prefix itself (the empty path), answering `201 Created` on success: the standard status for "a new thing now exists".

@@ 27-33
**`create_session`** — FastAPI fills each parameter in by itself:

- `body` — read from the JSON body and checked against `CreateSession`, because its type is a Pydantic model;
- `response` — the response being prepared, so the endpoint can add a header to it;
- `caller` — the result of `needs("sessions:write")`: the API key was checked, and it may create sessions;
- `svc` — the toolbox;
- `idempotency_key` — the request's `Idempotency-Key` header, if it has one. FastAPI turns the underscore into a dash and ignores capitals when it looks for the header.

`-> dict[str, Any]`: the endpoint returns a dict, which FastAPI sends as JSON.

@@ 34
**`make`** — the work itself, written as a small function *inside* the endpoint so that it can be run directly, or handed to the idempotency helper to run at most once.

@@ 35
Pydantic keeps the address as a special `Url` object; `str(...)` turns it back into text. No address stays `None`.

@@ 36-38
Call the use case with the caller's project and mode, and the checked values. It returns the new row and the client secret.

@@ 39
The answer: the created view — the ID, the status, the secret and the link.

@@ 41-42
Without an `Idempotency-Key`, just do the work: every such request makes a new session.

@@ 43-45
With one, prepare the idempotency helper's inputs. The **scope** keeps one website's keys apart from another's, and test mode apart from live mode: two websites that happen to choose the same key never meet. The **fingerprint** is a digest of what is being asked (`app/idempotency.py`).

The comment records a choice. A stored reply contains the session's client secret, so it is kept only as long as the session itself lives (`session_ttl_s`, 30 minutes): after that the secret opens nothing.

@@ 46-48
Run `make` at most once for this key: the first time it really runs; a repeat gets the first reply back.

@@ 49-51
A repeated answer is marked with the header `Idempotent-Replayed: true`, so a website's logs can tell a replay from a new session. Then answer.

@@ 54-60
**`list_sessions`** — `GET` on the prefix itself: one page of the project's sessions (Phase 4). It needs the `sessions:read` scope, and takes two optional query parameters:

- `limit` — how many sessions per page: 20 if not given, never fewer than 1 or more than `MAX_PAGE` (100). `Query(ge=1, le=…)` makes FastAPI refuse anything else with `422`;
- `starting_after` — the **cursor**: the ID of the last session on the previous page. The next page starts after it.

@@ 61
Call the use case with the caller's project and mode.

@@ 64
`GET /v1/verification-sessions/{session_text}` — the part in braces is a **path parameter**: whatever appears there, such as `vs_01JA8XQ2…`, is passed to the function as `session_text`.

@@ 65-69
**`retrieve_session`** — its parameters: the ID from the path, the caller (whose key must have `sessions:read`), and the toolbox.

@@ 70
Call the use case with the caller's project and mode. It refuses sessions belonging to anyone else, and mints the token.
