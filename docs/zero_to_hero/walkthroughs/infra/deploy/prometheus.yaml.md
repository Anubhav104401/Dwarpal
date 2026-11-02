---
fingerprint: 3c52b99be640c7ea
---
**Prometheus on the server** (§5.8.4): what it collects, which rules it checks, and where it sends the alerts.

@@ 1-2
What Prometheus does on the server: collects the metrics, checks the alert rules — the same file as on a laptop — and hands alerts that fire to Alertmanager.

@@ 3-5
Collect every 15 seconds, and check the rules every 15 seconds.

@@ 7-8
The rules, from `infra/observability/alerts.yaml`, which Compose mounts at this path.

@@ 10-13
Where firing alerts go: Alertmanager, by its name on Compose's private network.

@@ 15-18
What to collect: one target, the collector's port 8889. Prometheus also keeps `up{job="dwarpal"}`, 1 when that collection worked and 0 when not — the `MetricsMissing` alert watches it.
