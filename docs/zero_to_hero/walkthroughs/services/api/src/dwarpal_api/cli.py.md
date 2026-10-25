---
fingerprint: c4745db30f4f3f32
---
A small **command-line tool** for two jobs a developer needs before the API is useful:

- `migrate` — bring the database's tables up to date (§4.10);
- `seed-dev` — create a demo project ("Amber Cellars") with a fresh **test** API key, and print the key once.

The tests call the same two functions directly, so the commands developers run by hand are exactly the code the tests exercise.

!!! try "Try it yourself"
    With the local databases running (`docker compose -f infra/compose/compose.yaml up -d --wait`), run:

    1. `uv run --package dwarpal-api python -m dwarpal_api.cli migrate`
    2. `uv run --package dwarpal-api python -m dwarpal_api.cli seed-dev`

    The second command prints a project ID and a `dk_test_…` key. Keep the key: it is shown only once.

@@ 1-12
The docstring, with the eight commands. `python -m dwarpal_api.cli` runs this module as a program; `--package dwarpal-api` tells uv which workspace package's environment to use. `liveness-report` (added in Phase 3) summarises the liveness results of recent face attempts; `--since` says from when. Phase 4 added:

- `rotate-key` and `revoke-key`, which replace or switch off an API key, named by its **key id** — the 12 characters after `dk_test_` or `dk_live_`, which are not secret on their own — so the secret itself never has to be typed into a terminal, where it would stay in the shell's history;
- `deliver-webhooks`, the webhook delivery worker;
- `maintain`, the scheduled jobs: expire abandoned sessions, and purge what is past retention;
- `verify-audit`, which checks every organisation's audit chain.

@@ 14
The project-wide type-hint setting.

@@ 16-22
`argparse` (reading command-line arguments, as in `build.py`), `asyncio` (running async code from a normal program), `statistics` (the median, for the report), `sys` (the exit code), `Counter` (counting how often each value appears), date tools, and `Path`.

@@ 23
`Any` — the type for "a value of any type", used for the stored scores, which are free-form JSON.

@@ 25
`httpx`, the HTTP client the delivery worker sends webhooks with.

@@ 26-27
Alembic's ready-made commands (`command.upgrade` and friends), and its `Config` object.

@@ 28
SQLAlchemy's `select`, to read the attempts for the report.

@@ 30-37
Our database helpers and the master key, the tables — the three the seed fills (`Organization` since Phase 4), and `VerificationAttempt`, which the report reads — the audit log and the maintenance jobs, the delivery worker, the ID helpers, the list of every scope and the key generator, and the settings.

@@ 39
`MIGRATIONS` — the folder holding `env.py` and the migrations, found next to this file. Installed packages have no `alembic.ini` file, so the configuration is built in code instead.

@@ 40
`OPERATOR` — how the audit log names a change made with these tools: an operator, using the command line.

@@ 41
`DEMO_ORIGINS` — the two local web addresses the demo project may send people back to: the verify page (port 3000) and the demo shop (port 3100).

@@ 44
**`migration_config`** — build Alembic's configuration in code.

@@ 45-46
An empty configuration, then the one required setting: where the migration scripts are.

@@ 47-48
If a database address was given, pass it on. `env.py` reads it as `sqlalchemy.url`, and falls back to the API's settings when it is absent.

@@ 49
Return the configuration.

@@ 52-53
**`migrate`** — `command.upgrade(…, "head")` applies every migration not yet applied, up to the newest one (the "head" of the history). Running it again does nothing.

@@ 56-58
**`seed_dev`** — create the demo project and a key. It returns the project's public ID and the key in plain text. `livemode` lets tests create a *live* key too, to prove that live sessions are refused while the model is uncalibrated; `scopes` lets a test make a key that may do less (every scope by default).

@@ 59-60
Read the clock once, in UTC and in milliseconds.

@@ 61
A database engine for this one job. No `role` is given, so it keeps the rights of the login that owns the tables: creating a customer is an operator's job, done before any tenant exists, and the policies don't bind the tables' owner (§5.4.1).

@@ 62
A new key: test by default.

@@ 63-64
The demo **organisation** (Phase 4): a new ID, a name, and a slug made from that ID (`.hex` is the UUID's 32 hexadecimal digits without dashes), so seeding twice can't collide on the unique slug.

@@ 65-71
The project row: a new ID, the organisation that owns it, the demo name, its allowed web addresses (the given ones, or the defaults), and the creation time.

@@ 72-83
The key row: its own ID, the project it belongs to, its mode, its lookup and **digest** (never the key itself), a label, its scopes (`sorted` gives the set of every scope as a list in a fixed order), the creation time, and neither expiring nor revoked.

@@ 84-92
Save all three in one transaction, parents first. Each `flush()` sends what has been added so far to the database *before* the next row is added: the project's foreign key must point at an organisation that already exists, and the key's at a project. The new key is recorded in the organisation's audit log — by its id and scopes, never the key — in the same transaction.

@@ 93
Close the engine's connections; this was a one-off job.

@@ 94
Return the project's public ID (`prj_…`) and the plain key — the only moment the key exists in plain form.

@@ 97-99
**`rotate_key`** — **rotation** replaces a key with a new one. Good practice is to rotate keys regularly, and at once if one might have been seen by the wrong person. A website can't switch every server to the new key in the same instant, so the old key keeps working for a **grace period** (24 hours by default), and only then stops. There is never a moment in which neither key works.

@@ 100-101
Read the clock, and open an engine as the tables' owner: this is an operator's tool, and the key look-up is by key id, before any tenant is known.

@@ 102-106
Find the old key and **lock** its row (`with_for_update`), so two rotations at once can't both replace it. A key that doesn't exist, was revoked, or has already expired can't be rotated: stop with a message (`SystemExit` ends the program with that text).

@@ 107-121
Make the new key, in the same mode, and save its row: a new ID, the same project, name and scopes, created now, and neither expiring nor revoked.

@@ 122-123
Give the old key its end: now plus the grace period. If it already had an earlier end (it was rotated before), keep the earlier one: rotating again must never make an old key live *longer*.

@@ 124-127
Record the rotation in the organisation's audit log: which key was replaced, by which, and when the old one stops.

@@ 128
Commit both changes together: the new key exists exactly when the old one has its end.

@@ 129-130
Close the engine, even if something failed (`finally`).

@@ 131
Return the new key in plain text — the only moment it exists in that form.

@@ 134-135
**`revoke_key`** — switch a key off **at once**, with no grace period: for a key that has leaked. It reports whether there was such a key still working.

@@ 136-148
As the owner, find the key by its id among those not yet revoked; if there is one, record the moment it was revoked, note it in the audit log, and commit. Close the engine, and answer whether a key was found.

@@ 151-152
**`deliver_webhooks`** — run the delivery worker (`app/delivery.py`). It works for every project, so, like the other operator tools, it connects as the tables' owner.

@@ 153-161
Open an engine and an HTTP client with the receiver timeout from the settings, and build the worker: the session factory, the master key (to open each endpoint's sealed secret), the client, a function that tells the time (`lambda: datetime.now(UTC)` — a tiny function with no name), and whether private addresses are allowed.

@@ 162-165
Run it until stopped, or once; close the engine whatever happens.

@@ 168-170
**`maintain`** — the scheduled jobs, once (an operator runs it every few minutes, for instance from `cron`). `now` can be given, so a test can pretend it is two days later.

@@ 171-175
As the owner: first the **sweep** — expire open sessions whose time is up, and announce each (the ID maker is a small function making UUIDv7s for this moment) — then the **purge**.

@@ 176-178
Close the engine whatever happened, and report what was done in one line.

@@ 181-187
**`verify_audit`** — recompute every organisation's audit chain, as the owner.

@@ 188-191
Pick out the broken chains. Report how many organisations and entries were checked, one line per broken chain with its first bad entry, or that every chain is intact. Return the text, and whether all was well.

@@ 194-195
**`liveness_summary`** (Phase 3) — turn a list of face attempts into a short, readable report. Each attempt is a pair: its outcome (such as `retry`) and its stored scores. It is a separate, plain function — no database — so a test can call it with made-up attempts.

Its purpose is **measuring the liveness checks on real people**. If the owner makes, say, 30 genuine attempts, every failed pose challenge among them is a **false reject**: an honest person turned away. This report gives that rate, and the light measurements, from which the thresholds can be set (§5.3).

@@ 196
Count the outcomes: how many passes, retries, rejections and so on. `Counter` does the counting.

@@ 197
Pick out the liveness part of each attempt's scores, skipping attempts that have none (for example, ones whose analysis failed). `scores.get("liveness")` gives `None` instead of an error when the key is missing.

@@ 198
Count the kinds of evidence: `images` (measured) or `labels` (the test mode). A report on genuine attempts should show only `images`.

@@ 199
The pose results, where there was one.

@@ 200
Count every problem name over all pose results — `wrong_order`, `not_shown:turn_left` and so on. The double `for` reads left to right: for each pose result, for each of its problems.

@@ 201
Count the injection signs the same way.

@@ 202
How many attempts showed the screen colours at all. `.get("shown", True)` treats results stored before this field existed as shown.

@@ 203
The light results that could actually be measured (`usable`).

@@ 204
The skin correlations among them, leaving out any that are missing.

@@ 205
How many pose challenges passed. `sum` of `True`/`False` values counts the `True`s, because Python treats `True` as 1.

@@ 206
**How far each pose got**, gathered by pose name: `reach` maps a name such as `turn_left` to the list of its values. `dict[str, list[float]]` is the type: text keys, lists of numbers as values.

@@ 207-210
For each pose result, for each `[name, value]` pair it recorded, add the value to its name's list — skipping `None`, which means there was no face to measure. `pose.get("reached", [])` gives an empty list for results stored before this field existed. `setdefault(name, [])` returns the name's list, creating an empty one first if needed.

@@ 211
One short text per pose name: the **median** and the **lowest** value, such as `turn_left +0.42 / +0.29`. The lowest matters most: it is the honest attempt that came closest to failing, and it shows how much room the limit leaves. `sorted(…)` puts the names in alphabetical order.

@@ 212
Which measurement each pose check used, counted.

@@ 213-215
The presentation evidence, gathered over the attempts: the real-face chances, the screen patterns, and for every pose whether it was caught mid-turn (`True`/`False`). `.get(…)` skips results stored before these fields existed.

@@ 216-217
Build the report line by line. The first: the number of attempts and each outcome with its count, most common first. `", ".join(…)` puts commas between the parts.

@@ 218
The evidence counts — or `none`. `or "none"` works because an empty text counts as false.

@@ 219-224
How many pose challenges passed, as a count and a percentage (`:.0%` formats 0.9 as `90%`), and the **false-reject rate if every attempt was genuine** — the share that failed. The extra part is added only if there were pose results (`if poses else ""`), which also avoids dividing by zero.

@@ 225-228
The pose problems, the measurement used, how far each pose got (median and lowest — the numbers from which the pose limits are set), and the injection signs, each with its count, or `none`.

@@ 229-232
**The presentation line**: the real-face chance's median and lowest value (or `not measured`), the screen pattern's median, and how many poses were caught mid-turn. `sum` of `True`/`False` values counts the `True`s.

@@ 233-238
How many attempts showed the colours and how many had a usable light measurement, and — if there were any skin correlations — their **median** (the middle value, which one odd attempt can't drag far) and their range. `:+.2f` prints a number with two decimals and always a sign, such as `+0.62`.

@@ 239-240
Close the list, and join the lines with line breaks into one text.

@@ 243
**`liveness_report`** — read the attempts from the database and summarise them. It is `async` because the database code is.

@@ 244-245
Connect to the database and open a session.

@@ 246-252
Fetch only two columns — the outcome and the scores — of every **face** attempt created at or after `since`. `.all()` returns the rows.

@@ 253
Close the connection.

@@ 254
Turn each row into an (outcome, scores) pair and summarise them.

@@ 257
**`main`** — what runs when the module is started as a program. `argv` lets tests pass arguments directly; normally it is `None`, and `argparse` reads the real command line.

@@ 258-274
Describe the tool, accept exactly one of the eight commands (listed one per line), the optional `--since`, and for the key commands `--lookup` (the key id) and `--grace-hours` (24 if not given; `type=float` allows `0.5`); `--once` (`action="store_true"`: present means true) is for `deliver-webhooks`. Then read them. `type=datetime.fromisoformat` converts the text (such as `2026-10-17T12:00`) into a date and time; a malformed one is refused with a message. Anything else prints a helpful usage message and stops.

@@ 275-278
`migrate`: apply the migrations, say so, and return `0` (success).

@@ 279-285
`liveness-report`: from `--since`, or from 24 hours ago if it was left out. A time typed without a time zone is taken as UTC (`replace(tzinfo=UTC)`), because the database stores times in UTC and can't compare them with a time that has none. Print the report and return `0`.

`deliver-webhooks`: run the worker with the normal settings.

@@ 286-288
`maintain`: run the jobs and print the summary.

@@ 289-292
`verify-audit`: print the report, and fail (exit code `1`) if any chain is broken, so a scheduler or monitoring system notices.

@@ 293-294
The key commands need to know which key: without `--lookup`, `parser.error` prints the usage and stops with an error.

@@ 295-298
`rotate-key`: make the replacement, print it once with a reminder to store it and when the old key stops, and succeed.

@@ 299-302
`revoke-key`: switch the key off and say so, or say there was no such working key and return `1`, failure, so a script that calls this notices.

@@ 303
Otherwise, `seed-dev`: run the async seed with the normal settings. `asyncio.run` starts the async engine, runs the function to the end, and returns its result.

@@ 304-305
Print the project ID, the key, and the key id (characters 8 to 19 of the key: `plaintext[8:20]` skips `dk_test_` and takes the 12 that follow), with a reminder to store the key now. `\n` inside the text starts a new line.

The message uses only plain ASCII characters. An earlier version contained a long dash `—`, which came out as `�` when the output was saved to a file on Windows: Python then writes text with Windows' older character table, which other tools don't expect.

@@ 306
Success.

@@ 309-310
Run `main` only when the module is started as a program, and hand its result to the operating system as the **exit code**: `0` means success, anything else failure (§4.6).
