---
fingerprint: 29ae3cb5b9868bf8
---
The **Python SDK's** package description (Phase 9, §5.9.1).

@@ 1-4
The package's name on PyPI-style installers — `dwarpal` — its version, its one-line description, and its README.

@@ 5-7
It works on Python 3.11 and later — older than the services' 3.13 — so websites on an older Python can use it.

@@ 8-11
Its two dependencies, as *ranges* rather than exact pins: a library must fit into other people's projects, whose other libraries may need a slightly different version. `httpx` speaks HTTP; `joserfc` checks signed tokens.

@@ 13-15
How it is built: with `uv_build`, like the other packages here.
