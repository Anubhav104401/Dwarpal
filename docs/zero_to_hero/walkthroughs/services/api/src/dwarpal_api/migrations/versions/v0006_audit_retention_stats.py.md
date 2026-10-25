---
fingerprint: a605e823f1fc1acd
---
The **sixth migration** (Phase 4, §5.4.4): the audit log and its heads, the daily counts, and each project's retention period. The new tables follow the recipe of migration `0004` — rights, row-level security, policy — and the audit log, like events, may only be read and added to by the API.

@@ 1-10
The docstring: what the migration adds, its ID `0006`, the one it follows, its date, and how the chain and the retention work.

@@ 12
The project-wide type-hint setting.

@@ 14
`Sequence`, for the type hints below.

@@ 16-18
SQLAlchemy as `sa`, Alembic's operations as `op`, and PostgreSQL's `JSONB`.

@@ 20-23
This migration's ID, `0006`, and the one before it, `0005`.

@@ 25-27
The restricted role's name; the timestamp type; and the rule for tables kept per organisation: rows of organisations the tenant can see.

@@ 28
**`RIGHTS`** — for each new table, the API role's rights and its row rule:

@@ 29
the audit log: **read and add only** — the API can never change or delete an entry;

@@ 30
the heads: read, add and update (each append moves its organisation's head along);

@@ 31
the counts: read, add and update (each finished session adds one), per project.

@@ 32
End of the dictionary.

@@ 35
**`upgrade`**.

@@ 36-41
`audit_heads`: one row per organisation, with the number and hash of its latest entry.

@@ 42-54
`audit_log`: keyed by organisation and number; who, what, to what, the facts, the previous hash and its own, and when.

@@ 55-63
`session_stats`: keyed by project, mode, day, policy and outcome; the count.

@@ 64-67
For each new table: the rights, row-level security, and the policy.

@@ 68-69
Every project gets `retention_days`, 90 for existing ones; then the default is dropped, so the code always says.

@@ 70
A **check constraint**: the database itself refuses a retention outside 1 to 365 days.

@@ 71-72
An index on sessions' creation time, for the purge.

@@ 75
**`downgrade`** — the way back.

@@ 76-81
Drop the index, the constraint and the column, then the three tables.
