---
fingerprint: d5142cdfeaef7f88
---
Migration **0011** (Phase 9, §5.9.3): the Age Pass's two columns.

@@ 1-10
The migration's docstring: the policy's switch, and the one thing a session notes about passes — when it gave them out.

@@ 12-17
The project-wide type-hint setting, the type for a list of revisions, SQLAlchemy's column types, and Alembic's operations.

@@ 19-22
Revision `0011` comes after `0010`.

@@ 25-27
Add `accept_age_pass` to policies — false for every existing version, so nothing changes until a website opts in — and `age_pass_issued_at` to sessions, empty.

@@ 30-32
Undo: drop both columns.
