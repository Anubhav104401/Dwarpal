## 5.4 Phase 4 — the platform

Phases 1–3 built one honest age check: a website asks, a person looks at the camera, the server decides, and a signed answer goes back. Phase 4 turns that check into a **platform** — something many businesses can use at once, safely, without ever seeing one another's data — following the roadmap (§3.9) and ADR-0011.

| Step | What | Status |
| :-- | :-- | :-- |
| 1 | **Organisations, and row-level security** — the database itself keeps customers apart | ✅ §5.4.1 |
| 2 | People and sign-in — users, passwords (Argon2id), one-time codes, roles | 🗓 |
| 3 | Website features — scoped and rotating keys, versioned policies, idempotency, rate limits, pagination | 🗓 |
| 4 | Events — an outbox and signed webhooks | 🗓 |
| 5 | Accountability — a hash-chained audit log, retention, analytics | 🗓 |
| 6 | The contract — a published OpenAPI document, tested automatically | 🗓 |

### 5.4.1 Tenants, and a database that keeps them apart

Until now, Dwarpal had **projects**: one per website, each with its own API keys and verification sessions. Phase 4 puts an **organisation** above them, the customer that signs up. One business with a wine shop and a forum is one organisation with two projects.

```
organisation  "Amber Cellars Ltd"
   ├── project  "Amber Cellars"   (the shop)   ── API keys, verification sessions ── attempts, issued tokens
   └── project  "Amber Forum"                   ── API keys, verification sessions ── …
organisation  "Another Business"
   └── project  …
```

Each organisation, or project, is a **tenant**: a customer whose rows must never be seen by another. The code always asked for the right rows — `WHERE project_id = …` — but a promise kept by every query is only as strong as the one query that forgets. ADR-0011 chose to make the **database** keep the promise too, with **row-level security** (RLS).

!!! key "Key idea — three locks, each enough on its own to stop a leak"
    1. **A restricted role.** The API works as `dwarpal_app`, a database role that owns no tables. PostgreSQL applies row-level security to every role except a table's owner, so it applies to the API, always.
    2. **A named tenant.** Every unit of work names its tenant as its very first statement, for that transaction only. A unit of work that names none sees **nothing**: an empty answer rather than everyone's rows.
    3. **Policies.** Each of the six tenant tables has a condition that PostgreSQL adds to every query by itself: *this row belongs to the named tenant*. A row of another tenant can't be read, changed, deleted, or written in its place.

    Our own `WHERE project_id = …` checks stay too, as a fourth lock.

**How a request finds its tenant.** There are three ways in, and each names its tenant before reading anything else:

| Who is asking | How the tenant is found | Code |
| :-- | :-- | :-- |
| A website's server, with its API key | The key is looked up through `dwarpal_find_api_key`, a function allowed to see every key but return only what checking one needs. The genuine key's project becomes the tenant | `http/deps.py` |
| The verify page, with a flow token | The token names a verification session; `dwarpal_session_project` says which project owns it, and that project becomes the tenant in the same statement | `adapters/db.py`, `app/verification.py` |
| An operator, at the command line (migrations, `seed-dev`, `liveness-report`) | No tenant: these tools work as the tables' owner, whom the policies don't bind, because their job spans customers | `cli.py` |

The two look-up functions are deliberate, narrow doors. They run with the owner's rights (**`SECURITY DEFINER`**), because they answer questions asked *before* the tenant is known: "whose key is this?" and "whose session is this?". Each returns only the few values its question needs, and only `dwarpal_app` may call them.

!walk services/api/src/dwarpal_api/migrations/versions/v0002_tenancy.py

The rest of this step changed existing files, each re-explained in its own walkthrough:

- `adapters/db.py` — the engine becomes the restricted role on every new connection, and the helpers `tenant` and `session_tenant` give the use cases database sessions that have already named their tenant;
- `adapters/tables.py` — the `Organization` table and `Project.org_id`;
- `app/verification.py` — every use case opens its database session through one of those helpers;
- `http/deps.py` — the website's key is checked through the look-up function, and then its project is named;
- `settings.py` and `main.py` — the API's role, `dwarpal_app` by default;
- `cli.py` — `seed-dev` creates an organisation for the demo project.

**What the tests prove.** Every API test now runs as the restricted role, so the whole of Phases 1–3 is checked again under RLS. Four new tests aim at isolation itself (`services/api/tests/test_api.py`):

| Test | Proves |
| :-- | :-- |
| Each tenant sees only its own rows, and no tenant sees nothing | with no tenant named, all six tables look empty; project a1 sees its own sessions and organisation; organisation A sees its two projects and not B's; the connection is still the restricted role after a rollback |
| A tenant can't write another tenant's rows or switch the policies off | adding a session to b1 while named as a1 is refused by the database; updating b1's sessions changes nothing; after a commit the tenant is forgotten; `DISABLE ROW LEVEL SECURITY` is refused ("must be owner") |
| One website's key can't read another website's session | through the real API: `404 session_not_found`, exactly as if the session didn't exist |
| Every table but Dwarpal's own has row-level security | the only unprotected tables are `alembic_version` and `signing_keys`, so a future table can't be added without a policy, or a deliberate decision that it holds no customer's data |

!!! real "Real world — the test that failed first"
    The first run of these tests **failed**: the restricted role could see everything. The cause was subtle. The database driver quietly wraps every statement in a transaction, including the `SET ROLE` sent when a connection opens. The connection pool rolls back each connection when it's returned, and a rollback undoes `SET ROLE`. So every connection silently became the owner again after its first use, and the owner isn't bound by policies. The fix is SQLAlchemy's documented recipe, to run the `SET ROLE` with `autocommit` on (`db.py`). The first test now also asks the database "who am I?" after a rollback, so this can't quietly come back.

    This is why ADR-0011 insists that isolation be **tested directly**. Every other test passed during the bug, because the code's own `WHERE` clauses were still doing their job. Only a test that tried to cross the line showed that the second lock wasn't there.

!!! try "Try it yourself"
    With the local stack running and migrated, open a database shell (`docker compose -f infra/compose/compose.yaml exec postgres psql -U dwarpal`) and type:

    ```sql
    SELECT count(*) FROM projects;   -- as the owner: every project
    SELECT id FROM projects LIMIT 1; -- copy one project's ID
    SET ROLE dwarpal_app;            -- now work as the API does
    SELECT count(*) FROM projects;   -- no tenant named: 0
    BEGIN;
    SELECT set_config('app.project_id', 'paste-the-id-here', true);
    SELECT count(*) FROM projects;   -- one project named: 1
    COMMIT;
    SELECT count(*) FROM projects;   -- that transaction is over: 0 again
    RESET ROLE;                      -- back to the owner
    ```

    The `0` after `SET ROLE` is the whole idea in one number.

!!! honest "Honest limitation"
    - **One login, two roles.** For now the API logs in as the same database user that owns the tables, and switches to `dwarpal_app` with `SET ROLE`. A query that an attacker could fully control (SQL injection, which our code avoids by always sending values as parameters) could switch back with `RESET ROLE`. Production should log in as a separate user that *is* only a member of `dwarpal_app`, with `DWARPAL_DATABASE_ROLE` left empty. That belongs to the deployment work of Phase 7.
    - **`ENABLE`, not `FORCE`.** ADR-0011 planned `FORCE ROW LEVEL SECURITY`, which binds even the owner. It is left off because the two look-up functions run as the owner and must see past the policies. The API never works as the owner, so its protection is the same, and ADR-0011 now records the change.
    - **Policies cost a little.** The attempts and tokens policies look through sessions, which look through projects. That is quick at today's sizes. If one project grows to millions of sessions, the attempts table may need its own `project_id` column so the check can use an index directly.
    - **Signing keys aren't tenant data.** The restricted role can read Dwarpal's sealed signing keys, because signing tokens is its job. They are protected by the master key (§5.1.3), not by RLS.
