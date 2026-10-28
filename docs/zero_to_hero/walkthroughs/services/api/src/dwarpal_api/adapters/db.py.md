---
fingerprint: d4f71b5e17c1f25d
---
The API's connection to **PostgreSQL**, the database that remembers everything that must survive a restart: projects, keys, sessions, attempts, signing keys (§0.12, §4.10). The file is short because SQLAlchemy does the heavy lifting; these lines choose *how* it behaves.

Two ideas are needed:

- an **engine** owns a **connection pool**. Opening a new database connection is slow: the two programs must greet each other and check the password. So the engine keeps a few connections open and lends them out, like a library lending books, instead of building a new one for every request;
- a **session factory** makes **sessions** — SQLAlchemy's word for one **unit of work**: a conversation with the database that ends in a single **commit** (save everything) or **rollback** (save nothing).

!!! warn "Careful — two kinds of 'session'"
    This project uses the word *session* for two different things. A **verification session** is one person's age check (`VerificationSession`, `domain/sessions.py`). A **database session** is a unit of work with PostgreSQL. In the code, database sessions are always called `session`, and verification sessions are `row`, `session_id` or `VerificationSession`.

Phase 4 adds a third idea, the **tenant** (§5.4.1). Every customer of Dwarpal is a tenant, and the database itself, not only our code, keeps their rows apart. A unit of work first *names* its tenant; from then until it commits, PostgreSQL shows it that tenant's rows and nothing else.

@@ 1-2
The docstring: an async engine (a pool of connections), a factory for units of work, and the tenant each unit of work is confined to.

@@ 4
The project-wide type-hint setting.

@@ 6-10
Standard-library tools: `re` (patterns, to check a role name), `uuid` (the type of our IDs), `AsyncIterator` and `asynccontextmanager` (to write the `tenant` helpers as `async with` blocks, explained at line 62), and `Any`, for the database driver's own connection objects, which carry no type hints.

@@ 12
From SQLAlchemy: `event`, which runs our code when something happens (here: a new connection opens), and `text`, which wraps a piece of raw SQL so it can be sent with named parameters such as `:project`.

@@ 13
SQLAlchemy's **asyncio** pieces: the engine and session types, and the functions that make them. "Async" means a request waiting for the database doesn't block other requests (§4.8).

@@ 14
`DeclarativeBase` — the base class for describing tables as Python classes (`tables.py`).

@@ 16
`ROLE_NAME` — what a PostgreSQL role name may look like: a lower-case letter or `_`, then up to 62 more letters, digits or `_`. The role name ends up *inside* a SQL statement (line 43), where parameters can't go, so it is checked against this pattern first. A setting such as `dwarpal_app; DROP TABLE projects` is refused before it reaches the database.

@@ 17-21
**`NAME_TENANT`** — the statement that names the tenant. `set_config(name, value, true)` stores a value under a name for this connection; PostgreSQL calls these **settings** (or GUCs). Ours are `app.project_id`, `app.org_id` and, since the console (step 2), `app.user_id`; the policies in the migrations read them back.

The final `true` is the important part: *only until this transaction ends*. When the unit of work commits or rolls back, the names are forgotten, so the next transaction on the same pooled connection starts with no tenant, and sees nothing, rather than inheriting the last customer's view. The values arrive as parameters (`:project`, `:org`, `:user`), never pasted into the SQL.

@@ 22-25
**`NAME_SESSION_TENANT`** — the same, for the verify page. A browser in the middle of an age check holds only a flow token, which names a *verification session*, not a project. So the statement asks the function `dwarpal_session_project` (made by the migration) which project owns that session, and names it in one step. `coalesce(…, '')` turns "no such session" into an empty name, which matches no tenant: the unit of work then sees nothing, and the code answers 404.

@@ 26-27
**`FIND_USER`** — signing in to the console happens before anyone is named, just like checking an API key. The account is found by e-mail address through `dwarpal_find_user` (migration `0007`), which returns only what checking a password and a one-time code needs.

@@ 28-31
**`FIND_API_KEY`** — reading an API key happens *before* the tenant is known: the key is what tells us who the caller is. Under row-level security, a unit of work with no tenant can't see any key. So the key is read through `dwarpal_find_api_key`, a function the migration lets see every key but return only the five columns that checking a key needs.

Since migration `0003`, it also returns the key's scopes and its expiry.

@@ 34-35
`Base` — our project's own base class for tables. Every table class inherits from it, and SQLAlchemy collects them all into one catalogue, `Base.metadata`. Migrations and tests use that catalogue to compare the code with the real database (§4.10).

@@ 38
**`make_engine`** — create the engine for a database URL (see `settings.py`). The new, optional `role` names the restricted database role every connection should become. The API passes `dwarpal_app`; the command-line tools pass nothing, and keep the full rights of the login that owns the tables (they run migrations and reports).

@@ 39
`create_async_engine` with three choices:

- `pool_pre_ping=True` — before lending out a connection, check it still works. Databases restart and networks drop idle connections; without the check, the first request after such a hiccup would fail;
- `pool_size=10` — keep up to 10 connections open;
- `max_overflow=10` — at busy moments, open up to 10 more, temporary ones. So at most 20 connections exist at once, which protects PostgreSQL from being flooded.

@@ 40-42
If a role was asked for, check its name against `ROLE_NAME` first, and stop with an error if it doesn't fit.

@@ 44-45
`@event.listens_for(engine.sync_engine, "connect")` — run the function below **each time the pool opens a new connection**, before anyone uses it. (`sync_engine` is the engine's inner, non-async core, where SQLAlchemy's events live.) Because it happens once per connection, not once per request, it costs nothing on the busy path.

@@ 46-53
**`become_role`** — `SET ROLE dwarpal_app` switches the connection from the login that owns the tables to the restricted role. Row-level security doesn't bind a table's owner, but it binds every other role, so from this moment every query this connection runs is filtered by the policies.

The `autocommit` lines matter, and the tests caught it: the database driver quietly opens a transaction around any statement, and the pool's next **rollback** would undo the `SET ROLE` with it. The connection would silently go back to being the owner, and the policies would stop applying. With `autocommit` on, the statement runs outside any transaction, so nothing can roll it back; then the normal behaviour is switched back on.

PostgreSQL can't take a role's name as a query parameter, so it is written into the SQL text — which Semgrep flags as possible **SQL injection** (Phase 7). Here the name comes from the server's own settings, and `make_engine` has already refused anything but a plain name (`ROLE_NAME`); the `nosemgrep` comment records that this was reviewed.

@@ 55
Hand back the engine.

@@ 58
**`make_sessions`** — create the factory that makes database sessions. Its return type, `async_sessionmaker[AsyncSession]`, reads "a session maker that makes `AsyncSession`s".

@@ 59
`expire_on_commit=False` — after a commit, keep the values already loaded in Python objects. By default SQLAlchemy marks them as stale, and re-reads them from the database on next use. In async code, that hidden re-read would need an `await` where none is written, and fail. The use cases read a few values (such as the new status) right after committing, so this setting matters.

@@ 62-67
**`name_tenant`** — name the tenant inside a unit of work that is already open: one project, or one organisation, and for the console also the signed-in user.

@@ 68-69
Its docstring.

@@ 70-74
Turn each ID into text (an absent one becomes the empty text `""`, which the policies read as "none"), and run `NAME_TENANT` with them. The dictionary is built from three name-and-value pairs in one line, a **comprehension**.

@@ 77-83
**`tenant`** — the helper almost every use case calls. `@asynccontextmanager` turns a function with one `yield` into something usable with `async with`: the code before `yield` runs on entry, the caller's block runs at the `yield`, and the rest runs on exit, even after an error. It takes the session factory and the tenant — a project, an organisation, and for the console a user — and gives the caller a database session.

@@ 84-85
Its docstring.

@@ 86-88
Open a database session, name the tenant as its **very first** statement, and hand the session to the caller. When the caller's block ends, the outer `async with` closes the session. A use case can't forget to name its tenant, because it never gets a session that hasn't named one.

@@ 91-94
**`session_tenant`** — the verify page's version: given a verification session's ID instead of a project.

@@ 95-96
Its docstring, including the case of an unknown session: the unit of work is confined to nothing.

@@ 97-99
Open a session, run `NAME_SESSION_TENANT` with the verification session's ID as its first statement, and hand it over.
