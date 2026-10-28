---
fingerprint: 2c0d15eedeea161a
---
**Migration 0008** (Phase 5, §5.5.4): a column for console users' recovery codes — as fingerprints only.

@@ 1-10
What the migration adds, and why only fingerprints of the codes are kept.

@@ 12
Newer type-hint syntax on older Pythons.

@@ 14-18
The type for a sequence of names, SQLAlchemy's column types, Alembic's operations, and PostgreSQL's own types (for an array).

@@ 20-23
This migration's ID, the one before it, and no branches or dependencies.

@@ 26-30
**`upgrade`** — add `recovery_digests` to `users`: an **array** of texts (PostgreSQL can keep a list in one column), never empty-valued (`NOT NULL`), and starting as an empty list (`'{}'`, PostgreSQL's way to write one) for everyone already there.

@@ 33-34
**`downgrade`** — remove the column.
