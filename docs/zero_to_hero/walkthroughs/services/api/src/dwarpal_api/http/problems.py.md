---
fingerprint: 07d3f7ea4dbf3f52
---
Two jobs that every request shares:

1. **Errors in one shape.** However a request fails — a wrong key, a malformed field, a bug — the answer has the same JSON shape, the standard **problem details** format of RFC 9457 (§4.13). Programs calling the API need to learn only one way of reading errors:

    ```json
    {"type": "/errors/invalid_api_key", "title": "invalid api key", "status": 401,
     "detail": "this API key is unknown or revoked", "code": "invalid_api_key", "request_id": "req_3f9a1c0be27d4e51"}
    ```

2. **A request ID and a log line for every request.** Each request gets an ID, which is sent back in the `X-Request-Id` header, printed in every error, and written in the log. When a customer reports "it failed at 10:42", the ID leads straight to the right log line.

@@ 1
The docstring: one error shape, tagged with the request's ID.

@@ 3
The project-wide type-hint setting.

@@ 5-8
From the standard library: `logging`, `re` (regular expressions), `secrets` (random IDs) and `time` (measuring how long a request took).

@@ 10-12
From FastAPI: the app, request and response types; the error raised when a request's data fails Pydantic's checks; and the JSON response class.

@@ 13-15
From **Starlette**, the toolkit FastAPI is built on: header helpers, its own HTTP error class, and the types of the **ASGI** interface explained at `RequestIds` below.

@@ 17
Our own error class.

@@ 19
`SAFE_REQUEST_ID` — a **regular expression**: a pattern that text must match. It allows 8 to 64 characters, each a letter, a digit, a dot, an underscore or a hyphen. `^` and `$` mean the *whole* text must match, not just a part of it.

A caller may send its own request ID — handy when a website wants to follow one request through its own logs and ours. But that ID ends up in our logs and headers, so it must be harmless: no spaces, no line breaks that could fake extra log lines, nothing long.

@@ 20
`logger` — this module's logger, named `dwarpal.api` (see `logs.py` and `logging.json`).

@@ 23-25
**`problem`** — build one problem-details response.

It takes the refusal's extra headers too (Phase 4), if there are any.

@@ 26-33
The body:

- `type` — a reference that identifies the *kind* of problem, such as `/errors/invalid_api_key`. RFC 9457 asks for a URI here; a path with no host means "on this API's own address". Phase 5's documentation site can explain each code at exactly that path;
- `title` — a short human name, made from the code: `invalid_api_key` becomes `invalid api key`;
- `status` — the HTTP status code, repeated in the body for convenience;
- `detail` — the sentence explaining *this* occurrence;
- `code` — our stable code, which programs check (an **extension** member: the standard allows extra fields);
- `request_id` — this request's ID.

@@ 34
Send it with the status code and the media type `application/problem+json`, which tells the caller "this is a problem-details document".

`headers=headers` adds any extra headers, such as `Retry-After`.

@@ 37
**`on_unexpected`** — the last line of defence: any error nobody planned for — a bug, a database that vanished mid-request.

@@ 38
Log it at `error` level, with the error's class name, its full traceback (`exc_info=error`, for the developers), and the request ID.

@@ 39
Answer `500`, with a polite, *vague* sentence. The real cause stays in the log: an error message shown to strangers must never reveal internal details, which could help an attacker.

@@ 42-45
**`on_api_error`** — our own refusals become problems, carrying their status, code and sentence. The `isinstance` check guards against being called with the wrong kind of error: if that ever happened, the error is handled as unexpected rather than crashing the error handler itself.

An `ApiError`'s own headers travel with it into the response.

@@ 48-50
**`on_invalid_request`** — when FastAPI's Pydantic checks reject a request's data, for example a JSON body with a missing field.

@@ 51
List which fields were wrong. Each Pydantic error has a `loc` ("location") such as `("body", "policy")`. Skipping the first part (`[1:]`) and joining the rest with dots gives `policy`; an error about the body as a whole has nothing left, and `or "body"` names it instead. A set removes duplicates, and `sorted` fixes the order.

@@ 52
Answer `422` with one sentence naming the fields — but never echoing the *values* that were sent, which might be secrets typed in the wrong place.

@@ 55-58
**`on_http_error`** — Starlette's own HTTP errors, such as `404` for an address that doesn't exist at all, or `405` for a wrong method. They get the generic code `http_error`.

@@ 61
**`RequestIds`** — a **middleware**: code that wraps the whole app, seeing every request on its way in and every response on its way out (§4.8).

It is written in raw **ASGI**, the interface between a Python web server and a web app. In ASGI, an app is simply something you can call with three values:

- `scope` — a dict describing the request: its type, method, path, headers…;
- `receive` — a function to call to get the request's body;
- `send` — a function to call to send the response, in pieces called **messages**.

Writing middleware at this level is a little longer than FastAPI's shortcut decorator, but it sees *everything* — including requests that crash — and adds no overhead.

@@ 62-63
The middleware keeps the app it wraps.

@@ 65
`__call__` makes an object **callable** like a function: the server calls the middleware exactly as it would call the app.

@@ 66-68
Only HTTP requests get IDs. Other kinds of call — such as the **lifespan** messages a server sends at start-up and shutdown — pass straight through.

@@ 69-70
Read the caller's offered ID. Keep it if it is safe; otherwise make our own: `req_` plus 8 random bytes in hexadecimal.

@@ 71
Store the ID in the request's **state** — the place FastAPI exposes as `request.state` — so every later piece of code, such as `problem`, can find it. `setdefault` creates the state dict first if the server didn't.

@@ 72
Start the stopwatch, and assume the status is `500` until a response says otherwise: if the app crashes before answering, the log line will say `500`.

@@ 74
**`send_tagged`** — a wrapper around `send` that the app will use instead. A function defined inside another function can see the outer function's variables.

@@ 75
`nonlocal status` — "when I set `status`, I mean the outer function's variable", not a new local one.

@@ 76-78
The first message of every response, `http.response.start`, carries its status and headers. Note the status, and add our `X-Request-Id` header to it.

@@ 79
Pass the message on to the real `send`.

@@ 81-82
Run the app, with the wrapped `send`.

@@ 83-86
`finally` runs whether the app succeeded or crashed. Work out how long the request took, in milliseconds to one decimal place, and write **one log line** with the request's ID, method, path and status. The path has no query string, and nothing from the body is logged.

@@ 89
**`install`** — attach everything to an app; `main.py` calls it.

@@ 90
Add the request-ID middleware. Middleware added *last* ends up *outermost*, so `main.py` calls `install` after adding the others: the ID then exists before any other code runs.

@@ 91-94
Register the error handlers, from the most specific error class to the most general. For each error, FastAPI uses the handler registered for its own class, or for the closest class above it in the family tree — so an `ApiError` never ends up at the `Exception` handler.
