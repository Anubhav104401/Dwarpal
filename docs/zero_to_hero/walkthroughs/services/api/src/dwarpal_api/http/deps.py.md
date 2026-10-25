---
fingerprint: 9facfd6e766de8cf
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

@@ 5
`math`, for rounding a wait up to whole seconds.

@@ 6-9
`uuid`, `Awaitable` and `Callable` (to describe the function that `needs` returns), `dataclass`, and from `typing`: `Annotated` (attach extra information to a type, explained below) and `cast` (explained at line 28).

@@ 11
From FastAPI: `Depends` (mark a parameter as a dependency), `Header` (read a parameter from a request header) and `Request`.

@@ 13-17
The key look-up statement and `name_tenant` (`db.py`, Phase 4), the `Project` table, the toolbox and ID parser, the key helpers, and our error class.

@@ 20-25
**`Caller`** — who a website caller is: its project, whether it used a live or a test key, the key's lookup (its public ID) and the key's scopes. Read-only once made.

@@ 27-30
**`actor`** — how the audit log names this caller: an API key, by its public lookup (never the key itself). `@property` makes it read like a field: `caller.actor`.

@@ 33-34
**`services`** — the dependency that hands an endpoint the toolbox, which `main.py` stored on the app at start-up. `request.app.state` can hold anything, so the type checker only knows it as `Any`. `cast(Services, …)` tells it "trust me, this is a `Services`" — it changes nothing when the program runs.

@@ 37-39
**`bearer`** — take the credential out of an `Authorization` header. `partition(" ")` splits `"Bearer abc"` into `"Bearer"`, `" "` and `"abc"`. If the scheme (compared in lowercase, because HTTP says scheme names are case-insensitive) is `bearer`, return the credential without surrounding spaces; otherwise return empty text. A missing header (`None`) becomes empty text through `or ""`.

@@ 42-44
**`rp_caller`** — the gate for websites. Its two parameters show the **`Annotated`** style:

- `svc: Annotated[Services, Depends(services)]` — "a `Services`, obtained by running the `services` dependency";
- `authorization: Annotated[str | None, Header()] = None` — "text from the request header of the same name (`Authorization`), or `None` if there isn't one".

@@ 45-48
Take the credential out, and check its *shape*. Not shaped like one of our keys? Refuse at once with `401`, and say what a correct header looks like — before any database work.

@@ 49
The key's mode (live or test) and its lookup.

@@ 50-51
Find the key's row by its lookup. A unit of work with no tenant named can't see any key under row-level security, so the statement `FIND_API_KEY` asks the database function `dwarpal_find_api_key` instead (migration `v0002_tenancy.py`). `.one_or_none()` gives the single matching row, or `None` if there is none. The row's columns are read by name below: `key.revoked_at`, `key.secret_digest`, …

@@ 52-53
Refuse if there is no such key, if it was revoked, or if its mode doesn't match the prefix that was sent.

@@ 54-55
Refuse if the full key doesn't match the stored digest (a constant-time comparison, `domain/keys.py`).

Notice that every refusal above gives the **same** answer. Whether the lookup was unknown or only the last character of the key was wrong, the caller learns exactly the same thing: "unknown or revoked". Different answers would help an attacker learn which parts of a guess were right.

@@ 56-58
A **rotated** key that has passed its grace period gets its own refusal, `api_key_expired`, which tells the website what to do: use the replacement. It comes only *after* the full key matched, so only the key's real holder learns that it existed.

@@ 59-60
The key is genuine, so the caller's tenant is now known: **name it** for the rest of this unit of work. From this line on, the database shows only the key's own project.

@@ 61
Load the key's project — now visible, because it *is* the tenant.

@@ 62-63
A key without a project can't happen while the database's foreign key holds (deleting a project deletes its keys). Checking anyway costs nothing, and turns a theoretical bug into a refusal rather than a crash.

@@ 64-68
**The rate limit.** Take a token from this key's bucket (`adapters/store.py`). If none is left, refuse with `429 rate_limited` and a `Retry-After` header: the wait, rounded **up** to whole seconds (`math.ceil`), so a client that waits as told will find a token.

@@ 69
The caller is known: return it, with the key's scopes as a `frozenset` — a set that can't be changed.

@@ 72-73
**`needs`** — a function that *makes* a dependency: `needs("sessions:write")` returns a gate that admits only keys with that scope. Writing `Depends(needs("sessions:write"))` on an endpoint reads almost like a sentence.

@@ 75-78
The gate it returns: run `rp_caller` first (every check above), then refuse with `403 insufficient_scope` if the key lacks the scope. `403` means "I know who you are, and you may not do this", unlike `401`, "I don't know who you are".

@@ 80
Hand the gate back.

@@ 83-87
**`flow_session`** — the gate for the verify page. Its parameters: the session ID from the request's **path** (`session_text`, FastAPI fills it in by name), the toolbox, and the `Authorization` header.

@@ 88
If there is a bearer token, ask Valkey which session it belongs to; if not, there is no session. (`x if condition else y` picks one of two values.)

@@ 89-90
Refuse unless the token is valid **and** belongs to the very session named in the path. A token for session A can never be used to act on session B. The message tells the page how to recover: start the flow again.

@@ 91
Return the session's ID to the endpoint.
