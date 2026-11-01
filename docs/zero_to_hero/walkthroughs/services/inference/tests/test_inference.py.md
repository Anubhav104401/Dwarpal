---
fingerprint: 770f010a022afee0
---
Tests for the inference service, at two levels:

- **the pipeline** — calling the Python code directly;
- **the HTTP interface** — sending real multipart requests, exactly as the API will.

The stand-in age model makes the expected answers exact: "a 30-year-old" must come out as 30.

@@ 1
The module docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-6
`hashlib` and `json` — to write a small model's manifest, with its fingerprint (Phase 2).

@@ 7
`time`, for a stand-in pipeline that takes a known time.

@@ 8-9
Tools to write `client_for` (line 30), a helper that starts the app and opens a client to it.

@@ 10
`Path`, to find the shared test picture and the model file.

@@ 12
`anyio`, to send two requests at once.

@@ 14-18
- `httpx` — the HTTP client;
- `numpy` — blank images for the age-model tests;
- `onnx` — to build a tiny ONNX model for the tests (Phase 2; a development tool only, listed in the root `pyproject.toml`);
- `pytest`;
- `FastAPI` — only for the type hint of `client_for`.

@@ 19
From `onnx`: the data-type names (`TensorProto`), the graph builder (`helper`) and the converter from NumPy arrays (`numpy_helper`).

@@ 21-26
The code under test: the contracts (now with `DocumentAnalysis`), both age models with their fingerprint error and age scale, the backend chooser and the app factory, the pipeline and its frame chooser (`sharpest`), the settings, and the face detector.

@@ 30-32
The repository root (`parents[3]` climbs `tests → inference → services → root`). The portrait's bytes are read **once** and shared by every test, together with the model file's location.

@@ 35-36
**`burst(count)`** builds request metadata for `count` frames, 120 milliseconds apart, as the capture page would.

@@ 39-44
**`client_for(app)`** — run an app *in memory* and talk to it over HTTP, without opening any network port:

- `app.router.lifespan_context(app)` runs the app's start-up code (loading the model) and, at the end, its shutdown code;
- `httpx.ASGITransport(app=app)` is a "pretend network": requests go straight into the app's code;
- the client is handed (`yield`) to the test, and closed automatically afterwards.

Starlette 1.8 now recommends against its older built-in test client, so this plain-httpx approach avoids that deprecated path.

@@ 47-49
A module-wide fixture: one pipeline with the real detector and a stand-in model fixed at age 30 (spread 2.5 years).

@@ 52-56
**The stand-in model is a proper distribution centred on its age.**

- It returns 101 probabilities, one per age.
- They add up to 1, within a millionth of a millionth (rounding).
- Their weighted average age is 30.

@@ 59-66
**A burst becomes one analysis.** With three good frames:

- all three are usable;
- the age estimate exists and its mean is 30 (within half a year);
- P(age ≥ 18) is practically 1, and P(age ≥ 25) above 0.95 — a 30-year-old is very likely over 25, but less certainly than over 18;
- each frame has its own expected age.

@@ 69-70
**Test — the age model sees only the sharpest few** (Phase 7). Six good frames of the portrait.

@@ 71
All six count as usable…

@@ 72
…but only three were estimated: the analysis lists one age per estimated frame.

@@ 73
And the chooser on its own: the two 0.9s first, in their original order, then 0.5.

@@ 76-79
**One bad frame doesn't spoil the others.** The first "frame" is not an image at all. It is reported as `undecodable`, while the second frame is still used.

@@ 82-85
**No usable frame, no estimate.** Sixteen zero bytes are not an image, so there is no age estimate at all (`None`) — rather than a made-up one.

@@ 88
`@pytest.mark.anyio` — this test is **asynchronous** (`async def`). It must be run by an event loop, which anyio's pytest plugin provides.

@@ 89-90
**A real multipart request.** `files` maps each form field name (`frame_0`, `frame_1`) to a file name, its bytes and its content type, exactly as a browser sends uploads.

@@ 91-95
Start an app whose stand-in model says 40, then:

- post the metadata (`data`) and the frames (`files`) to the analysis endpoint;
- ask the readiness endpoint which model is loaded.

`await` waits for each response without blocking anything else.

@@ 96-100
The request succeeded (`200`). The response is read back through the contract (`model_validate`), which would fail if any field were wrong. The model version, the number of usable frames and the readiness answer are all as expected.

@@ 103-108
**Readiness says when the anti-spoofing networks are missing.** Start the service with file names that don't exist: it still starts, and `/readyz` reports `antispoof: missing`.

@@ 111-119
**A missing frame is refused, and named.** The metadata promises two frames but only `frame_0` is sent, so the answer must be `422` with the exact message `frame_1 is missing`.

@@ 122-123
**`tiny_model`** — build a stand-in ONNX age model with the real one's interface — pixels in, 101 probabilities out — without PyTorch or any training. The service must be testable on its own, in seconds.

@@ 124
Its only weights: a 3 × 101 grid of numbers spread evenly from −1 to 1.

@@ 125-136
The model's **graph**, node by node: average each colour over the whole picture (`GlobalAveragePool`, giving 3 numbers per face), lay them flat, multiply by the weights (101 scores), and turn them into probabilities (`Softmax`). Then its input and output, named and shaped exactly like the real model's (`faces` is a size left open), and the weights, scaled so that pixels of 0–255 give moderate scores.

@@ 137
Wrap the graph as a model for ONNX's operator set 18, in file-format version 10 — the format the real export uses. (The `onnx` library would otherwise write its newest format, 14, which ONNX Runtime 1.31 can't read yet: the first version of this test found that.)

@@ 138-143
Save it, fingerprint it, and write a minimal manifest naming its version, file and fingerprint.

@@ 146-153
**An ONNX model gives one distribution per face**: two faces in (all black, all white), two rows of 101 probabilities out, each adding up to 1, different from each other; and the version is the manifest's.

@@ 156-163
**The wrong file is refused**: a model file with a few extra bytes no longer matches its fingerprint, and the backend refuses to load it; a missing file is refused too.

@@ 166-170
**The settings choose the backend**: `onnx` with a model folder gives the ONNX model; the default settings still give the stand-in.

@@ 173-178
**`Slow`** — a stand-in pipeline that takes a quarter of a second and returns an empty analysis: enough to keep the one worker busy.

@@ 181-183
**Test — a short wait, then "busy"** (Phase 7), run twice (`parametrize`): with a wait of 0.05 s, one of two simultaneous requests must be told busy; with 1 s, both are served.

@@ 184-186
One frame, its labels, and an app with a single worker and the chosen wait.

@@ 187-189
Start it, swap in the slow pipeline, and collect the status codes.

@@ 191-192
**`send`** — one analysis request; note its status code.

@@ 194-196
Send two at once (`create_task_group` runs both, and waits for both).

@@ 197
In order: 200 and 503 for the short wait — the second request gave up while the first was being analysed; 200 and 200 for the long one — it waited its turn.

@@ 13
`cv2` (OpenCV) — to decode the test portrait into pixels, for drawing a specimen document (§5.6.2).

@@ 27-28
For the document checks: `Tesseract`, to find out whether OCR is available, and `specimen_jpeg`, which draws a photographed specimen passport.

@@ 200-208
`TESSERACT` — how to run Tesseract here: installed, or in the project's OCR container; `None` if neither answers.

@@ 211-214
**Test — a document check reads the zone and matches the selfie to the printed face.** Skipped without Tesseract.

@@ 215-217
Three selfie frames of the test portrait, and a photographed specimen passport carrying the same face.

@@ 218-222
Post them to the document address, and ask for readiness too.

@@ 223-226
Two lines read, starting `P<UTO`, and **no name** in them: the names line is blanked before it leaves the service.

@@ 227-230
One face found on the document, alike enough to the selfie (above 0.5; OpenCV's threshold for the same person is 0.363); the selfie analysed as a face attempt; and OCR reported ready.

@@ 233-236
**Test — without Tesseract, a document check says so.** A service told to start a program that doesn't exist.

@@ 237-240
Post the portrait as the "document": it has no MRZ at all.

@@ 241-244
No zone is read, for the right reason (no band was found, so Tesseract wasn't needed), and readiness says OCR is `missing`.
