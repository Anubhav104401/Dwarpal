---
fingerprint: 15e3286a90bf7962
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

@@ 12-14
The tenant helper, the two counts tables, and the median of bands (`domain/timing.py`).

@@ 16-17
The toolbox type, for type hints only (see `app/webhooks.py` for why).

@@ 20-22
**`session_counts`** — the last `days` days of a project's finished sessions, in one mode: test and live are counted apart, so a website's integration testing never blurs its real figures.

@@ 23
The first day to include: today counts as one of the `days`, hence `days - 1`.

@@ 24-28
The project's counts in this mode since then, by day, policy and outcome.

@@ 32-33
Read them in the project's tenant.

@@ 35-37
Add them up by outcome.

@@ 38-41
One row per day, policy and outcome.

@@ 42-65
The answer: the rows, the first day, the totals (sorted, so the answer is always in the same order), and the face checks' figures.

**`face_stage`** — how the face checks that reached a decision ended, and how long the median took. A session sent to a stronger check counts here as `step_up` straight away, though its final outcome — in the totals — comes only when it finishes or expires.

Add up the counts twice over: by outcome, and by band of time, across all the days.

The answer: how many were decided, the count of each outcome, and the median band's start and end (the end `None` for the last band), or `None` before anything was decided.

@@ 29-31
The face checks' counts over the same days, for the same project and mode.

@@ 34
Read in the same database session as the outcome counts, under the same tenant.
