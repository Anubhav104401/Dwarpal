---
fingerprint: d4652211021cd650
---
The API's **client for the inference service**: it sends the frames over the internal network and brings back a `FaceAnalysis` (§5.1.1).

The whole design fits in one sentence from the docstring: *any* failure becomes "no analysis". The service is down? No analysis. Too slow? No analysis. It answered with nonsense? No analysis. And the decision engine turns "no analysis" into *retry* or *step up* — never *pass* (`decision.py`, rule 1). A broken AI service can make the check annoying, but it can never make it unsafe.

@@ 1
The docstring and its promise.

@@ 3
The project-wide type-hint setting.

@@ 5-6
`httpx` (the HTTP client) and Pydantic's `ValidationError`.

@@ 8
The shared contracts: what the API sends (`FaceRequestMeta`) and what it expects back (`FaceAnalysis`, and for a document check `DocumentAnalysis`). Both services import the same classes, so they can't disagree about the shapes.

@@ 11-13
**`InferenceClient`** keeps an `httpx.AsyncClient` that it is given — already configured with the service's address and the face check's time limit (see `main.py`) — and how long the document check may take. Tests give it a client that talks to an inference app inside the same process instead (`test_api.py`).

@@ 16
**`analyze_face`** — send a burst of frames; get an analysis, or `None`.

@@ 17-20
Build the uploaded files: one entry per frame, named `frame_0`, `frame_1`, … Each value is a tuple of a file name, the bytes, and the **media type** `image/jpeg`.

`zip(meta.frames, frames, strict=True)` walks the two lists side by side, pairing each frame's description with its bytes. `strict=True` raises an error if the lists have different lengths, instead of silently dropping the extras.

@@ 21-24
Send it all as one **multipart** request (§4.13) to the inference service's internal endpoint: the frames as files, and the description as a JSON text field called `meta`. The path starts with `/internal/` — a reminder that only the API may call it.

@@ 25-26
`httpx.HTTPError` covers every network failure: refused connection, timeout, broken connection. Each one becomes `None`.

@@ 27-28
Any answer other than `200 OK` — such as `503` "busy, retry shortly" — also becomes `None`.

@@ 29-32
Parse and check the answer against the `FaceAnalysis` contract. A malformed answer raises `ValidationError` and also becomes `None`. Only a well-formed analysis ever reaches the decision engine.

@@ 34-37
**`analyze_document`** (§5.6.2) — the step-up's document check: the selfie frames and the photo of the document's page.

@@ 38-42
The upload, as for a face attempt: each frame under its own name, and the document as one more file named `document`.

@@ 43-57
Post it to the inference service's document address, with its own, longer time limit (`timeout=` on one request overrides the client's), and fail closed exactly as `analyze_face` does: a network error or a timeout, an answer other than 200, or an answer that doesn't fit the contract all become "no analysis" — which the step-up's rules turn into a retry, never a pass.

@@ 14
The document check's own time limit, kept for `analyze_document`.
