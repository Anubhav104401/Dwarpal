---
fingerprint: aab19b6708112bc6
---
**Grafana's data sources** (Phase 7, D11), set up automatically when it starts (Grafana calls this *provisioning*): Tempo for traces and Prometheus for metrics.

@@ 1
What this file is, and the two data sources it sets up.

@@ 2
The version of this file format.

@@ 3-8
One data source, named Tempo, of type `tempo`, reached through Grafana's own server (`proxy`) at the container's address, and selected by default.

@@ 9-13
The second, Prometheus, at its container's address and port 9090. Its `uid` — a fixed identifier — is set to `prometheus` so that the dashboard file (`dashboards/api.json`) can name it; without one, Grafana would invent a random one and the dashboard couldn't find its data.
