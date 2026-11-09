## 5.4 Phase 4 — the platform

Phases 1–3 built one honest age check: a website asks, a person looks at the camera, the server decides, and a signed answer goes back. Phase 4 turns that check into a **platform** — something many businesses can use at once, safely, without ever seeing one another's data — following the roadmap (§3.9) and ADR-0011.

| Step | What | Status |
| :-- | :-- | :-- |
| 1 | **Organisations, and row-level security** — the database itself keeps customers apart | ✅ §5.4.1 |
| 2 | People and sign-in — users, passwords (Argon2id), one-time codes, roles | ✅ §5.4.5 |
| 3 | Website features — scoped and rotating keys, versioned policies, idempotency, rate limits, pagination | ✅ §5.4.2 |
| 4 | Events — an outbox and signed webhooks; token introspection | ✅ §5.4.3 |
| 5 | Accountability — a hash-chained audit log, retention, analytics | ✅ §5.4.4 |
| 6 | The contract — a published OpenAPI document, tested automatically | ✅ §5.4.6 |

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

### 5.4.2 What a website's server needs from an API

A real website talks to Dwarpal from its own servers, many times a minute, over networks that sometimes fail. Step 3 adds the five things every serious API gives such callers. None of them changes how a face is checked. They change how safely and predictably a website can use the check.

| Feature | The problem it solves | How |
| :-- | :-- | :-- |
| **Idempotency** | A lost answer makes the website send "create a session" again, and the person gets two | `Idempotency-Key` header: a repeat gets the first answer, sealed in Valkey |
| **Rate limits** | One website (or a stolen key) flooding the API slows it down for everyone | a token bucket per key in Valkey: 100 requests a second, bursts of 200; `429` with `Retry-After` |
| **Pagination** | Listing every session at once grows slower and heavier for ever | `GET /v1/verification-sessions?limit=20&starting_after=…`: pages, newest first, with a cursor |
| **Scoped, rotating keys** | A key that can do everything is dangerous to leak; a key that can't be replaced must stay for ever | scopes (`sessions:read`, `sessions:write`, `policies:write`); `rotate-key` with a grace period; `revoke-key` at once |
| **Versioned policies** | Editing the rules mid-check would change a decision under way, and leave no record of the old rules | `POST /v1/policies` adds `name@version`; versions can't be changed; each session pins its version |

**Idempotency, and a secret in a cache.** The first answer to "create a session" contains the session's one-time client secret. To replay that answer, it must be kept, and anything kept in a cache can leak. Two choices limit the damage. The reply is **sealed** with AES-GCM, under a key derived from the website's own idempotency key and Dwarpal's master key, so a copy of Valkey's memory alone is an unreadable blob (a test looks inside Valkey to prove it). And it is kept only as long as the session lives, 30 minutes, after which the secret inside opens nothing.

!walk services/api/src/dwarpal_api/app/idempotency.py

**Rate limits as a token bucket.** Each key has a bucket of 200 tokens that refills at 100 a second; each request takes one. The whole update runs as one small script *inside* Valkey, timed by Valkey's own clock, so several API servers share one honest count (`adapters/store.py`). The refusal says how long to wait (`Retry-After`), so a well-behaved client slows down instead of hammering.

**Pages with a cursor, not an offset.** "Skip 40, give me 20" breaks when new sessions arrive between pages: everything shifts, and rows repeat. Dwarpal's IDs are UUIDv7s, which begin with the time they were made, so "the 20 sessions older than this one" is a plain comparison, served by an index on `(project_id, id)` (migration `0003`). The list shows summaries only: listing never makes an age token.

**Keys that can be limited, replaced and stopped.** A key now carries **scopes**, and each endpoint asks for the one it needs (`needs("sessions:write")` in `deps.py`): `403 insufficient_scope` otherwise. `rotate-key` makes a replacement and gives the old key a **grace period**, 24 hours by default, so a website can switch every server over with no moment in which neither key works. After it, the old key gets `401 api_key_expired`, a message only its genuine holder can ever see. `revoke-key` stops a leaked key at once.

!walk services/api/src/dwarpal_api/migrations/versions/v0003_keys_and_lists.py

**Policies as versions that never change.** A project can now make its own policy, say `shop_18` with a single attempt. Changing it adds `shop_18@2`, and version 1 stays exactly as it was. A session pins the version it was created with, so a check under way keeps its rules, and every result and token names them (`"policy": "shop_18@1"`). The database enforces it: the API's role may only read and add policy rows, never change or delete them. A new policy is accepted only if the age model has thresholds for its age and risk budget, so no website can choose rules the model was never calibrated for.

!walk services/api/src/dwarpal_api/migrations/versions/v0004_policy_versions.py

!walk services/api/src/dwarpal_api/app/policies.py

!walk services/api/src/dwarpal_api/http/policies.py

The rest of the step changed existing files, each re-explained in its walkthrough: `http/rp.py` (the list endpoint, idempotency and scopes), `http/deps.py` (expiry, the rate limit and `needs`), `app/verification.py` (pinned policies, the summary view and the list), `adapters/store.py` (the bucket script and the claim), `errors.py` and `http/problems.py` (refusals can carry headers), `adapters/tables.py`, `domain/keys.py`, `domain/policy.py`, `settings.py`, `main.py` and `cli.py`.

**What the tests prove** (`test_api.py`, all as the restricted role): a repeat with the same key gets the identical answer, marked `Idempotent-Replayed`; the same key with a different request is refused; Valkey never holds the client secret readably; the third request beyond a burst of two gets `429` with `Retry-After`; five sessions page as 2, 2, 1, newest first, none repeated or missed, with no tokens; a read-only key can't create; a rotated key works during its grace and gets `api_key_expired` after, while a revoked key stops at once; a session keeps `shop_18@1`'s three attempts after `shop_18@2` allows one; and the API's own role is refused when it tries to `UPDATE` or `DELETE` a policy version.

!!! honest "Honest limitation"
    - **A weak idempotency key weakens the seal.** The seal is only as hard to guess as the key the website chose *plus* the master key. Someone holding both a copy of Valkey and the master key could try guessable keys such as `order-1`. Without the master key, the sealed replies are unreadable.
    - ~~**Rate limits are per key only.**~~ The design also asks for per-session and per-address limits on the flow endpoints. Liveness challenges already had per-session, per-device and per-address budgets (§5.3.4). **Since 9 November every flow endpoint also counts against the caller's network address** (`per_address` in `http/flow.py`): the same token bucket, 10 calls a second with bursts of 300 — plenty for many people sharing an address, while a flood from one is refused before it reaches the database. The verify page then says to wait a minute and reload.
    - **No console yet.** Keys are rotated and revoked from the command line, and policies are added through the API. The console of Phase 5 will put both on a page, and step 2 (people and roles) decides who may press those buttons.

### 5.4.3 Telling websites what happened: events and webhooks

Until now a website learned a check's result only by asking (`GET /v1/verification-sessions/{id}`). That works when the person comes back to the website, but people close tabs, phones lose signal, and a website may want to know that a session expired unused. Step 4 lets Dwarpal **tell** the website, by calling an address on the website's own server: a **webhook**.

```
session completes ──► one transaction: outcome + event + one delivery row per endpoint ──► commit
                                                                   │
delivery worker (every 2 s) ── claims due rows (FOR UPDATE SKIP LOCKED), leases them for 60 s
     │
     ├─ checks the address again (public only)
     ├─ POST body = the event, with Dwarpal-Signature: t=<time>,v1=<HMAC-SHA256(secret, "<time>.<body>")>
     └─ 2xx → delivered      otherwise → retry in 1 min, 5 min, 30 min, 2 h, 6 h, 12 h, 24 h → dead (replayable)

website: verifyWebhook(raw body, header, secret) ── fresh (≤ 5 min)? HMAC matches? ──► trust the event
```

!!! key "Key idea — the transactional outbox"
    The event and its deliveries are written **in the same transaction** as the outcome. The database then guarantees what no amount of careful code could: either the outcome and its announcement are both saved, or neither is. A separate **worker** sends the saved deliveries afterwards, retrying for a day if the website is down. Nothing is announced that didn't happen, and nothing that happened goes unannounced.

**Events** are history. The API's role may only read and add them, never change or delete them, so the record of what happened can't be quietly rewritten. An event's data is a summary of the session — never a token.

!walk services/api/src/dwarpal_api/migrations/versions/v0005_events_and_webhooks.py

!walk services/api/src/dwarpal_api/app/webhooks.py

**Sending to an address a customer chose is dangerous.** If anyone could register `http://169.254.169.254/…` or `http://localhost:8001`, Dwarpal would become a tool for reaching inside its own network: **server-side request forgery (SSRF)**. So every address is looked up, and *every* address its name points to must be on the public internet. This is checked when the endpoint is registered, and **again before every delivery**, because a name can be pointed somewhere else later. Redirects are never followed, live webhooks must use `https`, and production can't switch the check off.

!walk services/api/src/dwarpal_api/adapters/webhooks.py

!walk services/api/tests/test_webhooks.py

**The worker** is a separate process (`cli deliver-webhooks`). It works for every project, so, like the other operator tools, it connects as the tables' owner. It claims rows with `SKIP LOCKED` and a one-minute lease, and sends outside any transaction. Several workers can run at once, and any of them can be stopped at any moment, without a webhook being sent twice in normal running or lost.

!walk services/api/src/dwarpal_api/app/delivery.py

!walk services/api/src/dwarpal_api/http/webhooks.py

**Signatures, checked by the website.** Each webhook carries `Dwarpal-Signature: t=<time>,v1=<HMAC>`: an HMAC-SHA256, keyed with the endpoint's secret, of the time and the exact body. Only Dwarpal and the website know the secret. It is shown once, when the endpoint is registered, and stored sealed under the master key. A matching HMAC therefore proves both the sender and the body. The time stops an old webhook being replayed: receivers refuse signatures more than five minutes old. The Node SDK does all of this in one call.

!walk packages/sdk-node/src/webhook.ts

!walk packages/sdk-node/test/webhook.test.ts

**Token introspection.** Some websites would rather not verify signatures at all. `POST /v1/tokens/introspect` checks an age token for them, and answers `{"active": true, …claims}` **once**: the token's record in `issued_tokens` is marked, so a second question, or one about a forged, expired or another website's token, gets only `{"active": false}`. That one-use rule also catches a token being replayed.

!walk services/api/src/dwarpal_api/http/tokens.py

The rest of the step changed existing files, each re-explained in its walkthrough: `adapters/tables.py` (the three tables, `introspected_at`), `adapters/signing.py` (`verify`), `app/verification.py` (`announce` on completion and expiry, `introspect`), `settings.py`, `domain/keys.py` (the `webhooks:write` scope), `main.py`, `cli.py` (`deliver-webhooks`), and the SDK's `errors.ts` and `index.ts`.

**What the tests prove**:
- a completed session reaches an in-memory receiver as one signed `POST`, whose HMAC the test recomputes as a website would, and whose body carries no token;
- a receiver failing eight times is retried after exactly 1 minute, 5, 30, 2 hours, 6, 12 and 24, is then dead, and is delivered after a replay;
- an expired session is announced exactly once;
- the API refuses `127.0.0.1` and unknown event types;
- nine inside-the-network addresses are refused without a database;
- a token is introspected once, and never by another website or for a forger;
- the SDK refuses a changed body, another secret, a stale signature and a malformed header.

!!! honest "Honest limitation"
    - **At least once, not exactly once.** If a worker sends a webhook and dies before recording it, the lease runs out and the webhook is sent again. Every webhook carries `Dwarpal-Event-Id`, so a receiver should ignore an ID it has already handled. This is how every webhook system behaves.
    - ~~**A gap between check and connect.**~~ **Closed 9 Nov.** The address used to be checked, and then the connection looked the name up again, so an attacker controlling a name's records could switch it between the two (**DNS rebinding**). Now `check_url` hands back the addresses it checked, and `send` connects to one of them: the website is still named in the `Host` header and to TLS (its **SNI** name), so the certificate must still be for that name, and the connection is closed after the one request, so it never carries another name's event. Only a failure to connect moves on to the next checked address (at most three); a failure after connecting waits for the retry schedule, since the event may have arrived. Limiting the worker's network to the public internet, which the design also suggested, isn't built — and is no longer the only defence.
    - **Expiry is announced when it is noticed.** Sessions expire lazily, when something reads them, so an `expired` event can come late, or never for a session nobody looks at again. A periodic sweep belongs with the retention jobs of step 5.
    - **The worker isn't yet part of the local stack** that the e2e tests start; it runs from the command line.

### 5.4.4 Accountability: an audit log that can't be quietly changed, and data that doesn't stay for ever

A platform that guards children's access to adult content will one day be asked hard questions. Who changed this website's policy, and when? Was that key revoked before or after the incident? Why is a person's data still here? Step 5 makes such questions answerable, and keeps the system from holding on to what it no longer needs.

**The audit log.** Every change to how a website is protected is recorded, in the same transaction as the change: keys created, rotated and revoked; policy versions added; webhook endpoints registered and removed. Each record names who acted — an API key by its public id, or an operator's tool — and the facts, never a secret. The records form a **hash chain** per organisation: each entry's hash covers the previous entry's hash, so editing or deleting any entry breaks every link after it, and `cli verify-audit` names the first broken one. The API's own role can only add entries, never change them.

!walk services/api/src/dwarpal_api/app/audit.py

**Retention.** Session metadata — statuses, outcomes, attempt scores, events — is personal data about a moment in someone's life, and it is kept only as long as the project's **retention period**: 90 days by default, 1 to 365, a limit the database itself enforces. `cli maintain` then deletes it. The same job sweeps up abandoned sessions, expiring and announcing them, which closes step 4's gap: an `expired` webhook no longer waits for someone to read the session.

!walk services/api/src/dwarpal_api/app/maintenance.py

**Analytics from counts.** When a session finishes, a counter for its project, day, policy and outcome goes up by one, in the same transaction. Counts describe no one, so they outlive the purge, and `GET /v1/analytics/sessions` reads them. Test and live sessions are counted apart.

!walk services/api/src/dwarpal_api/app/analytics.py

!walk services/api/src/dwarpal_api/http/analytics.py

!walk services/api/src/dwarpal_api/migrations/versions/v0006_audit_retention_stats.py

The rest of the step changed existing files, each re-explained in its walkthrough: `adapters/tables.py` (the three tables, `retention_days`), `app/verification.py` (`record_final`: event and count together), `app/policies.py`, `app/webhooks.py` and their HTTP modules (audit entries), `http/deps.py` (`Caller.actor`), `main.py`, and `cli.py` (`maintain`, `verify-audit`, and audit entries for key commands).

**What the tests prove**: four real changes appear in order in the chain, naming the key by its id and never containing it; the chain verifies as intact; the API's role is refused when it tries to change an entry; an owner's edit to entry 2 is reported as broken at entry 2, and deleting the last entry as broken at entry 4; two passed sessions show as `{"pass": 2}` in analytics; an abandoned session is expired and announced by the sweep; with a one-day retention, the purge keeps it after 23 hours and removes it after two days, while its count remains.

!!! honest "Honest limitation"
    - **The chain detects tampering; it doesn't prevent it.** Someone with full control of the database could rewrite an organisation's whole chain consistently. Publishing each day's latest hash outside the database would expose that, and isn't done yet.
    - **The audit log isn't purged yet.** The design keeps it for a year, but removing old entries means the chain must start from a stored anchor rather than from zero; that work comes with the console.
    - **People aren't audited yet,** because there are no people yet: logins, members and roles arrive with step 2.

### 5.4.5 People: accounts, sign-in and roles

Until now only programs used Dwarpal: a website's server with its API key. Step 2 adds **people** — the developers, administrators and analysts at Dwarpal's customers, who will use the web console of Phase 5. (The people whose age is checked are never stored as users; nothing in this section concerns them.)

**Accounts and passwords.** Signing up creates a person, an organisation they **own**, and a first project. Passwords are stored only as **Argon2id** hashes: slow and memory-hungry on purpose (about 50 ms and 64 MiB each), so a stolen table of hashes is useless to anyone trying billions of guesses. Each hash also carries its own random salt.

!walk services/api/src/dwarpal_api/adapters/passwords.py

**Signing in without giving anything away.** A wrong password and an address with no account get exactly the same answer, after exactly the same work: for an unknown address, a decoy hash is checked, so not even timing reveals who has an account. Attempts are limited per account and per network address (5 at once, then one a minute). A successful sign-in creates a **session**: a long random token in an `HttpOnly`, `Secure`, `SameSite` cookie named with the `__Host-` prefix, while its facts live in Valkey for 12 hours from last use.

**One-time codes.** A person can switch on **TOTP** codes from an authenticator app, the six digits that change every 30 seconds. After that, a password alone no longer signs in. Each code works only once: the step of the last code used is remembered.

!walk services/api/src/dwarpal_api/domain/totp.py

**Forged requests.** Because a browser sends a site's cookie with every request to it, even one triggered by another site, every change must also repeat the session's **CSRF token** in a header, and come from one of the console's own origins.

**Roles.** Each person has a role in each organisation they belong to — owner, admin, developer or analyst — and the design's matrix decides what each may do. Every organisation action asks the matrix first; an organisation you don't belong to answers `404`, exactly as if it didn't exist. Row-level security now also knows the signed-in user. Sign-ins, members added, keys created and one-time codes switched on are all written to the audit log.

!walk services/api/src/dwarpal_api/domain/roles.py

!walk services/api/src/dwarpal_api/app/console.py

!walk services/api/src/dwarpal_api/http/console.py

!walk services/api/src/dwarpal_api/migrations/versions/v0007_users_and_members.py

!walk services/api/tests/test_console_rules.py

**What the tests prove**:
- the role matrix, cell by cell, and an unknown role allowed nothing;
- one-time codes matching RFC 6238's own published values, accepted once near their time and never again;
- Argon2id hashes salted, and an unknown account never matching;
- through the API: sign-up, sign-in and sign-out, where a wrong password and an unknown address can't be told apart, and capitals in the address don't matter;
- changes refused without the CSRF token or from another origin;
- codes required once switched on, and a replayed code refused;
- the third sign-in attempt over the limit refused with `429`;
- an analyst refused a key that a developer may create — and that key working on the API;
- a developer refused member management, and an outsider seeing `404`;
- the owner's audit log listing it all, in order, with an intact chain and no key in it.

!!! honest "Honest limitation"
    - **No console pages yet.** These are the API's endpoints; the pages come in Phase 5.
    - **No invitations, password resets or account deletion yet.** All three need e-mail, which Dwarpal doesn't send yet. Members can only be added if they already have an account.
    - **No recovery codes for one-time codes.** Someone who loses their phone needs an operator's help today; recovery codes belong with the console.
    - ~~**The sign-in limit is a rate, not a growing lock-out.**~~ **Built 9 Nov:** the design's **lock-out back-off**. After five wrong passwords or codes in a row for one account from one network address, that address waits before trying the account again: a minute, then twice as long after each further wrong one, at most an hour (`lock_s`). Only that address is locked, so a stranger's guessing can't lock the owner out — and a passkey never asks for the password at all. A right password, or a day without wrong ones, starts the count afresh; an account that doesn't exist locks just the same, so a lock gives nothing away. Asking for the password again (to change it, delete the account, switch codes off or add a passkey) counts the same way. The sign-in page says how long the lock lasts, from the answer's `Retry-After`.

### 5.4.6 The contract: a published document, tested against itself

A website's developers learn the API from its **OpenAPI document**: a machine-readable description of every operation, its inputs, and every answer it may give. FastAPI writes it from the code. Step 6 makes it complete and trustworthy:

- **Every refusal is described.** Every operation now lists the problem statuses it may answer with (`400`, `401`, `403`, `404`, `405`, `409`, `413`, `422`, `429`, `503`), each as `application/problem+json` with the `Problem` shape (`http/problems.py`).
- **Rules are written into the document where they can be.** The idempotency key's pattern, a policy name's pattern and a one-time code's six digits are stated there, so callers know them before they are refused.
- **It is published** as `docs/api/openapi.json` by `cli openapi`, and a test fails whenever the code and the published file disagree.
- **It is tested** by **Schemathesis**, a **contract tester**. It reads the document from the running API, generates 25 requests for each of the 31 operations — valid ones, odd ones, and malformed ones — and checks every answer: never a server error, and always a status, content type, body and headers that the document allows.

!!! real "Real world — the contract test found real bugs"
    On its first run, Schemathesis found that a `405 Method Not Allowed` answer had lost its `Allow` header, which HTTP requires: the problem-details handler threw away the error's headers. Fixing that revealed a second fault, inside Starlette. When `GET` and `POST` on one path are two routes, it names only one route's methods. The handler now gathers them from every route that matches. The same session's migration round-trip caught a third bug: migration `0007`'s downgrade dropped things in an order PostgreSQL refuses. Hand-written tests had covered none of these, because nobody had thought to send a `TRACE` request.

One check is switched off, and the test says why: Schemathesis's "a request the document allows must succeed". Some of the API's rules depend on data rather than shape — whether the age model is calibrated for an age, whether an address is among a project's allowed origins — and refusing such requests with `422` is correct.

The rest of steps 2 and 6 changed existing files, each re-explained in its walkthrough: `adapters/db.py` (the user as tenant, `FIND_USER`), `adapters/store.py` (`fetch`, a sliding expiry), `adapters/tables.py` (`User`, `Membership`), `http/problems.py` (`Problem`, the documented refusals, `Allow`), `http/rp.py` and `http/policies.py` (patterns), `main.py`, `settings.py` (console settings), `cli.py` (`openapi`), the two `pyproject.toml` files (the new packages), `book.toml` (the generated document is left out of the line count), and `test_api.py` (the console, contract and drift tests).
