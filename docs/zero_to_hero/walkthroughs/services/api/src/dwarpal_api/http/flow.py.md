---
fingerprint: dc9f3b3ce220c522
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
From FastAPI: the router, `Depends` and `Request`. From Pydantic: the model tools and `ValidationError`. From Starlette: `UploadFile`, the type of an uploaded file. (It is Starlette's own class that the form parser creates, so the `isinstance` check below must use exactly that one.)

@@ 13-18
The use cases, the toolbox type, the `Outcome` names, our error class, the two dependencies used here, and the limits and frame description from the shared contracts.

@@ 20
The router: every path starts with `/v1/flow/sessions/{session_text}`, so each endpoint automatically receives the session's ID from its address.

@@ 21
`CHALLENGE_ID` — the pattern a challenge ID must match: 8 to 64 URL-safe characters. Checking the *shape* before using an ID as part of a Valkey key keeps junk out.

@@ 24-27
**`StartFlow`** — the body of `/start`: just the client secret, between 20 and 200 characters, and no unknown fields.

@@ 30-32
**`/start`** — needs no flow token (it is how you *get* one); the client secret in the body proves the right. It calls the use case, which checks the secret before anything else.

@@ 35-39
**`/challenge`** — the `flow_session` dependency has already checked the flow token and returns the session's ID, called `flow` here. The use case issues the challenge.

@@ 42-45
**`/face-attempts`** — the upload. It receives the raw `Request`, because the body is a **multipart form** — files plus text fields — which FastAPI doesn't turn into a Pydantic model the way it does with JSON.

@@ 46
Parse the form, accepting at most 16 files and 2 text fields; anything more is refused by the parser itself. (The total size was already checked from the headers, `limits.py`.)

@@ 47-49
Read the challenge ID (or empty text if it's missing) and check its shape. Wrong? `422`.

@@ 50-53
Read the `meta` field — the JSON description of the frames — and check it against the `FaceRequestMeta` contract: 1 to 16 frames, each with a valid index and time. `from None` drops Pydantic's long internal error from the response; the client gets one clear sentence.

@@ 54
An empty list, for the frames' bytes.

@@ 55-58
For each frame described in `meta`, the form must contain a file called `frame_<index>`. Missing, or not a file? `422`, naming the frame.

@@ 59-61
Read at most one byte more than the per-frame limit. If that extra byte arrived, the frame is too big: `413`, naming the frame and the limit.

@@ 62
Keep the frame's bytes.

@@ 63
Hand everything to the use case, which uses up the challenge, asks the AI, decides and records. It returns the decision and the attempts left.

@@ 64
**Never explain a rejection.** A `reject` means "this looked like an attack" (from Phase 3). If the answer said *why* — "the screen glare gave you away" — an attacker would learn how to improve. So every rejection is reported with the same vague reason, `verification_failed`. Every other outcome shares its reasons, which help honest people succeed: "too dark", "no face".

@@ 65
Answer with the outcome, the reasons, and the attempts left — never below zero.

@@ 68-72
**`/finish`** — the use case returns where the page should send the person (or `None`), wrapped in a small JSON object.
