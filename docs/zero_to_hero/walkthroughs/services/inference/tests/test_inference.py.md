---
fingerprint: 99da7af3d0cdde0b
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
Tools to write `client_for` (line 30), a helper that starts the app and opens a client to it.

@@ 7
`Path`, to find the shared test picture and the model file.

@@ 9-12
- `httpx` — the HTTP client;
- `numpy` — a blank image for the stand-in model test;
- `pytest`;
- `FastAPI` — only for the type hint of `client_for`.

@@ 14-19
The code under test: the contracts, the stand-in model and its age scale, the app factory, the pipeline, the settings and the detector.

@@ 21-23
The repository root (`parents[3]` climbs `tests → inference → services → root`). The portrait's bytes are read **once** and shared by every test, together with the model file's location.

@@ 26-27
**`burst(count)`** builds request metadata for `count` frames, 120 milliseconds apart, as the capture page would.

@@ 30-35
**`client_for(app)`** — run an app *in memory* and talk to it over HTTP, without opening any network port:

- `app.router.lifespan_context(app)` runs the app's start-up code (loading the model) and, at the end, its shutdown code;
- `httpx.ASGITransport(app=app)` is a "pretend network": requests go straight into the app's code;
- the client is handed (`yield`) to the test, and closed automatically afterwards.

Starlette 1.8 now recommends against its older built-in test client, so this plain-httpx approach avoids that deprecated path.

@@ 38-40
A module-wide fixture: one pipeline with the real detector and a stand-in model fixed at age 30 (spread 2.5 years).

@@ 43-47
**The stand-in model is a proper distribution centred on its age.**

- It returns 101 probabilities, one per age.
- They add up to 1, within a millionth of a millionth (rounding).
- Their weighted average age is 30.

@@ 50-57
**A burst becomes one analysis.** With three good frames:

- all three are usable;
- the age estimate exists and its mean is 30 (within half a year);
- P(age ≥ 18) is practically 1, and P(age ≥ 25) above 0.95 — a 30-year-old is very likely over 25, but less certainly than over 18;
- each frame has its own expected age.

@@ 60-63
**One bad frame doesn't spoil the others.** The first "frame" is not an image at all. It is reported as `undecodable`, while the second frame is still used.

@@ 66-69
**No usable frame, no estimate.** Sixteen zero bytes are not an image, so there is no age estimate at all (`None`) — rather than a made-up one.

@@ 72
`@pytest.mark.anyio` — this test is **asynchronous** (`async def`). It must be run by an event loop, which anyio's pytest plugin provides.

@@ 73-74
**A real multipart request.** `files` maps each form field name (`frame_0`, `frame_1`) to a file name, its bytes and its content type, exactly as a browser sends uploads.

@@ 75-79
Start an app whose stand-in model says 40, then:

- post the metadata (`data`) and the frames (`files`) to the analysis endpoint;
- ask the readiness endpoint which model is loaded.

`await` waits for each response without blocking anything else.

@@ 80-84
The request succeeded (`200`). The response is read back through the contract (`model_validate`), which would fail if any field were wrong. The model version, the number of usable frames and the readiness answer are all as expected.

@@ 87-95
**A missing frame is refused, and named.** The metadata promises two frames but only `frame_0` is sent, so the answer must be `422` with the exact message `frame_1 is missing`.

This test caught a real bug while it was being written: the endpoint checked uploads against the wrong `UploadFile` class (see `main.py`, line 11).
