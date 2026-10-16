---
fingerprint: e1eb36812931bba2
---
The **first migration**: it creates all six tables of Phase 1 in an empty database. It describes the same tables as `tables.py`, but as *instructions* ("create this table with these columns") rather than as Python classes.

Why say it twice? `tables.py` describes how the tables should look **now**. Migrations describe **how to get there**, one step at a time, from any older version. When Phase 4 adds a column, `tables.py` simply gains a line, while a new migration says "add this column to the existing table" — and every database, from a developer's laptop to production, follows exactly the same steps. A test checks that the two descriptions agree (see `test_api.py`).

@@ 1-6
The docstring, generated from the blueprint (`script.py.mako`): what this migration does, its ID `0001`, nothing before it, and its date.

@@ 8
The project-wide type-hint setting.

@@ 10
`Sequence`, for the type hints below.

@@ 12-13
SQLAlchemy as `sa`, and Alembic's operations as `op`.

@@ 14
PostgreSQL-only column types: `ARRAY` and `JSONB`.

@@ 16
`revision = "0001"` — this migration's ID. Alembic would normally invent a random one such as `3fa9c2e1b7d4`; short numbers in order are easier for people to follow.

@@ 17
`down_revision = None` — nothing comes before it: this is where the history starts.

@@ 18-19
No branch labels, and no other migrations it depends on.

@@ 21
`TIMESTAMP` — the date-and-time type with a time zone, used for every time column (as in `tables.py`).

@@ 24
**`upgrade`** — create everything.

@@ 25-31
The `projects` table. `sa.Column(name, type, ...)` describes one column:

- `id` — a `uuid` column, and the **primary key**;
- `name` — text of up to 120 characters; `nullable=False` means it may never be empty (`NOT NULL`);
- `allowed_origins` — an array of texts;
- `created_at` — a time.

@@ 32-42
The `api_keys` table. New things to notice:

- `sa.ForeignKey("projects.id", ondelete="CASCADE")` — this column must point at an existing project, and the key is deleted together with its project;
- `unique=True` on `lookup` — the database itself refuses two keys with the same lookup;
- `sa.LargeBinary(32)` — raw bytes, for the 32-byte digest;
- `revoked_at` is the one column that may be empty (`nullable=True`).

@@ 43
An **index** on `api_keys.project_id`, so "all keys of this project" is found without reading the whole table. Its name follows the pattern `ix_<table>_<column>`, the same name SQLAlchemy would give it.

@@ 44-60
The `verification_sessions` table — every column described in `tables.py`, in the same order. `sa.Integer()` is a whole number, for `attempts_count`.

@@ 61
An index on `verification_sessions.project_id`.

@@ 62-73
The `verification_attempts` table. The `session_id` column is split over three lines only because it is long. `postgresql.ARRAY(sa.Text())` stores the reasons as a list of texts, and `postgresql.JSONB()` stores the scores.

@@ 74
An index on `verification_attempts.session_id`.

@@ 75-82
The `signing_keys` table. Its primary key is the text `kid` rather than a UUID, and `private_key_sealed` has no length limit, because a sealed PEM key is longer than a digest.

@@ 83-92
The `issued_tokens` table, with the token's `jti` as its primary key.

@@ 93
An index on `issued_tokens.session_id`.

@@ 96
**`downgrade`** — undo everything: drop the six tables.

@@ 97-104
The order matters. PostgreSQL refuses to drop a table while another table still has a foreign key pointing at it, so the tables that *point* (the **dependents**) go first: tokens, signing keys, attempts, then sessions, API keys, and projects last. (Signing keys point at nothing and nothing points at them, so their place in the list doesn't matter.) The variable's name, `dependents_first`, says why the list is in this order.

@@ 105-106
Drop each table in that order. Dropping a table also drops its indexes.
