---
fingerprint: 3463869991d2e23a
---
**Who is calling?** Before an endpoint's own code runs, the API must know who sent the request, and refuse strangers. FastAPI handles this with **dependencies**: small functions that an endpoint lists among its parameters. FastAPI runs them first and passes in their results. If a dependency raises an error, the endpoint never runs.

!!! kid "Explain like I'm six — the ticket check"
    At a theme park, the ticket is checked at the gate, not on every ride. Dependencies are the gate: an endpoint written as "this ride needs a valid ticket" can be sure that, by the time it runs, someone already checked.

There are two kinds of caller, and two gates:

| Caller | Proves itself with | Dependency |
| :-- | :-- | :-- |
| a website's server | its API key: `Authorization: Bearer dk_test_…` | `rp_caller` |
| the verify page in a person's browser | a flow token: `Authorization: Bearer <token>` | `flow_session` |

`Bearer` is the standard way to send a token in HTTP: "whoever bears (carries) this token may do this".

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-7
`uuid`, `dataclass`, and from `typing`: `Annotated` (attach extra information to a type, explained below) and `cast` (explained at line 25).

@@ 9
From FastAPI: `Depends` (mark a parameter as a dependency), `Header` (read a parameter from a request header) and `Request`.

@@ 11-15
The key look-up statement and `name_tenant` (`db.py`, Phase 4), the `Project` table, the toolbox and ID parser, the key helpers, and our error class.

@@ 18-21
**`Caller`** — who a website caller is: its project, and whether it used a live or a test key. Read-only once made.

@@ 24-25
**`services`** — the dependency that hands an endpoint the toolbox, which `main.py` stored on the app at start-up. `request.app.state` can hold anything, so the type checker only knows it as `Any`. `cast(Services, …)` tells it "trust me, this is a `Services`" — it changes nothing when the program runs.

@@ 28-30
**`bearer`** — take the credential out of an `Authorization` header. `partition(" ")` splits `"Bearer abc"` into `"Bearer"`, `" "` and `"abc"`. If the scheme (compared in lowercase, because HTTP says scheme names are case-insensitive) is `bearer`, return the credential without surrounding spaces; otherwise return empty text. A missing header (`None`) becomes empty text through `or ""`.

@@ 33-35
**`rp_caller`** — the gate for websites. Its two parameters show the **`Annotated`** style:

- `svc: Annotated[Services, Depends(services)]` — "a `Services`, obtained by running the `services` dependency";
- `authorization: Annotated[str | None, Header()] = None` — "text from the request header of the same name (`Authorization`), or `None` if there isn't one".

@@ 36-39
Take the credential out, and check its *shape*. Not shaped like one of our keys? Refuse at once with `401`, and say what a correct header looks like — before any database work.

@@ 40
The key's mode (live or test) and its lookup.

@@ 41-42
Find the key's row by its lookup. A unit of work with no tenant named can't see any key under row-level security, so the statement `FIND_API_KEY` asks the database function `dwarpal_find_api_key` instead (migration `v0002_tenancy.py`). `.one_or_none()` gives the single matching row, or `None` if there is none. The row's columns are read by name below: `key.revoked_at`, `key.secret_digest`, …

@@ 43-44
Refuse if there is no such key, if it was revoked, or if its mode doesn't match the prefix that was sent.

@@ 45-46
Refuse if the full key doesn't match the stored digest (a constant-time comparison, `domain/keys.py`).

Notice that every refusal above gives the **same** answer. Whether the lookup was unknown or only the last character of the key was wrong, the caller learns exactly the same thing: "unknown or revoked". Different answers would help an attacker learn which parts of a guess were right.

@@ 47-48
The key is genuine, so the caller's tenant is now known: **name it** for the rest of this unit of work. From this line on, the database shows only the key's own project.

@@ 49
Load the key's project — now visible, because it *is* the tenant.

@@ 50-51
A key without a project can't happen while the database's foreign key holds (deleting a project deletes its keys). Checking anyway costs nothing, and turns a theoretical bug into a refusal rather than a crash.

@@ 52
The caller is known: return it.

@@ 55-59
**`flow_session`** — the gate for the verify page. Its parameters: the session ID from the request's **path** (`session_text`, FastAPI fills it in by name), the toolbox, and the `Authorization` header.

@@ 60
If there is a bearer token, ask Valkey which session it belongs to; if not, there is no session. (`x if condition else y` picks one of two values.)

@@ 61-62
Refuse unless the token is valid **and** belongs to the very session named in the path. A token for session A can never be used to act on session B. The message tells the page how to recover: start the flow again.

@@ 63
Return the session's ID to the endpoint.
