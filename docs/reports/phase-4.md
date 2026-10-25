# Phase 4 report — the platform

**Dates:** from 24 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Decision record:** [ADR-0011](../adr/0011-postgresql-rls-and-valkey.md) (amended 24 Oct) · **Status:** 🟡 steps 1, 3, 4 and 5 of 6 built and tested locally (step 2 waits for approval to add `argon2-cffi`; step 6 for `schemathesis`).

**Goal (from the roadmap):** turn the single age check into a platform many businesses can use at once: organisations and people, safe keys and policies, events, an audit trail, and a published contract. **Exit:** contract and integration suites green; **RLS isolation tests green**; audit-chain verification green.

## Steps

| Step | Scope | Status |
| :-- | :-- | :-- |
| 1 | Organisations; row-level security on every tenant table, with isolation tests | ✅ 24 Oct |
| 2 | Users (Argon2id), TOTP, members and roles, console sessions, CSRF | 🗓 (needs approval to add `argon2-cffi`) |
| 3 | Scoped and rotating keys, versioned policies, idempotency, rate limits, cursor pagination | ✅ 25 Oct |
| 4 | Events, outbox, webhook worker (HMAC, retries, SSRF guard), token introspection | ✅ 25 Oct |
| 5 | Hash-chained audit log and its verifier, retention purge, analytics | ✅ 25 Oct |
| 6 | Published OpenAPI document, Schemathesis contract tests | 🗓 (needs approval to add `schemathesis`) |

## Step 1 — organisations and row-level security

| Area | Delivered |
| :-- | :-- |
| Schema | `organizations` (id, name, unique slug, created_at); `projects.org_id` (required, foreign key with cascade, indexed). Migration `0002` back-fills one organisation per existing project, and has a tested downgrade |
| Role | `dwarpal_app`: `NOLOGIN`, owns no tables, may read and write rows of every table except `alembic_version`. The API's engine runs `SET ROLE dwarpal_app` on each new connection, in autocommit so a rollback can't undo it (`DWARPAL_DATABASE_ROLE`, default `dwarpal_app`). Migrations and the CLI stay the owner |
| Tenant | Each unit of work names its tenant first: `set_config('app.project_id' / 'app.org_id', …, true)`, for one transaction only. `tenant(sessions, project_id | org_id)` and `session_tenant(sessions, session_id)` in `adapters/db.py`; every database session in `app/verification.py` opens through one of them |
| Policies | `ENABLE ROW LEVEL SECURITY` + policy `tenant` on all six tenant tables: organisations, projects (by project or organisation), api_keys and verification_sessions (via visible projects), verification_attempts and issued_tokens (via visible sessions). `USING` only, so it also checks writes |
| Pre-tenant look-ups | `dwarpal_find_api_key(lookup)` (five columns) and `dwarpal_session_project(id)`: `SECURITY DEFINER`, `search_path` pinned, `EXECUTE` revoked from `PUBLIC` and granted to `dwarpal_app` only |
| Book | §5.4 and §5.4.1; the migration walked through; db, tables, settings, main, deps, verification, cli and the API tests re-explained; five glossary terms; strict build 161 files, 10,493/10,493 lines |

### What was measured

| Check | Result |
| :-- | :-- |
| Python lint, format, mypy (strict) | clean (81 files) |
| Python tests | **177 passed** (116 + 61 ML), incl. 4 new isolation tests; **all 21 API tests now run as `dwarpal_app`** |
| Isolation | no tenant → 0 rows in all six tables; project a1 sees only a1; organisation A sees a1 and a2, not b1; writing a b1 session as a1 → refused by PostgreSQL; updating b1 as a1 → 0 rows; tenant forgotten after commit; `DISABLE ROW LEVEL SECURITY` → "must be owner"; still `dwarpal_app` after a rollback; another website's key → `404`; every table except `alembic_version` and `signing_keys` has RLS |
| Migration | upgrade → downgrade → upgrade on a fresh PostgreSQL 18.6: clean |
| JS lint, typecheck, unit tests | clean; 30 passed |
| End-to-end | **4 passed** (main story ~41 s), through the restricted role |
| Local database | migrated to `0002`: 19 organisations back-filled, 0 projects without one, 99 Phase 3 attempts intact; as `dwarpal_app` with no tenant, 0 visible |

## Step 3 — what a website's server needs

| Area | Delivered |
| :-- | :-- |
| Idempotency | `Idempotency-Key` on `POST /v1/verification-sessions` (8–255 printable characters). First request claims a Valkey slot atomically (`SET NX GET`); repeats get the identical reply with `Idempotent-Replayed: true`; same key + different body → `422 idempotency_key_reused`; still running → `409`; a failed request releases the key. Replies sealed with AES-GCM under a key derived (HMAC) from the idempotency key and the master key; slot names are derived too; kept for the session's lifetime (30 min) |
| Rate limits | Token bucket per API key, one Lua script in Valkey timed by Valkey's clock: 100 req/s, burst 200 (design §3.7); `429 rate_limited` with `Retry-After`. Refusals can now carry headers (`ApiError.headers`) |
| Pagination | `GET /v1/verification-sessions?limit=1..100&starting_after=vs_…`, newest first by UUIDv7, `has_more` and `next_cursor`; index `(project_id, id)`; summaries only — listing never mints a token |
| Keys | `api_keys.scopes` (`sessions:read`, `sessions:write`, `policies:write`; existing keys got the first two) and `expires_at`; `needs(scope)` gate → `403 insufficient_scope`; `cli rotate-key --lookup <id> [--grace-hours 24]` (replacement with the same scopes; old key ends after the grace, never later than an earlier end) and `cli revoke-key`; an expired key gets `401 api_key_expired`, only after its full secret matched. Look-up function replaced (migration `0003`) |
| Policies | `policies` table (migration `0004`): immutable versions per project and name — the API role has only `SELECT, INSERT`; RLS policy as for other per-project tables. `POST /v1/policies` adds the next version (name 3–40 chars, not a preset's; only ages and risk budgets the model has thresholds for); `GET /v1/policies` lists presets and versions. Sessions pin `policy_version` (0 = preset); every use case reads the pinned version; results and tokens name it (`shop_18@2`) |
| Book | §5.4.2; five new walkthroughs (idempotency, policies use cases and API, migrations 0003 and 0004); 14 changed files re-explained; six glossary terms; strict build 166 files, 11,094/11,094 lines |

### What was measured

| Check | Result |
| :-- | :-- |
| Python lint, format, mypy (strict) | clean (86 files) |
| Python tests | **184 passed** (123 + 61 ML); 28 API tests, 7 of them new for step 3 |
| Idempotency | identical replay with the header; key reuse refused; short key refused; no key → separate sessions; Valkey holds no readable client secret |
| Rate limit | burst 2 → `200, 200, 429`, `Retry-After ≥ 1` |
| Pagination | 5 sessions → pages of 2, 2, 1, newest first, none repeated or missed, no tokens; `limit=101` → `422` |
| Keys | read-only key can't create (`403`); rotated key works during grace, `api_key_expired` after; revoked key `401` at once |
| Policies | `shop_18@1` session keeps 3 attempts after `shop_18@2` (1 attempt) exists; preset name, uncalibrated age and unknown policy refused; `UPDATE` / `DELETE` of a version as the API role → "permission denied" |
| Migrations | 0001 → 0004 → 0001 → 0004 → 0002 on a fresh PostgreSQL 18.6: clean |
| End-to-end | **4 passed** |

## Step 4 — events, webhooks and introspection

| Area | Delivered |
| :-- | :-- |
| Schema (migration `0005`) | `webhook_endpoints` (sealed secret, events, enabled; full rights), `events` (**SELECT, INSERT only**), `webhook_deliveries` (SELECT, INSERT, UPDATE; partial index on due pending rows); all with RLS; `issued_tokens.introspected_at` |
| Events | `verification_session.completed` and `.expired`, plus `webhook_endpoint.test`; written by `emit` in the same transaction as the change, with one delivery per subscribed, enabled endpoint (transactional outbox); data is the session summary, never a token |
| Endpoints API | `POST/GET /v1/webhook-endpoints`, `DELETE …/{id}`, `POST …/{id}/test`, `GET …/{id}/deliveries`, `POST /v1/webhook-deliveries/{id}/replay`; scope `webhooks:write`; at most 16 per project; secret `whsec_…` shown once, sealed with AES-GCM under the master key with the endpoint ID as associated data |
| SSRF guard | http(s) only, https in live mode, no credentials in the URL; every resolved address must be global and not multicast (IPv4-mapped IPv6 unwrapped); checked at creation **and before each delivery**; redirects never followed; `DWARPAL_WEBHOOK_ALLOW_PRIVATE` for development only, refused in production |
| Delivery worker | `cli deliver-webhooks [--once]`, as the owner: claims due rows `FOR UPDATE SKIP LOCKED`, 60 s lease, sends outside transactions; `Dwarpal-Signature: t=…,v1=HMAC-SHA256(secret, "t.body")`, `Dwarpal-Event-Id`; retries at 1 min, 5 min, 30 min, 2 h, 6 h, 12 h, 24 h, then `dead` |
| Introspection | `POST /v1/tokens/introspect` (scope `sessions:read`): signature (`KeyRing.verify`), issuer, audience = caller's project, expiry, and one use (`introspected_at`, row lock); anything else `{"active": false}` with no reason |
| SDK | `verifyWebhook(rawBody, header, secret)` in `@dwarpal/node`: format, ±5-minute freshness, constant-time HMAC check; `WebhookSignatureError` |
| Book | §5.4.3; nine new walkthroughs; ten changed files re-explained; six glossary terms; strict build 175 files, 11,972/11,972 lines |

### What was measured

| Check | Result |
| :-- | :-- |
| Python lint, format, mypy (strict) | clean (93 files) |
| Python tests | **205 passed** (144 + 61 ML): 16 new database-free webhook tests, 5 new database tests |
| JS | lint and typecheck clean; **35 passed** (web 16, SDK 16, shop 3) |
| Delivery | one signed POST per completed session; HMAC recomputed by the test as a receiver would; no token in the body; recorded `delivered, 1, 200` |
| Retries | eight `500`s → waits of exactly 60, 300, 1800, 7200, 21,600, 43,200, 86,400 s, then `dead`; replay → delivered |
| Expiry | announced exactly once across two reads |
| SSRF | 127.0.0.1, localhost, 10/8, 192.168/16, 169.254.169.254, ::1, ::ffff:10.0.0.1, fc00::/7, 0.0.0.0 refused; API refuses 127.0.0.1 |
| Introspection | first genuine → active; second, forged, other website's → `{"active": false}` |
| Migrations | 0001 → 0005 → 0001 → 0005 → 0002 on a fresh PostgreSQL 18.6: clean |
| End-to-end | **4 passed** |

## Step 5 — accountability

| Area | Delivered |
| :-- | :-- |
| Audit log (migration `0006`) | `audit_log` (per-organisation `seq`; **SELECT, INSERT only** for the API role) and `audit_heads`; `hash_n = SHA-256(hash_n−1 ‖ canonical JSON)`; appends inside the business transaction under a lock on the organisation's head (first head created with `ON CONFLICT DO NOTHING`) |
| Audited actions | `api_key.created` (seed), `.rotated`, `.revoked` (operator); `policy.version_added`, `webhook_endpoint.created`, `.deleted` (API key, named by its lookup). Facts only, never secrets |
| Verification | `audit.verify`: numbering, previous hash, own hash, and the head (catches deletions at the end); `cli verify-audit` checks every organisation, exit code 1 if any chain is broken |
| Retention | `projects.retention_days` (default 90; database check 1–365); `cli maintain` purges sessions (with attempts and tokens) and events (with deliveries) past each project's own period in one statement each |
| Sweep | `cli maintain` first expires open sessions past their time (`SKIP LOCKED`, 500 per run) and announces each — closing step 4's lazy-expiry gap |
| Analytics | `session_stats` (project, mode, day, policy label, outcome → count), incremented by an upsert in the same transaction as the event (`record_final`); kept after the purge; `GET /v1/analytics/sessions?days=1..365` with totals |
| Book | §5.4.4; five new walkthroughs; ten changed files re-explained; two glossary terms; strict build 180 files, 12,458/12,458 lines |

### What was measured

| Check | Result |
| :-- | :-- |
| Python lint, format, mypy (strict) | clean (98 files) |
| Python tests | **208 passed** (147 + 61 ML); 3 new database tests |
| Audit | 4 real changes chained in order, intact; API role `UPDATE` → "permission denied"; owner's edit of entry 2 → broken at 2; deletion of the last → broken at 4; the key appears only as its id |
| Analytics | two passes → `{"pass": 2}`; `days=366` → `422` |
| Sweep and purge | abandoned session expired and announced (1 delivery); retention 1 day: kept at +23 h, purged at +2 days (`404`), count `{"expired": 1}` kept |
| Migrations | 0001 → 0006 → 0001 → 0006 → 0002 on a fresh PostgreSQL 18.6: clean |
| End-to-end | **4 passed** |

## Findings

- **The isolation tests failed first, and only they could have.** The driver wraps `SET ROLE` in a transaction, and the pool's rollback undid it, so every connection silently reverted to the owner after first use. Every functional test still passed, because the code's own `WHERE` clauses held. Fixed with autocommit around `SET ROLE`; the test now asserts `current_user` after a rollback.
- **asyncpg runs one statement per call**: the migration's function block had to be split.
- **`FORCE` conflicts with owner-run look-ups**, so `ENABLE` is used. The application role owns nothing, so this changes nothing for it. Recorded in ADR-0011.
- **`GRANT … ON ALL TABLES` includes `alembic_version`**, so it is revoked explicitly.
- **A cached reply is a cached secret.** Idempotency has to keep the first answer, which holds the client secret; sealing it under a key the website re-presents, and keeping it only for the session's life, keeps Valkey free of usable secrets.
- **Grants are the cheapest immutability.** Giving the API role no `UPDATE` or `DELETE` on `policies` makes "versions never change" a database fact, tested directly. The same holds for `events`.
- **Tests need their own clock.** The first delivery tests failed because the worker's clock was read before the events were written; a clock the test controls (a one-item list behind a function) also made a 24-hour retry schedule testable in a second.

## Open items

1. **Separate login for production.** The API currently logs in as the owner and switches role; a fully attacker-controlled statement could `RESET ROLE`. Production (Phase 7) must log in as a user that is only a member of `dwarpal_app`, with `DWARPAL_DATABASE_ROLE` empty.
2. **New tables need explicit grants and policies** in their own migrations (no default privileges were set, on purpose). A test now fails if any table other than `alembic_version` and `signing_keys` lacks RLS; a missing *grant* shows up as failing API tests.
3. **Policy cost at scale.** Attempts and tokens are checked through sessions, which are checked through projects. If one project reaches millions of sessions, consider a denormalised `project_id` on attempts.
4. **Remote CI** has not run these changes yet.
5. **Flow-endpoint rate limits.** Per-key limits cover websites; the design's per-session and per-address limits for the verify page exist only for challenges (Phase 3 budgets), not yet for `start` and `finish`.
6. **Guessable idempotency keys** weaken the seal for someone who also holds the master key; the docs should tell websites to use random keys (Phase 5 developer docs).
7. **Step 2 needs approval**: adding `argon2-cffi` (password hashing) from PyPI.
8. **Webhooks are at-least-once**: a worker dying between sending and recording resends after its lease; receivers must de-duplicate by `Dwarpal-Event-Id` (documented in §5.4.3).
9. **DNS rebinding window** between the address check and the connection; the production backstop is egress filtering on the worker (Phase 7).
10. ~~Lazy expiry~~ — **resolved by step 5**: `cli maintain` sweeps and announces abandoned sessions. The webhook worker and the maintenance jobs aren't yet started by the local stack or the e2e run; production scheduling belongs to Phase 7.
11. **Audit anchoring and retention**: the chain detects edits but not a consistent rewrite of a whole chain by someone controlling the database; publishing daily head hashes outside the database would. Audit entries aren't purged yet (the design keeps one year), which needs an anchor for verification to start from.
