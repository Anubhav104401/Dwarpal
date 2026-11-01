---
fingerprint: 9df6b396e266926c
---
The **background jobs** (§5.8.3): the webhook worker, always running, and maintenance, every hour.

@@ 1-2
The API image's two background jobs. `$image` is worked out once, from the API's image setting.

@@ 3-16
**The webhook worker**: a Deployment of one copy, named and labelled as the others.

@@ 17-23
Its pod: labelled, never root, as the API image's user, with the default system-call filter.

@@ 24-37
One container, running `deliver-webhooks`, with the Secret's values and the settings the API needs, under the same security as the services, and a small share of the computer.

@@ 38-47
**Maintenance**: a **CronJob** — a job Kubernetes starts on a schedule — at 17 minutes past every hour (`17 * * * *`), never two at once (`Forbid`).

@@ 48-53
Each run's pod: retried if it fails (`OnFailure`), never root.

@@ 54-66
One container running `cli maintain`, with the same settings and security.
