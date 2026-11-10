## 5.8 Phase 8 — deployment

Phases 1–7 run on one computer. Phase 8 puts Dwarpal on the internet: a server, a domain, HTTPS, deployments that can be undone, and backups that are proven to restore. From the roadmap (§3.9):

| Area | What | Status |
| :-- | :-- | :-- |
| Server | A cloud server, prepared by a script: hardened SSH, a firewall, automatic security updates | ✅ live since 10 Nov 2026: the first-boot script's steps, run over SSH (Part 6) |
| Running services | The production Compose file with Caddy; the domain and its DNS; images on GHCR; deployment over SSH, checked and reversible | ✅ deployed 10 Nov at `dwarpal-age.duckdns.org` (§5.8.2, Part 6) |
| Data safety | Encrypted off-site backups, and a restore drill on record | ✅ nightly backups to Object Storage; the restore drill passed on the server, 10 Nov (Part 6, §6.12) |
| Operations | Runbooks: deploy, roll back, rotate keys, restore, incidents | 🟢 `docs/operations/runbooks.md` |
| Kubernetes | A Helm chart, checked in CI | 🟢 the chart (§5.8.3), linted and rendered by CI with Helm 4 (D19) |

### 5.8.1 Choosing the server, and preparing it

The owner chose **Oracle Cloud's free tier** (decision O2), in its India South (Hyderabad) region — near the users of the India launch. Oracle's free Arm ("Ampere") machines are the most generous free servers available, but the free amount has shrunk: **2 cores and 12 GB of memory** for an Always Free account, or 4 cores and 24 GB free on an upgraded, pay-as-you-go one. The owner chose to stay on Always Free (O2b), so the server is sized to 2 cores from the start: nothing then breaks when the account's 30-day trial, with its far larger limits, ends.

A server must be safe before anything runs on it. Instead of typing commands into it, Dwarpal describes it in one file that the server reads on its first boot:

!walk infra/vm/cloud-init.yaml

On launch night Oracle's console refused this file as the initialization script, so its steps were run over SSH right after the server started, with the same result (§6.2, §6.4).

!!! honest "Honest limitation"
    - **Capacity on 2 cores is unmeasured.** The load test met its target — 50 people checking at once — on 4 cores (§5.7.4). On 2 it will be measured again once the server runs; until then, expect about half.
    - **Oracle may reclaim an idle free server.** It counts one as idle when, over 7 days, CPU use (95th percentile), network use and, for Arm machines, memory use all stay under 20 %. This chapter first said a running Dwarpal keeps well above that. Measured on the live server (10 Nov), it doesn't: with few visitors it uses about 12 % of the memory and almost no CPU. The account is now Pay As You Go; Oracle's page on reclamation names only *Always Free* instances and doesn't say whether upgraded accounts are spared. Until that is confirmed, the outside check (§5.8.5) would email the owner if the server stopped.

### 5.8.2 Everything the server will run

While the owner creates the server, everything that will run on it can be written and checked here. Five pieces:

1. **Container images** — one recipe per service. Each installs exactly the locked versions, runs as an unprivileged user, and carries no build tools. The two web apps share one recipe; the inference service gains Tesseract, which in development runs in its own container.
2. **The production Compose file** — every service on one server. Only **Caddy** faces the internet, getting HTTPS certificates by itself; everything else talks on a private network. The services log in to the database as `dwarpal_api`, a member of the restricted role only: this closes the Phase 4 item about the owner-login role switch. The inference service can't write to its disk at all.
3. **Secrets made on the server**: `gen_secrets.py` writes every password and key, fresh and random, into a file only its owner can read, and refuses to replace it.
4. **A deploy that undoes itself**: `deploy.sh` migrates, starts the new version and waits for every health check; if any fails within five minutes, it puts the previous version back. A GitHub workflow, started by hand only, builds the images on Arm machines, publishes them and runs it.
5. **Backups that are proven**: `backup.sh` streams the database straight into **restic**, which encrypts it before it leaves the server; `restore_drill.sh` restores the latest backup into a throwaway database and reports what came back — the record Phase 8's exit asks for.

!!! key "Key idea — nothing on the server is done by hand"
    Every step from an empty account to a running Dwarpal is a file in this repository: the first-boot script, the images, the Compose file, the deploy, the backups. A person runs them in order (`infra/deploy/README.md`), and the runbooks (`docs/operations/runbooks.md`) say what to do when something goes wrong. A lost server is rebuilt from Git and the latest backup.

!walk services/api/Dockerfile

!walk services/inference/Dockerfile

!walk apps/Dockerfile

!walk infra/deploy/compose.yaml

**The name.** Caddy needs a name to get certificates for, and the sites live under it: `<domain>`, `api.<domain>`, `shop.<domain>`. On 8 November the owner chose a **free DuckDNS name** (decision D40) — such as `dwarpal-age.duckdns.org` — so the whole deployment stays free. Two things were checked before relying on it, on 9 November. DuckDNS answers *every* name under one with the same address (asked of three names: `api.`, `shop.www.` and a random one all answered), so nothing needs adding for `api.` and `shop.`. And `duckdns.org` is on the **Public Suffix List** — the list browsers use to tell where one site ends and the next begins — so `dwarpal-age.duckdns.org` is a site of its own: the console's sign-in cookie works between it and its `api.` exactly as with a bought domain, and Let's Encrypt's limits aren't shared with every other DuckDNS user. `dwarpal.duckdns.org` itself turned out to be taken.

!walk infra/deploy/Caddyfile

!walk infra/deploy/gen_secrets.py

!walk infra/deploy/deploy.sh

!walk infra/deploy/backup.sh

!walk infra/deploy/restore_drill.sh

!walk .github/workflows/deploy.yml

!walk services/api/tests/test_deploy.py

The `.gitignore` gained rules for private keys and secrets, and a `.dockerignore` keeps installed packages, builds, secrets and data out of every image's build.

!walk .dockerignore

!!! honest "Honest limitation"
    - **Nothing here has run on a server yet.** The Compose file is validated, the secrets generator and the scripts' safety settings are tested, and the shell scripts parse; and since 9 November CI builds all four images on GitHub's Arm machines on every push — the base images were approved for those machines (D17) — and starts each as far as it can alone (the `images` job). Its first run failed, usefully: the Python images lacked the Python SDK's `pyproject.toml`, and the model fetcher lacked httpx — both would have stopped the first deploy. Each is fixed and guarded by a test. A third such trap was found by reading rather than building: on the first deploy the demo shop has no key yet, can't serve a page, and `deploy.sh` would have waited for it in vain and rolled back; it now leaves the shop out until its key is in `.env`, and a test runs the script with a stand-in `docker` to prove it. A fourth came when CI started the inference image as the server does — read-only, with the fetched models: it reported the **anti-spoofing networks missing**. They are served as ONNX files made from PyTorch weights on the owner's computer, and the README's model step named only what the fetcher fetches; a server set up by it would have refused every live check. The README now lists the exact files, and every deploy reports whether the networks are loaded. Finally, the API's image now **rehearses the server's first deploy** in CI: the real secrets generator and Compose file, the migrations, the restricted `dwarpal_api` login, the API in production mode, a real backup and the real restore drill. It found the fifth trap — the drill asked a fresh PostgreSQL whether it was ready on its socket alone, and caught the temporary server PostgreSQL's image runs while setting itself up, which then shut down under it. The drill now waits for the real server, and the rehearsal restores a backup on every push. A sixth was found by reading the code beside it: the webhook worker and the hourly maintenance shared the API's settings, so they logged in as `dwarpal_api` — and row-level security shows that login only the organisation a request names. Naming none, they would have found nothing to do: no webhook sent, no abandoned session announced, nothing purged after its retention period, all without an error. They now log in as the tables' owner, as the operator's tools do through a new `operator` service; the rehearsal checks they see every organisation. But nothing is published yet (D18), and the deploy, the backups and the drill run only once the server, the domain and a storage bucket exist (O2, O8).
    - **Each web image is built for one domain**: Next.js writes the API's public address into the code it builds.
    - **Rolling back doesn't undo migrations.** That is safe only if every migration works with the code before it too — a rule the runbook states and reviews must keep.

### 5.8.3 A Helm chart, for when one server isn't enough

ADR-0015 chose one server, and keeps a **Helm chart** ready for a cluster: Kubernetes runs many machines as one, moving services between them and adding copies when they're busy. The chart describes the same services as the Compose file, with what a cluster adds:

- **probes** — Kubernetes sends a copy traffic only once it answers its health address, and restarts it when it stops;
- **autoscaling** — more copies of the API and the inference service when their CPU passes 70 %;
- **a network policy** — the inference service, which sees face frames, can be reached from the API only;
- **least privilege** everywhere: never root, read-only files, no Linux powers, scratch space in memory only.

The databases aren't in the chart: a cluster normally uses managed ones, whose addresses come, with the other secrets, from a Secret the cluster already holds.

!walk infra/helm/dwarpal/Chart.yaml

!walk infra/helm/dwarpal/values.yaml

!walk infra/helm/dwarpal/templates/workloads.yaml

!walk infra/helm/dwarpal/templates/jobs.yaml

!walk infra/helm/dwarpal/templates/ingress.yaml

!walk infra/helm/dwarpal/templates/scaling-and-network.yaml

A small file of shared template pieces (`templates/_helpers.tpl`) builds each image's full name and the labels every object carries.

!!! honest "Honest limitation"
    The chart is checked on every push — CI lints it and renders every template with Helm 4 (decision D19, 2 Nov) — but it has never been installed on a real cluster. Rendering proves the templates are well formed, not that the services run well under Kubernetes.

### 5.8.4 Alerts by email

Phase 7 wrote the alert rules — server errors spending the month's allowance too fast, slow face checks — but on a laptop they only lit up a page nobody was watching. On 2 November the owner chose **email**: when a rule fires, a mail arrives, and another when it is over.

Three more programs do it, all on the server and none reachable from outside it. The API sends its counts to the **collector**; **Prometheus** collects them every 15 seconds and checks the rules; **Alertmanager** groups what fires and sends the mail. They stay off until the owner runs one script, which asks for the mail account's password without showing it and turns them on.

!walk infra/deploy/alert_email.py

!walk infra/deploy/collector.yaml

!walk infra/deploy/prometheus.yaml

The rules themselves are the laptop's (`infra/observability/alerts.yaml`, §5.7), with one more: if Prometheus can't reach the collector for five minutes, that is an alert too — otherwise a broken pipe would look like a quiet, healthy service.

!!! honest "Honest limitation"
    Everything here runs on the server it watches. If the whole server stops, no mail comes: the outside check (§5.8.5) covers that. The checks that the settings are valid run in CI, and since 9 November CI also rehearses the whole chain: it switches alerts on as the README does, starts the three programs with the files `alert_email.py` wrote, and requires the API's counts to reach Prometheus, the availability rule to compute a share, the rules to be loaded and Alertmanager to be known. Only the mail itself hasn't been sent: there is no mail server in CI, so that waits for the server.

### 5.8.5 Watching from outside

An alarm inside a house can't report that the house burned down. For that, the owner chose (decision D33) a check from somewhere else that costs nothing and needs no new account: a **scheduled GitHub workflow**. Every 15 minutes GitHub asks the API whether it is ready, loads the home page, and reads both HTTPS certificates. When any of that fails, the run fails — and GitHub emails the repository's owner about failed runs by itself.

!walk .github/workflows/uptime.yml

The certificate check looks a week ahead. Caddy renews a certificate when a third of its life is left (a month, for Let's Encrypt's 90-day certificates), so one with under a week left means renewal has been failing for weeks — and the check says so while there is still time, instead of on the day browsers start refusing the site.

!!! honest "Honest limitation"
    - **GitHub's schedules are best effort**: a run may start a few minutes late, or — at GitHub's busiest — be skipped. An outage is reported within about 15 to 30 minutes, not to the second.
    - **GitHub switches off schedules** in a public repository after 60 days without activity; the README says how to switch it back on.
    - **It sees what a visitor sees**, from GitHub's machines far from the server: it can't tell a broken server from a broken network between them, and doesn't run a face check (that needs a camera).

