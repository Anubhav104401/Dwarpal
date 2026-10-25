---
fingerprint: 85d0e682b04d386c
---
**Scheduled jobs** for the operator (Phase 4, §5.4.4), run by `cli maintain` and `cli verify-audit`, for instance every few minutes from a scheduler:

- **the sweep**: expire open sessions whose time is up, and announce each one. Sessions also expire when they are next read, but a session that nobody reads again would otherwise never be announced;
- **the purge**: delete session metadata older than each project's **retention period** (90 days by default, 1 to 365). Personal data shouldn't be kept longer than needed, a principle of every privacy law in §1.3. The daily counts are kept, because they say nothing about any one person;
- **the chain check**: verify every organisation's audit chain.

They work across every project, so, like the other operator tools, they run as the tables' owner.

@@ 1-2
The docstring.

@@ 4
The project-wide type-hint setting.

@@ 6-9
`uuid`, `Callable`, `dataclass` and `datetime`.

@@ 11-12
SQLAlchemy's `delete`, `select` and `text`, and the session types.

@@ 14-17
The tables involved, the audit module, `record_final` (the same announcement and count a use case makes), and the state machine.

@@ 19
`OPEN` — the statuses of a session that hasn't finished.

@@ 20-24
**`TOO_OLD`** — the purge's condition, in SQL: created before now minus *this row's own project's* retention period. The inner `SELECT` looks up the retention of the project the row belongs to; `make_interval(days => …)` turns that number into a length of time. One statement purges every project, each by its own rule. `CAST(:now AS timestamptz)` tells PostgreSQL what kind of value `:now` is, which it can't work out on its own here.

@@ 27-31
**`sweep_expired`** — expire and announce abandoned sessions, at most 500 at a time.

@@ 32-39
Open sessions whose expiry time has passed, oldest first, **locked**, skipping any another job has locked (`skip_locked`), so two sweeps never expire the same session twice.

@@ 40-44
For each: move it to `expired` through the state machine, write its event and count (`record_final`), and commit them all together.

@@ 45
Say how many.

@@ 48-51
**`Purged`** — what a purge removed: sessions and events.

@@ 54-56
**`purge`** — delete what is past retention. Deleting a session also deletes its attempts and issued tokens; deleting an event also deletes its deliveries (the foreign keys' `CASCADE`). The counts and the audit log stay.

@@ 57-61
Two `DELETE` statements with the same condition, one transaction, and the numbers of rows each removed.

@@ 64-65
**`_count`** — the number of rows a statement affected, read safely (the result's `rowcount`, or 0).

@@ 68-72
**`verify_all_chains`** — every organisation's chain, checked in one unit of work, as a dictionary from organisation to report.
