---
fingerprint: e6e0d2d38fbc7cbd
---
The **blueprint** for every new migration file. When a developer runs Alembic's `revision` command, Alembic fills in this template and saves the result in `versions/`. The language is **Mako**: ordinary text with `${...}` **placeholders**, each replaced by the value of the Python expression inside it.

Keeping our own blueprint means every future migration starts out matching the project's rules — type hints that pass `mypy --strict`, and the project's import style — without anyone having to remember them.

@@ 1
The new file's docstring begins with `${message}`: the short description the developer typed, such as "add webhooks table".

@@ 3
`Revision ID:` — this migration's own name.

@@ 4
`Revises:` — the migration it comes after. `| comma,n` passes the value through two **filters**: `comma` (provided by Alembic) joins several parents with commas, for the rare migration that merges two branches; `n` switches off Mako's default text filters.

@@ 5
`Created:` — when the file was generated.

@@ 6
The docstring ends.

@@ 8
The project-wide type-hint setting.

@@ 10
`Sequence` — used in the type hints below, for values that may be a list of revisions.

@@ 12-13
The two imports every migration needs: SQLAlchemy (as the short name `sa`) for column types, and Alembic's `op` — the operations, such as `op.create_table` and `op.drop_table`.

@@ 14
Any extra imports Alembic decides the migration needs — for example, PostgreSQL-only types. `if imports else ""` writes nothing when there are none.

@@ 16-19
Four variables that Alembic reads to place the migration in its history. `repr(...)` writes each value as Python source code — a text in quotes, or `None`. The type hints say what each may hold:

- `revision` — this migration's ID;
- `down_revision` — the one before it (`None` for the very first);
- `branch_labels` — optional names for a line of history;
- `depends_on` — other migrations that must run first.

@@ 22-23
**`upgrade`** — the steps that move the database *forward*. Alembic can generate a first draft by comparing the tables in the code with the real database; a developer always reviews it. If there are no steps, the body is `pass` ("do nothing"), because a Python function can't be empty.

@@ 26-27
**`downgrade`** — the steps that move the database *back*, undoing `upgrade`.
