---
fingerprint: 4e22488a74934c9a
---
**Security headers** on every answer the API sends (Phase 7, §5.7.1). The API serves only JSON to programs, so browsers are told to treat its answers as nothing else. The web apps already send their own, stricter-for-pages policies (`next.config.ts`).

| Header | What it tells a browser |
| :-- | :-- |
| `X-Content-Type-Options: nosniff` | believe the stated content type; never guess that JSON is a script |
| `Referrer-Policy: no-referrer` | never tell another site which address a link came from |
| `X-Frame-Options: DENY` and `frame-ancestors 'none'` | never show this inside another site's frame |
| `Content-Security-Policy: default-src 'none'` | if this is ever shown as a page, load and run nothing |
| `Cache-Control: no-store` | keep no copy: answers can hold secrets and tokens |
| `Strict-Transport-Security` (production only) | for two years, reach this site only over HTTPS |

@@ 1-2
The docstring.

@@ 4
The project-wide type-hint setting.

@@ 6-7
Starlette's editable headers, and the ASGI types for a middleware.

@@ 9-15
**`HEADERS`** — the headers every answer gets, each with its reason in a comment.

@@ 16-17
The interactive documentation is a real page with scripts and styles, so the strict content policy is left off those two paths.

@@ 18
**`HSTS`** — *HTTP Strict Transport Security*: two years of HTTPS only, for this host and its sub-domains. Sent only in production; over plain HTTP during development it would mean nothing.

@@ 21-24
**`SecurityHeaders`** — a middleware, written like `RequestIds` (`http/problems.py`): it wraps the app, and is told whether this is production.

@@ 26-29
Only HTTP requests get headers; anything else passes straight through.

@@ 30
Is this request for the documentation pages?

@@ 32-33
A function that sends each message on — but when the message starts a response, it first adds the headers.

@@ 34-37
Add each header **unless the route already set it**, so a route that may be cached (the public key set) keeps its own `Cache-Control`; and leave the content policy off the documentation pages.

@@ 38-39
In production, add HSTS too.

@@ 40
Send the message on.

@@ 42
Run the app with the wrapped sender.
