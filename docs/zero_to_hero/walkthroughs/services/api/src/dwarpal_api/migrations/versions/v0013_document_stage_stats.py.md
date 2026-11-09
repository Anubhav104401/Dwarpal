---
fingerprint: 949085cd0dc31c19
---
**Migration 0013** (9 Nov, §5.5.2): the daily counts behind the dashboard's ID-document figures — how many sessions reached the check, and how those checks ended.

@@ 1-12
What the migration adds, and why: the design's step-up conversion needs to know how many people reached the ID-document check, and how many of those finished it. Like the other counts, these outlive the sessions and name no one.

@@ 14
Newer type-hint syntax on older Pythons.

@@ 16-19
The type for the "revises" line, SQLAlchemy's column types (as `sa`), and Alembic's operations (`op`).

@@ 21-24
Alembic's bookkeeping: this is migration 0013, it comes after 0012, and it belongs to no branch and needs no other migration.

@@ 26
The database role the API runs as, which needs rights on the new table.

@@ 29
**`upgrade`** — moving the database forward.

@@ 30-31
The new table, `document_stage_stats`.

@@ 32-35
Its key, which is every column but the count: the project (removed with it, `CASCADE`), test or live, the day, and the step — `opened`, or how the check ended.

@@ 36-37
How many sessions fall in that cell.

@@ 38
The API may read, add and update counts — never delete them.

@@ 39-40
Row-level security, as on every table: a project's counts are visible only while the database is set to that project's tenant.

@@ 43-44
**`downgrade`** — undoing it: the table goes.
