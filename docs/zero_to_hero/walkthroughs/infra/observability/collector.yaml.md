---
fingerprint: 2794d98d1114592c
---
The **OpenTelemetry collector's** settings (Phase 7, D11): a relay that receives traces from the API and forwards them to Tempo. In production a collector also lets traces be filtered, sampled or sent elsewhere without touching the API.

@@ 1-2
What this file is: the collector's settings. It is the API's single destination for telemetry — traces go on to Tempo, and metrics wait here for Prometheus to collect.

@@ 3-7
**Receivers**: listen for traces and metrics in OpenTelemetry's standard format (OTLP) over HTTP, on port 4318, on every network interface inside the container (the compose file exposes it to this computer only).

@@ 9-10
**Processors**: group what arrives into batches before passing it on.

@@ 12-16
**Exporters**: send traces to Tempo, over gRPC (a compact binary protocol) on port 4317. `tempo` is the container's name, which Docker's private network resolves. No encryption: both containers sit on that private network.

@@ 17-18
And offer metrics in **Prometheus's own text format** on port 8889. Prometheus works by *pulling*: every 15 seconds it asks this address for the latest totals (`prometheus.yaml`), rather than being sent them.

@@ 20-25
**The pipelines**: traces come in through the receiver, are batched, and go out to Tempo.

@@ 26-29
And metrics come in through the same receiver, are batched, and wait at the Prometheus exporter to be collected.
