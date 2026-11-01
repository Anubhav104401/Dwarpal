---
fingerprint: 794ceccea119a2c5
---
The inference service's **HTTP interface**, built with **FastAPI**. It is internal only: in deployment it sits on a private network with no route from the internet and no way out (§3.8, "the clean room").

@@ 1
The docstring states the most important property: internal only.

@@ 3
The project-wide type-hint setting.

@@ 5-6
Tools for the **lifespan**: code that runs once at start-up, before any request, and once at shutdown.

@@ 8
**anyio** — runs the heavy, blocking image work on worker threads, with a limit on how many run at once.

@@ 9
FastAPI's application class, its error type for HTTP errors, and the incoming request object.

@@ 10
Pydantic's validation error, caught when the `meta` field is invalid.

@@ 11
Starlette's `UploadFile`, the class that `request.form()` really returns for uploaded files.

!!! real "Real world — a bug the tests caught"
    The first version imported FastAPI's `UploadFile`, which is a *subclass* of this one. The `isinstance` check on line 58 therefore never matched, and every frame looked "missing". The test of a valid upload failed immediately, and the fix was this one import.

@@ 13-25
Our own pieces:

- from the contracts: the size limits (`MAX_FRAME_BYTES`, `MAX_FRAMES`, and since Phase 6 `MAX_DOCUMENT_BYTES`), and the message shapes `FaceAnalysis`, `FaceRequestMeta` and `DocumentAnalysis`. The API enforces the very same limits, because both import them from the same place;
- the age-model interface and both age models, the document reader (§5.6.2), the pipeline, and the settings;
- from the vision library, the face detector, the face mesh, the hand detector and the anti-spoofing models.

@@ 30-33
**`build_age_backend`** — the age model the settings ask for: the ONNX model from its registry folder, or the stand-in.

@@ 36-54
**`build_pipeline`** — load every model and return a ready pipeline: the face detector, the face mesh, the hand detector, the anti-spoofing networks and the chosen age model, which sees `age_frames` frames per attempt.

The anti-spoofing networks are the exception to "every model must be there": they are made from the pinned weights by `python -m dwarpal_ml.antispoof`, which needs PyTorch. As the comment says, without them the pipeline still runs — every result then has an empty `presentation`, and the decision has one signal fewer.

`trust_labels` is on only when the setting `liveness` is `"labels"` — the test mode in which liveness reads each frame's phase label instead of measuring the head (§5.3). The settings refuse that mode unless the stand-in age model is in use, so it can never reach a real deployment.

@@ 77
**`create_app`** — an **app factory**: a function that builds a fresh application. It takes optional settings, which tests use. Uvicorn calls it with `--factory`, so importing this module never starts loading models as a side effect.

@@ 78
Use the given settings, or read them from the environment.

@@ 79
A **capacity limiter**: at most `workers` analyses may run at the same time.

@@ 81-87
**The lifespan.** At start-up, build the pipeline (loading the models) and the document reader, and keep them on `app.state`, the application's shared storage. Then ask Tesseract once whether it answers, and remember `ready` or `missing` for the readiness check: without it, every document check says "unavailable" and is retried, never decided. `yield` hands control to the running server until shutdown.

@@ 89
Create the FastAPI app. The automatic documentation pages (`docs_url`, `redoc_url`, `openapi_url`) are switched off: an internal service should advertise nothing.

@@ 91-93
**`/livez`** — "is the process alive?" Container platforms poll it, and restart the container if it stops answering.

@@ 95-105
**`/readyz`** — "is it ready for work?" It answers only once the pipeline is loaded, and reports which age model is active, whether the anti-spoofing networks are `loaded` or `missing` (without them, live sessions can't be decided: the API refuses), and since Phase 6 whether OCR is `ready` or `missing`.

@@ 107-108
**The main endpoint**: `POST /internal/v1/analyze/face` returns a `FaceAnalysis`. FastAPI turns the returned model into JSON automatically.

@@ 109-110
Read the **multipart form**: at most `MAX_FRAMES` (16) files and 1 ordinary field (`meta`). Anything more is refused by the parser before it is stored.

As in the API, the form is opened with `async with`, so the uploads are closed as soon as the block ends — however it ends — rather than whenever the garbage collector gets to them.

@@ 111-114
Parse and validate `meta` with the contract. A missing or invalid value becomes a clear `422 Unprocessable` error. `from error` keeps the original cause for debugging.

@@ 154
Return the finished application.

@@ 26-27
And for the document check: `Tesseract`, which runs the OCR engine, and `FaceMatcher`, which compares faces with SFace (§5.6.2).

@@ 57-60
**`build_reader`** — the document check's parts: SFace from its file, Tesseract as the settings say to start it, and the pipeline and face detector already built for faces, shared rather than loaded twice.

@@ 63-64
**`read_frames`** — what both uploads share: the frames the meta lists, each read only up to its size limit. (`form` is typed as `object` and its `get` allowed by a comment for mypy: Starlette's form type isn't exported where this module could name it simply.)

@@ 65-69
For each frame the meta promises, the matching upload `frame_<index>` must exist. Otherwise the request is refused with `422`, naming the missing frame.

@@ 70-74
Read at most one byte more than `MAX_FRAME_BYTES`. If that extra byte arrives, the frame is too big and is refused with `413 Content Too Large`. Asking for just one extra byte means an oversized upload is never held in memory whole. Return the frames' bytes, in order.

@@ 115
Read the frames with `read_frames`. This is the end of the `async with` block, where the uploads close.

@@ 116-118
Then run the analysis inside `worker()` — below — which waits briefly for a free worker. The analysis runs **on a worker thread**: image work is CPU-heavy and *blocking*, and running it here would freeze the server's event loop and stall every other request, including health checks.

@@ 120-123
**`/internal/v1/analyze/document`** (§5.6.2) — the document check: a photo of the document's page and the selfie frames of a face challenge, answered with a `DocumentAnalysis`.

@@ 124-128
Parse the form — one more file than a face analysis, for the document — and validate the meta with the contract, as for faces.

@@ 129-134
The `document` upload must be there (`422` if not), and no larger than its limit (`413` if it is), read as frames are: never more than one byte past the limit.

@@ 135
Then the selfie frames.

@@ 136-138
Run the reader's analysis on a worker thread, waiting for a worker like a face analysis.

@@ 140-148
**`worker()`** — the wait for a free worker, shared by both analyses: `limiter.acquire()` waits for one of the `workers` slots; `anyio.fail_after` gives up after `queue_s` seconds, and then the answer is `503 busy` with `Retry-After: 1` — which the API turns into a safe *try again*, never a pass.

Until Phase 7 the service refused the moment all workers were busy; a bounded wait served most of those people at the cost of a short delay (§5.7.4). The upload is read and checked *before* waiting, so a malformed request never takes a place in the queue. `@asynccontextmanager` makes the function usable with `async with`: the code before `yield` runs on entry, the code after it on exit.

@@ 149-152
`yield` hands control to the analysis; `finally` hands the slot back however the analysis ends.
