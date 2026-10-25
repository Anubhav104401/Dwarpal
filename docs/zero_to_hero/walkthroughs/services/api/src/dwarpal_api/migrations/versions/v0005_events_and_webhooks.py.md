---
fingerprint: 8d910e3aff9be0ca
---
The **fifth migration** (Phase 4, §5.4.3): the three tables of events and webhooks, and a column that lets an age token be introspected only once. Each new table follows the recipe of migration `0004`: create it, grant the API's role exactly what it needs, enable row-level security, add the `tenant` policy.

@@ 1-10
The docstring: what the migration adds, its ID `0005`, the one it follows, its date, and the transactional outbox in one paragraph.

@@ 12
The project-wide type-hint setting.

@@ 14
`Sequence`, for the type hints below.

@@ 16-18
SQLAlchemy as `sa`, Alembic's operations as `op`, and PostgreSQL's `ARRAY` and `JSONB` types.

@@ 20-23
This migration's ID, `0005`, and the one before it, `0004`.

@@ 25-27
The restricted role's name; the timestamp type; and the usual per-project rule, written once.

@@ 28
**`RIGHTS`** — for each new table, what the API's role may do with it, and which rows it sees:

@@ 29
endpoints: everything — a website may add, change and remove its endpoints;

@@ 30
events: **read and add only**. With no `UPDATE` or `DELETE`, the database refuses to rewrite history: the record of what happened can't be quietly changed later.

@@ 31
deliveries: read, add and update (their status changes as they are sent), but not delete; their rows are visible through their endpoint, which is visible through its project.

@@ 32
End of the dictionary.

@@ 35
**`upgrade`**.

@@ 36-46
Create `webhook_endpoints`: ID, project (deleted with it), mode, address, the sealed secret, the event types, on or off, and when it was made.

@@ 47
Index it by project.

@@ 48-56
Create `events`: ID, project, mode, type, the JSON data, and when it happened.

@@ 57
Index it by project and ID, for reading a project's events in time order.

@@ 58-70
Create `webhook_deliveries`: ID, endpoint and event (each deleted with its parent), status, attempts, when it is next due, what happened last, and when it was made and delivered.

@@ 71
Index it by endpoint, for listing an endpoint's deliveries.

@@ 72-78
The worker's index: `next_attempt_at`, but only for **pending** rows (`postgresql_where`). It answers "what is due now?" while staying small, because delivered and dead rows never enter it.

@@ 79-82
For each new table: the rights, row-level security, and the policy.

@@ 83
And `issued_tokens.introspected_at`, empty for every token issued so far.

@@ 86
**`downgrade`** — the way back.

@@ 87-90
Drop the column, then the tables, children before parents.
