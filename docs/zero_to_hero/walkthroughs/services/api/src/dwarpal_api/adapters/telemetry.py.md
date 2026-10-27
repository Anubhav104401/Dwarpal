---
fingerprint: 8c3aa5cfe8b52fa8
---
**Traces** for the API (Phase 7, decision D11, §5.7.2): for each request, the route it took, how it ended and how long it took, sent with **OpenTelemetry** — the open standard for this — to a collector, only when one is configured. A trace must say nothing about the person, so this module also blanks what the instrumentation would otherwise record about them.

@@ 1-5
What a trace holds, when traces are made, and what they must never hold: no body, header or query string, and not the visitor's network address or browser.

@@ 7
Newer type-hint syntax on older Pythons.

@@ 9
`Any`, for the request's details, which come as a loosely typed dictionary.

@@ 11-17
FastAPI's type, and from OpenTelemetry: the **exporter**, which sends traces over HTTP in the standard format (OTLP); the FastAPI **instrumentation**, which records each request; the **resource**, naming who produced a trace; the **tracer provider**, the hub that makes traces; the **batch processor**, which sends them in groups; and the type of a **span** (one timed piece of work — here, one request).

@@ 19
The name every trace carries: `dwarpal-api`.

@@ 20-21
Health checks aren't traced: a load balancer calls them every few seconds, and they would drown everything else.

@@ 22-30
**`BLANKED`** — what the instrumentation records about the caller by default, and what each becomes: the caller's network address and port, and their browser's self-description (the *user agent*), all emptied. These identify a person's network and device, which the DPIA promises are never kept.

@@ 33-38
**`provider_for`** — a tracer provider whose traces are named `dwarpal-api` and sent, in batches, to the collector's standard path (`/v1/traces`) at the given address.

@@ 41-44
**`_blank_the_caller`** — runs at the start of each request's span: replace the full address, which includes the query string, with the path alone, and blank the caller's details. The test proved that overwriting works; the instrumentation offers no way to stop recording them.

@@ 47-55
**`install`** — trace every request to the app with that provider, except health checks; only one span per request (not one for each piece of the body read or written, `exclude_spans`); and blank the caller on each.
