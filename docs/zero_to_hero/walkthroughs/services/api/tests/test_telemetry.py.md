---
fingerprint: 823de242ab6512b7
---
The tests for traces and metrics (Phase 7): a request's trace keeps its route, status and timing, and nothing about who sent it — not the query string, the body, the headers, the network address or the browser; and its running totals are labelled with the route's pattern, never the real address. They need no database: a tiny app is enough.

@@ 1
What the test proves.

@@ 3
Newer type-hint syntax on older Pythons.

@@ 5-11
FastAPI and its test client; and from OpenTelemetry, a meter provider and a **reader that keeps metrics in memory** for the test to read, a tracer provider, a processor that sends each span at once, and an exporter that simply keeps spans in memory.

@@ 13
The module under test.

@@ 16-17
**Test** — a tiny app…

@@ 19-21
…with a route shaped like the verify page's "start the flow"…

@@ 23-25
…and a health check.

@@ 27-30
Keep every finished span in memory, and install tracing on the app with that provider.

@@ 31-36
Send the start request with secrets everywhere a careless trace might keep them: one in the query string, one in the body, a bearer token, and a recognisable browser name.

@@ 37
And a health check.

@@ 39
Exactly one span: the health check made none.

@@ 40-42
It is named after the route's *pattern* (not the session's ID), and records the route and the status.

@@ 43
The address is the path alone: the query string is gone.

@@ 44
The network address and browser are blank.

@@ 45-47
And none of the secrets — nor the test client's own name for itself — appears anywhere in what was recorded.

@@ 50
**The second test**: the totals a request adds to carry its route's pattern and status, and nothing about the caller.

@@ 51-55
A tiny app with one route that has a variable part, `{session}` — the part that must never reach a label.

@@ 57-58
A meter provider whose only reader keeps the totals in memory; install telemetry with it (and a tracer provider that goes nowhere, since this test is about metrics).

@@ 59
One request whose real address holds a session's text (`vs_1`) and a secret in its query string, sent with a browser name that identifies a person.

@@ 61-62
Ask the reader for everything recorded so far; it must have something.

@@ 63-69
Gather each metric's labels by name. The data come nested — resource, then *scope* (which library recorded them), then metrics, then their *data points* — so four `for` clauses walk down to every point.

@@ 70-71
`http.server.duration` — the histogram of how long requests took, which the dashboards and alerts use — is labelled with the route's pattern, `{session}` and all, and the status `200`.

@@ 72-74
And none of the secrets — not the session's text, the query string's value, the browser or the test client's name — appears in any label.
