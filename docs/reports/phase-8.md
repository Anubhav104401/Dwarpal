# Phase 8 report — deployment

**Dates:** from 1 Nov 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Design:** [ADR-0015](../adr/0015-single-vm-compose-deployment.md) · **Status:** 🟡 in progress — everything the server will run is written and checked locally; the server, the domain, backups' storage and the first deploy wait for the owner's steps and approvals ([pending decisions](pending-decisions.md): O2b decided, D17, D18, O8, O9)

**Exit (from the roadmap):** a public HTTPS address serving the demo shop, the verify flow and the console; a successful restore drill on record.

## What is built

| Area | Delivered |
| :-- | :-- |
| Server | Oracle Cloud, India South (Hyderabad), Always Free Ampere (O2, O2b: 2 cores, 12 GB). `infra/vm/cloud-init.yaml`: keys-only SSH, no root login; firewall open to 80/443 only; daily security updates (restarts 03:00 IST); Docker and Compose with capped logs; 4 GB swap |
| Images | `services/api/Dockerfile`, `services/inference/Dockerfile` (with Tesseract), `apps/Dockerfile` (web or demo shop): two stages, locked versions, unprivileged users, models mounted not baked |
| Running services | `infra/deploy/compose.yaml`: Caddy (HTTPS from Let's Encrypt; `<domain>`, `api.`, `shop.`) the only service facing the internet; API, webhook worker, hourly maintenance, inference (read-only filesystem), PostgreSQL, Valkey (password) |
| Database login | Services log in as `dwarpal_api`, a member of `dwarpal_app` only — closes Phase 4's open item 1 (the owner login's role switch); the owner's password is used only for migrations and backups |
| Secrets | `infra/deploy/gen_secrets.py`, run on the server: fresh random values, file mode 600, never overwritten |
| Deploy | `infra/deploy/deploy.sh`: pull, migrate as owner, ensure `dwarpal_api`, start and wait for every health check (5 min), else roll back; `.github/workflows/deploy.yml`: by hand only, images built natively on Arm, pushed to GHCR, deployed over SSH with a pinned host key |
| Backups | `infra/deploy/backup.sh`: `pg_dump` streamed into restic (encrypted before leaving the server) with `.env`; 7/4/6 retention; `restic check`. `restore_drill.sh`: restore into a throwaway database and report |
| Operations | `infra/deploy/README.md` (first-time setup), `docs/operations/runbooks.md` (deploy, roll back, rotate keys, restore, incident) |
| Book | §5.8, §5.8.1, §5.8.2; thirteen walkthroughs |

## What was measured

| Check | Result |
| :-- | :-- |
| Production Compose file | `docker compose config` valid with a test `.env` |
| Secrets generator | fresh values each run, 32-byte master key, mode 600, refuses to overwrite (tests) |
| Compose vs generator | every `${NAME}` without a default is written by the generator (test) |
| Shell scripts | parse (`bash -n`); all stop at the first error (`set -euo pipefail`, test) |

## Open items

1. **The server, domain and first deploy** — owner's steps (instance with cloud-init, security list, DNS, GitHub settings: O9) and approvals (base images D17, publishing D18).
2. **Backups and the restore drill** — need the storage bucket and key (O8); the drill's report is Phase 8's exit criterion.
3. **Capacity on 2 cores** — re-run the load test against the server (NFR-05 was met on 4 cores).
4. **Alert delivery** (from Phase 7) — Alertmanager and a destination; the observability profile isn't part of the production Compose file yet.
5. **Helm chart** — written (`infra/helm/dwarpal`: workloads with probes and least privilege, background jobs, ingress, autoscaling, a network policy around the inference service); linting it in CI needs Helm (D19).
6. **Static INT8 and per-domain web builds** — the web image carries the API's address; a domain change means a rebuild.
