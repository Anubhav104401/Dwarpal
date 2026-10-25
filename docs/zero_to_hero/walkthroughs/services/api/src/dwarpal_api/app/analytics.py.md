---
fingerprint: 2e5e0935b90c9fb6
---
**Analytics** (Phase 4, §5.4.4): how a project's checks have been ending, day by day — read from `session_stats`, the counts written when each session finishes (`record_final` in `app/verification.py`). Because they are only counts, they say nothing about any person, and they are kept after the sessions themselves are purged.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-8
`uuid`, `Counter` (a dictionary that counts), `timedelta`, and `TYPE_CHECKING` and `Any`.

@@ 10
SQLAlchemy's `select`.

@@ 12-13
The tenant helper and the counts table.

@@ 15-16
The toolbox type, for type hints only (see `app/webhooks.py` for why).

@@ 19-21
**`session_counts`** — the last `days` days of a project's finished sessions, in one mode: test and live are counted apart, so a website's integration testing never blurs its real figures.

@@ 22
The first day to include: today counts as one of the `days`, hence `days - 1`.

@@ 23-27
The project's counts in this mode since then, by day, policy and outcome.

@@ 28-29
Read them in the project's tenant.

@@ 30-32
Add them up by outcome.

@@ 33-36
One row per day, policy and outcome.

@@ 37
The answer: the rows, the first day, and the totals (sorted, so the answer is always in the same order).
