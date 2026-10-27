---
fingerprint: 5491561b45149959
---
The test for traces (Phase 7): a request's trace keeps its route, status and timing, and nothing about who sent it — not the query string, the body, the headers, the network address or the browser. It needs no database: a tiny app with two routes is enough.

@@ 1
What the test proves.

@@ 3
Newer type-hint syntax on older Pythons.

@@ 5-9
FastAPI and its test client; and from OpenTelemetry, a tracer provider, a processor that sends each span at once, and an exporter that simply keeps spans in memory for the test to read.

@@ 11
The module under test.

@@ 14-15
**Test** — a tiny app…

@@ 17-19
…with a route shaped like the verify page's "start the flow"…

@@ 21-23
…and a health check.

@@ 25-28
Keep every finished span in memory, and install tracing on the app with that provider.

@@ 29-34
Send the start request with secrets everywhere a careless trace might keep them: one in the query string, one in the body, a bearer token, and a recognisable browser name.

@@ 35
And a health check.

@@ 37
Exactly one span: the health check made none.

@@ 38-40
It is named after the route's *pattern* (not the session's ID), and records the route and the status.

@@ 41
The address is the path alone: the query string is gone.

@@ 42
The network address and browser are blank.

@@ 43-45
And none of the secrets — nor the test client's own name for itself — appears anywhere in what was recorded.
