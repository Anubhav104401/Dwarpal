# Deploying Dwarpal (Phase 8)

One server (Oracle Cloud's Always Free Ampere machine, decision O2b), Docker Compose, and Caddy for HTTPS — as
[ADR-0015](../../docs/adr/0015-single-vm-compose-deployment.md) decided. The runbooks for day-to-day work are in
[docs/operations/runbooks.md](../../docs/operations/runbooks.md).

| File | What it is |
| :-- | :-- |
| [`../vm/cloud-init.yaml`](../vm/cloud-init.yaml) | The server's first-boot setup: keys-only SSH, firewall, updates, Docker |
| [`compose.yaml`](compose.yaml) | Every service, as it runs in production |
| [`Caddyfile`](Caddyfile) | HTTPS and routing: `<domain>`, `api.<domain>`, `shop.<domain>` |
| [`gen_secrets.py`](gen_secrets.py) | Makes the server's `.env` of fresh secrets, on the server |
| [`deploy.sh`](deploy.sh) | Deploys one version; rolls back if it isn't healthy |
| [`backup.sh`](backup.sh) / [`restore_drill.sh`](restore_drill.sh) | Encrypted off-site backups, and the proof they restore |
| [`alert_email.py`](alert_email.py), [`collector.yaml`](collector.yaml), [`prometheus.yaml`](prometheus.yaml) | Alerts by email: the mail settings, and what carries the metrics to the alert rules ([`../observability/alerts.yaml`](../observability/alerts.yaml)) |
| [`../../.github/workflows/deploy.yml`](../../.github/workflows/deploy.yml) | Builds the images on GitHub, publishes them to GHCR, deploys |

## First-time setup

Done once, after the server exists (the owner's steps: account, instance with `cloud-init.yaml`, ports 80/443 open in
the network's security list, the domain bought).

1. **DNS.** At the domain's registrar, point four names at the server's public IP address — four `A` records:
   `@` (the domain itself), `www`, `api` and `shop`. Caddy can't get certificates until these resolve.
2. **Files.** From a checkout of the repository, on your computer:

   ```
   scp infra/deploy/compose.yaml infra/deploy/Caddyfile infra/deploy/*.sh infra/deploy/*.py infra/deploy/collector.yaml \
     infra/deploy/prometheus.yaml infra/observability/alerts.yaml ubuntu@<ip>:/opt/dwarpal/
   ```

3. **Secrets**, made on the server and never copied anywhere else:

   ```
   ssh ubuntu@<ip>
   cd /opt/dwarpal && python3 gen_secrets.py --domain <domain> --email <your email> --ghcr-owner <github account>
   ```

4. **Models.** The services read their models from `/opt/dwarpal/models` (mounted read-only). Copy the face detector,
   face mesh, hand detector, anti-spoofing networks, SFace and the age model's manifest there — the files
   `uv run infra/scripts/fetch_models.py` fetches, plus `models/registry/age/stub/manifest.json`. While no age model is
   certified, live checks are decided by an ID document (decision D24) and the age estimate decides test checks only.
5. **GitHub settings** (repository → Settings):
   - *Variables*: `DWARPAL_PUBLIC_API_URL` = `https://api.<domain>`, `DEPLOY_HOST` = the server's IP,
     `DEPLOY_KNOWN_HOSTS` = the output of `ssh-keyscan <ip>` (so the deploy knows it's talking to the real server);
   - *Secrets*: `DEPLOY_SSH_KEY` = the private half of a **separate** key made only for deploys, whose public half
     is added to `/home/ubuntu/.ssh/authorized_keys` on the server;
   - *Environments*: a `production` environment, ideally requiring your approval before each deploy.
6. **First deploy.** On GitHub: Actions → deploy → Run workflow, **with "Also deploy" unticked** the first time: it
   builds the four images on Arm machines and publishes them to GHCR. GitHub makes a new package private, so then
   make each of the four `dwarpal-*` packages **public** (your profile → Packages → the package → Package settings →
   Change visibility → Public; decision D18): the server pulls public images without logging in. Then run the
   workflow again with "Also deploy" ticked: it builds again, copies this folder's files to the server and runs
   `deploy.sh`. Every later deploy is a single run.
7. **The demo shop's key.** Sign up on the console at `https://<domain>/console`, create a project whose allowed origin
   is `https://shop.<domain>`, and a **test** key. Put the project's ID and the key in `/opt/dwarpal/.env`
   (`DWARPAL_SHOP_PROJECT_ID`, `DWARPAL_SHOP_API_KEY`), then `docker compose up -d shop`.
8. **Backups.** Create an Object Storage bucket `dwarpal-backups` and a *customer secret key* (Oracle's S3-style key),
   write `/opt/dwarpal/backup.env` as described at the top of `backup.sh` (mode 600), store the restic password
   offline as well, then schedule it daily:

   ```
   sudo tee /etc/systemd/system/dwarpal-backup.service >/dev/null <<'EOF'
   [Unit]
   Description=Dwarpal encrypted backup
   [Service]
   Type=oneshot
   User=ubuntu
   ExecStart=/opt/dwarpal/backup.sh
   EOF
   sudo tee /etc/systemd/system/dwarpal-backup.timer >/dev/null <<'EOF'
   [Unit]
   Description=Daily Dwarpal backup
   [Timer]
   OnCalendar=*-*-* 20:30:00
   RandomizedDelaySec=15m
   Persistent=true
   [Install]
   WantedBy=timers.target
   EOF
   sudo systemctl daemon-reload && sudo systemctl enable --now dwarpal-backup.timer
   ```

9. **The restore drill**, once backups exist: `./restore_drill.sh`, and record its report in the Phase 8 report —
   the phase's exit criterion.

10. **Alerts by email** (decided 2 Nov). Make a password for sending mail — for Gmail, an *app password*
    (Google Account → Security → 2-Step Verification → App passwords) — then, on the server:

    ```
    cd /opt/dwarpal && python3 alert_email.py --to <your email> --smtp-host smtp.gmail.com:587 --smtp-user <gmail address>
    docker compose up -d --wait
    ```

    It asks for the password twice without showing it, keeps it in `smtp_password` (readable by you only), writes
    `alertmanager.yml`, and adds `COMPOSE_PROFILES=alerts` to `.env`, so Compose starts the collector, Prometheus
    (`prom/prometheus:v3.13.4`) and Alertmanager (`prom/alertmanager:v0.34.1`, 38 MB). You get a mail when server
    errors spend the month's allowance too fast, when face checks are slow, or when the metrics stop arriving — and
    another when each is over. They watch from inside the server, so if the whole server stops, no mail comes: a free
    outside uptime check of `https://api.<domain>/readyz` covers that.
