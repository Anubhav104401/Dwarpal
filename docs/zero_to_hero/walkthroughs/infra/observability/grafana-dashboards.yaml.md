---
fingerprint: 3cf76c0ccca6f79e
---
**Where Grafana finds dashboards** (Phase 7, D11) — the second kind of provisioning, after data sources: rather than building dashboards by clicking, they are files kept in the repository and loaded when Grafana starts, so everyone sees the same ones and changes go through review.

@@ 1
What this file is.

@@ 2
The version of this file format.

@@ 3-7
One *provider* of dashboards, named `dwarpal`, of type `file`: load every dashboard file in `/var/lib/grafana/dashboards` — the folder where the compose file mounts `infra/observability/dashboards`.
