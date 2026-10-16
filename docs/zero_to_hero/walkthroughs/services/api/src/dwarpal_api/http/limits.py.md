---
fingerprint: eb55241bfeeaa225
---
A guard at the door that **measures every request before letting it in**. An attacker who sends a 10-gigabyte "upload" would otherwise make the API read and store it all before any check ran. This middleware refuses oversized bodies from the headers alone, before a single byte of the body has been read.

Two rules:

1. **Every body must declare its size.** A request can either state its size up front, in the `Content-Length` header, or send its body in chunks of unknown total size (`Transfer-Encoding: chunked`). Browsers and normal HTTP clients state the size for the requests this API receives, so chunked bodies are simply refused with `411 Length Required`.
2. **The declared size must be within the limit**: 64 KiB for JSON requests, and 16 frames × 512 KiB plus 64 KiB of packaging for face uploads. Anything bigger gets `413 Content Too Large`.

Once the size is declared, the server itself makes sure no more bytes than that are delivered — so a declared size really is a ceiling.

!!! real "Real world — why this lives outside FastAPI"
    The first idea was to count bytes while FastAPI read the body. It didn't work: FastAPI catches *any* error raised while it reads a JSON body and replaces it with a generic `400 There was an error parsing the body`. Checking the headers before the request ever reaches FastAPI avoids that, and costs nothing.

@@ 1
The docstring: limits enforced from the headers, before the body is read.

@@ 3
The project-wide type-hint setting.

@@ 5-6
Starlette's `Request` (needed by `problem`) and the ASGI types (see `RequestIds` in `problems.py`).

@@ 8-9
`problem` — the one error shape — and the frame limits from the shared contracts.

@@ 11
`JSON_LIMIT` — 64 KiB for every ordinary request. The biggest legitimate JSON body, creating a session, is a few hundred bytes.

@@ 12
`UPLOAD_LIMIT` — for face uploads: the most frames allowed (16) times the most bytes per frame (512 KiB), plus 64 KiB for the multipart packaging and the `meta` text. Computing it from the contracts' values keeps it right if those ever change.

@@ 13
Which requests are uploads: those whose path ends in `/face-attempts`.

@@ 16-18
**`BodyLimit`** — an ASGI middleware, built like `RequestIds`.

@@ 20-21
For every HTTP request…

@@ 22
…turn the header list into a dict, for easy lookups. In ASGI, header names arrive in lowercase, as **bytes** — hence the `b"…"` keys below.

@@ 23
Pick the limit that applies to this path.

@@ 24
The declared size, or `0` if no size was declared (a request without a body, such as a `GET`).

@@ 25
No refusal so far.

@@ 26-27
A chunked body: refuse with `411`, saying how to fix it.

@@ 28-29
A size that isn't a plain number, or is over the limit: refuse with `413`, stating the limit.

@@ 30-32
If there is a refusal, send it — a response is itself an ASGI app, so it is *called* with the same three values — and stop. The real app never sees the request.

@@ 33
Otherwise pass the request on, unchanged.
