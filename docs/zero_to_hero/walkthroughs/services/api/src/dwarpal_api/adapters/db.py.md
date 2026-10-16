---
fingerprint: 9f639bd3c6fae0e9
---
The API's connection to **PostgreSQL**, the database that remembers everything that must survive a restart: projects, keys, sessions, attempts, signing keys (§0.12, §4.10). The file is short because SQLAlchemy does the heavy lifting; these lines choose *how* it behaves.

Two ideas are needed:

- an **engine** owns a **connection pool**. Opening a new database connection is slow: the two programs must greet each other and check the password. So the engine keeps a few connections open and lends them out, like a library lending books, instead of building a new one for every request;
- a **session factory** makes **sessions** — SQLAlchemy's word for one **unit of work**: a conversation with the database that ends in a single **commit** (save everything) or **rollback** (save nothing).

!!! warn "Careful — two kinds of 'session'"
    This project uses the word *session* for two different things. A **verification session** is one person's age check (`VerificationSession`, `domain/sessions.py`). A **database session** is a unit of work with PostgreSQL. In the code, database sessions are always called `session`, and verification sessions are `row`, `session_id` or `VerificationSession`.

@@ 1
The docstring: an async engine (a pool of connections) and a factory for units of work.

@@ 3
The project-wide type-hint setting.

@@ 5
SQLAlchemy's **asyncio** pieces: the engine and session types, and the functions that make them. "Async" means a request waiting for the database doesn't block other requests (§4.8).

@@ 6
`DeclarativeBase` — the base class for describing tables as Python classes (`tables.py`).

@@ 9-10
`Base` — our project's own base class for tables. Every table class inherits from it, and SQLAlchemy collects them all into one catalogue, `Base.metadata`. Migrations and tests use that catalogue to compare the code with the real database (§4.10).

@@ 13
**`make_engine`** — create the engine for a database URL (see `settings.py`).

@@ 14
`create_async_engine` with three choices:

- `pool_pre_ping=True` — before lending out a connection, check it still works. Databases restart and networks drop idle connections; without the check, the first request after such a hiccup would fail;
- `pool_size=10` — keep up to 10 connections open;
- `max_overflow=10` — at busy moments, open up to 10 more, temporary ones. So at most 20 connections exist at once, which protects PostgreSQL from being flooded.

@@ 17
**`make_sessions`** — create the factory that makes database sessions. Its return type, `async_sessionmaker[AsyncSession]`, reads "a session maker that makes `AsyncSession`s".

@@ 18
`expire_on_commit=False` — after a commit, keep the values already loaded in Python objects. By default SQLAlchemy marks them as stale, and re-reads them from the database on next use. In async code, that hidden re-read would need an `await` where none is written, and fail. The use cases read a few values (such as the new status) right after committing, so this setting matters.
