---
fingerprint: cfbfcef655c108cf
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

@@ 32-38
**Caddy** — the only service with ports open to the internet: 80, 443 over TCP, and 443 over UDP for HTTP/3.

@@ 39-41
The domain and the e-mail address for Let's Encrypt, which the `Caddyfile` reads.

@@ 42-45
Its settings file, mounted read-only, and two named volumes where it keeps its certificates and state between restarts.

@@ 46-48
Start after the services it passes requests to — the web app and the API, but not the shop, which runs only once it has its key (`deploy.sh`); Caddy looks names up as requests arrive, so it finds the shop whenever it is there. And start again by itself after a crash or a reboot, unless someone stopped it (`unless-stopped`, on every service).

@@ 50-54
**The web app** — home page, verify page, console. It reaches the API inside the server for the home page's figures, and links to the demo shop's public address.

@@ 55-61
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass. Here Node fetches the home page and exits with 0 (healthy) only if it answers well.

@@ 63-75
**The demo shop.** It reaches the API inside the server, but checks tokens against the API's public name, which tokens carry. Its project, test key and signing secret come from `.env`. Since 13 Nov also the **policy** its checks follow: `DWARPAL_SHOP_POLICY` from `.env`, or the preset `uk_osa_18` when `.env` doesn't name one (`${…:-uk_osa_18}`). The comment gives the reason: the trained age model has no pass marks for the presets' risk budget.

@@ 76-82
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass.

@@ 84-88
**The API**, with the shared settings and the models mounted read-only (`:ro`).

@@ 89-92
It starts only once PostgreSQL, Valkey and the inference service are healthy.

@@ 93-99
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass. Python fetches `/readyz`, which answers only when the API can reach its databases.

@@ 101-110
**The webhook worker** (Phase 4) — the same image, running the `deliver-webhooks` command instead of the API, with the API's settings but the owner's login (`*owner-env`), once the API is healthy.

@@ 112-121
**Maintenance** — the same image again, running `cli maintain` (expire abandoned sessions, tidy the counts) once an hour, for ever: `sh -c` runs the little loop. Since 9 Nov it logs in as the tables' owner (`*owner-env`), so it sees every organisation's sessions.

@@ 133-137
**The inference service** — the stand-in age model unless `.env` chooses the ONNX model, and two workers: one per core of the Always Free server.

@@ 138-142
Models read-only; and the whole container **read-only** except a small `/tmp` held in memory (`tmpfs`): frames can't be written to disk even by mistake.

@@ 143-149
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass. The first 30 seconds are forgiven: loading the models takes a while.

@@ 151-156
**PostgreSQL 18**, the same image as in development. Its owner, `dwarpal`, has its own password, used only for migrations (`deploy.sh`) and backups.

@@ 157-164
Its data in a named volume, and its health check: `pg_isready` must answer.

@@ 166-170
**Valkey**, keeping its data on disk (`--appendonly`) in a named volume, and asking every client for its password.

@@ 171-178
Its health check pings it with the password, which it gets through its environment (`$$` writes a literal `$`, for the shell inside the container, not for Compose).

@@ 218-222
The named volumes: Docker keeps them across restarts and upgrades. `pgdata` is what the backups copy.

@@ 22-23
Where the services send their metrics. Empty — nothing sent — until `alert_email.py` sets it to the collector; the empty default also keeps the deploy test's rule that every setting without a default is one `gen_secrets.py` writes.

@@ 180-182
**Alerts by email** (§5.8.4): three services, each marked with the profile `alerts`, so Compose skips them until `.env` says `COMPOSE_PROFILES=alerts`. None publishes a port: only the other containers can reach them.

@@ 183-189
The **collector**, the version the laptop already uses, with the server's own settings (`collector.yaml`).

@@ 191-197
**Prometheus**, also the laptop's version. Its data lives in `/prometheus`, kept to 2 GB at most (and 15 days, its default), so it can't fill the disk.

@@ 198-203
Its settings, the shared alert rules and its data volume; it starts after the collector and Alertmanager.

@@ 205-209
**Alertmanager** v0.34.1 (approved 2 Nov). It runs as the user `alert_email.py` recorded — the owner of the password's file, which only that owner may read; without it, as *nobody*.

@@ 210-213
Its settings file, and the password's file at the path the settings name.

@@ 214-216
Its memory of silences and of mails already sent is kept in memory only (`tmpfs`): after a restart, an alert still firing may be mailed once more — better than a mail lost.

@@ 223
The volume holding Prometheus's data.

@@ 25-27
**The owner's settings** (9 Nov): the jobs that work across every organisation — webhook delivery, the hourly maintenance, the operator's tools — log in as the tables' owner. Row-level security shows the services' login, `dwarpal_api`, only the organisation a request names; a job that names none would see no rows at all and quietly find nothing to do — no webhook sent, no session expired, nothing purged after its retention period. That was the case until 9 Nov, found by reading before any deploy.

@@ 28-30
`x-owner-env` is the API's settings (`<<: *api-env` copies every entry of that anchor in) with one entry replaced: the database address, with the owner's name and password.

@@ 123-124
**`operator`** (9 Nov) — the operator's tools, run by hand: the migrations (`deploy.sh`) and the runbooks' commands, such as rotating or stopping a website's key.

@@ 125-131
The API's image with the command line as its entrypoint, so `docker compose run --rm operator migrate` runs `python -m dwarpal_api.cli migrate`; the owner's login; and the models. Its profile, `tools`, is never switched on, so `up` never starts it — `run` names it, which is enough.
