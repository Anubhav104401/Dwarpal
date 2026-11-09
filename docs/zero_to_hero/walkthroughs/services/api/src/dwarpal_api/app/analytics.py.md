---
fingerprint: 0a7c280618585530
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
The tenant helper, the three counts tables — outcomes, face checks and (since 9 Nov) ID-document checks — and the median of bands (`domain/timing.py`).

@@ 16-17
The toolbox type, for type hints only (see `app/webhooks.py` for why).

@@ 20-22
**`session_counts`** — the last `days` days of a project's finished sessions, in one mode: test and live are counted apart, so a website's integration testing never blurs its real figures.

@@ 23
The first day to include: today counts as one of the `days`, hence `days - 1`.

@@ 24-28
The project's counts in this mode since then, by day, policy and outcome.

@@ 37-38
Read them in the project's tenant.

@@ 41-43
Add them up by outcome.

@@ 44-47
One row per day, policy and outcome.

@@ 29-31
The face checks' counts over the same days, for the same project and mode.

@@ 39
Read in the same database session as the outcome counts, under the same tenant.

@@ 32-36
The ID-document checks' counts (9 Nov), for the same project, mode and days.

@@ 40
Read in the same database session, under the same tenant.

@@ 48-55
The answer: the rows, the first day, the totals (sorted, so the answer is always in the same order), the face checks' figures, and (since 9 Nov) the ID-document checks'.

@@ 58-61
**`face_stage`** — how the face checks that reached a decision ended, and how long the median took. A session sent to a stronger check counts here as `step_up` straight away, though its final outcome — in the totals — comes only when it finishes or expires.

@@ 62-66
Add up the counts twice over: by outcome, and by band of time, across all the days.

@@ 67-72
The answer: how many were decided, the count of each outcome, and the median band's start and end (the end `None` for the last band), or `None` before anything was decided.

@@ 75-78
**`document_stage`** (9 Nov) — how many sessions reached the ID-document check, and how many of those checks ended each way. Those that reached it with no ending either left or are still on it; the share that ended is the design's step-up conversion, which the page works out.

@@ 79-81
Add up the counts by step, across all the days.

@@ 82-83
Take `opened` out of the counter (`pop`, 0 if there was none): what is left are the endings. The answer: how many reached the check, and how many ended each way, sorted.
