---
fingerprint: 247e65dd27e8f3ac
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

@@ 13-17
Our own pieces:

- from the contracts: the two size limits `MAX_FRAME_BYTES` and `MAX_FRAMES`, and the message shapes `FaceAnalysis` and `FaceRequestMeta`. The API enforces the very same limits, because both import them from the same place;
- the age-model interface and both age models, the pipeline, the settings and the face detector.

From the vision library, the new measuring pieces: the face mesh, the hand detector, and the anti-spoofing detector with its model description.

@@ 20-23
**`build_age_backend`** — the age model the settings ask for: the ONNX model from its registry folder, or the stand-in.

@@ 26-43
**`build_pipeline`** — load every model and return a ready pipeline: the face detector, the face mesh, the hand detector, the anti-spoofing networks and the chosen age model.

The anti-spoofing networks are the exception to "every model must be there": they are made from the pinned weights by `python -m dwarpal_ml.antispoof`, which needs PyTorch. As the comment says, without them the pipeline still runs — every result then has an empty `presentation`, and the decision has one signal fewer.

`trust_labels` is on only when the setting `liveness` is `"labels"` — the test mode in which liveness reads each frame's phase label instead of measuring the head (§5.3). The settings refuse that mode unless the stand-in age model is in use, so it can never reach a real deployment.

@@ 46
**`create_app`** — an **app factory**: a function that builds a fresh application. It takes optional settings, which tests use. Uvicorn calls it with `--factory`, so importing this module never starts loading models as a side effect.

@@ 47
Use the given settings, or read them from the environment.

@@ 48
A **capacity limiter**: at most `workers` analyses may run at the same time.

@@ 50-53
**The lifespan.** At start-up, build the pipeline (loading the model) and keep it on `app.state`, the application's shared storage. `yield` hands control to the running server until shutdown.

@@ 55
Create the FastAPI app. The automatic documentation pages (`docs_url`, `redoc_url`, `openapi_url`) are switched off: an internal service should advertise nothing.

@@ 57-59
**`/livez`** — "is the process alive?" Container platforms poll it, and restart the container if it stops answering.

@@ 61-66
**`/readyz`** — "is it ready for work?" It answers only once the pipeline is loaded, and reports which age model is active and — as the comment says — whether the anti-spoofing networks are `loaded` or `missing`. Without them the service still analyses faces, but the API won't decide a live session (`domain/decision.py`); this answer lets an operator see why at a glance.

@@ 68-69
**The main endpoint**: `POST /internal/v1/analyze/face` returns a `FaceAnalysis`. FastAPI turns the returned model into JSON automatically.

@@ 70-71
**Back-pressure.** If every worker slot is busy, refuse immediately with `503 Service Unavailable` and `Retry-After: 1`, instead of piling up requests until the server collapses.

@@ 72
Read the **multipart form**: at most `MAX_FRAMES` (16) files and 1 ordinary field (`meta`). Anything more is refused by the parser before it is stored.

@@ 73-76
Parse and validate `meta` with the contract. A missing or invalid value becomes a clear `422 Unprocessable` error. `from error` keeps the original cause for debugging.

@@ 77
Collect each frame's bytes, in order.

@@ 78-81
For each frame the metadata promises, the matching upload `frame_<index>` must exist. Otherwise the request is refused with `422`, naming the missing frame.

@@ 82-84
Read at most one byte more than `MAX_FRAME_BYTES`. If that extra byte arrives, the frame is too big and is refused with `413 Content Too Large`. Asking for just one extra byte means an oversized frame is never copied into memory in full.

To be precise about who checks what: by this point the form parser has already received the whole upload, keeping large files in a temporary file on disk. The size of a *whole request* is capped earlier — by the API, which is the only program allowed to call this service, and in production also by the web server at the front door.

@@ 85
Keep the frame's bytes.

@@ 86-87
**Run the analysis on a worker thread**, within the limiter. Image work is CPU-heavy and *blocking*. Running it directly here would freeze the server's event loop and stall every other request, including health checks.

@@ 89
Return the finished application.
