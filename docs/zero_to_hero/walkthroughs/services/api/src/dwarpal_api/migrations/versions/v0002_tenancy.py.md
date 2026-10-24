---
fingerprint: ebe1ee08e727dd97
---
The **second migration**, and the heart of Phase 4's first step (§5.4.1). It does two things to a database that already holds Phase 1–3's tables:

1. **Organisations.** It adds the `organizations` table and gives every project an owner, `projects.org_id`;
2. **Row-level security (RLS).** It creates a restricted database role, `dwarpal_app`, for the API to work as, and gives each of the six tenant tables a **policy**: a condition PostgreSQL adds, invisibly, to every query that role runs. The condition compares each row with the **tenant** that the unit of work has named (`db.py`). Rows of other tenants don't fail to match a filter: for that unit of work, they don't exist.

!!! kid "Explain like I'm six — the magic glasses"
    Picture a library where every book has a sticker with its owner's name. Before you walk in, the librarian gives you glasses with your name written on them, and through those glasses you can see only the books with your sticker. Even if you ask for "every book in the library", you get only yours. If you walk in with no name on your glasses, the shelves look empty. The librarian, who owns the library, doesn't wear glasses at all.

    The glasses are the policies, the name on them is the tenant, and the librarian is the tables' owner — who runs migrations and operator tools, never customer requests.

Why bother, when every query in our code already says which project it wants? Because one forgotten `WHERE project_id = …`, in one query, in one future change, would show one customer's data to another. With RLS, that mistake returns nothing instead of someone else's rows (ADR-0011).

@@ 1-10
The docstring: what the migration does, its ID `0002`, the migration it follows (`0001`), its date, and the rules in one paragraph. The API works as `dwarpal_app`, which owns no tables, so the policies bind it. Each unit of work names its tenant first, and with none named it sees nothing. Migrations and operator tools run as the owner, whom the policies don't bind.

@@ 12
The project-wide type-hint setting.

@@ 14
`Sequence`, for the type hints below.

@@ 16-17
SQLAlchemy as `sa` (column types), and Alembic's operations as `op`.

@@ 19-22
This migration's ID, `"0002"`, and the one it follows, `"0001"`. Alembic reads these to put migrations in order: a database at `0001` runs this one next; a new, empty database runs `0001` and then this. No branch labels, no other dependencies.

@@ 24
`TIMESTAMP` — a date and time with a time zone, as in every other table.

@@ 25
`APP_ROLE` — the name of the restricted role, written once.

@@ 26-33
`TENANT_TABLES` — the six tables whose rows belong to a tenant. The downgrade walks through them to take the protection off again. (`signing_keys` isn't one: Dwarpal's signing keys belong to Dwarpal.)

@@ 35-36
The comment that summarises the policies below: each table shows the rows of the tenant the transaction named — one project's rows, or the rows of every project in one organisation. Attempts and tokens follow their verification session, which is already confined.

@@ 37
**`POLICIES`** — one condition per table, written in SQL. A row is visible (and writable) only if its condition is true.

@@ 38
`organizations`: visible if it *is* the named organisation (`app_org()`), or if it owns the named project. `(SELECT org_id FROM projects WHERE id = app_project())` looks up that project's organisation.

@@ 39
`projects`: visible if it is the named project, or belongs to the named organisation.

@@ 40-41
`api_keys` and `verification_sessions`: visible if their project is one of the visible projects. `IN (SELECT id FROM projects)` is a trick worth noticing: that inner query is *itself* filtered by the `projects` policy, so this one short rule inherits every case above, project or organisation, without repeating it.

@@ 42-43
`verification_attempts` and `issued_tokens`: visible if their verification session is visible — the same trick, one level further down.

@@ 44
End of the dictionary.

@@ 46
The comment: the database driver (asyncpg) runs **one** statement per call. The first version of this migration sent all five as one block of text, and the driver refused it ("cannot insert multiple commands into a prepared statement").

@@ 47
**`FUNCTIONS`** — five SQL statements, kept in a tuple and run one by one in `upgrade`.

@@ 48-49
**`app_project()`** — a tiny SQL function: the named project, as a UUID. `current_setting('app.project_id', true)` reads the setting that `db.py` sets; the `true` means "if it was never set, give me nothing instead of an error". `nullif(…, '')` turns the empty text — "no project named" — into SQL's `NULL`. `::uuid` converts the text into a UUID.

`NULL` matters here: in SQL, `id = NULL` is never true, so with no tenant named, **no row matches**. `STABLE` tells PostgreSQL the answer can't change during one statement, so it may ask once rather than once per row.

@@ 50-51
**`app_org()`** — the same, for the named organisation.

@@ 52-53
The comment for the next two functions. They answer questions asked **before** the tenant is known — "whose key is this?" and "whose verification session is this?" — so they must see past the policies. They do it by running as the tables' owner, and they return only what those questions need.

@@ 54-57
**`dwarpal_find_api_key`** — given a key's lookup (its public first part), return five columns of its row: ID, project, mode, the digest of the secret, and when it was revoked. Not the name, not the creation date: nothing beyond what checking a key needs.

- `RETURNS TABLE (…)` — the result has these named columns, like a small table;
- **`SECURITY DEFINER`** — run with the rights of the function's **owner** (whoever ran the migration), not of the caller. That is how the restricted role gets an answer the policies would hide from it;
- `SET search_path = public` — while the function runs, unqualified names like `api_keys` mean `public.api_keys` and nothing else. Without this, a caller who could create a look-alike table elsewhere might trick an owner-rights function into reading it. Pinning the search path is the standard precaution for every `SECURITY DEFINER` function;
- `$$ … $$` — PostgreSQL's way to quote a function body without escaping the quotes inside it.

@@ 58-60
**`dwarpal_session_project`** — given a verification session's ID, return its project's ID, and nothing else. The verify page's requests carry only a flow token for a session (`db.py`'s `NAME_SESSION_TENANT` calls this).

@@ 61
`REVOKE ALL … FROM PUBLIC` — PostgreSQL lets **every** role run a new function unless told otherwise (`PUBLIC` means everyone). Owner-rights functions shouldn't be open to everyone, so that default is taken away. Only `dwarpal_app` gets them back, below.

@@ 62
End of the tuple.

@@ 65
**`upgrade`** — the steps from version `0001` to `0002`.

@@ 66-72
Create `organizations`: an ID (the primary key), a name of up to 120 characters, a unique slug of up to 60, and the creation time. All required (`nullable=False`).

@@ 73
Add `org_id` to `projects` — at first **allowed to be empty** (`nullable=True`). The existing projects have no organisation yet, and a required column can't be added to a table that already has rows without a value for them.

@@ 74-78
**Back-fill**: for every existing project, create an organisation of its own. Reusing the project's ID as the organisation's ID makes the next step trivial. The name is the project's name plus " (organisation)" (`||` joins texts in SQL). The slug is `org-` and the ID's 32 hexadecimal digits, which is unique because the ID is: `replace(id::text, '-', '')` removes the dashes.

@@ 79
Point every project at its new organisation: the one with the same ID.

@@ 80
Now that every project has one, make `org_id` **required**.

@@ 81
The **foreign key**: `projects.org_id` must name an existing organisation, and deleting an organisation deletes its projects (`CASCADE`), which deletes their keys and sessions in turn.

@@ 82
An **index** on `projects.org_id`, so the `projects` policy's "`org_id = app_org()`" doesn't have to read every project.

@@ 84-87
Create the restricted role **if it doesn't exist yet**. Roles belong to the whole database server, not one database, so a second database on the same server (a test database, say) may already have made it. `DO $$ … $$` runs a small anonymous program in PostgreSQL's own language; `pg_roles` lists the server's roles. **`NOLOGIN`**: nobody can connect *as* `dwarpal_app`. A connection logs in as a real login and then becomes it (`SET ROLE`, `db.py`).

@@ 88-89
Allow the login that runs the migrations to **become** the role. A superuser may become any role anyway, but since PostgreSQL 16 an ordinary login that *creates* a role doesn't automatically get to `SET ROLE` to it.

@@ 90-91
Create the five functions, one statement at a time.

@@ 92
`GRANT USAGE ON SCHEMA public` — let the role look inside the `public` schema, the folder our tables live in. Without this it couldn't even name them.

@@ 93
Give the role the four everyday rights on every table: read (`SELECT`), add (`INSERT`), change (`UPDATE`) and remove (`DELETE`). Not the right to alter or drop tables — those stay with the owner. Rights decide **what** it may do with a table; the policies decide **which rows**.

@@ 94
But not on `alembic_version`, Alembic's one-row table that records which migration the database is at. The migration history belongs to migrations alone, so `REVOKE ALL` takes back the rights the line above just gave.

@@ 95
Let the role run the two owner-rights lookup functions.

@@ 96-98
For each tenant table: **turn on** row-level security, then create its policy, named `tenant`, with the table's condition.

`ENABLE ROW LEVEL SECURITY` binds every role except the table's owner (and superusers). ADR-0011 planned `FORCE` as well, which binds the owner too; it was left out on purpose. The two lookup functions run *as the owner*, and with `FORCE` the policies would hide from them the very rows they exist to find. The API works as a role that owns nothing, so `ENABLE` already binds it fully, and the tests prove it.

A policy written with only `USING` applies its condition twice. **Reading**: rows that don't match are invisible to `SELECT`, `UPDATE` and `DELETE`. **Writing**: a new or changed row must match too, or PostgreSQL refuses it with "new row violates row-level security policy". So a tenant can't slip a row into another tenant's project.

@@ 101
**`downgrade`** — the way back, from `0002` to `0001`, in the reverse order.

@@ 102-104
For each tenant table: drop its policy (if it's there) and turn row-level security off.

@@ 105
Drop the four functions. The policies used `app_project()` and `app_org()`, so the policies had to go first.

@@ 106-107
Take the role's rights away again. The role itself is left in place: it belongs to the whole server, and another database there may still use it.

@@ 108-111
Remove the index, the foreign key, the `org_id` column, and finally the `organizations` table: the database is back to version `0001`.
