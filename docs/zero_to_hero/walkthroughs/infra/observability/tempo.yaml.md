---
fingerprint: f1450dbc93447884
---
**Tempo's** settings (Phase 7, D11): Grafana's trace store, kept on local disk — for looking at traces on this computer, not for production.

@@ 1
What this file is.

@@ 2-3
Its web interface — used by Grafana — on port 3200.

@@ 5-10
Accept traces from the collector in OpenTelemetry's format over gRPC, on port 4317.

@@ 12-18
Store traces on the local disk, in the container's data volume, with a write-ahead log (WAL: new data is written to a log first, so a crash loses nothing).
