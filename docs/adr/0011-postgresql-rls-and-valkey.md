# ADR-0011: PostgreSQL 18 with row-level security; Valkey for ephemeral state

- **Status:** Accepted — 2026-10-15

## Context
Multi-tenant data must never leak between relying parties, even if application code has a bug. Some state — challenges, rate limits, console sessions, job queues — is short-lived and must be fast.

## Decision
- **PostgreSQL 18** is the system of record. Every tenant-scoped table has `ENABLE` + `FORCE ROW LEVEL SECURITY`, with policies keyed on `current_setting('app.org_id' | 'app.project_id')`, set per transaction with `SET LOCAL`. The application role owns no tables; migrations use a separate role. IDs come from native `uuidv7()`.
- **Valkey 9** (BSD-licensed Redis fork) holds ephemeral state with TTLs: challenges, token buckets (Lua), console sessions, the arq queue and the idempotency cache.

## Consequences
- **Good:** defence-in-depth tenant isolation that can be tested directly; transactional integrity for outcome + event + audit + outbox; a clean licence for the cache.
- **Cost:** RLS adds a little query overhead and setup discipline (every transaction must set context — enforced by the DB session helper and tests).

## Alternatives considered
Application-only tenant filtering (one forgotten `WHERE` leaks data), schema-per-tenant or database-per-tenant (operationally heavy), Redis 8 (licence: AGPL/RSAL/SSPL options) — Valkey is protocol-compatible and BSD-licensed.

## Amendment — 2026-10-24 (Phase 4, step 1)
- Tenant tables use `ENABLE ROW LEVEL SECURITY` without `FORCE`. Two `SECURITY DEFINER` look-ups (`dwarpal_find_api_key`, `dwarpal_session_project`) run as the table owner and must see past the policies, because they answer "whose key / whose session is this?" before a tenant is known. The application role `dwarpal_app` owns no tables, so `ENABLE` binds it fully; tests prove it.
- The tenant is named with `set_config('app.project_id' | 'app.org_id', value, true)`, the parameterised equivalent of `SET LOCAL`.
- Until deployment (Phase 7) the API logs in as the owner and switches with `SET ROLE dwarpal_app` on each new connection. Production must log in as a separate user that is only a member of `dwarpal_app` (and leave `DWARPAL_DATABASE_ROLE` empty), so that no statement can `RESET ROLE` back to the owner.
