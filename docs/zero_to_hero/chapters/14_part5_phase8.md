## 5.8 Phase 8 — deployment

Phases 1–7 run on one computer. Phase 8 puts Dwarpal on the internet: a server, a domain, HTTPS, deployments that can be undone, and backups that are proven to restore. From the roadmap (§3.9):

| Area | What | Status |
| :-- | :-- | :-- |
| Server | A cloud server, prepared by a script: hardened SSH, a firewall, automatic security updates | 🟡 the first-boot script (§5.8.1); the account exists, the server isn't made yet |
| Running services | The production Compose file with Caddy; the domain and its DNS; images on GHCR; deployment over SSH, checked and reversible | 🗓 |
| Data safety | Encrypted off-site backups, and a restore drill on record | 🗓 |
| Operations | Runbooks: deploy, roll back, rotate keys, restore, incidents | 🗓 |
| Kubernetes | A Helm chart, checked in CI | 🗓 |

### 5.8.1 Choosing the server, and preparing it

The owner chose **Oracle Cloud's free tier** (decision O2), in its India South (Hyderabad) region — near the users of the India launch. Oracle's free Arm ("Ampere") machines are the most generous free servers available, but the free amount has shrunk: **2 cores and 12 GB of memory** for an Always Free account, or 4 cores and 24 GB free on an upgraded, pay-as-you-go one. The owner chose to stay on Always Free (O2b), so the server is sized to 2 cores from the start: nothing then breaks when the account's 30-day trial, with its far larger limits, ends.

A server must be safe before anything runs on it. Instead of typing commands into it, Dwarpal describes it in one file that the server reads on its first boot:

!walk infra/vm/cloud-init.yaml

!!! honest "Honest limitation"
    - **Capacity on 2 cores is unmeasured.** The load test met its target — 50 people checking at once — on 4 cores (§5.7.4). On 2 it will be measured again once the server runs; until then, expect about half.
    - **Oracle may reclaim an idle free server** (for Arm machines, memory use under 20 % for a week). A running Dwarpal keeps well above that, but a stopped one could be taken back.
