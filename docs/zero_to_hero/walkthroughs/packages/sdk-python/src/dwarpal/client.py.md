---
fingerprint: a8448db511b51c22
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

@@ 26-33
**`CreatedSession`** — what creating a session gives back. Its `url` carries a one-time secret: never to be logged or stored.

@@ 36-47
**`SessionResult`** — a session's result, with its signed age token once completed, which the website must verify before trusting.

@@ 50-55
**`_field`** — one field of the API's answer, of the expected kind. A `bool` is refused where a whole number is expected (in Python, `True` is also an `int`). Anything unexpected is the API misbehaving, and is reported, not trusted.

@@ 58-64
**`_choice`** — a field that must be one of a set of values, or empty where allowed.

@@ 67-68
**`_when`** — a date and time from the API's text, or none.

@@ 71-79
**`_created`** — an answer to creating a session, read field by field.

@@ 82-94
**`_result`** — a session's result, read field by field.

@@ 97-99
**`_session_body`** — the request's body: only the fields given, in the API's spelling.

@@ 114-117
**`_session_path`** — a session's address, once its ID has the right shape: nothing unexpected is ever put into an address.

@@ 120-126
**`_answer`** — the answer's JSON, read carefully: an answer that isn't a JSON object counts as empty.

@@ 127-133
A refusal becomes a `DwarpalApiError`, with the API's stable code and detail (or plain stand-ins), and its request ID.

@@ 136-139
**`_headers`** — the key's shape is checked, then sent as a *bearer* token, asking for JSON back.

@@ 142-147
**`Client`** — its docstring: server only, since the key is secret; and how it is used, in a `with` block that closes its connections at the end.

@@ 149-151
Its HTTP client — given, for tests, or a new one with the API's address and a 10-second time limit — with the key's headers.

@@ 153-162
**`create_session`** — the body from the settings given and the headers from the key (none without one), posted together; then the answer is read.

@@ 164-166
**`retrieve_session`** — read the session's result.

@@ 168-175
Closing, and the `with` block's entry and exit.

@@ 178-185
**`AsyncClient`** — the same, with httpx's asynchronous client.

@@ 187-198
The same two methods, awaited — `create_session` with the same optional key.

@@ 200-207
Closing (`aclose`), and the `async with` block's entry and exit.

@@ 23
**`IDEMPOTENCY_KEY`** — the shape the API requires of an idempotency key: 8 to 255 printable characters, no spaces (`\x21` is `!`, `\x7e` is `~`, and everything between them in ASCII is printable).

@@ 102-106
**`_idempotency`** (9 Nov) — the `Idempotency-Key` header, when a key is given. What it is for and how to make one is in the docstring: repeat a request whose answer was lost with the same key, and the first session comes back; make each key random and new (`secrets.token_urlsafe(16)`).

@@ 107-108
No key: no header.

@@ 109-110
A malformed key is refused before anything is sent. **`fullmatch`**, not `match`: in Python, `$` also matches just before a final line break, so `match` would accept `"abcdefgh\n"` — and a line break in a header breaks the request.

@@ 111
The header, as a dictionary to send with the request.
