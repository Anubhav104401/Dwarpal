---
fingerprint: 44edf980f4be3ec9
---
The verify page's **client for the flow API** (§5.1.3): four methods, one per step of the check, that run in the person's browser.

```
start(secret)   →  flow token + what this check is about
attempt(frames) →  a fresh challenge, then the upload → pass / fail / retry / step up / reject
finish()        →  the address to return to
```

It is the browser's twin of the SDK's `DwarpalClient`, with one difference in attitude: an answer it can't read degrades to safe defaults (empty text, zero) instead of throwing. Any real problem still arrives as an error status from the API, which becomes a `FlowError` — and the screens show a friendly message for it (`advice.ts`).

@@ 1
The doc comment: the client, and the rule that every call after `start` carries the flow token.

@@ 3
`SessionStatus` — the three statuses in which the verify page can have a flow at all (the API refuses the others).

@@ 4
`AttemptOutcome` — the five answers to a face attempt (§5.1.2, `decision.py`).

@@ 6-13
`FlowSession` — what the page knows about its session: the ID, status, outcome (if finished), the website's name, the minimum age, and the attempts left.

@@ 15-19
`AttemptResult` — the answer to one attempt: the outcome, the reason codes, the attempts left.

@@ 21-24
`CapturedFrame` — one photo from the camera: the JPEG as a `Blob` (a chunk of raw bytes held by the browser), and when it was taken, in milliseconds since the burst began.

@@ 26-38
**`FlowError`** — the error for any refusal, built exactly like the SDK's `DwarpalApiError` (see `packages/sdk-node/src/errors.ts`): a status, a stable code, a message and the request ID.

@@ 40
`Json` — "an object with unknown values", as in the SDK.

@@ 42
**`asJson`** — any value as an object: the value itself if it *is* a (non-null) object, otherwise an empty one.

@@ 43
**`asText`** — any value as text: the value if it is a string, otherwise empty text.

@@ 44
**`asCount`** — any value as a whole number: the value if it is one, otherwise 0.

@@ 46
**`FlowClient`** — one client per session.

@@ 47-48
Two private fields: the base address for this session's flow endpoints, and the flow token — `null` until `start` has run.

@@ 50-52
The constructor builds the base address: the API's address without a trailing slash, then `/v1/flow/sessions/` and the session's ID. `encodeURIComponent` makes the ID safe inside an address, even if it contained odd characters — the page has already checked its shape, but checking again costs nothing.

@@ 54-55
**`start`** — exchange the link's one-time secret for a flow token.

@@ 56
Send the secret as JSON to `/start`.

@@ 57
Keep the flow token, in a private field. It lives only in this page's memory: not in the address, not in browser storage, and gone the moment the tab closes.

@@ 58-67
Turn the API's `session` object into a `FlowSession`, translating snake_case into camelCase. `as SessionStatus` tells TypeScript to trust that the status is one of the three; the screens treat anything unexpected as finished, so a surprise can't unlock anything.

@@ 69-70
**`attempt`** — one face attempt with a burst of frames. `readonly CapturedFrame[]` promises the method won't change the list it was given.

@@ 71
First, ask for a fresh one-time challenge. It has no body, so `null`.

@@ 72
Build a **multipart form** (§4.13). `FormData` is the browser's own builder for one.

@@ 73
The challenge's ID, as a text field.

@@ 74-77
The `meta` field: a JSON description of the frames — for each one, its position (`index`) and when it was taken (`t_ms`, rounded to whole milliseconds). `map` turns each frame into a new value; its second argument is the position in the list.

@@ 78-80
Each frame's bytes as a file field named `frame_0`, `frame_1`, …, with a file name. `forEach` runs a function for every item of a list.

@@ 81
Upload it all to `/face-attempts`.

@@ 82-87
The answer: the outcome, the reasons (keeping only text — `Array.isArray` checks that it really is a list), and the attempts left.

@@ 89-93
**`finish`** — ask where to send the person: the address, or `null`.

@@ 95
**`#post`** — the one private method that sends every request. Its body may be JSON text, a form, or nothing.

@@ 96-99
Headers: ask for JSON back, and — once there is a flow token — send it as a bearer token.

@@ 100-102
Only JSON text gets an explicit `Content-Type`. For a `FormData` body, the browser writes the header itself, including the random **boundary** that separates the parts. Setting it by hand would leave the boundary out, and the server couldn't read the form.

@@ 103-108
Send the request. `fetch` only throws when no answer came back at all — the network is down, or the server unreachable. That becomes a `FlowError` with the special status 0 and the code `network_error`, so the screens can say "you seem to be offline".

@@ 109
Read the answer as JSON, falling back to an empty object if it isn't JSON.

@@ 110-114
Not a success? Throw a `FlowError` with the API's code and message, falling back to generic ones. `||` picks the right-hand value when the left is empty text.

@@ 115-117
Success: return the answer. The closing braces end the method and the class.
