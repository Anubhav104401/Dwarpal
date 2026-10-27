---
fingerprint: 28a96433225513a1
---
The file that **assembles** the API. Every other module is a part; this one connects them in the right order when the program starts, and disconnects them when it stops. It follows the same pattern as the inference service's `main.py` (§5.1.1): an **app factory** called `create_app`.

What happens when the API starts, in order:

1. Uvicorn calls `create_app()`, which builds the FastAPI app: its middleware, error handlers and endpoints.
2. Before accepting any request, the app runs its **lifespan** start-up: it connects to PostgreSQL and Valkey, prepares the inference client, loads (or creates) the signing key, and reads the model manifest.
3. Requests are served.
4. On shutdown, the lifespan closes every connection it opened.

If any step of 2 fails — a wrong master key, a missing manifest, an unreachable database — the API refuses to start, loudly. A service that starts "half-working" is much harder to diagnose than one that doesn't start at all.

@@ 1-4
The docstring, with the exact command to run the API: Uvicorn (§4.8), the import path of the factory, `--factory` (call it to get the app), the port, and the logging configuration (`logging.json`).

@@ 6
The project-wide type-hint setting.

@@ 8-10
`AsyncIterator` (the type of the lifespan function), `asynccontextmanager` (explained at line 31), and the date tools.

@@ 12-15
`httpx` for the inference client, FastAPI itself, its **CORS** middleware (§4.13), and the async Valkey client.

@@ 17
The tracing module (Phase 7, §5.7.2).

@@ 18-28
Every part, from every layer: database helpers, the inference client, the key classes, the store, the idempotency module (for its secret), the toolbox, the manifest loader, the ten HTTP modules, the security headers (Phase 7), the body-size guard, and the settings.

@@ 31
**`create_app`** — build and return the app. Both parameters are optional, and only tests use them: `settings` to point the API at test databases, and `inference_http` to talk to an inference app running inside the same process.

@@ 32
Use the given settings, or read them from the environment.

@@ 33
**Traces**: if a collector's address is set, a tracer provider that sends to it; otherwise none.

@@ 35-36
The **lifespan** function. `@asynccontextmanager` turns a function with a single `yield` into a "before and after" pair: everything before `yield` runs at start-up, and everything after it at shutdown. Defining it *inside* `create_app` lets it use `settings` and `inference_http` directly.

@@ 37-38
Create the database engine (the connection pool), working as the restricted role from the settings (`dwarpal_app`, so row-level security applies to every query), and the session factory (`db.py`). The key ring just below loads the signing keys through it: they belong to Dwarpal, not to a tenant, so no tenant is needed.

@@ 39
Create the Valkey client from its URL. It connects lazily, on first use.

@@ 40-42
The HTTP client for the inference service: the one a test passed in, or a new one with the service's base address and timeout from the settings.

@@ 43-44
Build the master key, then the key ring around it. `get_secret_value()` is the only way out of a `SecretStr`, so this is one of very few lines in the project that ever touches the master key in plain form. A malformed key stops the start-up right here. The master key itself is kept for the toolbox: it also seals webhook secrets.

@@ 45-46
Load the signing key, creating one if the database has none (`signing.py`, with its lock against two copies starting at once).

@@ 47-56
Fill the toolbox and store it on the app, where the `services` dependency finds it for every request. The model manifest is read from `models_dir`; a broken or missing manifest stops the start-up. The idempotency secret is derived from the master key once, here (`app/idempotency.py`), and the master key goes in too.

@@ 57-58
`yield` hands control to the server: the app now serves requests until shutdown begins.

@@ 59-63
`finally` runs at shutdown — even after a crash. Close the inference client only if *we* created it (a test closes its own; whoever creates a resource closes it), then the Valkey client, then the database pool.

@@ 64-65
At shutdown, if tracing is on, send the traces still waiting in their batch, so the last requests aren't lost.

@@ 67-76
Create the FastAPI app, with a title and version for its automatic documentation, the lifespan, and (Phase 4) the refusals every operation may answer with, so the published API document lists them for every operation (`http/problems.py`).

Since Phase 7, the **interactive** documentation pages (`/docs`, and `/redoc`, never used) exist only outside production: they load scripts and styles from the internet, which the API's strict content policy would forbid, and production has no need for them. The document itself, `/openapi.json`, is always published.

@@ 77
Add the body-size guard (`limits.py`).

@@ 78
Add the security headers to every answer (`http/headers.py`), with HSTS only in production.

@@ 79-85
Add the **CORS** middleware, which tells browsers which other websites may call this API from their pages (§4.13):

- `allow_origins` — only the origins in the settings: the verify page;
- `allow_methods` — only `GET` and `POST`, the only methods the API uses;
- `allow_headers` — the only request headers a page may send: the token, the body's type, a request ID, and the verify page's device ID (`X-Dwarpal-Device`, for the per-device budgets);
- `expose_headers` — lets the page's code read our `X-Request-Id` header, so the verify page can show it in an error message.

@@ 86
Install the request IDs, request log and error handlers (`problems.py`). Middleware added later wraps everything added before, so the order of these lines decides the order requests flow through:

```
request → RequestIds → CORS → BodyLimit → error handlers → endpoint
```

Request IDs come first, so every later step — even a refusal by the size guard — can name the request. CORS comes before the size guard, so browsers can read even a "too large" answer.

@@ 87-88
Add the nine routers — the relying-party API, policies, webhooks, token introspection, analytics, the console, the flow API, the well-known addresses and the health checks.

@@ 89-90
If tracing is on, record every request — added last, so it wraps everything else.

@@ 91
Return the finished app.
