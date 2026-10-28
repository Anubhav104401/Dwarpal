---
fingerprint: 09842c283564837f
---
**Prometheus's settings** (Phase 7, D11): **Prometheus** is a database for numbers that change over time — *time series*, such as "requests answered so far, by route". It collects them itself, by visiting an address on a timer (*scraping*), keeps them, and checks rules against them.

@@ 1-2
What this file is: what Prometheus collects, how often, and which rules it checks.

@@ 3-5
`global` settings: collect every 15 seconds, and check the rules every 15 seconds too — the same pace at which the API sends its totals to the collector.

@@ 7-8
The file of rules to check (`alerts.yaml`), at the path where the compose file mounts it inside the container.

@@ 10-13
What to collect: one *job*, `dwarpal`, with one fixed target — the collector's Prometheus exporter, `collector:8889`, reached by its container name on Docker's private network.
