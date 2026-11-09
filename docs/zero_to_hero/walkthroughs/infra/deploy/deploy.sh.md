---
fingerprint: 15370e1fd7d791bd
---
**Deploying a version** (Phase 8, §5.8.2): pull its images, migrate the database, start everything, and wait until all is healthy — or roll back to what was running. Health-gated and reversible, as the roadmap asks.

@@ 1
The *shebang*: run this file with bash, wherever it is installed.

@@ 2-5
What it does — deploy one version, and roll back if it isn't healthy — how to call it, and who does: GitHub Actions over SSH, or a person by hand.

@@ 6
**`set -euo pipefail`** — stop at the first failed command (`-e`), at any unset variable (`-u`), and when any part of a pipe fails (`pipefail`). A half-done deploy must never carry on as if it had worked.

@@ 8-9
The tag to deploy — required (`:?` stops with the usage line if it's missing) — and work in the script's own folder.

@@ 11-14
**`env_value`** — read one value from `.env`: the services' database password, and the tag running now, kept for a rollback. (The owner's password isn't needed here any more: the migrations run through `operator`, whose settings carry it.)

@@ 16
**`set_tag`** — change the image tag in `.env` (`sed -i` edits the file in place). Compose reads it from there.

@@ 18-20
Say what happens, switch to the new tag, and download its images (`pull`).

@@ 22-25
Start the databases and wait until they are healthy; then run the **migrations** in a one-off container (`run --rm`) of the `operator` service, which logs in as the tables' owner (compose.yaml) — the API never does.

@@ 27-34
Make sure the services' login exists — `dwarpal_api`, a member of `dwarpal_app` only — and that its password matches `.env`. The SQL goes to `psql` inside the PostgreSQL container (`<<'SQL'` sends the following lines as its input, untouched by bash):
- the `SELECT` writes the `CREATE ROLE` statement only if no such role exists, and `\gexec` runs what it wrote — a way to say "create if missing", which `CREATE ROLE` itself can't;
- `ALTER ROLE` sets the password, given to psql as the variable `pw` and written as `:'pw'`, which psql quotes safely.

@@ 57-63
If not: say so, show which services are unhealthy, put the previous tag back and start it again, and fail — so the workflow shows red. Migrations are not undone; the runbook's rule (each migration works with the previous code too) is what makes this safe. The rollback leaves the shop out in the same way.

@@ 36-39
**The demo shop** (9 Nov): it runs only once its project and key are in `.env` (README, step 7). Before that — on the first deploy, always — it can't serve a page, its health check fails, and waiting for it would fail the whole deploy and its rollback too. So while the key is empty, `shop` holds `--scale shop=0`: start no shop containers at all. `[ -n … ]` asks whether the value is non-empty; `||` runs the assignment when it isn't.

@@ 41-43
Start or update every service, removing any no longer in the file, and **wait up to 5 minutes until every health check passes** — leaving the shop out while it has no key (`"${shop[@]}"` adds `--scale shop=0`, or nothing). If they pass, report the version deployed…

@@ 44-48
…then ask the inference service whether it is ready (`/readyz`, from inside its container) and print the answer — or *no answer*. Live checks need the anti-spoofing networks, and the server starts without them, so this is where a missing file shows (9 Nov: CI found it).

@@ 49-52
Unless the answer says the networks are **loaded**, warn on the error output: every live check would be refused. The deploy still succeeds — test checks work without them.

@@ 53-55
Delete images unused for a week, and stop: deployed.
