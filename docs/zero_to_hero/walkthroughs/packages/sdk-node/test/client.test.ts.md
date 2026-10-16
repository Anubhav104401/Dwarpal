---
fingerprint: 0aceacfdfe98461a
---
The tests for `DwarpalClient`. They never touch a network: each test gives the client a **fake `fetch`** that records the request it was given and answers with whatever the test chose. The tests can then check both directions — what the client *sent*, and what it made of the *answer*.

@@ 1
Vitest's building blocks.

@@ 3
The code under test, from the SDK's front door.

@@ 5-6
A test key with the right shape, and a session ID.

@@ 8
**`fakeFetch`** — makes a fake `fetch` that always answers with the given status and body. Requests it receives are pushed into `seen`, if the test passes a list to collect them in. Its return type, `typeof fetch`, means TypeScript checks that the fake really has the same shape as the built-in.

@@ 9-10
The fake itself: an `async` function taking the same two arguments as `fetch`. It rebuilds them into a standard `Request` object — the browser's and Node.js's own description of a request — so the tests can inspect its address, headers and body.

@@ 11-12
Answer with a standard `Response`: the body as JSON, the status, a JSON content type and a request ID.

@@ 13-14
The closing braces.

@@ 16
All the tests below are about `DwarpalClient`.

@@ 17-28
**Creating a session.** The fake answer looks exactly like the API's: ID, object type, status, mode, policy, client secret, link and expiry.

@@ 29-33
A client with the test key, an address *with* a trailing slash (to prove it is removed), and the fake `fetch`.

@@ 34-37
Create a session with a policy and a return address.

@@ 38
`const [request] = seen` — **array destructuring**: take the first recorded request.

@@ 39-41
What was **sent**: the right address (with no double slash), the key as a bearer token, and a body in the API's own snake_case names. `?.` (**optional chaining**) reads a property only if the thing before it exists; if `request` were missing, the check would fail cleanly instead of crashing.

@@ 42-44
What was **made of the answer**: the link unchanged, the expiry turned into a real date — and *no* `client_secret` property, which the SDK deliberately leaves out.

@@ 45
The end of the test.

@@ 47-59
**Reading a completed session.** The fake answer is a finished, passed session with its token.

@@ 60-64
A client whose fake `fetch` returns that answer.

@@ 65-69
The SDK's result has the outcome, the minimum age as a number, the completion time as a date, and the token.

@@ 70
The end of the test.

@@ 72-73
**Errors.** The fake answers `401` with problem details, as the API does for a bad key.

@@ 74-78
A client that will get that answer.

@@ 79
Try to create a session. `.catch((error: unknown) => error)` turns the expected failure into a value, so the test can examine the error itself.

@@ 80-85
It must be a `DwarpalApiError` carrying the status, the stable code and the request ID. `toMatchObject` checks just these properties, ignoring any others.

@@ 86
The end of the test.

@@ 88-89
**Malformed input is refused before anything is sent.** `seen` will collect any request that goes out — there should be none.

@@ 90-92
A key from some other service (`sk_live_…`) is refused when the client is made. `expect(() => …).toThrow(…)` passes a *function* to `expect`, so Vitest can call it and catch the error itself.

@@ 93-97
A proper client, with a recording fake.

@@ 98
An ID that is far too short is refused with a `TypeError`…

@@ 99
…and `seen` is still empty: no request was ever made.

@@ 100-101
The closing braces.
