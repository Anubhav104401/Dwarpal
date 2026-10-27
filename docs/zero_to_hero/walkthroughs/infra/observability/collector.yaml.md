---
fingerprint: 41bbfe42c6955257
---
The **OpenTelemetry collector's** settings (Phase 7, D11): a relay that receives traces from the API and forwards them to Tempo. In production a collector also lets traces be filtered, sampled or sent elsewhere without touching the API.

@@ 1
What this file is.

@@ 2-6
**Receivers**: listen for traces in OpenTelemetry's standard format (OTLP) over HTTP, on port 4318, on every network interface inside the container (the compose file exposes it to this computer only).

@@ 8-9
**Processors**: group traces into batches before sending.

@@ 11-15
**Exporters**: send them to Tempo, over gRPC (a compact binary protocol) on port 4317. `tempo` is the container's name, which Docker's private network resolves. No encryption: both containers sit on that private network.

@@ 17-22
**The pipeline**: traces come in through the receiver, are batched, and go out to Tempo.
