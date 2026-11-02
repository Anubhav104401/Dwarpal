---
fingerprint: fb4d19d54191ceb1
---
**Tests for the inference client** (2 Nov 2026): the document check gets its own, longer time limit.

@@ 1
What this file tests: the inference client gives the document check more time than the face check.

@@ 3
The project-wide type-hint setting.

@@ 5-9
**`anyio`** runs an `async` function from ordinary code; `httpx`'s fake transport stands in for the inference service; then the client under test, and the request's description.

@@ 12-13
The smallest valid description of a request: one frame, at time 0.

@@ 16-21
The test. A fake inference service records how long each request was allowed to wait for an answer (`httpx` puts it in the request's `extensions`), by address, and then answers 503 ("unavailable").

@@ 23-27
Both checks through one client whose usual limit is 5 seconds and whose document limit is 20: each answers "no analysis", as an unavailable service must.

@@ 29-30
Run them, then compare: the face check waited 5 seconds, the document check 20.
