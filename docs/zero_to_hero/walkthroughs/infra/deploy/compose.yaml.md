---
fingerprint: 89bd3d3d459412eb
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

@@ 23-29
**Caddy** — the only service with ports open to the internet: 80, 443 over TCP, and 443 over UDP for HTTP/3.

@@ 30-32
The domain and the e-mail address for Let's Encrypt, which the `Caddyfile` reads.

@@ 33-36
Its settings file, mounted read-only, and two named volumes where it keeps its certificates and state between restarts.

@@ 37-38
Start after the services it passes requests to; and start again by itself after a crash or a reboot, unless someone stopped it (`unless-stopped`, on every service).

@@ 40-44
**The web app** — home page, verify page, console. It reaches the API inside the server for the home page's figures, and links to the demo shop's public address.

@@ 45-51
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass. Here Node fetches the home page and exits with 0 (healthy) only if it answers well.

@@ 53-62
**The demo shop.** It reaches the API inside the server, but checks tokens against the API's public name, which tokens carry. Its project, test key and signing secret come from `.env`.

@@ 63-69
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass.

@@ 71-75
**The API**, with the shared settings and the models mounted read-only (`:ro`).

@@ 76-79
It starts only once PostgreSQL, Valkey and the inference service are healthy.

@@ 80-86
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass. Python fetches `/readyz`, which answers only when the API can reach its databases.

@@ 88-97
**The webhook worker** (Phase 4) — the same image, running the `deliver-webhooks` command instead of the API, with the same settings, once the API is healthy.

@@ 99-108
**Maintenance** — the same image again, running `cli maintain` (expire abandoned sessions, tidy the counts) once an hour, for ever: `sh -c` runs the little loop.

@@ 110-114
**The inference service** — the stand-in age model unless `.env` chooses the ONNX model, and two workers: one per core of the Always Free server.

@@ 115-119
Models read-only; and the whole container **read-only** except a small `/tmp` held in memory (`tmpfs`): frames can't be written to disk even by mistake.

@@ 120-126
A **health check**: Docker asks the service every 15 seconds whether it is working (5 seconds to answer, 5 failures in a row before it counts as unhealthy, the first 20 seconds forgiven while it starts). `deploy.sh` waits for these to pass. The first 30 seconds are forgiven: loading the models takes a while.

@@ 128-133
**PostgreSQL 18**, the same image as in development. Its owner, `dwarpal`, has its own password, used only for migrations (`deploy.sh`) and backups.

@@ 134-141
Its data in a named volume, and its health check: `pg_isready` must answer.

@@ 143-147
**Valkey**, keeping its data on disk (`--appendonly`) in a named volume, and asking every client for its password.

@@ 148-155
Its health check pings it with the password, which it gets through its environment (`$$` writes a literal `$`, for the shell inside the container, not for Compose).

@@ 157-161
The named volumes: Docker keeps them across restarts and upgrades. `pgdata` is what the backups copy.
