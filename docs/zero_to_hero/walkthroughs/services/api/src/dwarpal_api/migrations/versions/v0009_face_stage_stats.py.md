---
fingerprint: 20733097e5e8d548
---
**Migration 0009** (Phase 7, §5.5.2): when a person began, and the daily counts behind the dashboard's face-check figures.

@@ 1-11
What the migration adds: a start time on each session, and a table of counts that — like `session_stats` — outlives the sessions and names no one.

@@ 13
Newer type-hint syntax on older Pythons.

@@ 15-18
The type for the "revises" line, SQLAlchemy's column types (as `sa`), and Alembic's operations (`op`).

@@ 20-23
Alembic's bookkeeping: this is migration 0009, it comes after 0008, and it belongs to no branch and needs no other migration.

@@ 25
The database role the API runs as, which needs rights on the new table.

@@ 28
**`upgrade`** — moving the database forward.

@@ 29
A new column on sessions, `started_at`: when the person opened the verify page. It may be empty — for sessions nobody has opened, and for those made before this migration.

@@ 30-31
The new table, `face_stage_stats`.

@@ 32-36
Its key, which is every column but the count: the project (removed with it, `CASCADE`), test or live, the day, the face check's decision, and the band of time it took — named by where the band starts, in seconds (`domain/timing.py`). A small integer is enough for that.

@@ 37-38
How many face checks fall in that cell.

@@ 39
The API may read, add and update counts — never delete them.

@@ 40-41
Row-level security, as on every table: a project's counts are visible only while the database is set to that project's tenant.

@@ 44-46
**`downgrade`** — undoing it: the table, then the column.
