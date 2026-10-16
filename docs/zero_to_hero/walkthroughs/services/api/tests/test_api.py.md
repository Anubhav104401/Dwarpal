---
fingerprint: e1112379a8bd3358
---
The **integration tests**: the whole API, end to end, against the *real* things it depends on —

- a real **PostgreSQL** and a real **Valkey**, each started in a throwaway **Docker container** by the **Testcontainers** library, and deleted afterwards (§4.14);
- the real **inference service**, running inside the same Python process, with its stand-in age model set to whatever age a test needs;
- the real migrations, the real signing keys, the real JWKS.

Unit tests (`test_domain.py`) prove that each rule is right. These tests prove that the pieces are **connected** right: that a pass really produces a token a website can verify, that a wrong key really gets a `401`, that the migrations really build the tables the code expects.

!!! kid "Explain like I'm six — the dress rehearsal"
    Checking each actor's lines separately is the unit test. The dress rehearsal is everyone on stage together, with real costumes and real lights. Mistakes that only appear when people interact — someone walks on at the wrong moment — are only found in the rehearsal.

If Docker isn't running, these tests are **skipped**, with a message saying why — not failed. Everything else can still be tested.

@@ 1
The docstring: the API, against real databases and the real inference service.

@@ 3
The project-wide type-hint setting.

@@ 5-11
Standard-library tools: `asyncio`, `logging`, the iterator types for fixtures, `asynccontextmanager`, `dataclass`, `Path` and `Any`.

@@ 13-17
OpenCV and NumPy (to make a test picture), the `docker` client (to ask whether Docker is running), `httpx` (to call the apps) and `pytest`.

@@ 18-19
Alembic's `compare_metadata` and `MigrationContext`, for the drift test at the end.

@@ 20-21
joserfc's `jwt` and `KeySet`: the tests verify tokens exactly as a website would.

@@ 22-23
SQLAlchemy types for the drift test.

@@ 24-26
Testcontainers: a ready-made PostgreSQL container, a general container for Valkey, and a **wait strategy** — "the container is ready when this line appears in its log".

@@ 28-34
The code under test: the table catalogue, the CLI's `migrate` and `seed_dev`, both apps' factories (renamed with `as` so the two `create_app`s can't be confused), both settings classes, and the frame contracts.

@@ 36-37
The repository folder, and the public-domain portrait from the vision library's tests — a real face, so the real face detector finds it.

@@ 38
The demo shop's return address, which the seeded project allows.

@@ 41-44
**`blank_frame`** — a plain grey 320 × 240 picture, saved as JPEG: a valid image with no face in it. `np.full` fills an array with one value (128, middle grey). `cv2.imencode` returns two values — whether it worked, and the encoded bytes.

@@ 47-48
**The `databases` fixture.** A **fixture** is something a test needs, prepared by pytest and passed in by name. `scope="session"` means it is built **once for the whole test run** and shared: starting two containers takes seconds, so doing it once matters. It provides the two addresses.

@@ 49-52
Is Docker running? Ask it, giving up after 5 seconds. If not, skip every test that needs this fixture, with the reason.

@@ 53-58
A PostgreSQL container, using exactly the image the local Compose file uses. The password is a throwaway for a throwaway container; the comment explains why the linter's warning about a hard-coded password doesn't apply.

@@ 59-63
A Valkey container, with its port exposed, considered ready when Valkey logs `Ready to accept connections`.

@@ 64-65
Start both. Each `start()` waits until its container is ready.

@@ 66-68
Docker maps each container's port to a random free port on this computer, so the addresses are built from what the containers report. Random ports mean tests never clash with a database already running locally.

@@ 69
Apply the migrations — the same function a developer runs from the command line.

@@ 70
`yield` hands the addresses to the tests. Everything after it runs when the whole test run is over…

@@ 71-72
…stopping (and removing) both containers.

@@ 75-79
**`Harness`** — what each test gets to work with: an HTTP client connected to the API, the seeded project's test API key, and the project's public ID.

@@ 82-83
**`harness`** — sets up a complete, fresh API for one test. Its options: the age the stand-in model should "see" (30 by default — clearly an adult), and whether the seeded key is live.

@@ 84
Unpack the two database addresses.

@@ 85
Create an inference app whose stand-in model reports the chosen age.

@@ 86-90
Start the inference app's lifespan (loading its face detector), and open an HTTP client wired to it through **`ASGITransport`** — httpx calls the app's Python code directly, with no network and no server. One `async with` with two parts, in brackets, opens both and closes both.

@@ 91-92
Create the API with test settings — the test databases' addresses — and the in-process inference client.

@@ 93
Run the API's lifespan: connect, load the signing key, read the manifest.

@@ 94
Seed a project and a key, exactly as a developer would with `seed-dev`.

@@ 95-97
Open a client wired to the API the same way, and hand the harness to the test. When the test ends, every `async with` closes in reverse order.

@@ 100-102
**`create`** — create a session as the demo shop would, with the API key. Any keyword arguments replace the defaults, so a test can write `create(h, policy="anything_goes")`.

@@ 105-106
**`secret`** — the body for `/start`: the session's client secret.

@@ 109-112
**`start`** — start the flow and return the `Authorization` header with the flow token, ready for the next calls. The `assert` includes the response text, so if starting fails, the test report shows why.

@@ 115-120
**`attempt`** — one complete face attempt, as the verify page makes it: get a challenge, describe the frames (taken 120 ms apart), package them as files `frame_0`, `frame_1`, …, and upload everything as a multipart form.

@@ 123-124
**The main story: an adult passes, and the website can verify the token.** `@pytest.mark.anyio` lets pytest run an `async` test function.

@@ 125-131
Create, start, attempt with four portraits — the stand-in model says 30, so it passes — then finish: the redirect goes back to the shop with the session's ID.

@@ 132
Start the flow *again*, as if the person reloaded the page afterwards.

@@ 133-135
As the shop's server: read the result with the API key, and fetch the public keys.

@@ 136-137
The reloaded page sees the completed session and its outcome — no error for the person.

@@ 138-139
The result says completed, and passed.

@@ 140
**Verify the token** exactly as a website would: with the published key set, accepting only Ed25519. If the signature didn't match, this line would raise an error.

@@ 141-146
The token is an age token, says pass, says `age_over_18: true` (the literal `True`, checked with `is`), and is addressed to this project, about this session, in test mode.

@@ 147
**No age inside.** None of these names appears among the claims: the set of forbidden names and the set of claim names have nothing in common (`&` is set intersection; an empty set counts as false).

@@ 150-162
**A clear child is refused, unmistakably.** With the stand-in model at 12, the attempt fails, and the signed token says `outcome: fail` *and* `age_over_18: false` — so even a website that read only the age claim would refuse entry.

@@ 165-171
**A teenager near the limit must use a stronger check.** At 16, the probability of being 18 or over is neither high enough to pass nor low enough to fail, so the answer is step up, with the reason `age_uncertain`.

@@ 174-186
**Poor frames: retry, retry, then step up.** Three attempts with blank grey frames: each finds no face. The first two are retries — the first saying `no_face` and that 2 attempts remain — and the third becomes a step-up. The session waits for a stronger check, and has no token.

@@ 189-204
**Credentials are checked, and errors are problem details.** No API key at all: `401`, with the problem-details media type, the stable code, the type reference, and a request ID that matches the response header. A wrong client secret and a missing flow token each get their own code.

@@ 207-211
**Each request is logged once, with its ID, and never with secrets.** `caplog` is pytest's log-capturing fixture; `set_level` makes it collect `INFO` lines from `dwarpal.api`.

@@ 212-213
Create one session. (Setting up the harness makes no HTTP requests, so this is the only request.)

@@ 214-217
Exactly one request log line, with the right method, path and status, and the same ID the response carried. `vars(record)` reads a log record's fields as a dict.

@@ 218-219
Neither the API key nor the new client secret appears anywhere in the captured logs.

@@ 222-236
**A challenge can be used only once.** The same challenge, sent twice: the first attempt is accepted, the second gets `409 challenge_invalid`.

@@ 239-247
**A session gets a limited number of challenges.** Seven requests in a row: six are granted (3 attempts × 2), the seventh gets `429 too_many_challenges`.

@@ 250-253
**Oversized and unmeasured bodies are refused before they are read.** `stream` is an async generator: given as a body, it makes httpx send the request in chunks of unknown total size.

@@ 255-258
A JSON body of about 100 KB (over the 64 KiB limit), and a chunked body.

@@ 259-263
`413 request_too_large` — still with a request ID — and `411 length_required`.

@@ 266-278
**Sessions refuse foreign return addresses, unknown policies, and live mode with a stand-in model.** A return address on another website, a policy that doesn't exist, and a session created with a *live* key while the model is uncalibrated: each gets its own code.

@@ 281-291
**Discovery and readiness.** The configuration document names Ed25519 and admits the model is uncalibrated; the key set may be cached for 5 minutes and holds only Ed25519 keys; and `/readyz` reports both databases as `ok`.

@@ 294
**The drift test: the migrations build exactly the tables the code describes.** It is not `async`, so it starts the async engine itself (line 305).

@@ 295-296
**`differences`** — Alembic's `compare_metadata` compares the real database (migrated by the fixture) with `METADATA`, the tables described in `tables.py`, and lists every difference: a missing table, an extra column, a different type.

@@ 298-303
**`check`** — connect to the test database and run the comparison through `run_sync`, because Alembic's comparison code isn't async (as in `env.py`).

@@ 305
The list of differences must be **empty**. If someone adds a column to `tables.py` but forgets the migration — or the other way round — this test fails, long before a real database meets the mismatch.
