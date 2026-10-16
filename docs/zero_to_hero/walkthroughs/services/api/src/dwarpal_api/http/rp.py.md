---
fingerprint: 97e5d2162b719be5
---
The **relying-party API** — the two endpoints a website's *server* calls. ("Relying party" is the standard name for a service that relies on someone else's check; here, any website that uses Dwarpal.)

| Method and path | What it does |
| :-- | :-- |
| `POST /v1/verification-sessions` | create a session; returns its ID and the link to send the person to |
| `GET /v1/verification-sessions/{id}` | read a session's result, with a freshly signed age token if it is finished |

Both require the website's secret API key. Notice how thin the file is: each endpoint checks its input, calls one use case, and returns the answer. The rules live in `app/verification.py`.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5
`Annotated` (see `deps.py`) and `Any`.

@@ 7
`APIRouter` — a group of endpoints that share a path prefix; `main.py` adds the group to the app. `Depends` marks dependencies.

@@ 8
From Pydantic: `AnyHttpUrl` — a type that only accepts a well-formed `http://` or `https://` address; `BaseModel`, `ConfigDict` and `Field`.

@@ 10-12
The use cases (imported as a module, so calls read `verification.create_session`), the toolbox type, and the two dependencies.

@@ 14
The router: every path in this file starts with `/v1/verification-sessions`. The `v1` is the API's **version**. If a future change ever has to break existing integrations, it goes under `v2`, and websites built against `v1` keep working. `tags` groups these endpoints in the API's automatic documentation.

@@ 17-18
**`CreateSession`** — the shape of the request body, checked by Pydantic before the endpoint runs. `extra="forbid"` refuses unknown fields, so a typo such as `polcy` is reported instead of silently ignored.

@@ 20
`policy` — which policy to check, at most 40 characters. If left out, it is `uk_osa_18`.

@@ 21
`return_url` — where to send the person afterwards. Optional, but if given it must be a real web address; the use case then checks that it belongs to the project.

@@ 22
`external_ref` — the website's own reference, such as an order number: optional, at most 200 characters.

@@ 25
`@router.post("", status_code=201)` makes the function below an endpoint for `POST` on the router's prefix itself (the empty path), answering `201 Created` on success: the standard status for "a new thing now exists".

@@ 26-30
**`create_session`** — FastAPI fills each parameter in by itself:

- `body` — read from the JSON body and checked against `CreateSession`, because its type is a Pydantic model;
- `caller` — the result of `rp_caller`, which checked the API key;
- `svc` — the toolbox.

`-> dict[str, Any]`: the endpoint returns a dict, which FastAPI sends as JSON.

@@ 31
Pydantic keeps the address as a special `Url` object; `str(...)` turns it back into text. No address stays `None`.

@@ 32-34
Call the use case with the caller's project and mode, and the checked values. It returns the new row and the client secret.

@@ 35
Answer with the created view: the ID, the status, the secret and the link.

@@ 38
`GET /v1/verification-sessions/{session_text}` — the part in braces is a **path parameter**: whatever appears there, such as `vs_01JA8XQ2…`, is passed to the function as `session_text`.

@@ 39-43
**`retrieve_session`** — its parameters: the ID from the path, the checked caller, and the toolbox.

@@ 44
Call the use case with the caller's project and mode. It refuses sessions belonging to anyone else, and mints the token.
