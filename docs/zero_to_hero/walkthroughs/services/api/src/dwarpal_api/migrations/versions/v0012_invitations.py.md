---
fingerprint: 6b2a4b1fb562270d
---
**Migration 0012: invitations** (decision D44, 8 Nov 2026).

@@ 1-10
The migration's docstring: invitations (decision D44) — someone without an account is invited by address, and joins on signing up. No e-mail is sent (D25). Since signing up happens before any organisation is named, the invitations are taken through a function the policies don't bind.

@@ 12
The project-wide type-hint setting.

@@ 14-17
Types, SQLAlchemy and Alembic.

@@ 19-22
This migration is number 0012, after 0011.

@@ 24-25
The application's database role, and the type of a moment.

@@ 27-32
**`dwarpal_take_invitations`** — every invitation for an address, deleted and returned in one statement (`DELETE … RETURNING`), so none can be taken twice. `SECURITY DEFINER` runs it with its owner's rights, unbound by the policies; `search_path` is fixed so nothing can slip a different `invitations` table in front.

@@ 33-35
Only the application's role may call it.

@@ 38-49
**The `invitations` table**: an ID, the organisation (deleted with it), the address, the role (the same four as memberships), who invited (an account), when — and one invitation per address in an organisation.

@@ 50
Indexed by address: sign-up looks invitations up that way.

@@ 51-52
The function.

@@ 53
The application may read, make and delete invitations — never change one.

@@ 54-56
Row-level security: an organisation sees only its own invitations.

@@ 59-61
Undoing it: the table, then the function.
