---
fingerprint: d8c3a2685340085d
---
**Alembic** is the tool that changes the database's tables, step by step, in a recorded order (§4.10). Every step is a **migration**: a small Python file in `versions/` that says how to go *up* to the new layout and *down* again. Alembic remembers, inside the database itself, which migrations have already been applied, so running "upgrade to the latest" twice does nothing the second time.

This file, `env.py`, is Alembic's **entry point**: Alembic runs it every time a migration command runs. Its job is to connect to the right database and hand over the connection.

@@ 1
The docstring: connect, and apply the migrations, using the API's own settings.

@@ 3
The project-wide type-hint setting.

@@ 5
`asyncio` — Python's built-in engine for `async` code (§4.8). Our database driver is async, so we need it to run anything at all.

@@ 7
`context` — Alembic's handle on the *current run*: its settings, whether it is "online" or "offline", and the methods to configure and run migrations.

@@ 8-9
The type of a database connection, and the function that creates an async engine (`db.py`).

@@ 11-12
The catalogue of our tables (`tables.py`) and the API's settings. Using the same `Settings` as the API means migrations always go to the same database the API uses — there is no second configuration to keep in step.

@@ 15
**`run_migrations`** — the part that actually changes tables. It receives an open connection.

@@ 16
Tell Alembic which connection to use, and what the tables *should* look like (`METADATA`). `compare_type=True` makes Alembic's comparisons also notice a column whose *type* changed — say, `String(16)` to `String(40)` — not just added or removed columns. The project's drift test relies on that (see `test_api.py`).

@@ 17-18
Run every migration that hasn't been applied yet, inside one **transaction**: if any step fails, PostgreSQL undoes all of them, so the database is never left half-migrated. `with` makes sure the transaction is finished — committed or rolled back — whatever happens.

@@ 21
**`run_online`** — connect to a real database, then migrate it.

@@ 22
Which database? If whoever started Alembic passed an address (the tests and `cli.py` do), use that; otherwise use the API's normal setting. `or` picks the first value that isn't empty.

@@ 23
Create an engine for that address.

@@ 24
Open one connection. `async with` closes it again at the end, even after an error.

@@ 25
Alembic's own code is **synchronous** (ordinary, non-async functions), but our connection is async. `run_sync` bridges the two: it runs `run_migrations` with a connection that behaves like a normal one, while SQLAlchemy keeps it async underneath.

@@ 26
Close the engine's pool. A migration is a one-off job, so nothing should be left running.

@@ 29-30
Alembic also has an **offline** mode that writes SQL scripts for someone to run by hand, without connecting. We refuse it with a clear message: scripts made that way can't run our checks, and every migration in this project is applied by the tools, against a real database. `SystemExit` ends the program with that message.

@@ 31
Otherwise — the normal case — run `run_online` to completion. `asyncio.run` starts the async engine, runs the function, and shuts the engine down again.
