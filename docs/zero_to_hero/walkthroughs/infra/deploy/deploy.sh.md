---
fingerprint: 2974e635af4e4682
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

@@ 11-15
**`env_value`** — read one value from `.env`. The owner's and the services' database passwords, and the tag running now, kept for a rollback.

@@ 17
**`set_tag`** — change the image tag in `.env` (`sed -i` edits the file in place). Compose reads it from there.

@@ 19-21
Say what happens, switch to the new tag, and download its images (`pull`).

@@ 23-27
Start the databases and wait until they are healthy; then run the **migrations** in a one-off container (`run --rm`) of the API's image, logged in as the database's owner — the only time anything uses the owner's password. The services themselves never do.

@@ 29-36
Make sure the services' login exists — `dwarpal_api`, a member of `dwarpal_app` only — and that its password matches `.env`. The SQL goes to `psql` inside the PostgreSQL container (`<<'SQL'` sends the following lines as its input, untouched by bash):
- the `SELECT` writes the `CREATE ROLE` statement only if no such role exists, and `\gexec` runs what it wrote — a way to say "create if missing", which `CREATE ROLE` itself can't;
- `ALTER ROLE` sets the password, given to psql as the variable `pw` and written as `:'pw'`, which psql quotes safely.

@@ 38-43
Start or update every service, removing any no longer in the file, and **wait up to 5 minutes until every health check passes**. If they do: report it, delete images unused for a week, and succeed.

@@ 45-51
If not: say so, show which services are unhealthy, put the previous tag back and start it again, and fail — so the workflow shows red. Migrations are not undone; the runbook's rule (each migration works with the previous code too) is what makes this safe.
