# Phase 4 report — the platform

**Dates:** from 24 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Decision record:** [ADR-0011](../adr/0011-postgresql-rls-and-valkey.md) (amended 24 Oct) · **Status:** 🟡 step 1 of 6 built and tested locally.

**Goal (from the roadmap):** turn the single age check into a platform many businesses can use at once: organisations and people, safe keys and policies, events, an audit trail, and a published contract. **Exit:** contract and integration suites green; **RLS isolation tests green**; audit-chain verification green.

## Steps

| Step | Scope | Status |
| :-- | :-- | :-- |
| 1 | Organisations; row-level security on every tenant table, with isolation tests | ✅ 24 Oct |
| 2 | Users (Argon2id), TOTP, members and roles, console sessions, CSRF | 🗓 (needs approval to add `argon2-cffi`) |
| 3 | Scoped and rotating keys, versioned policies, idempotency, rate limits, cursor pagination | 🗓 |
| 4 | Events, outbox, webhook worker (HMAC, retries, SSRF guard), token introspection | 🗓 |
| 5 | Hash-chained audit log and its verifier, retention purge, analytics | 🗓 |
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

## Findings

- **The isolation tests failed first, and only they could have.** The driver wraps `SET ROLE` in a transaction, and the pool's rollback undid it, so every connection silently reverted to the owner after first use. Every functional test still passed, because the code's own `WHERE` clauses held. Fixed with autocommit around `SET ROLE`; the test now asserts `current_user` after a rollback.
- **asyncpg runs one statement per call**: the migration's function block had to be split.
- **`FORCE` conflicts with owner-run look-ups**, so `ENABLE` is used. The application role owns nothing, so this changes nothing for it. Recorded in ADR-0011.
- **`GRANT … ON ALL TABLES` includes `alembic_version`**, so it is revoked explicitly.

## Open items

1. **Separate login for production.** The API currently logs in as the owner and switches role; a fully attacker-controlled statement could `RESET ROLE`. Production (Phase 7) must log in as a user that is only a member of `dwarpal_app`, with `DWARPAL_DATABASE_ROLE` empty.
2. **New tables need explicit grants and policies** in their own migrations (no default privileges were set, on purpose). A test now fails if any table other than `alembic_version` and `signing_keys` lacks RLS; a missing *grant* shows up as failing API tests.
3. **Policy cost at scale.** Attempts and tokens are checked through sessions, which are checked through projects. If one project reaches millions of sessions, consider a denormalised `project_id` on attempts.
4. **Remote CI** has not run these changes yet.
