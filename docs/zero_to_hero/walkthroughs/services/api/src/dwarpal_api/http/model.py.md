---
fingerprint: 6c08e7c28c6939c5
---
**The model's published performance** (§5.5.9): `GET /v1/model`, which anyone may read without a key or a sign-in.

@@ 1-2
What it is for: a provider should publish how well its system works (ISO/IEC 27566-1); the home page's accuracy table reads it.

@@ 4
The project-wide type-hint setting.

@@ 6
`Annotated` (a type with a note FastAPI reads) and `Any`.

@@ 8
FastAPI's router, its dependencies, and the response, for a header.

@@ 10-12
The console's application code, the services and how a route gets them.

@@ 14
The router: addresses under `/v1`, listed under "model" in the API document.

@@ 17-18
**`GET /v1/model`** — no `Reader` and no key: open to anyone.

@@ 19-20
Browsers and caches may keep the answer for five minutes (the model changes only when the service restarts); the answer is the console's description of the model without the lines' scores (`published_model`).
