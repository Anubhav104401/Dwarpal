---
fingerprint: 8958c945a6ae526d
---
**Helm** is Kubernetes' package manager: a *chart* is a folder of templates that, filled in with settings, become Kubernetes' own descriptions of what to run. `Chart.yaml` names the chart (§5.8.3).

@@ 1-2
What this is — the same services as the Compose file, for a **Kubernetes** cluster — and its place: the single server stays the plan (ADR-0015); this is ready for whoever outgrows it.

@@ 3-6
The chart format's version (`v2`, Helm 3's), the chart's name, its description, and its kind: an application (not a library of templates).

@@ 7-9
The chart's own version, and Dwarpal's version it installs unless told otherwise — the image tag.
