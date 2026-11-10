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
| [`../../.github/workflows/uptime.yml`](../../.github/workflows/uptime.yml) | Checks the live server from outside every 15 minutes; GitHub emails you when a check fails |

## First-time setup

Done once, after the server exists (the owner's steps: account, instance with `cloud-init.yaml`, ports 80/443 open in
the network's security list, and a name for it). Done on 10 Nov 2026 for `dwarpal-age.duckdns.org`.

**If Oracle refuses `cloud-init.yaml`** ("Incorrectly formatted request", as it did on 10 Nov), create the instance
with the initialization script empty, then run the same steps over SSH as root: the `write_files` contents into their
paths, the `packages` with `apt-get install`, and the `runcmd` lines in order (`iptables-persistent` asks two
questions on install: answer them first with `debconf-set-selections`). The result is the same server.

1. **A name for the server** — the *domain* in the steps below. Either:
   - **A free DuckDNS name** (decision D40). Sign in at [duckdns.org](https://www.duckdns.org) with an account you
     already have (GitHub, Google and others), add a name, type the server's public IP address into its *current ip*
     box and press *update ip*. The domain is then `<name>.duckdns.org`. `dwarpal` itself is taken; `dwarpal-age`
     and `getdwarpal` were free on 9 Nov 2026. Nothing else to add: DuckDNS answers every name under yours —
     `www.`, `api.`, `shop.` — with the same address. Oracle keeps an instance's public address while it is
     stopped and releases it only when the instance is deleted, so this is done once; a new instance means typing
     its address there again.
   - **A domain you own.** At its registrar, point four names at the server's public IP address — four `A` records:
     `@` (the domain itself), `www`, `api` and `shop`.

   Caddy can't get certificates until the names resolve: `nslookup api.<domain>` should answer with the server's
   address. A DuckDNS name works like a bought one: duckdns.org is on the
   [Public Suffix List](https://publicsuffix.org/), so browsers and Let's Encrypt treat `<name>.duckdns.org` as a site
   of its own — the console's sign-in works between `<domain>` and `api.<domain>`, and certificate limits aren't
   shared with other DuckDNS names. DuckDNS is free and run by volunteers, so a bought domain is the sturdier choice
   once real websites depend on Dwarpal. Moving to one later means a new `DWARPAL_DOMAIN` in `.env`, a new
   `DWARPAL_PUBLIC_API_URL` on GitHub (the web image is built with the API's address), the demo shop's allowed origin
   changed in the console, and a deploy; tokens issued before then name the old address as their issuer.

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

   The domain is the bare name, such as `dwarpal-age.duckdns.org` — no `https://` and no `/`; the script refuses
   anything else before writing a single secret.

4. **Models.** The services read their models from `/opt/dwarpal/models` (mounted read-only). On your computer,
   `uv run infra/scripts/fetch_models.py` fetches them; the two **anti-spoofing networks** come as PyTorch weights and
   are served as ONNX files, which `uv run --package dwarpal-ml python -m dwarpal_ml.antispoof` makes from them
   (done on this computer on 20 Oct: the `.onnx` files are already in `models/third_party`). Then copy exactly these:

   ```
   ssh ubuntu@<ip> mkdir -p /opt/dwarpal/models/third_party /opt/dwarpal/models/registry/age/stub
   cd models
   scp third_party/face_detection_yunet_2023mar.onnx third_party/face_landmarker.task \
     third_party/hand_landmarker.task third_party/face_recognition_sface_2021dec_int8.onnx \
     third_party/minifasnet_v2_2.7.onnx third_party/minifasnet_v1se_4.0.onnx \
     ubuntu@<ip>:/opt/dwarpal/models/third_party/
   scp registry/age/stub/manifest.json ubuntu@<ip>:/opt/dwarpal/models/registry/age/stub/
   ```

   Without the two `minifasnet_*.onnx` files the server still starts, but **every live check is refused**: a live
   session is never decided without the anti-spoofing verdict. `deploy.sh` says after each deploy whether they are
   loaded. While no age model is certified, live checks are decided by an ID document (decision D24) and the age
   estimate decides test checks only.
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
   (`DWARPAL_SHOP_PROJECT_ID`, `DWARPAL_SHOP_API_KEY`), then `docker compose up -d shop`. (Until then `deploy.sh`
   leaves the shop out: without its key it can't serve a page, and every deploy would wait for it in vain.)
8. **Backups.** Create an Object Storage bucket `dwarpal-backups` and a *customer secret key* (Oracle's S3-style key),
   write `/opt/dwarpal/backup.env` as described at the top of `backup.sh` (mode 600), store the restic password
   offline as well, then schedule it daily. The scripts take the storage's region from its address (Oracle refuses
   requests signed for another region with a bare "Access Denied"). A brand-new secret key may be refused now and
   then for its first few minutes: run the backup again.

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
    another when each is over. They watch from inside the server, so if the whole server stops, no mail comes: the
    outside check covers that (step 11).

11. **The outside check** (decision D33) needs nothing more: once `DWARPAL_PUBLIC_API_URL` is set (step 5), the
    [`uptime`](../../.github/workflows/uptime.yml) workflow asks `https://api.<domain>/readyz` and the home page every
    15 minutes, and checks that both certificates last another week. When a check fails, GitHub emails whoever last
    changed the workflow's schedule — the repository's owner — as long as your account's notification settings
    (*Settings → Notifications*, under *Actions*) email you about failed workflows, as they do unless changed. Two
    things to know: GitHub may run a schedule a few minutes late, and it switches off schedules in a public repository
    after 60 days without activity such as a commit — *Actions → uptime → Enable workflow* turns it back on. To try it
    at once: *Actions → uptime → Run workflow*.
