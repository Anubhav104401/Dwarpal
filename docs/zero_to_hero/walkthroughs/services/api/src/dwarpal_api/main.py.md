---
fingerprint: e1e5def9d6cd06f0
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

@@ 17-26
Every part, from every layer: database helpers, the inference client, the key classes, the store, the idempotency module (for its secret), the toolbox, the manifest loader, the ten HTTP modules, the body-size guard, and the settings.

@@ 29
**`create_app`** — build and return the app. Both parameters are optional, and only tests use them: `settings` to point the API at test databases, and `inference_http` to talk to an inference app running inside the same process.

@@ 30
Use the given settings, or read them from the environment.

@@ 32-33
The **lifespan** function. `@asynccontextmanager` turns a function with a single `yield` into a "before and after" pair: everything before `yield` runs at start-up, and everything after it at shutdown. Defining it *inside* `create_app` lets it use `settings` and `inference_http` directly.

@@ 34-35
Create the database engine (the connection pool), working as the restricted role from the settings (`dwarpal_app`, so row-level security applies to every query), and the session factory (`db.py`). The key ring just below loads the signing keys through it: they belong to Dwarpal, not to a tenant, so no tenant is needed.

@@ 36
Create the Valkey client from its URL. It connects lazily, on first use.

@@ 37-39
The HTTP client for the inference service: the one a test passed in, or a new one with the service's base address and timeout from the settings.

@@ 40-41
Build the master key, then the key ring around it. `get_secret_value()` is the only way out of a `SecretStr`, so this is one of very few lines in the project that ever touches the master key in plain form. A malformed key stops the start-up right here. The master key itself is kept for the toolbox: it also seals webhook secrets.

@@ 42-43
Load the signing key, creating one if the database has none (`signing.py`, with its lock against two copies starting at once).

@@ 44-53
Fill the toolbox and store it on the app, where the `services` dependency finds it for every request. The model manifest is read from `models_dir`; a broken or missing manifest stops the start-up. The idempotency secret is derived from the master key once, here (`app/idempotency.py`), and the master key goes in too.

@@ 54-55
`yield` hands control to the server: the app now serves requests until shutdown begins.

@@ 56-60
`finally` runs at shutdown — even after a crash. Close the inference client only if *we* created it (a test closes its own; whoever creates a resource closes it), then the Valkey client, then the database pool.

@@ 62
Create the FastAPI app, with a title and version for its automatic documentation, the lifespan, and (step 6) the refusals every operation may answer with, so the published API document lists them for every operation (`http/problems.py`).

@@ 63
Add the body-size guard (`limits.py`).

@@ 64-70
Add the **CORS** middleware, which tells browsers which other websites may call this API from their pages (§4.13):

- `allow_origins` — only the origins in the settings: the verify page;
- `allow_methods` — only `GET` and `POST`, the only methods the API uses;
- `allow_headers` — the only request headers a page may send: the token, the body's type, a request ID, and the verify page's device ID (`X-Dwarpal-Device`, for the per-device budgets);
- `expose_headers` — lets the page's code read our `X-Request-Id` header, so the verify page can show it in an error message.

@@ 71
Install the request IDs, request log and error handlers (`problems.py`). Middleware added later wraps everything added before, so the order of these lines decides the order requests flow through:

```
request → RequestIds → CORS → BodyLimit → error handlers → endpoint
```

Request IDs come first, so every later step — even a refusal by the size guard — can name the request. CORS comes before the size guard, so browsers can read even a "too large" answer.

@@ 72-73
Add the nine routers — the relying-party API, policies, webhooks, token introspection, analytics, the console, the flow API, the well-known addresses and the health checks.

@@ 74
Return the finished app.
