---
fingerprint: 8d8a84ed68a2b48d
---
The **Docker Compose file** for local development. It describes two containers — the PostgreSQL database and Valkey — and how to run them, so that one command starts both, healthy and ready (§4.5). In Phase 1 it grows to include our own services too.

YAML reminder: indentation shows what belongs to what, and `#` starts a comment.

@@ 1-3
Comments: what the file is for, and the exact commands to start and stop it.

- `-f` names this file.
- `up -d` starts the containers in the background (*detached*).
- `--wait` returns only when every health check passes.
- `down -v` also deletes the data **v**olumes — a fresh start.

@@ 5-7
**Seeing traces and metrics** (Phase 7): start the observability containers too, run the API with the collector's address, and open Grafana in a browser — its "Dwarpal API" dashboard — or Prometheus's own page, which lists the alerts and whether any is firing.

@@ 9
`name: dwarpal` — the **project name**. Compose prefixes everything it creates with it (`dwarpal-postgres-1`, `dwarpal_pgdata`), so these containers never clash with another project's.

@@ 11
`services:` — the list of containers to run, each under its own name.

@@ 12
`postgres:` — the first service, the PostgreSQL database. Inside Compose's private network, other containers will reach it simply by the name `postgres`.

@@ 13
`image: postgres:18.6-alpine3.24` — the official PostgreSQL image, pinned: version **18.6**, built on **Alpine Linux 3.24** (a tiny Linux distribution, so the image is small). Version 18 is required for the built-in `uuidv7()` function (ADR-0011).

@@ 14
`environment:` — settings passed into the container. The official image reads these on its first start.

@@ 15-17
The database name, user and password. `${POSTGRES_DB:-dwarpal}` means "use the variable `POSTGRES_DB` if it is set — for example in an `.env` file — otherwise use `dwarpal`". The default password is labelled `local-only`, as a reminder that it must never be used anywhere real.

@@ 18-19
`ports:` — **publish** the container's port 5432 on the computer, so programs outside Docker (our services during development, a database viewer) can connect.

The `127.0.0.1:` at the front is a security choice. It publishes the port **only to this computer**, not to every device on the same Wi-Fi network. The middle number can be changed through `POSTGRES_PORT`, in case 5432 is already in use.

@@ 20-21
`volumes:` — keep the database's files in a **named volume** called `pgdata`, so the data survives when the container is replaced.

The volume is mounted at `/var/lib/postgresql`, the location **PostgreSQL 18's** image expects. Older versions used `/var/lib/postgresql/data`; the change makes future major-version upgrades easier.

@@ 22
`healthcheck:` — how Docker decides the database is truly *ready*, not just started.

@@ 23
`test` — the check: run `pg_isready` inside the container, for our user and database. `CMD-SHELL` means "run this through the container's shell".

The doubled `$$` is an escape. A single `$` would be filled in by Compose on your computer; `$$` becomes a literal `$`, so the variable is filled in *inside* the container, by the container's shell.

@@ 24-26
Check every 5 seconds, allow each check 3 seconds, and only declare the container *unhealthy* after 20 failures in a row — about 100 seconds, which gives a first start plenty of time.

@@ 27
`restart: unless-stopped` — if the database crashes or the computer restarts, Docker starts it again automatically. The exception is when you stopped it yourself.

@@ 29
`valkey:` — the second service: Valkey, the fast short-term memory (ADR-0011).

@@ 30
`image: valkey/valkey:9.1.2-alpine3.24` — the official Valkey image, version 9.1.2 on Alpine 3.24, pinned.

@@ 31
`command:` — the program the container runs: `valkey-server` with **append-only** persistence switched on. Every change is also appended to a log file on disk, so the queued background jobs and other short-lived state survive a restart.

@@ 32-33
Publish Valkey's port 6379 to **this computer only**, with an optional override through `VALKEY_PORT`.

@@ 34-35
Keep Valkey's files in the named volume `valkeydata`, mounted at `/data`, where the image stores them.

@@ 36-40
The health check: `valkey-cli ping` must answer (with `PONG`). Same timing as for PostgreSQL. `CMD` (instead of `CMD-SHELL`) runs the program directly, since no shell features are needed.

@@ 52
Restart it if it stops.

@@ 54-55
**The observability containers** (Phase 7, decision D11): the collector passes traces to Tempo and offers metrics to Prometheus, and Grafana shows both. Each has `profiles: [observability]`, so a plain `up` leaves them out; they start only when asked for.

@@ 56-64
**`collector`** — the OpenTelemetry collector, which receives the API's traces and metrics over HTTP on port 4318 (on this computer only, `127.0.0.1`) and passes them on (`collector.yaml`). Its configuration file is mounted read-only from `infra/observability`; it starts after Tempo (`depends_on`).

@@ 66-75
**`tempo`** — Grafana Tempo, which stores traces and answers searches, on port 3200. Its data lives in a named volume. It runs as root inside its container (`user: "0"`) because the fresh volume belongs to root and Tempo's own user couldn't write to it.

@@ 77-86
**`prometheus`** — stores the metrics as time series, collecting them from the collector every 15 seconds, and checks the alert rules against them. Its two files — what to collect (`prometheus.yaml`) and the rules (`alerts.yaml`) — are mounted read-only; its page is on port 9090, on this computer only. It starts after the collector. Its data aren't kept in a volume: they are rebuilt from scratch whenever it restarts, which is fine on a laptop.

@@ 88-95
**`grafana`** — the web page for exploring traces and metrics. Signing in is switched off and every visitor is an administrator — acceptable only because the port listens on this computer alone.

@@ 96-102
Three mounted files and a folder set it up: its data sources (Tempo and Prometheus), where to find dashboards, and the dashboards themselves. Its page is on port **3300**, because the web app already uses 3000; it starts after both of its sources.

@@ 104-106
`volumes:` at the top level **declares** the two named volumes used above. Docker creates them on first use and keeps them until they are explicitly deleted (`down -v`).

@@ 107
`tempodata` — Tempo's traces.

@@ 4
And a note that the OCR container (§5.6.2) starts with the databases.

@@ 41
Restart Valkey if it stops.

@@ 43-44
**The OCR container** (Phase 6, decision D6b): Tesseract, for reading documents' MRZ, kept in a container rather than installed on the computer. It sits idle; the inference service runs `tesseract` inside it with `docker exec`, one picture at a time through a pipe.

@@ 45-47
Built from `infra/ocr/Dockerfile` (§5.6.2), and named `dwarpal-ocr:local` — a local name, never pushed anywhere.

@@ 48-51
Locked down, since it handles document photos:
- `network_mode: none` — no network at all: pictures arrive through `docker exec`'s pipe, and nothing can leave;
- `read_only: true` — its files can't be changed (Tesseract needs no disk: it reads and writes through pipes);
- `cap_drop: [ALL]` — none of Linux's special privileges;
- `no-new-privileges` — and no way to gain any.
