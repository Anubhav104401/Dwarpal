---
fingerprint: f934f4851414b335
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

@@ 1-7
The docstring, with the three commands. `python -m dwarpal_api.cli` runs this module as a program; `--package dwarpal-api` tells uv which workspace package's environment to use. The third, `liveness-report` (added in Phase 3), summarises the liveness results of recent face attempts; `--since` says from when.

@@ 9
The project-wide type-hint setting.

@@ 11-17
`argparse` (reading command-line arguments, as in `build.py`), `asyncio` (running async code from a normal program), `statistics` (the median, for the report), `sys` (the exit code), `Counter` (counting how often each value appears), date tools, and `Path`.

@@ 18
`Any` — the type for "a value of any type", used for the stored scores, which are free-form JSON.

@@ 20-21
Alembic's ready-made commands (`command.upgrade` and friends), and its `Config` object.

@@ 22
SQLAlchemy's `select`, to read the attempts for the report.

@@ 24-28
Our database helpers, the tables — the two the seed fills, and `VerificationAttempt`, which the report reads — the ID helpers, the key generator, and the settings.

@@ 30
`MIGRATIONS` — the folder holding `env.py` and the migrations, found next to this file. Installed packages have no `alembic.ini` file, so the configuration is built in code instead.

@@ 31
`DEMO_ORIGINS` — the two local web addresses the demo project may send people back to: the verify page (port 3000) and the demo shop (port 3100).

@@ 34
**`migration_config`** — build Alembic's configuration in code.

@@ 35-36
An empty configuration, then the one required setting: where the migration scripts are.

@@ 37-38
If a database address was given, pass it on. `env.py` reads it as `sqlalchemy.url`, and falls back to the API's settings when it is absent.

@@ 39
Return the configuration.

@@ 42-43
**`migrate`** — `command.upgrade(…, "head")` applies every migration not yet applied, up to the newest one (the "head" of the history). Running it again does nothing.

@@ 46
**`seed_dev`** — create the demo project and a key. It returns the project's public ID and the key in plain text. `livemode` lets tests create a *live* key too, to prove that live sessions are refused while the model is uncalibrated.

@@ 47-48
Read the clock once, in UTC and in milliseconds.

@@ 49
A database engine for this one job.

@@ 50
A new key: test by default.

@@ 51-53
The project row: a new ID, the demo name, its allowed web addresses (the given ones, or the defaults), and the creation time.

@@ 54-63
The key row: its own ID, the project it belongs to, its mode, its lookup and **digest** (never the key itself), a label, the creation time, and not revoked.

@@ 64-68
Save both in one transaction. `flush()` sends the project to the database *before* the key is added: the key's foreign key must point at a project row that already exists.

@@ 69
Close the engine's connections; this was a one-off job.

@@ 70
Return the project's public ID (`prj_…`) and the plain key — the only moment the key exists in plain form.

@@ 73-74
**`liveness_summary`** (Phase 3) — turn a list of face attempts into a short, readable report. Each attempt is a pair: its outcome (such as `retry`) and its stored scores. It is a separate, plain function — no database — so a test can call it with made-up attempts.

Its purpose is **measuring the liveness checks on real people**. If the owner makes, say, 30 genuine attempts, every failed pose challenge among them is a **false reject**: an honest person turned away. This report gives that rate, and the light measurements, from which the thresholds can be set (§5.3).

@@ 75
Count the outcomes: how many passes, retries, rejections and so on. `Counter` does the counting.

@@ 76
Pick out the liveness part of each attempt's scores, skipping attempts that have none (for example, ones whose analysis failed). `scores.get("liveness")` gives `None` instead of an error when the key is missing.

@@ 77
Count the kinds of evidence: `images` (measured) or `labels` (the test mode). A report on genuine attempts should show only `images`.

@@ 78
The pose results, where there was one.

@@ 79
Count every problem name over all pose results — `wrong_order`, `not_shown:turn_left` and so on. The double `for` reads left to right: for each pose result, for each of its problems.

@@ 80
Count the injection signs the same way.

@@ 81
The light results that could actually be measured (`usable`).

@@ 82
The skin correlations among them, leaving out any that are missing.

@@ 83
How many pose challenges passed. `sum` of `True`/`False` values counts the `True`s, because Python treats `True` as 1.

@@ 84
**How far each pose got**, gathered by pose name: `reach` maps a name such as `turn_left` to the list of its values. `dict[str, list[float]]` is the type: text keys, lists of numbers as values.

@@ 85-88
For each pose result, for each `[name, value]` pair it recorded, add the value to its name's list — skipping `None`, which means there was no face to measure. `pose.get("reached", [])` gives an empty list for results stored before this field existed. `setdefault(name, [])` returns the name's list, creating an empty one first if needed.

@@ 89
One short text per pose name: the **median** and the **lowest** value, such as `turn_left +0.42 / +0.29`. The lowest matters most: it is the honest attempt that came closest to failing, and it shows how much room the limit leaves. `sorted(…)` puts the names in alphabetical order.

@@ 90-91
Build the report line by line. The first: the number of attempts and each outcome with its count, most common first. `", ".join(…)` puts commas between the parts.

@@ 92
The evidence counts — or `none`. `or "none"` works because an empty text counts as false.

@@ 93-98
How many pose challenges passed, as a count and a percentage (`:.0%` formats 0.9 as `90%`), and the **false-reject rate if every attempt was genuine** — the share that failed. The extra part is added only if there were pose results (`if poses else ""`), which also avoids dividing by zero.

@@ 99-101
The pose problems and the injection signs, each with its count, or `none`. Between them, the pose reach line (Phase 3): the numbers from which the pose limits are set.

@@ 102-107
How many attempts had a usable light measurement, and — if there were any skin correlations — their **median** (the middle value, which one odd attempt can't drag far) and their range. `:+.2f` prints a number with two decimals and always a sign, such as `+0.62`.

@@ 108-109
Close the list, and join the lines with line breaks into one text.

@@ 112
**`liveness_report`** — read the attempts from the database and summarise them. It is `async` because the database code is.

@@ 113-114
Connect to the database and open a session.

@@ 115-121
Fetch only two columns — the outcome and the scores — of every **face** attempt created at or after `since`. `.all()` returns the rows.

@@ 122
Close the connection.

@@ 123
Turn each row into an (outcome, scores) pair and summarise them.

@@ 126
**`main`** — what runs when the module is started as a program. `argv` lets tests pass arguments directly; normally it is `None`, and `argparse` reads the real command line.

@@ 127-130
Describe the tool, accept exactly one command — `migrate`, `seed-dev` or `liveness-report` — and the optional `--since`, and read them. `type=datetime.fromisoformat` converts the text (such as `2026-10-17T12:00`) into a date and time; a malformed one is refused with a message. Anything else prints a helpful usage message and stops.

@@ 131-134
`migrate`: apply the migrations, say so, and return `0` (success).

@@ 135-138
`liveness-report`: from `--since`, or from 24 hours ago if it was left out. A time typed without a time zone is taken as UTC (`replace(tzinfo=UTC)`), because the database stores times in UTC and can't compare them with a time that has none. Print the report and return `0`.

@@ 139
Otherwise, `seed-dev`: run the async seed with the normal settings. `asyncio.run` starts the async engine, runs the function to the end, and returns its result.

@@ 140
Print the project ID and the key, with a reminder to store the key now. `\n` inside the text starts a new line.

The message uses only plain ASCII characters. An earlier version contained a long dash `—`, which came out as `�` when the output was saved to a file on Windows: Python then writes text with Windows' older character table, which other tools don't expect.

@@ 141
Success.

@@ 144-145
Run `main` only when the module is started as a program, and hand its result to the operating system as the **exit code**: `0` means success, anything else failure (§4.6).
