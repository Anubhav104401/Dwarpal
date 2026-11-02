## 5.8 Phase 8 — deployment

Phases 1–7 run on one computer. Phase 8 puts Dwarpal on the internet: a server, a domain, HTTPS, deployments that can be undone, and backups that are proven to restore. From the roadmap (§3.9):

| Area | What | Status |
| :-- | :-- | :-- |
| Server | A cloud server, prepared by a script: hardened SSH, a firewall, automatic security updates | 🟡 the first-boot script (§5.8.1); the account exists, the server isn't made yet |
| Running services | The production Compose file with Caddy; the domain and its DNS; images on GHCR; deployment over SSH, checked and reversible | 🟡 all written and checked here (§5.8.2); waits for the server, the domain, and approval to pull base images and publish (D17, D18) |
| Data safety | Encrypted off-site backups, and a restore drill on record | 🟡 backup and drill scripts (§5.8.2); wait for a storage bucket (O8) and restic's image (D17) |
| Operations | Runbooks: deploy, roll back, rotate keys, restore, incidents | 🟢 `docs/operations/runbooks.md` |
| Kubernetes | A Helm chart, checked in CI | 🟢 the chart (§5.8.3), linted and rendered by CI with Helm 4 (D19) |

### 5.8.1 Choosing the server, and preparing it

The owner chose **Oracle Cloud's free tier** (decision O2), in its India South (Hyderabad) region — near the users of the India launch. Oracle's free Arm ("Ampere") machines are the most generous free servers available, but the free amount has shrunk: **2 cores and 12 GB of memory** for an Always Free account, or 4 cores and 24 GB free on an upgraded, pay-as-you-go one. The owner chose to stay on Always Free (O2b), so the server is sized to 2 cores from the start: nothing then breaks when the account's 30-day trial, with its far larger limits, ends.

A server must be safe before anything runs on it. Instead of typing commands into it, Dwarpal describes it in one file that the server reads on its first boot:

!walk infra/vm/cloud-init.yaml

!!! honest "Honest limitation"
    - **Capacity on 2 cores is unmeasured.** The load test met its target — 50 people checking at once — on 4 cores (§5.7.4). On 2 it will be measured again once the server runs; until then, expect about half.
    - **Oracle may reclaim an idle free server** (for Arm machines, memory use under 20 % for a week). A running Dwarpal keeps well above that, but a stopped one could be taken back.

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

!walk infra/deploy/Caddyfile

!walk infra/deploy/gen_secrets.py

!walk infra/deploy/deploy.sh

!walk infra/deploy/backup.sh

!walk infra/deploy/restore_drill.sh

!walk .github/workflows/deploy.yml

!walk services/api/tests/test_deploy.py

The `.gitignore` gained rules for private keys and secrets, and a `.dockerignore` keeps installed packages, builds, secrets and data out of every image's build.

!!! honest "Honest limitation"
    - **Nothing here has run on a server yet.** The Compose file is validated, the secrets generator and the scripts' safety settings are tested, and the shell scripts parse; but the images haven't been built (pulling their base images needs approval, D17), nothing is published (D18), and the deploy, the backups and the drill run only once the server, the domain and a storage bucket exist (O2, O8).
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
