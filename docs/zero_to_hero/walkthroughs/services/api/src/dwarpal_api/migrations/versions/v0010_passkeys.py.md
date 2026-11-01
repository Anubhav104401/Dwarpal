---
fingerprint: 3233769ab111f5b9
---
Migration **0010** (Phase 9, §5.9.2): the passkeys table.

@@ 1-10
The migration's docstring: what it adds — a table of passkeys, holding only public keys — and why a passkey is found through a special function.

@@ 12-17
The project-wide type-hint setting, the type for a list of revisions, SQLAlchemy's column types, and Alembic's operations.

@@ 19-22
Revision `0010` comes after `0009`.

@@ 24-25
The application's database role (which the policies bind), and a timestamp type with a time zone.

@@ 27-34
**`dwarpal_find_passkey`** — signing in with a passkey happens before anyone is named, so row-level security would hide every passkey. Like `dwarpal_find_user` (migration `0007`), this function runs with its owner's rights (`SECURITY DEFINER`) and returns only what checking a signature needs: the passkey's ID, its owner, its public key and its counter. Only the application's role may call it.

@@ 37-48
**The `passkeys` table**: an ID; the owner (deleted with their account: `CASCADE`); the device's ID for the passkey, unique — a passkey belongs to one account; the public key; the counter; the person's name for it; and when it was added and last used.

@@ 49-50
Create the function.

@@ 51-53
The application may read, add, change and remove passkeys — but, under the policy, **only the signed-in person's own** (`user_id = app_user()`).

@@ 56-58
Undo: the table first (its policy goes with it), then the function.
