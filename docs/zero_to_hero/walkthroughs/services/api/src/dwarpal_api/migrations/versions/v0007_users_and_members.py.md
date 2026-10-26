---
fingerprint: d301303439928a4e
---
The **seventh migration** (Phase 4, §5.4.5): **people**. `users` holds the people at Dwarpal's customers who sign in to the console, and `memberships` their roles in organisations. Row-level security now knows a third name, the signed-in **user**: a user sees their own row, their own memberships, the organisations they belong to, and the people who share those organisations with them.

@@ 1-10
The docstring: what the migration adds, its ID `0007`, the one it follows, its date, and the rule that users are never the people whose age is checked.

@@ 12
The project-wide type-hint setting.

@@ 14
`Sequence`, for the type hints below.

@@ 16-17
SQLAlchemy as `sa`, and Alembic's operations as `op`.

@@ 19-22
This migration's ID, `0007`, and the one before it, `0006`.

@@ 24-25
The restricted role's name, and the timestamp type.

@@ 26
The organisations rule as it was before this migration, kept so the downgrade can put it back.

@@ 27-28
The new rule: as before, **or** an organisation the named user belongs to. (`memberships` shows a user only their own rows, so this subquery lists exactly their organisations. The `noqa` tells the linter that this SQL is built from fixed text, not from anything a user typed.)

@@ 30
**`FUNCTIONS`** — four statements, run one by one:

@@ 31-32
**`app_user()`** — the named user, like `app_project()` and `app_org()`.

@@ 33-37
**`dwarpal_find_user`** — signing in happens before anyone is named, so the account is found by address through a function that runs as the tables' owner, like the API-key look-up. It returns only the ID, the password hash and the sealed one-time-code secret.

@@ 38-39
Open it to nobody, then to the API's role alone.

@@ 40
End of the tuple.

@@ 43
**`upgrade`**.

@@ 44-54
Create `users`: an ID, a unique address, the password's Argon2id hash, the sealed one-time-code secret and a pending one, the last code's step, and when the account was made and last signed in.

@@ 55-62
Create `memberships`: the organisation and the user together as the key (each deleted with its parent), the role — which a check constraint limits to the four — and when it was given.

@@ 63
Index memberships by user, for "which organisations does this person belong to?".

@@ 64-65
Create the functions.

@@ 66-67
The API's rights: read, add and change users (never delete — accounts are closed deliberately, later), and all four on memberships.

@@ 68-69
Row-level security on both tables.

@@ 70-71
A membership is visible if it is yours, or belongs to the named organisation.

@@ 72-73
A user is visible if it is you, or appears in a visible membership — someone in the named organisation.

@@ 74-75
Replace the organisations rule with the new one.

@@ 78
**`downgrade`** — the way back.

@@ 79-80
Put the old organisations rule back.

@@ 81-86
Then, in an order the database accepts: the users rule reads `memberships`, and `memberships` points at `users`, so the rule goes first, then the two tables (with the memberships rule), and only then the functions those rules used. The migration round-trip test found that the first version of this downgrade had the order wrong.
