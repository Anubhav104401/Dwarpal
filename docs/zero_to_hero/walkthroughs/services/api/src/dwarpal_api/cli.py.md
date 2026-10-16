---
fingerprint: cd140e3e44b8a26b
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

@@ 1-5
The docstring, with the two commands. `python -m dwarpal_api.cli` runs this module as a program; `--package dwarpal-api` tells uv which workspace package's environment to use.

@@ 7
The project-wide type-hint setting.

@@ 9-13
`argparse` (reading command-line arguments, as in `build.py`), `asyncio` (running async code from a normal program), `sys` (the exit code), date tools, and `Path`.

@@ 15-16
Alembic's ready-made commands (`command.upgrade` and friends), and its `Config` object.

@@ 18-22
Our database helpers, the two tables the seed fills, the ID helpers, the key generator, and the settings.

@@ 24
`MIGRATIONS` — the folder holding `env.py` and the migrations, found next to this file. Installed packages have no `alembic.ini` file, so the configuration is built in code instead.

@@ 25
`DEMO_ORIGINS` — the two local web addresses the demo project may send people back to: the verify page (port 3000) and the demo shop (port 3100).

@@ 28
**`migration_config`** — build Alembic's configuration in code.

@@ 29-30
An empty configuration, then the one required setting: where the migration scripts are.

@@ 31-32
If a database address was given, pass it on. `env.py` reads it as `sqlalchemy.url`, and falls back to the API's settings when it is absent.

@@ 33
Return the configuration.

@@ 36-37
**`migrate`** — `command.upgrade(…, "head")` applies every migration not yet applied, up to the newest one (the "head" of the history). Running it again does nothing.

@@ 40
**`seed_dev`** — create the demo project and a key. It returns the project's public ID and the key in plain text. `livemode` lets tests create a *live* key too, to prove that live sessions are refused while the model is uncalibrated.

@@ 41-42
Read the clock once, in UTC and in milliseconds.

@@ 43
A database engine for this one job.

@@ 44
A new key: test by default.

@@ 45-47
The project row: a new ID, the demo name, its allowed web addresses (the given ones, or the defaults), and the creation time.

@@ 48-57
The key row: its own ID, the project it belongs to, its mode, its lookup and **digest** (never the key itself), a label, the creation time, and not revoked.

@@ 58-62
Save both in one transaction. `flush()` sends the project to the database *before* the key is added: the key's foreign key must point at a project row that already exists.

@@ 63
Close the engine's connections; this was a one-off job.

@@ 64
Return the project's public ID (`prj_…`) and the plain key — the only moment the key exists in plain form.

@@ 67
**`main`** — what runs when the module is started as a program. `argv` lets tests pass arguments directly; normally it is `None`, and `argparse` reads the real command line.

@@ 68-70
Describe the tool, accept exactly one command — `migrate` or `seed-dev` — and read it. Anything else prints a helpful usage message and stops.

@@ 71-74
`migrate`: apply the migrations, say so, and return `0` (success).

@@ 75
Otherwise, `seed-dev`: run the async seed with the normal settings. `asyncio.run` starts the async engine, runs the function to the end, and returns its result.

@@ 76
Print the project ID and the key, with a reminder to store the key now. `\n` inside the text starts a new line.

The message uses only plain ASCII characters. An earlier version contained a long dash `—`, which came out as `�` when the output was saved to a file on Windows: Python then writes text with Windows' older character table, which other tools don't expect.

@@ 77
Success.

@@ 80-81
Run `main` only when the module is started as a program, and hand its result to the operating system as the **exit code**: `0` means success, anything else failure (§4.6).
