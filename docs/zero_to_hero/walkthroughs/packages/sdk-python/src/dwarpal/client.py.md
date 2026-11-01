---
fingerprint: 61b6bc17fa23e064
---
The SDK's **API client** (§5.9.1): create a session, read its result — the two calls a website makes. It checks what it sends and what it gets back, so a mistake shows up at once, in plain words.

@@ 1-4
The module's docstring, and its two forms: `Client`, which waits for each answer, and `AsyncClient`, for `async` frameworks.

@@ 6
The project-wide type-hint setting.

@@ 8-15
Regular expressions, dataclasses, dates, type helpers, httpx, and the SDK's API error.

@@ 17-20
The statuses and outcomes a session can have, as types (`Literal`) and as sets to check answers against.

@@ 21-22
The shapes of an API key and a session ID: checked before anything is sent.

@@ 25-32
**`CreatedSession`** — what creating a session gives back. Its `url` carries a one-time secret: never to be logged or stored.

@@ 35-46
**`SessionResult`** — a session's result, with its signed age token once completed, which the website must verify before trusting.

@@ 49-54
**`_field`** — one field of the API's answer, of the expected kind. A `bool` is refused where a whole number is expected (in Python, `True` is also an `int`). Anything unexpected is the API misbehaving, and is reported, not trusted.

@@ 57-63
**`_choice`** — a field that must be one of a set of values, or empty where allowed.

@@ 66-67
**`_when`** — a date and time from the API's text, or none.

@@ 70-78
**`_created`** — an answer to creating a session, read field by field.

@@ 81-93
**`_result`** — a session's result, read field by field.

@@ 96-98
**`_session_body`** — the request's body: only the fields given, in the API's spelling.

@@ 101-104
**`_session_path`** — a session's address, once its ID has the right shape: nothing unexpected is ever put into an address.

@@ 107-113
**`_answer`** — the answer's JSON, read carefully: an answer that isn't a JSON object counts as empty.

@@ 114-120
A refusal becomes a `DwarpalApiError`, with the API's stable code and detail (or plain stand-ins), and its request ID.

@@ 123-126
**`_headers`** — the key's shape is checked, then sent as a *bearer* token, asking for JSON back.

@@ 129-134
**`Client`** — its docstring: server only, since the key is secret; and how it is used, in a `with` block that closes its connections at the end.

@@ 136-138
Its HTTP client — given, for tests, or a new one with the API's address and a 10-second time limit — with the key's headers.

@@ 140-145
**`create_session`** — post the body; read the answer.

@@ 147-149
**`retrieve_session`** — read the session's result.

@@ 151-158
Closing, and the `with` block's entry and exit.

@@ 161-168
**`AsyncClient`** — the same, with httpx's asynchronous client.

@@ 170-177
The same two methods, awaited.

@@ 179-186
Closing (`aclose`), and the `async with` block's entry and exit.
