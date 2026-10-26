---
fingerprint: 885ae365431a65ba
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

@@ 9
`Any`, for the API document's loosely shaped dictionaries.

@@ 11-13
From FastAPI: the app, request and response types; the error raised when a request's data fails Pydantic's checks; and the JSON response class.

@@ 14
Pydantic's `BaseModel`, to describe the shape of a problem (step 6).

@@ 15-17
The errors that mean a dependency can't be reached (Phase 7): Valkey refusing a connection or timing out (renamed on import, so they don't hide Python's own `ConnectionError` and `TimeoutError`), and the database's "operational" and "interface" errors, which SQLAlchemy raises when a connection fails. Also `DBAPIError`, the family every database error belongs to, for the next handler.

@@ 18-20
From **Starlette**, the toolkit FastAPI is built on: header helpers, its own HTTP error class, and the types of the **ASGI** interface explained at `RequestIds` below.

@@ 22
Our own error class.

@@ 24
`SAFE_REQUEST_ID` — a **regular expression**: a pattern that text must match. It allows 8 to 64 characters, each a letter, a digit, a dot, an underscore or a hyphen. `^` and `$` mean the *whole* text must match, not just a part of it.

A caller may send its own request ID — handy when a website wants to follow one request through its own logs and ours. But that ID ends up in our logs and headers, so it must be harmless: no spaces, no line breaks that could fake extra log lines, nothing long.

@@ 25
`logger` — this module's logger, named `dwarpal.api` (see `logs.py` and `logging.json`).

@@ 28-29
**`Problem`** — the shape of every refusal (RFC 9457), described as a Pydantic model so the published API document can show it (Phase 4, step 6).

@@ 31-36
Its six fields: the problem's type and title, the HTTP status, the human sentence, the stable code programs check, and the request's ID.

@@ 39-51
**`REFUSALS`** — every status code an operation may refuse with, and a short description of each, for the API document.

@@ 52-58
**`PROBLEM_RESPONSES`** — the same, in the form FastAPI's `responses` option takes: for each status, its description and its content, `application/problem+json`, whose schema is a **reference** (`$ref`) to the `Problem` shape, defined once in the document's components. `main.py` gives this to every operation.

@@ 61-63
**`problem`** — build one problem-details response.

It takes the refusal's extra headers too (Phase 4), if there are any.

@@ 64-71
The body:

- `type` — a reference that identifies the *kind* of problem, such as `/errors/invalid_api_key`. RFC 9457 asks for a URI here; a path with no host means "on this API's own address". Phase 5's documentation site can explain each code at exactly that path;
- `title` — a short human name, made from the code: `invalid_api_key` becomes `invalid api key`;
- `status` — the HTTP status code, repeated in the body for convenience;
- `detail` — the sentence explaining *this* occurrence;
- `code` — our stable code, which programs check (an **extension** member: the standard allows extra fields);
- `request_id` — this request's ID.

@@ 72
Send it with the status code and the media type `application/problem+json`, which tells the caller "this is a problem-details document".

`headers=headers` adds any extra headers, such as `Retry-After`.

@@ 75
**`on_unexpected`** — the last line of defence: any error nobody planned for — a bug, a database that vanished mid-request.

@@ 76
Log it at `error` level, with the error's class name, its full traceback (`exc_info=error`, for the developers), and the request ID.

@@ 77
Answer `500`, with a polite, *vague* sentence. The real cause stays in the log: an error message shown to strangers must never reveal internal details, which could help an attacker.

@@ 80-81
The comment states the rule: **fail closed**. Without the database or Valkey, nothing can be decided safely, so nothing is. The caller is told to try again shortly, and no check can ever pass by accident.

@@ 82
**`DEPENDENCY_FAILURES`** — every kind of error that means "a dependency is down": Valkey's two, the database's two, and Python's own `ConnectionError` and `TimeoutError`, which lower layers raise directly.

@@ 83
How long to suggest waiting: five seconds.

@@ 86-89
**`on_dependency_down`** — the answer for those errors: a warning in the log (with the request's ID, never its contents), and `503 service_unavailable` with `Retry-After: 5`. Before Phase 7 these fell through to the generic `500 internal_error`. That also failed closed, but it told the caller nothing useful and broke the published contract, which promises `503` for exactly this.

@@ 92-94
**Text the database can't store** (Phase 5). PostgreSQL refuses the NUL character (U+0000) in text, and JSON (`\u0000`) and addresses (`%00`) can both carry it. The contract tests' random inputs found a request that reached the database with one and got `500 internal_error`. The fault was the request's, so the answer should be a refusal. The two SQLSTATE codes are PostgreSQL's names for "this character can't be stored".

@@ 97-100
**`on_database_error`** — if the database's own error code says the text was unstorable, `422 invalid_text`; any other database error is unexpected, as before. One handler covers every route, including any added later.

@@ 103-106
**`on_api_error`** — our own refusals become problems, carrying their status, code and sentence. The `isinstance` check guards against being called with the wrong kind of error: if that ever happened, the error is handled as unexpected rather than crashing the error handler itself.

An `ApiError`'s own headers travel with it into the response.

@@ 109-111
**`on_invalid_request`** — when FastAPI's Pydantic checks reject a request's data, for example a JSON body with a missing field.

@@ 112
List which fields were wrong. Each Pydantic error has a `loc` ("location") such as `("body", "policy")`. Skipping the first part (`[1:]`) and joining the rest with dots gives `policy`; an error about the body as a whole has nothing left, and `or "body"` names it instead. A set removes duplicates, and `sorted` fixes the order.

@@ 113
Answer `422` with one sentence naming the fields — but never echoing the *values* that were sent, which might be secrets typed in the wrong place.

@@ 116-118
**`on_http_error`** — Starlette's own HTTP errors, such as `404` for an address that doesn't exist at all, or `405` for a wrong method. They get the generic code `http_error`.

@@ 119
Keep any headers the error carries.

@@ 120-123
For `405 Method Not Allowed`, HTTP requires an `Allow` header listing every method the address accepts. The contract tests (step 6) found two problems here: the headers were being thrown away, and Starlette lists only one route's methods even when `GET` and `POST` on the same path are two routes. So the list is gathered from all of them.

@@ 124
Answer as problem details, with the headers.

@@ 127-133
**`allowed_methods`** — every method of every route whose path pattern matches this address. `getattr(route, "path_regex", None)` reads an attribute if the route has it, and gives `None` otherwise: not every route (the automatic documentation pages, for instance) is an ordinary endpoint. `|=` adds one set to another; `sorted` gives a stable order.

@@ 136
**`RequestIds`** — a **middleware**: code that wraps the whole app, seeing every request on its way in and every response on its way out (§4.8).

It is written in raw **ASGI**, the interface between a Python web server and a web app. In ASGI, an app is simply something you can call with three values:

- `scope` — a dict describing the request: its type, method, path, headers…;
- `receive` — a function to call to get the request's body;
- `send` — a function to call to send the response, in pieces called **messages**.

Writing middleware at this level is a little longer than FastAPI's shortcut decorator, but it sees *everything* — including requests that crash — and adds no overhead.

@@ 137-138
The middleware keeps the app it wraps.

@@ 140
`__call__` makes an object **callable** like a function: the server calls the middleware exactly as it would call the app.

@@ 141-143
Only HTTP requests get IDs. Other kinds of call — such as the **lifespan** messages a server sends at start-up and shutdown — pass straight through.

@@ 144-145
Read the caller's offered ID. Keep it if it is safe; otherwise make our own: `req_` plus 8 random bytes in hexadecimal.

@@ 146
Store the ID in the request's **state** — the place FastAPI exposes as `request.state` — so every later piece of code, such as `problem`, can find it. `setdefault` creates the state dict first if the server didn't.

@@ 147
Start the stopwatch, and assume the status is `500` until a response says otherwise: if the app crashes before answering, the log line will say `500`.

@@ 149
**`send_tagged`** — a wrapper around `send` that the app will use instead. A function defined inside another function can see the outer function's variables.

@@ 150
`nonlocal status` — "when I set `status`, I mean the outer function's variable", not a new local one.

@@ 151-153
The first message of every response, `http.response.start`, carries its status and headers. Note the status, and add our `X-Request-Id` header to it.

@@ 154
Pass the message on to the real `send`.

@@ 156-157
Run the app, with the wrapped `send`.

@@ 158-161
`finally` runs whether the app succeeded or crashed. Work out how long the request took, in milliseconds to one decimal place, and write **one log line** with the request's ID, method, path and status. The path has no query string, and nothing from the body is logged.

@@ 164-165
**`describe_problems`** — FastAPI builds the API document from the endpoints, but it only knows the `Problem` shape by its reference. This adds the shape itself.

@@ 166
Keep FastAPI's own document builder.

@@ 168-173
A replacement builder: build the document as before (FastAPI builds it once and keeps it), then make sure the components contain `Problem`, as Pydantic describes it (`model_json_schema`). `setdefault` adds a key only if it is missing, so running it twice changes nothing.

@@ 175
Put the replacement in place of FastAPI's. (Replacing a method on an object is unusual, hence the note to mypy; it is FastAPI's documented way to customise the document.)

@@ 178
**`install`** — attach everything to an app; `main.py` calls it.

@@ 179
Describe the problems, first of all.

@@ 180
Add the request-ID middleware. Middleware added *last* ends up *outermost*, so `main.py` calls `install` after adding the others: the ID then exists before any other code runs.

@@ 181-187
Register the error handlers. For each error, FastAPI uses the handler registered for its own class, or for the closest class above it in the family tree — so an `ApiError` never ends up at the `Exception` handler. Database errors in general go to `on_database_error`; the connection failures among them (`OperationalError`, `InterfaceError`) are closer relatives of their own handler, so each dependency failure still gets `503`.
