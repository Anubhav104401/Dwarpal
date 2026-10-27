---
fingerprint: 38ece4a7a797e8d3
---
**Grafana's data sources** (Phase 7, D11), set up automatically when it starts (Grafana calls this *provisioning*): just one, Tempo.

@@ 1
What this file is.

@@ 2
The version of this file format.

@@ 3-8
One data source, named Tempo, of type `tempo`, reached through Grafana's own server (`proxy`) at the container's address, and selected by default.
