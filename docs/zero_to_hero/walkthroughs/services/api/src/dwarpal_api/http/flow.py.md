---
fingerprint: 523aadd78847e26a
---
The **capture-flow API** — the endpoints the hosted verify page calls from the person's browser while the check is happening:

| Method and path (under `/v1/flow/sessions/{id}`) | Proves itself with | What it does |
| :-- | :-- | :-- |
| `POST /start` | the client secret | opens a flow; returns a flow token and the page's view of the session |
| `POST /challenge` | the flow token | issues a one-time challenge |
| `POST /face-attempts` | the flow token | uploads frames; returns the decision |
| `POST /finish` | the flow token | returns where to send the person next |

Because these calls come from a browser, they are the most exposed part of the API: anyone can open the browser's developer tools and send whatever they like. So every input is checked again here, and the answers reveal as little as possible.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-7
`re` (regular expressions), `uuid`, `Annotated` and `Any`.

@@ 9-11
From FastAPI: the router, `Depends`, `Header` (to read a request header) and `Request`. From Pydantic: the model tools and `ValidationError`. From Starlette: `UploadFile`, the type of an uploaded file. (It is Starlette's, because FastAPI is built on Starlette.)

@@ 13-18
The use cases, the toolbox type, the `Outcome` names, our error class, the two dependencies used here, and the limits and frame description from the shared contracts.

@@ 20
The router: every path starts with `/v1/flow/sessions/{session_text}`, so each endpoint automatically receives the session's ID from its address.

@@ 21
`CHALLENGE_ID` — the pattern a challenge ID must match: 8 to 64 URL-safe characters. Checking the *shape* before using an ID as part of a Valkey key keeps junk out.

@@ 22-23
`DEVICE_ID` — what a device ID must look like: 16 to 64 letters, digits and hyphens (the verify page sends a UUID). As the comment says, anything else is ignored, exactly as if no ID had been sent.

@@ 26-29
**`StartFlow`** — the body of `/start`: just the client secret, between 20 and 200 characters, and no unknown fields.

@@ 32-34
**`/start`** — needs no flow token (it is how you *get* one); the client secret in the body proves the right. It calls the use case, which checks the secret before anything else.

@@ 37-41
**`/frame-ancestor`** (decision D16) — asked by the verify page's web server before it serves the page: which website may show it in a frame (`proxy.ts`). It needs no secret: the server has none, and the answer only names the website the session will send the person back to anyway. The answer is `{"origin": …}`, with `null` for none.

@@ 44-53
**`/challenge`** — the `flow_session` dependency has already checked the flow token and returns the session's ID, called `flow` here. The browser's device ID arrives in the `X-Dwarpal-Device` header (FastAPI reads the header from the parameter's name: `x_dwarpal_device`) and is kept only if well-formed; the network address comes from the connection. The use case spends the per-device budgets and issues the challenge.

@@ 56-59
**`/face-attempts`** — the upload. It receives the raw `Request`, because the body is a **multipart form** — files plus text fields — which FastAPI doesn't turn into a Pydantic model the way it does with JSON.

@@ 60-61
Parse the form, accepting at most 16 files and 2 text fields; anything more is refused by the parser itself. (The total size was already checked from the headers, `limits.py`.)

It is parsed with **`async with`**: when the block ends — normally, or because a check below refuses the request — every uploaded file is **closed**, and the memory holding the frame is let go at once. Without it, the uploads stayed open until Python's garbage collector happened to find them: a chaos test (Phase 7) showed the warnings. The frames live on only as the bytes copied into `frames`, which the use case needs.

@@ 62-64
Read the challenge ID (or empty text if it's missing) and check its shape. Wrong? `422`.

@@ 65-68
Read the `meta` field — the JSON description of the frames — and check it against the `FaceRequestMeta` contract: 1 to 16 frames, each with a valid index and time. `from None` drops Pydantic's long internal error from the response; the client gets one clear sentence.

@@ 69
An empty list, for the frames' bytes.

@@ 70-73
For each frame described in `meta`, the form must contain a file called `frame_<index>`. Missing, or not a file? `422`, naming the frame.

@@ 74-76
Read at most one byte more than the per-frame limit. If that extra byte arrived, the frame is too big: `413`, naming the frame and the limit.

@@ 77
Keep the frame's bytes. This is the end of the `async with` block: the uploads close here.

@@ 78
Hand everything to the use case, which uses up the challenge, asks the AI, decides and records. It returns the decision and the attempts left.

@@ 79
**Never explain a rejection.** A `reject` means "this looked like an attack" (from Phase 3). If the answer said *why* — "the screen glare gave you away" — an attacker would learn how to improve. So every rejection is reported with the same vague reason, `verification_failed`. Every other outcome shares its reasons, which help honest people succeed: "too dark", "no face".

@@ 80
Answer with the outcome, the reasons, and the attempts left — never below zero.

@@ 83-87
**`/finish`** — the use case returns where the page should send the person (or `None`), wrapped in a small JSON object.
