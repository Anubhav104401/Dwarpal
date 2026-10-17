---
fingerprint: ea1e2532b0bbf3f4
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
`LabelledFrame` — one captured photo with its time and its phase label (`camera.ts`). `import type` brings in only the type: nothing is loaded when the page runs.

@@ 4
From `challenge.ts` (Phase 3): the `Challenge` type, `readChallenge` (which turns the API's answer into one), and the `Signals` type. The `type` keyword inside the braces marks which names are only types.

@@ 6
`SessionStatus` — the three statuses in which the verify page can have a flow at all (the API refuses the others).

@@ 7
`AttemptOutcome` — the five answers to a face attempt (§5.1.2, `decision.py`).

@@ 9-16
`FlowSession` — what the page knows about its session: the ID, status, outcome (if finished), the website's name, the minimum age, and the attempts left.

@@ 18-22
`AttemptResult` — the answer to one attempt: the outcome, the reason codes, the attempts left.

@@ 24-30
**`CapturedAttempt`** (Phase 3) — everything the camera produced for one attempt, as the docstring says:

- `challengeId` — the challenge it answers;
- `frames` — the labelled photos. `readonly` promises they won't be changed here;
- `lightStartedMs` — when the screen colours started, on the frames' clock, or `null` if they weren't shown;
- `signals` — what the browser noticed about itself.

@@ 32-44
**`FlowError`** — the error for any refusal, built exactly like the SDK's `DwarpalApiError` (see `packages/sdk-node/src/errors.ts`): a status, a stable code, a message and the request ID.

@@ 46
`Json` — "an object with unknown values", as in the SDK.

@@ 48
**`asJson`** — any value as an object: the value itself if it *is* a (non-null) object, otherwise an empty one.

@@ 49
**`asText`** — any value as text: the value if it is a string, otherwise empty text.

@@ 50
**`asCount`** — any value as a whole number: the value if it is one, otherwise 0.

@@ 52
**`FlowClient`** — one client per session.

@@ 53-54
Two private fields: the base address for this session's flow endpoints, and the flow token — `null` until `start` has run.

@@ 56-58
The constructor builds the base address: the API's address without a trailing slash, then `/v1/flow/sessions/` and the session's ID. `encodeURIComponent` makes the ID safe inside an address, even if it contained odd characters — the page has already checked its shape, but checking again costs nothing.

@@ 60-61
**`start`** — exchange the link's one-time secret for a flow token.

@@ 62
Send the secret as JSON to `/start`.

@@ 63
Keep the flow token, in a private field. It lives only in this page's memory: not in the address, not in browser storage, and gone the moment the tab closes.

@@ 64-73
Turn the API's `session` object into a `FlowSession`, translating snake_case into camelCase. `as SessionStatus` tells TypeScript to trust that the status is one of the three; the screens treat anything unexpected as finished, so a surprise can't unlock anything.

@@ 75-76
**`challenge`** — ask the API for a fresh, one-time challenge, as the comment says. It is `async`, so it returns a `Promise` that will hold the `Challenge`.

@@ 77-78
Post to `/challenge` — with no body, so `null` — and check and convert the answer with `readChallenge`.

@@ 80-82
**`attempt`** — upload one attempt. `const { frames, signals } = captured;` is **destructuring**: it takes those two fields out of `captured` into variables of the same names, to keep the lines below short.

@@ 83
Build a **multipart form** (§4.13). `FormData` is the browser's own builder for one.

@@ 84
The challenge's ID, as a text field.

@@ 85-97
The `meta` field: a JSON description of the attempt, in the API's spelling (`t_ms`, not `tMs`):

- `frames` — for each one, its position (`index`), when it was taken (`t_ms`, rounded to whole milliseconds) and its `phase`. `map` turns each frame into a new value; its second argument is the position in the list;
- `light_started_ms` — when the colours began, rounded, or `null`. `a === null ? x : y` means "if `a` is null, `x`, otherwise `y`";
- `signals` — the browser's signals, renamed field by field into the API's names.

@@ 98-100
Each frame's bytes as a file field named `frame_0`, `frame_1`, …, with a file name. `forEach` runs a function for every item of a list.

@@ 101
Upload it all to `/face-attempts`.

@@ 102-107
The answer: the outcome, the reasons (keeping only text — `Array.isArray` checks that it really is a list), and the attempts left.

@@ 109-113
**`finish`** — ask where to send the person: the address, or `null`.

@@ 115
**`#post`** — the one private method that sends every request. Its body may be JSON text, a form, or nothing.

@@ 116-119
Headers: ask for JSON back, and — once there is a flow token — send it as a bearer token.

@@ 120-122
Only JSON text gets an explicit `Content-Type`. For a `FormData` body, the browser writes the header itself, including the random **boundary** that separates the parts. Setting it by hand would leave the boundary out, and the server couldn't read the form.

@@ 123-128
Send the request. `fetch` only throws when no answer came back at all — the network is down, or the server unreachable. That becomes a `FlowError` with the special status 0 and the code `network_error`, so the screens can say "you seem to be offline".

@@ 129
Read the answer as JSON, falling back to an empty object if it isn't JSON.

@@ 130-134
Not a success? Throw a `FlowError` with the API's code and message, falling back to generic ones. `||` picks the right-hand value when the left is empty text.

@@ 135-137
Success: return the answer. The closing braces end the method and the class.
