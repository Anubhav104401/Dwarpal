---
fingerprint: bed539292ec1bddd
---
**Dwarpal in production** (Phase 8, §5.8.2): every service, on one server, as Docker Compose runs them. It differs from the development compose file (`infra/compose/compose.yaml`) in three ways: the services themselves run here as containers; nothing but Caddy can be reached from outside; and every secret comes from the server's `.env`, never from this file.

@@ 1-4
What this file is: every service of Dwarpal in production, on one server, behind Caddy (ADR-0015); how it is run, with its secrets in `.env` beside it; and where the images come from — GitHub's container registry, tagged with the commit they were built from.

@@ 6
The project's name: containers are called `dwarpal-api-1` and so on.

@@ 8-9
**`x-api-env: &api-env`** — settings shared by the three services built from the API's image. `x-…` sections are ignored by Compose itself; `&api-env` names the block so it can be reused below with `*api-env` (a YAML *anchor*). First: production mode.

@@ 10-12
The database address. The services log in as **`dwarpal_api`**, which is only a member of the restricted `dwarpal_app` role (Phase 4): row-level security binds everything it does, whatever a query tries. The password comes from `.env` (`${…}` is filled in by Compose).

@@ 13-14
Valkey, with its password; and the inference service — each reached by its service's name on the private network Compose creates.

@@ 15
The master key, which seals the token-signing keys (§5.4).

@@ 16-19
The public addresses: tokens name the API (`iss`); sessions' links point to the verify page; and only the site itself may call the API from a browser (CORS) or use the console.

@@ 20-21
Where the models are mounted, and which age model's manifest to use: the stand-in, unless `.env` names another.

@@ 25-31
**Caddy** — the only service with ports open to the internet: 80, 443 over TCP, and 443 over UDP for HTTP/3.

@@ 32-34
The domain and the e-mail address for Let's Encrypt, which the `Caddyfile` reads.

@@ 35-38
Its settings file, mounted read-only, and two named volumes where it keeps its certificates and state between restarts.

@@ 39-40
Start after the services it passes requests to; and start again by itself after a crash or a reboot, unless someone stopped it (`unless-stopped`, on every service).

@@ 42-46
**The web app** — home page, verify page, console. It reaches the API inside the server for the home page's figures, and links to the demo shop's public address.

@@ 47-53
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass. Here Node fetches the home page and exits with 0 (healthy) only if it answers well.

@@ 55-64
**The demo shop.** It reaches the API inside the server, but checks tokens against the API's public name, which tokens carry. Its project, test key and signing secret come from `.env`.

@@ 65-71
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass.

@@ 73-77
**The API**, with the shared settings and the models mounted read-only (`:ro`).

@@ 78-81
It starts only once PostgreSQL, Valkey and the inference service are healthy.

@@ 82-88
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass. Python fetches `/readyz`, which answers only when the API can reach its databases.

@@ 90-99
**The webhook worker** (Phase 4) — the same image, running the `deliver-webhooks` command instead of the API, with the same settings, once the API is healthy.

@@ 101-110
**Maintenance** — the same image again, running `cli maintain` (expire abandoned sessions, tidy the counts) once an hour, for ever: `sh -c` runs the little loop.

@@ 112-116
**The inference service** — the stand-in age model unless `.env` chooses the ONNX model, and two workers: one per core of the Always Free server.

@@ 117-121
Models read-only; and the whole container **read-only** except a small `/tmp` held in memory (`tmpfs`): frames can't be written to disk even by mistake.

@@ 122-128
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass. The first 30 seconds are forgiven: loading the models takes a while.

@@ 130-135
**PostgreSQL 18**, the same image as in development. Its owner, `dwarpal`, has its own password, used only for migrations (`deploy.sh`) and backups.

@@ 136-143
Its data in a named volume, and its health check: `pg_isready` must answer.

@@ 145-149
**Valkey**, keeping its data on disk (`--appendonly`) in a named volume, and asking every client for its password.

@@ 150-157
Its health check pings it with the password, which it gets through its environment (`$$` writes a literal `$`, for the shell inside the container, not for Compose).

@@ 197-201
The named volumes: Docker keeps them across restarts and upgrades. `pgdata` is what the backups copy.

@@ 22-23
Where the services send their metrics. Empty — nothing sent — until `alert_email.py` sets it to the collector; the empty default also keeps the deploy test's rule that every setting without a default is one `gen_secrets.py` writes.

@@ 159-161
**Alerts by email** (§5.8.4): three services, each marked with the profile `alerts`, so Compose skips them until `.env` says `COMPOSE_PROFILES=alerts`. None publishes a port: only the other containers can reach them.

@@ 162-168
The **collector**, the version the laptop already uses, with the server's own settings (`collector.yaml`).

@@ 170-176
**Prometheus**, also the laptop's version. Its data lives in `/prometheus`, kept to 2 GB at most (and 15 days, its default), so it can't fill the disk.

@@ 177-182
Its settings, the shared alert rules and its data volume; it starts after the collector and Alertmanager.

@@ 184-188
**Alertmanager** v0.34.1 (approved 2 Nov). It runs as the user `alert_email.py` recorded — the owner of the password's file, which only that owner may read; without it, as *nobody*.

@@ 189-192
Its settings file, and the password's file at the path the settings name.

@@ 193-195
Its memory of silences and of mails already sent is kept in memory only (`tmpfs`): after a restart, an alert still firing may be mailed once more — better than a mail lost.

@@ 202
The volume holding Prometheus's data.
