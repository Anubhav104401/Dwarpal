---
fingerprint: d1f0e72947f9e077
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

@@ 4
`LabelledFrame` — one captured photo with its time and its phase label (`camera.ts`). `import type` brings in only the type: nothing is loaded when the page runs.

@@ 5
From `challenge.ts` (Phase 3): the `Challenge` type, `readChallenge` (which turns the API's answer into one), and the `Signals` type. The `type` keyword inside the braces marks which names are only types.

@@ 6
`deviceId` — this browser's random device ID, for the API's per-device budgets (`device.ts`).

@@ 8
`SessionStatus` — the three statuses in which the verify page can have a flow at all (the API refuses the others).

@@ 9
`AttemptOutcome` — the five answers to a face attempt (§5.1.2, `decision.py`).

@@ 32-36
`AttemptResult` — the answer to one attempt: the outcome, the reason codes, the attempts left.

@@ 38-44
**`CapturedAttempt`** (Phase 3) — everything the camera produced for one attempt, as the docstring says:

- `challengeId` — the challenge it answers;
- `frames` — the labelled photos. `readonly` promises they won't be changed here;
- `lightStartedMs` — when the screen colours started, on the frames' clock, or `null` if they weren't shown;
- `signals` — what the browser noticed about itself.

@@ 46-58
**`FlowError`** — the error for any refusal, built exactly like the SDK's `DwarpalApiError` (see `packages/sdk-node/src/errors.ts`): a status, a stable code, a message and the request ID.

@@ 60
`Json` — "an object with unknown values", as in the SDK.

@@ 62
**`asJson`** — any value as an object: the value itself if it *is* a (non-null) object, otherwise an empty one.

@@ 63
**`asText`** — any value as text: the value if it is a string, otherwise empty text.

@@ 64
**`asCount`** — any value as a whole number: the value if it is one, otherwise 0.

@@ 66
**`FlowClient`** — one client per session.

@@ 67-68
Two private fields: the base address for this session's flow endpoints, and the flow token — `null` until `start` has run.

@@ 70-72
The constructor builds the base address: the API's address without a trailing slash, then `/v1/flow/sessions/` and the session's ID. `encodeURIComponent` makes the ID safe inside an address, even if it contained odd characters — the page has already checked its shape, but checking again costs nothing.

@@ 74-75
**`start`** — exchange the link's one-time secret for a flow token.

@@ 76
Send the secret as JSON to `/start`.

@@ 77
Keep the flow token, in a private field. It lives only in this page's memory: not in the address, not in browser storage, and gone the moment the tab closes.

@@ 78-90
Turn the API's `session` object into a `FlowSession`, translating snake_case into camelCase; a return origin that isn't text becomes `null`. `as SessionStatus` tells TypeScript to trust that the status is one of the three; the screens treat anything unexpected as finished, so a surprise can't unlock anything. The Age Pass's two fields are `true` only if the API says exactly `true`.

@@ 92-93
**`challenge`** — ask the API for a fresh, one-time challenge. As the comment says, it carries this browser's device ID, if it has one. It is `async`, so it returns a `Promise` that will hold the `Challenge`.

@@ 94-98
The device ID is a parameter whose default is `deviceId()` — evaluated each time the method is called without one. Tests pass their own. Post to `/challenge` with no body (`null`), adding the `X-Dwarpal-Device` header when there is an ID (`{}` adds nothing), then check and convert the answer with `readChallenge`.

@@ 138-142
**`finish`** — ask where to send the person: the address, or `null`.

@@ 144-148
**`#post`** — the one private method that sends every request. Its body may be JSON text, a form, or nothing; `extra` holds any additional headers, none by default.

@@ 149-152
Headers: ask for JSON back, add the extra headers (`...extra` copies them in), and — once there is a flow token — send it as a bearer token.

@@ 153-155
Only JSON text gets an explicit `Content-Type`. For a `FormData` body, the browser writes the header itself, including the random **boundary** that separates the parts. Setting it by hand would leave the boundary out, and the server couldn't read the form.

@@ 156-161
Send the request. `fetch` only throws when no answer came back at all — the network is down, or the server unreachable. That becomes a `FlowError` with the special status 0 and the code `network_error`, so the screens can say "you seem to be offline".

@@ 162
Read the answer as JSON, falling back to an empty object if it isn't JSON.

@@ 163-167
Not a success? Throw a `FlowError` with the API's code and message, falling back to generic ones. `||` picks the right-hand value when the left is empty text.

@@ 168-170
Success: return the answer. The closing braces end the method and the class.

@@ 100-103
**`attempt`** — upload one face attempt: build its form (`attemptForm`, below), post it to `/face-attempts`, and read the answer (`readResult`).

@@ 172-173
**`attemptForm`** — what both uploads share, moved out of `attempt` in Phase 6: an attempt as a **multipart form** (§4.13). `const { frames, signals } = captured;` is **destructuring**: it takes those two fields out of `captured` into variables of the same names, to keep the lines below short.

@@ 174-176
`FormData` is the browser's own builder for a multipart form. First field: the challenge's ID, as text.

@@ 177-189
The `meta` field: a JSON description of the attempt, in the API's spelling (`t_ms`, not `tMs`):

- `frames` — for each one, its position (`index`), when it was taken (`t_ms`, rounded to whole milliseconds) and its `phase`. `map` turns each frame into a new value; its second argument is the position in the list;
- `light_started_ms` — when the colours began, rounded, or `null`. `a === null ? x : y` means "if `a` is null, `x`, otherwise `y`";
- `signals` — the browser's signals, renamed field by field into the API's names.

@@ 190-194
Each frame's bytes as a file field named `frame_0`, `frame_1`, …, with a file name. `forEach` runs a function for every item of a list. Return the form.

@@ 196-202
**`readResult`** — an attempt's answer: the outcome, the reasons (keeping only text — `Array.isArray` checks that it really is a list), and the attempts left.

@@ 2-3
The type of a holder's public key, from the Age Pass module (Phase 9) — only its type, so nothing of that module is loaded with this one.

@@ 11-23
`FlowSession` — what the page knows about its session: the ID, status, outcome (if finished), the website's name, the minimum age, the attempts left, and the website's **return origin** (decision D16) — the only page this one will talk to when it is inside that website's frame. Since Phase 9 also whether the website's policy accepts **Age Passes**, and whether the session is live or a test, which a kept pass must match (§5.9.3).

@@ 25-30
**`IssuedPasses`** (Phase 9) — a batch of Age Passes as the API gives it: the passes, the age lines each states, and when they expire.

@@ 105-110
**`documentAttempt`** (§5.6.3) — the step-up with an ID document: the same form as a face attempt — the selfie's frames answering a new challenge — plus the document's photo as one more file, posted to `/stepup/mrz`. The answer has the same shape.

@@ 112-120
**`issueAgePasses`** (Phase 9) — after a passed check, send the public keys this browser made, as JSON, and read back the passes, their lines and their expiry.

@@ 122-131
**`agePassNonce`** — a one-time nonce and the audience (this session) for a presentation. It sends the device ID, as a face challenge does: both spend from the same hourly budget.

@@ 133-136
**`presentAgePass`** — send a presentation. A refusal throws a `FlowError` with the API's code, which the page reads to decide whether to keep the pass.
