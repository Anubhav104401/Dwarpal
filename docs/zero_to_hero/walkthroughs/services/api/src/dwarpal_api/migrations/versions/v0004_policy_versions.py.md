---
fingerprint: 8e5579c68ae74893
---
The **fourth migration** (Phase 4, §5.4.2): the `policies` table, which holds the versions of each project's own policies, and the column with which each session **pins** the version it follows.

It is the first table made after row-level security arrived, so it shows the full recipe every new tenant table needs: create it, **grant** the API's role exactly the rights it needs, **enable** row-level security, and add the `tenant` **policy**. A test fails if a table is ever made without the last two (`test_every_table_but_dwarpals_own_has_row_level_security`).

@@ 1-10
The docstring: what the migration does, its ID `0004`, the one it follows, its date, and the two rules it serves — a session keeps its policy version, and versions can't be changed.

@@ 12
The project-wide type-hint setting.

@@ 14
`Sequence`, for the type hints below.

@@ 16-17
SQLAlchemy as `sa`, and Alembic's operations as `op`.

@@ 19-22
This migration's ID, `0004`, and the one before it, `0003`.

@@ 24
The restricted role's name.

@@ 27
**`upgrade`**.

@@ 28-29
Create the table `policies`, with these columns:

@@ 30-31
An ID, and the project that owns the version (deleting a project deletes its policies).

@@ 32-33
The policy's name and the version's number.

@@ 34-37
The four rules: the age, the risk budget, the attempts, the token's lifetime.

@@ 38
When the version was made.

@@ 39-40
No project may have two versions with the same number for the same name.

@@ 41
The rights: `SELECT` and `INSERT` **only**. With no `UPDATE` or `DELETE`, the database itself refuses to change or remove a version, whatever our code does: this is how "versions never change" is enforced, not just promised.

@@ 42-43
Row-level security, with the same rule as the other per-project tables: rows of visible projects only.

@@ 44-47
Add `policy_version` to every session. Every existing session followed a preset, so the existing rows get `0`.

@@ 48
Then drop the default: new sessions must always say which version they follow.

@@ 51
**`downgrade`** — the way back.

@@ 52-53
Drop the column, then the table.
