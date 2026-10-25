---
fingerprint: 850be1bc2e208611
---
The **third migration** (Phase 4, §5.4.2): API keys gain **scopes** and an **expiry**, and verification sessions gain an index for the paginated list. Because the key look-up function from migration `0002` must now also return the scopes and the expiry, it is replaced.

@@ 1-9
The docstring: what the migration does, its ID `0003`, the one it follows, its date, and why the look-up function is replaced.

@@ 11
The project-wide type-hint setting.

@@ 13
`Sequence`, for the type hints below.

@@ 15-17
SQLAlchemy as `sa`, Alembic's operations as `op`, and PostgreSQL's `ARRAY` type.

@@ 19-22
This migration's ID, `0003`, and the one before it, `0002`; no branches or other dependencies.

@@ 24
The restricted role's name.

@@ 25
`EVERY_SCOPE` — PostgreSQL's way of writing a text array: braces around comma-separated values. These are the two scopes that existed when the migration was written.

@@ 26-30
**`FIND_KEY`** — the look-up function's definition, as a template with two gaps: `{extra}` for more result columns, and `{columns}` for more selected columns. The same template makes both the new version (with the gaps filled) and, in the downgrade, the old one (with them empty), so the two can't drift apart. Everything else is as in migration `0002`: owner's rights, a pinned search path.

@@ 33-37
**`replace_find_key`** — a function's result columns can't be changed in place, so drop it and create it again from the template. A fresh function is open to everyone by default, so take that away again, and give the API's role back the right to call it.

@@ 40
**`upgrade`**.

@@ 41-43
Add `scopes` to every key. Existing keys get both scopes, so nothing that worked before stops working (`server_default` fills the existing rows). Then the default is removed: from now on, whoever makes a key must say what it may do, rather than inherit a default by accident.

@@ 44
Add `expires_at`, empty for every existing key: none has been rotated yet.

@@ 45
The index over `(project_id, id)` for listing a project's sessions newest first.

@@ 46
Replace the look-up function with one that also returns the scopes and the expiry.

@@ 49
**`downgrade`** — the way back, in reverse order.

@@ 50
Put back the old function, with the gaps empty.

@@ 51-53
Drop the index and the two columns.
