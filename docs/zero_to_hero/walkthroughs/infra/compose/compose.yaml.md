---
fingerprint: 3cef46c151d2b054
---
The **Docker Compose file** for local development. It describes two containers — the PostgreSQL database and Valkey — and how to run them, so that one command starts both, healthy and ready (§4.5). In Phase 1 it grows to include our own services too.

YAML reminder: indentation shows what belongs to what, and `#` starts a comment.

@@ 1-3
Comments: what the file is for, and the exact commands to start and stop it.

- `-f` names this file.
- `up -d` starts the containers in the background (*detached*).
- `--wait` returns only when every health check passes.
- `down -v` also deletes the data **v**olumes — a fresh start.

@@ 4-5
**Seeing traces** (Phase 7): start the observability containers too, run the API with the collector's address, and open Grafana in a browser.

@@ 7
`name: dwarpal` — the **project name**. Compose prefixes everything it creates with it (`dwarpal-postgres-1`, `dwarpal_pgdata`), so these containers never clash with another project's.

@@ 9
`services:` — the list of containers to run, each under its own name.

@@ 10
`postgres:` — the first service, the PostgreSQL database. Inside Compose's private network, other containers will reach it simply by the name `postgres`.

@@ 11
`image: postgres:18.6-alpine3.24` — the official PostgreSQL image, pinned: version **18.6**, built on **Alpine Linux 3.24** (a tiny Linux distribution, so the image is small). Version 18 is required for the built-in `uuidv7()` function (ADR-0011).

@@ 12
`environment:` — settings passed into the container. The official image reads these on its first start.

@@ 13-15
The database name, user and password. `${POSTGRES_DB:-dwarpal}` means "use the variable `POSTGRES_DB` if it is set — for example in an `.env` file — otherwise use `dwarpal`". The default password is labelled `local-only`, as a reminder that it must never be used anywhere real.

@@ 16-17
`ports:` — **publish** the container's port 5432 on the computer, so programs outside Docker (our services during development, a database viewer) can connect.

The `127.0.0.1:` at the front is a security choice. It publishes the port **only to this computer**, not to every device on the same Wi-Fi network. The middle number can be changed through `POSTGRES_PORT`, in case 5432 is already in use.

@@ 18-19
`volumes:` — keep the database's files in a **named volume** called `pgdata`, so the data survives when the container is replaced.

The volume is mounted at `/var/lib/postgresql`, the location **PostgreSQL 18's** image expects. Older versions used `/var/lib/postgresql/data`; the change makes future major-version upgrades easier.

@@ 20
`healthcheck:` — how Docker decides the database is truly *ready*, not just started.

@@ 21
`test` — the check: run `pg_isready` inside the container, for our user and database. `CMD-SHELL` means "run this through the container's shell".

The doubled `$$` is an escape. A single `$` would be filled in by Compose on your computer; `$$` becomes a literal `$`, so the variable is filled in *inside* the container, by the container's shell.

@@ 22-24
Check every 5 seconds, allow each check 3 seconds, and only declare the container *unhealthy* after 20 failures in a row — about 100 seconds, which gives a first start plenty of time.

@@ 25
`restart: unless-stopped` — if the database crashes or the computer restarts, Docker starts it again automatically. The exception is when you stopped it yourself.

@@ 27
`valkey:` — the second service: Valkey, the fast short-term memory (ADR-0011).

@@ 28
`image: valkey/valkey:9.1.2-alpine3.24` — the official Valkey image, version 9.1.2 on Alpine 3.24, pinned.

@@ 29
`command:` — the program the container runs: `valkey-server` with **append-only** persistence switched on. Every change is also appended to a log file on disk, so the queued background jobs and other short-lived state survive a restart.

@@ 30-31
Publish Valkey's port 6379 to **this computer only**, with an optional override through `VALKEY_PORT`.

@@ 32-33
Keep Valkey's files in the named volume `valkeydata`, mounted at `/data`, where the image stores them.

@@ 34-38
The health check: `valkey-cli ping` must answer (with `PONG`). Same timing as for PostgreSQL. `CMD` (instead of `CMD-SHELL`) runs the program directly, since no shell features are needed.

@@ 39
`restart: unless-stopped` — restart automatically, as for PostgreSQL.

@@ 41
**The observability containers** (Phase 7, decision D11). Each has `profiles: [observability]`, so a plain `up` leaves them out; they start only when asked for.

@@ 42-50
**`collector`** — the OpenTelemetry collector, which receives the API's traces over HTTP on port 4318 (on this computer only, `127.0.0.1`) and passes them on to Tempo. Its configuration file is mounted read-only from `infra/observability`; it starts after Tempo (`depends_on`).

@@ 52-61
**`tempo`** — Grafana Tempo, which stores traces and answers searches, on port 3200. Its data lives in a named volume. It runs as root inside its container (`user: "0"`) because the fresh volume belongs to root and Tempo's own user couldn't write to it.

@@ 63-70
**`grafana`** — the web page for exploring traces. Signing in is switched off and every visitor is an administrator — acceptable only because the port listens on this computer alone.

@@ 71-75
Its data source (Tempo) is set up from a mounted file; its page is on port **3300**, because the web app already uses 3000.

@@ 77-79
`volumes:` at the top level **declares** the two named volumes used above. Docker creates them on first use and keeps them until they are explicitly deleted (`down -v`).

@@ 80
`tempodata` — Tempo's traces.
