---
fingerprint: a7aa4e52977f4bb5
---
Tests for the verify page's `FlowClient`. As in the SDK's tests, no network is involved — but this client uses the browser's built-in `fetch` directly, so the tests replace that global function itself, with Vitest's **`vi.stubGlobal`**, and put the real one back after each test.

@@ 1
Vitest's building blocks, plus `afterEach` (run after every test) and `vi`, Vitest's toolbox for fakes.

@@ 3
The code under test.

@@ 5-6
The API's address and a session ID.

@@ 8-13
**`answer`** — builds a fake API answer: a `Response` with the given status and JSON body, a JSON content type, and a request ID.

@@ 15-17
After every test, **un-stub** all globals: put back the real `fetch`, so no test can leak its fake into the next one.

@@ 19
All the tests below are about `FlowClient`.

@@ 20-21
**The main journey: start, then one attempt.** `seen` will collect every request.

@@ 22-43
The three answers the fake API will give, in order: the start (a flow token and the session's view), a challenge — one pose and two colours — and an attempt's result: a retry, because the photos were too dark.

@@ 44-47
Replace `fetch`: record each request, and answer with the next prepared reply. `replies.shift()` removes and returns the first item of the list; if the list is empty — the client made an unexpected extra request — answer `500`, so the test fails loudly.

@@ 48
A client whose API address has a trailing slash, to prove it is handled.

@@ 49
Start the flow with a secret.

@@ 50
Ask for a challenge.

@@ 51-60
A fake frame: three bytes that begin every JPEG file (`255, 216, 255`), as a `Blob`. Then one attempt, answering that challenge, with the fake image twice: a baseline frame 12.4 ms in, and a `turn_left` frame 1560.2 ms in. The colours started 3.1 ms in, and the browser reports a virtual camera.

@@ 62
The session view was translated correctly.

@@ 63-67
Exactly three requests were made, to exactly these addresses, in this order: start, challenge, face attempt. `new URL(request.url).pathname` takes just the path part of each address.

@@ 68-69
**The token rule**: the first request carries no `Authorization` header (there's no token yet); the second carries the token that `start` received.

@@ 70-71
Read the upload back as a form. It carries the challenge's ID.

@@ 72-77
The challenge came back in the page's own spelling: `challenge_id` became `id`, `step_ms` became `stepMs`, and the fields the page doesn't need — the nonce and the expiry — were left out.

@@ 78-85
The `meta` field describes both frames with their phases, their times rounded to whole milliseconds, the colours' start time (also rounded), and the signals in the API's spelling.

@@ 86
The second frame was attached as a file.

@@ 87
The attempt's result was translated into the page's own shape.

@@ 88
The end of the test.

@@ 90-99
**Refusals become `FlowError`s.** The fake `fetch` answers `401` with problem details; starting must fail with a `FlowError` carrying the status, the code and the request ID.

@@ 101-106
**A lost connection.** This fake `fetch` throws, as the real one does when there's no network at all. The client must turn that into a `FlowError` with the code `network_error`, which the screens explain as "You seem to be offline".

@@ 107
The end of the group.
