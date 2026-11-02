---
fingerprint: 3eefc4ed1060345a
---
**The collector on the server** (§5.8.4): the OpenTelemetry collector's settings when alerts by email are on.

@@ 1-2
What this collector does on the server: it receives the API's metrics and offers them to Prometheus. The laptop's collector (§5.7) also passed traces to Tempo; the server keeps no traces, so they are dropped.

@@ 3-7
One way in: OpenTelemetry's protocol over HTTP, on port 4318 — where the API sends (`DWARPAL_OTEL_ENDPOINT=http://collector:4318`).

@@ 9-10
**`batch`**: gathers what arrives into batches before passing it on.

@@ 12-15
Two ways out: **`prometheus`** offers the metrics on port 8889 for Prometheus to collect; **`nop`** accepts whatever it's given and forgets it.

@@ 17-25
The pipelines: metrics go in, are batched, and are offered to Prometheus; traces go in and are forgotten — accepted, so the API sees no errors for sending them.
