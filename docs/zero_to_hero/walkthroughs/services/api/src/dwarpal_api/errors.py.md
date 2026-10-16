---
fingerprint: 2e7a04057967dfb2
---
When the API says "no" on purpose — wrong key, unknown policy, session already finished — it raises an **`ApiError`**. The HTTP layer catches it and turns it into a tidy error response (`http/problems.py`, §4.13).

Python **exceptions** are the language's way of saying "stop, something is wrong" (§X.8). Raising one jumps straight out of the current function, and out of every function that called it, until some code **catches** it. That makes refusals short to write: deep inside a use case, one line — `raise ApiError(404, "session_not_found", "no such verification session")` — ends the whole request with the right answer.

@@ 1
The docstring: this is the *one* kind of error raised on purpose, and it always carries three things.

@@ 3
The project-wide type-hint setting.

@@ 6
`ApiError` is a kind of `Exception`, Python's base class for ordinary errors.

@@ 7
Making one takes three values:

- `status` — the **HTTP status code** (§0.8), such as 401 (who are you?), 404 (not found), 409 (conflicts with the current state) or 422 (the request makes no sense);
- `code` — a short, **stable** name such as `invalid_api_key`. Programs check the code, not the human sentence, so the sentence can be improved later without breaking anyone;
- `detail` — a sentence for the human reading it.

@@ 8
`super().__init__(detail)` runs `Exception`'s own set-up, so the error prints its sentence like any other exception.

@@ 9-11
Store the three values on the error object, so whoever catches it can read them.
