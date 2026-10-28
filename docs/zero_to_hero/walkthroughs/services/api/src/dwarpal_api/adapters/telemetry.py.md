---
fingerprint: 24179259844250cd
---
**Traces and metrics** for the API (Phase 7, decision D11, §5.7.2 and §5.7.7): for each request, the route it took, how it ended and how long it took — as one trace each, and as running totals (*metrics*) for dashboards and alerts — sent with **OpenTelemetry**, the open standard for this, to a collector, only when one is configured. Neither may say anything about the person, so this module also blanks what the instrumentation would otherwise record about them.

@@ 1-7
What is recorded (a trace per request, and running totals), when (only if `DWARPAL_OTEL_ENDPOINT` is set), and what must never be: no body, header or query string, not the visitor's network address or browser — and metrics are labelled with a route's *pattern*, such as `/v1/flow/sessions/{session_text}/start`, never with a real address, which would contain a session's text.

@@ 9
Newer type-hint syntax on older Pythons.

@@ 11
`Any`, for the request's details, which come as a loosely typed dictionary.

@@ 13-22
FastAPI's type, and from OpenTelemetry: two **exporters**, which send metrics and traces over HTTP in the standard format (OTLP); the FastAPI **instrumentation**, which records each request; the **meter provider**, the hub that keeps the running totals, and the **periodic reader**, which hands them to the exporter on a timer; the **resource**, naming who produced the data; the **tracer provider**, the hub that makes traces; the **batch processor**, which sends traces in groups; and the type of a **span** (one timed piece of work — here, one request).

@@ 24
The name every trace carries: `dwarpal-api`.

@@ 25-26
Health checks aren't traced: a load balancer calls them every few seconds, and they would drown everything else.

@@ 27-35
**`BLANKED`** — what the instrumentation records about the caller by default, and what each becomes: the caller's network address and port, and their browser's self-description (the *user agent*), all emptied. These identify a person's network and device, which the DPIA promises are never kept.

@@ 38-43
**`provider_for`** — a tracer provider whose traces are named `dwarpal-api` and sent, in batches, to the collector's standard path (`/v1/traces`) at the given address.

@@ 46-50
**`meters_for`** — a meter provider whose totals are named `dwarpal-api` and sent to the collector's metrics path (`/v1/metrics`) every 15 seconds (15,000 milliseconds). Totals, unlike traces, are tiny — a count and a histogram of durations per route and status code — so sending them on a clock is cheap.

@@ 53-56
**`_blank_the_caller`** — runs at the start of each request's span: replace the full address, which includes the query string, with the path alone, and blank the caller's details. The test proved that overwriting works; the instrumentation offers no way to stop recording them.

@@ 59-69
**`install`** — trace every request to the app with the tracer provider, and count it with the meter provider when one is given (`None` leaves metrics off, as the older tests do); skip health checks; only one span per request (not one for each piece of the body read or written, `exclude_spans`); and blank the caller on each.
