---
fingerprint: bdf5afdeda44fa91
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

@@ 5-22
Standard-library tools: `asyncio` (also for the chaos tests' cutter, a small TCP relay), `base64` (a test master key), `contextlib` (to ignore a connection's expected errors), `hashlib` and `hmac` (to check a webhook's signature as a receiver would), `json`, `logging`, `re` (to check a recovery code's shape), `threading` and `time` (to run a real server beside the tests), `uuid` (fresh IDs), the iterator types for fixtures and `Callable` (the type of a function passed in), `asynccontextmanager`, `dataclass` and `replace` (a copy of a dataclass with one field changed), `UTC`, `datetime` and `timedelta` (a length of time, for key rotation and webhook retries), `Path`, `Any`, `Literal`, for the harness's liveness option (Phase 3) — and `urlsplit`, which takes a web address apart (the chaos tests reroute Valkey's).

@@ 24-29
OpenCV and NumPy (to make a test picture), the `docker` client (to ask whether Docker is running), `httpx` (to call the apps) and `pytest`. Since Phase 9 also `dwarpal`, the Python SDK (§5.9.1), for a test that runs it against this API.

@@ 30-31
`schemathesis`, the contract tester (step 6), and `uvicorn`, the server program, to serve the API on a real port for it.

@@ 33-34
Alembic's `compare_metadata` and `MigrationContext`, for the drift test at the end.

@@ 35-38
Since Part 7: the `cryptography` library's tools for making a throwaway signing key and its certificate, for the made-up Aadhaar Secure QR below.

@@ 39
Hypothesis's `settings` and `HealthCheck`, to tell Schemathesis (which uses Hypothesis inside) how many requests to make per operation.

@@ 40-41
joserfc's `jwt` and `KeySet`: the tests verify tokens exactly as a website would.

@@ 43
Pydantic's `SecretStr`, to give production settings a master key.

@@ 44
An async Valkey client, so a test can look at what the API stored there (Phase 4).

@@ 45-46
Schemathesis's `Case` — one generated request — and `positive_data_acceptance`, the one check the contract test leaves out (explained there).

@@ 47
SQLAlchemy's query builders, for the Phase 4 tests: `delete` (to remove a row on purpose), `select` and `func` (to count rows), `text` (raw SQL), and `update` (to try changing rows).

@@ 48-50
SQLAlchemy types: `Connection` for the drift test, `make_url` (which reads a database address so a chaos test can change its host and port), `DBAPIError` — the error SQLAlchemy raises when the database itself refuses a statement — and `create_async_engine`.

@@ 51-53
Testcontainers: a ready-made PostgreSQL container, a general container for Valkey, and a **wait strategy** — "the container is ready when this line appears in its log".

@@ 55-83
The code under test: the database helpers (`make_engine`, `make_sessions`, `tenant`), the master key, the table catalogue and the fifteen tables that belong to tenants, the audit and maintenance modules, the delivery worker, the CLI's `API_DOCUMENT`, `api_document`, `maintain`, `migrate`, `seed_dev`, `rotate_key` and `revoke_key`, both apps' factories (renamed with `as` so the two `create_app`s can't be confused), the ID and one-time-code helpers, both settings classes, and the contracts for frames, challenges and browser signals. The brackets let one `import` span several lines.

@@ 84
The vision library's makers of a specimen Secure QR (Part 7): the bytes, the photo, the number and the picture.

@@ 88-89
The repository folder, and the public-domain portrait from the vision library's tests — a real face, so the real face detector finds it.

@@ 90
The demo shop's return address, which the seeded project allows.

@@ 102-105
**`blank_frame`** — a plain grey 320 × 240 picture, saved as JPEG: a valid image with no face in it. `np.full` fills an array with one value (128, middle grey). `cv2.imencode` returns two values — whether it worked, and the encoded bytes.

@@ 108-109
**The `databases` fixture.** A **fixture** is something a test needs, prepared by pytest and passed in by name. `scope="session"` means it is built **once for the whole test run** and shared: starting two containers takes seconds, so doing it once matters. It provides the two addresses.

@@ 110-113
Is Docker running? Ask it, giving up after 5 seconds. If not, skip every test that needs this fixture, with the reason.

@@ 114-119
A PostgreSQL container, using exactly the image the local Compose file uses. The password is a throwaway for a throwaway container; the comment explains why the linter's warning about a hard-coded password doesn't apply.

@@ 120-124
A Valkey container, with its port exposed, considered ready when Valkey logs `Ready to accept connections`.

@@ 125-126
Start both. Each `start()` waits until its container is ready.

@@ 127-129
Docker maps each container's port to a random free port on this computer, so the addresses are built from what the containers report. Random ports mean tests never clash with a database already running locally.

@@ 130
Apply the migrations — the same function a developer runs from the command line.

@@ 131
`yield` hands the addresses to the tests. Everything after it runs when the whole test run is over…

@@ 132-133
…stopping (and removing) both containers.

@@ 136-140
**`Harness`** — what each test gets to work with: an HTTP client connected to the API, the seeded project's test API key, and the project's public ID.

@@ 141
`transport` — the in-process connection to the API (step 2): a test can open more clients on it, one per person, each with its own cookies.

@@ 144-154
**`harness`** — sets up a complete, fresh API for one test. Its options: the age the stand-in model should "see" (30 by default — clearly an adult), whether the seeded key is live, how liveness gets its evidence (Phase 3) — `"labels"` by default, because the tests' portrait is a still photo that can't turn its head — the seeded key's scopes (every scope by default), something to put in front of the inference service (`inference_via`, for the chaos tests: a function that takes the connection to it and returns another), and any other API settings to change (`**overrides`: extra named arguments, collected into a dict), such as a smaller device budget or rate limit. Since Part 7 also `aadhaar_keys_dir`: a folder of certificates for the inference service to trust for Aadhaar Secure QR codes, in place of UIDAI's.

@@ 155
Unpack the two database addresses.

@@ 156-161
Create an inference app whose stand-in model reports the chosen age, with the chosen liveness evidence, and with Tesseract as found above (or its default, where there's none — then document checks say OCR is unavailable). Since Part 7, with the chosen folder of Aadhaar certificates (empty: UIDAI's own).

@@ 162
The connection to it: **`ASGITransport`** — httpx calls the app's Python code directly, with no network and no server. Its type is written as any async transport, so the next lines may put another in its place.

@@ 163-164
If the test asked for it, wrap the connection — in a `Switch`, below, that can make the service "die".

@@ 165-168
Start the inference app's lifespan (loading its face detector), and open an HTTP client on that connection. One `async with` with two parts, in brackets, opens both and closes both.

@@ 169-170
Create the API with test settings — the test databases' addresses, plus any overrides — and the in-process inference client. The settings' default `database_role` applies, so **every test in this file runs as the restricted role**, under row-level security, exactly as the API will in production.

@@ 171
Run the API's lifespan: connect, load the signing key, read the manifest.

@@ 172
Seed a project and a key, exactly as a developer would with `seed-dev`, with the scopes asked for.

@@ 173-178
Open a client wired to the API the same way — since 9 Nov as a visitor at an address of its own, one of the addresses kept for documentation (`198.51.100.x`, RFC 5737), so limits per address count one test's requests, not the whole run's, just as each test has its own key — and hand the harness to the test, with the transport. When the test ends, every `async with` closes in reverse order.

@@ 181-184
**`create`** — create a session as the demo shop would, with the API key, plus any extra headers (`headers_extra`, such as an `Idempotency-Key`). Any keyword arguments replace the body's defaults, so a test can write `create(h, policy="anything_goes")`.

@@ 187-188
**`secret`** — the body for `/start`: the session's client secret.

@@ 191-194
**`start`** — start the flow and return the `Authorization` header with the flow token, ready for the next calls. The `assert` includes the response text, so if starting fails, the test report shows why.

@@ 197-198
**`following`** (Phase 3) — the labels for a burst whose head follows the given poses: frontal **baseline** frames first, then one frame per pose, in order. With 6 frames and 3 poses: baseline, baseline, baseline, then the three poses.

@@ 199
`["baseline"] * n` makes a list of n copies; `+ poses` adds the poses after them.

@@ 200
One `FrameMeta` per phase, numbered from 0, taken 120 ms apart. `enumerate` gives each item with its position.

The comment at the end, `# type: ignore[arg-type]`, silences one complaint of the type checker: it can't know that the plain texts in `poses` are valid `Phase` names. Pydantic checks them anyway when the `FrameMeta` is created.

@@ 203-212
**`attempt`** — one complete face attempt, as the verify page makes it. Besides the frames, three optional inputs let a test play an attacker (Phase 3):

- `poses` — label the frames with these poses instead of the ones asked for;
- `signals` — report these browser signals;
- `claimed` — put a challenge of the browser's own choosing into the request.

And a fourth, for the chaos tests: `challenge`, one fetched earlier — so a test can fetch it while everything works, then make a service die before the frames are sent.

@@ 213-215
The docstring says the same, in short.

@@ 216-217
Unless one was given, get a challenge — the server picks its random poses and colours.

@@ 218-220
Label the frames: by default they follow the challenge's own poses (an honest attempt), otherwise the poses the test gave. A challenge has 3 or 4 poses, so first make sure there are enough frames — at least 3 frontal ones, then one per pose — by repeating the last frame as many times as needed (`frames[-1:] * n`: a list of the last frame, `n` times; `max(0, …)` keeps `n` from going negative).

@@ 221
Describe the attempt: the frames' labels, the signals (normal ones unless given), and any claimed challenge.

@@ 222-224
Package the frames as files `frame_0`, `frame_1`, …, add the description and the challenge's ID, and upload everything as a multipart form.

@@ 227-229
**Who may frame a verify page** (decision D16): only the website a session returns to.

@@ 230-232
Three sessions: one with the shop's return address (the default), one without a return address, and one to be "over". The first is started.

@@ 233-242
Make the third expire: as the tables' owner, move its expiry time a minute into the past.

@@ 244-247
**`ancestor`** — ask who may frame a page; then ask it for the three sessions, a well-formed but unknown session, and something that isn't a session at all.

@@ 248
Start the first session again: the verify page's view of it.

@@ 249-251
Every answer is a `200` — this is asked while a page is being served, so it never fails. Only the session with a return address names a website, the shop's origin; the others name none. And the verify page learns the same origin when it starts.

@@ 254-255
**The main story: an adult passes, and the website can verify the token.** `@pytest.mark.anyio` lets pytest run an `async` test function.

@@ 256-262
Create, start, attempt with six portraits — the stand-in model says 30, so it passes — then finish: the redirect goes back to the shop with the session's ID.

@@ 263
Start the flow *again*, as if the person reloaded the page afterwards.

@@ 264-266
As the shop's server: read the result with the API key, and fetch the public keys.

@@ 267-268
The reloaded page sees the completed session and its outcome — no error for the person.

@@ 269-270
The result says completed, and passed.

@@ 271
**Verify the token** exactly as a website would: with the published key set, accepting only Ed25519. If the signature didn't match, this line would raise an error.

@@ 272-277
The token is an age token, says pass, says `age_over_18: true` (the literal `True`, checked with `is`), and is addressed to this project, about this session, in test mode.

@@ 278
**No age inside.** None of these names appears among the claims: the set of forbidden names and the set of claim names have nothing in common (`&` is set intersection; an empty set counts as false).

@@ 308-320
**A clear child is refused, unmistakably.** With the stand-in model at 12, the attempt fails, and the signed token says `outcome: fail` *and* `age_over_18: false` — so even a website that read only the age claim would refuse entry.

@@ 323-329
**A teenager near the limit must use a stronger check.** At 16, the probability of being 18 or over is neither high enough to pass nor low enough to fail, so the answer is step up, with the reason `age_uncertain`.

@@ 338-340
**`aadhaar_specimen`** (Part 7) — a picture of a made-up Aadhaar Secure QR, and — written into `folder` — the certificate of the key that signed it. No real Aadhaar is used anywhere in the tests.

@@ 341-354
Make a signing key of the kind UIDAI uses (RSA, 2,048 bits) and a certificate for it, valid for two days and signed by itself, and save the certificate as `test_issuer.cer`. A test that passes this folder to `harness` makes the inference service trust this key as it would trust UIDAI's.

@@ 355-358
The test portrait, cut close round the face as an ID photo is and squeezed as a Secure QR's photo is; the specimen's bytes with the given date of birth, signed with the throwaway key exactly as UIDAI signs (PKCS #1 v1.5 with SHA-256); written as the code's long number; drawn as a QR picture.

@@ 372-382
**An Aadhaar Secure QR as the document** (Part 7), for an adult and for a child. The docstring says what decides, and what is kept.

@@ 383-400
Make the specimen and start an API whose inference service trusts the specimen's key. A face check that can't decide (the stand-in model "sees" 16) sends the person to the document check, which gets the code's picture. Then read back the session, the public keys, and — straight from the database — what was kept of the document attempt.

@@ 401-409
The outcome is the expected one, with the reason `aadhaar_qr`; the token's claim is right, and its methods say **`document_aadhaar_qr`**. Of the code, exactly two things were kept: the signing key's name and the birth year and month. The specimen's name and reference number are nowhere in the record.

@@ 412-422
**A code UIDAI didn't sign never passes.** The same made-up code — claiming a birth in 1960 — shown to a service that trusts only UIDAI's real keys (no `aadhaar_keys_dir`). It is read, and refused for its signature each time: retry, retry, and on the third attempt, fail.

@@ 481-494
**Poor frames: retry, retry, then step up.** Three attempts with blank grey frames: each finds no face. The first two are retries — the first saying `no_face` and that 2 attempts remain — and the third becomes a step-up. The session waits for a stronger check, and has no token. It isn't finished, so it isn't in the totals yet; but its face check has reached a decision — once, not once per attempt — and is counted as a step-up.

@@ 501-516
**Credentials are checked, and errors are problem details.** No API key at all: `401`, with the problem-details media type, the stable code, the type reference, and a request ID that matches the response header. A wrong client secret and a missing flow token each get their own code.

@@ 519-523
**Each request is logged once, with its ID, and never with secrets.** `caplog` is pytest's log-capturing fixture; `set_level` makes it collect `INFO` lines from `dwarpal.api`.

@@ 524-525
Create one session. (Setting up the harness makes no HTTP requests, so this is the only request.)

@@ 526-529
Exactly one request log line, with the right method, path and status, and the same ID the response carried. `vars(record)` reads a log record's fields as a dict.

@@ 530-531
Neither the API key nor the new client secret appears anywhere in the captured logs.

@@ 534-548
**A challenge can be used only once.** The same challenge, sent twice: the first attempt is accepted, the second gets `409 challenge_invalid`.

@@ 551-560
**A session gets a limited number of challenges.** Thirteen requests in a row: twelve are granted — two per attempt, for three face attempts and, since Phase 6, three document attempts — and the thirteenth gets `429 too_many_challenges`.

@@ 563-566
**Oversized and unmeasured bodies are refused before they are read.** `stream` is an async generator: given as a body, it makes httpx send the request in chunks of unknown total size.

@@ 568-571
A JSON body of about 100 KB (over the 64 KiB limit), and a chunked body.

@@ 572-576
`413 request_too_large` — still with a request ID — and `411 length_required`.

@@ 682
**The drift test: the migrations build exactly the tables the code describes.** It is not `async`, so it starts the async engine itself (line 305).

@@ 683-684
**`differences`** — Alembic's `compare_metadata` compares the real database (migrated by the fixture) with `METADATA`, the tables described in `tables.py`, and lists every difference: a missing table, an extra column, a different type.

@@ 686-691
**`check`** — connect to the test database and run the comparison through `run_sync`, because Alembic's comparison code isn't async (as in `env.py`).

@@ 693
The list of differences must be **empty**. If someone adds a column to `tables.py` but forgets the migration — or the other way round — this test fails, long before a real database meets the mismatch.

@@ 696-698
**Red team, from here on** (Phase 3): tests that play the attacker. **Red-teaming** means attacking your own system on purpose, to find its weaknesses before someone else does.

The first: **a printed photo**. The "person" is the still test portrait, and here liveness measures the images for real (`liveness="images"`).

@@ 699-702
Two attempts with six identical portraits. The photo looks straight ahead throughout — it can't turn left, right or up when asked.

@@ 703-704
The first attempt gets a retry, with the vague `liveness_check_failed` (a real person may just have been slow). The second gets **rejected** — and from outside the reason is only `verification_failed`, which doesn't even say liveness was involved.

@@ 707-712
**Poses in the wrong order.** Labels mode is on, so the frames' labels are believed — but the attacker labels them `turn_right` three times, whatever the challenge asked. A challenge never repeats a pose twice in a row, so this can never match it.

@@ 713
Caught: retry, `liveness_check_failed`.

@@ 716-718
**A challenge claimed by the browser.** The attacker sends an easy challenge of its own choosing — one pose, `turn_left`, two colours.

@@ 719-722
And four frames that would satisfy *that* easy challenge: three baseline frames, then `turn_left`.

@@ 723
Caught: the server judged the frames against the challenge it **issued** (three random poses), not the claimed one, so the pose check fails.

@@ 726-733
**Automation and virtual cameras.** Two fresh sessions; in each the browser honestly reports one warning sign — a program driving the browser, or a virtual camera. The frames themselves are fine and the person is a clear adult.

@@ 734
Both go to **step up** with `liveness_uncertain`: not passed on a face that may have been injected, but not rejected either, because these signs can have innocent causes. `[x] * 2` is a list of two copies of `x`.

@@ 737-740
**One device gets only so many challenges, however many sessions it starts.**

@@ 741-744
A helper that creates a fresh session, starts it, and asks for a challenge with a given device ID — the flow token's headers plus `X-Dwarpal-Device` (`|` joins two dicts).

@@ 746-748
With a budget of 2 challenges an hour: three requests from the same device, each in a new session, then one from a different device.

@@ 749-751
The same device gets two challenges and then `429 too_many_attempts` — new sessions don't reset its budget; the other device is unaffected.

@@ 754-770
**The tenancy tests (Phase 4).** `TENANT_TABLES` — the fifteen tables whose rows belong to a tenant: from organisations to the audit log, the daily counts, the console's users and their memberships. (The signing keys belong to Dwarpal itself, not to any customer.)

@@ 771
`NOT_TENANT_DATA` — the only two tables allowed to have no row-level security: Alembic's migration history and Dwarpal's own signing keys. Neither belongs to any customer.

@@ 774-791
**`a_session`** — a minimal verification session for a given project, made directly as a table row rather than through the API: just enough to be a row worth hiding or showing. It follows a preset (`policy_version=0`). `bytes(32)` is 32 zero bytes, standing in for the client secret's digest.

@@ 794-796
**`two_organisations`** — the scene for the tests, built as the tables' **owner**, whom the policies don't bind: organisation A with projects a1 and a2, organisation B with project b1, and one verification session in each project.

@@ 797-798
The time, and a fresh random ID for each name. `uuid.uuid4()` is fine here: these IDs only need to be different from everything else in the shared test database.

@@ 799-808
An engine with **no role** — the owner. Add both organisations, then (after a `flush`, so the foreign keys find them) the three projects, then one session per project, and commit. `add_all` adds a whole list at once.

@@ 809-810
Close the engine, and return the IDs by name, so each test can say `made["a1"]`.

@@ 813-814
**Test 1 — reading.** Each tenant sees only its own rows, and a unit of work that names no tenant sees nothing at all.

@@ 815-817
Build the scene, then open an engine as the API does: as `dwarpal_app`.

@@ 818-822
First, a unit of work that names **no** tenant counts the rows of every tenant table — expected: zero everywhere, although this database holds rows from every test so far. Then roll back and ask PostgreSQL who we are (`current_user`). This guards the bug the tests found while this step was built: a rollback used to undo `SET ROLE`, and the connection quietly became the owner again (`db.py`).

@@ 823-825
Named as project **a1**: which projects own the sessions it can see, and which organisations it can see.

@@ 826-827
Named as organisation **A**: which projects it can see.

@@ 828-829
`finally` closes the engine even if something above fails, so a failing test doesn't leave connections open.

@@ 830-834
The verdicts. Still the restricted role; zero rows of anything with no tenant; project a1 sees only its own sessions and its own organisation; organisation A sees both its projects, and not b1.

@@ 837-840
**Test 2 — writing.** A tenant can't create or change another tenant's rows, and can't switch the protection off.

@@ 841-843
The same scene and the same restricted engine.

@@ 844-848
Named as **a1**, try to add a session belonging to **b1**. The database must refuse at commit with "new row violates **row-level security** policy". `pytest.raises(…, match=…)` passes only if that error, with that text, happens.

@@ 849-854
Named as **a1**, try to change b1's sessions: an `update` with a `where` that picks exactly them. `.returning(…)` asks the database to send back the ID of every row it changed. b1's rows are invisible to a1, so the update finds nothing to change.

@@ 855-856
After the commit, count sessions again in the same database session. The tenant was named with `set_config(…, true)`, for **one** transaction, and this is a new one: it sees nothing.

@@ 857-859
Could the restricted role simply turn the policies off? `ALTER TABLE … DISABLE ROW LEVEL SECURITY` is allowed only to a table's owner, so PostgreSQL answers "**must be owner** of table projects".

@@ 860-861
Close the engine, whatever happened.

@@ 862-863
The verdicts: no row changed, and nothing visible once the transaction had ended.

@@ 866-867
**Test 3 — through the API.** One website's key can't read another website's session.

@@ 868-871
Inside the usual harness, the first website creates a session. Then `seed_dev` makes a **second** organisation, project and key in the same database — a second customer.

@@ 872-877
Ask for the first website's session with the second website's key, and then with its own.

@@ 878-880
A foreign key gets the same `404 session_not_found` as a session that doesn't exist — it can't even learn that the session is there — while the owner reads it normally.

@@ 883
**Test 4 — no table forgotten.** The tests above prove that the policies work; this one proves that **every** table has them. A future migration that adds a table and forgets its policy would fail here, until someone either protects the table or decides, in this file, that it holds no customer's data.

@@ 884-890
Connect as the owner, and ask PostgreSQL's own catalogue. `pg_class` lists every table the database knows; the conditions keep ordinary tables (`relkind = 'r'`) in our `public` schema (`'public'::regnamespace` turns the schema's name into its internal ID) whose row-level security is **off** (`NOT relrowsecurity`). `connection.scalars` returns the first column of each row: the names. `set(…)` collects them, and the engine is closed.

@@ 892
The unprotected tables must be exactly the two allowed ones, no more and no fewer.

@@ 895-896
**`bearer_of`** — the `Authorization` header for a given key. The tests below use several keys, so `h.key` alone won't do.

@@ 899-902
**Idempotency.** Sending the same request twice with the same `Idempotency-Key` gets the first answer, not a second session.

@@ 903-908
The same request twice with one key; the same key with a *different* request; a key that is too short; and two requests with no key at all.

@@ 909-912
Look inside Valkey itself. `scan_iter("idem:*")` walks through every stored reply. Each must exist, and none may contain the client secret in readable form: the reply is sealed (`app/idempotency.py`), so a copy of Valkey reveals no secret.

@@ 913-916
Both requests succeeded, the second answer is **identical** to the first — the same session and the same client secret — and only the repeat carries `Idempotent-Replayed`.

@@ 917-921
The same key with a different request is refused (`422 idempotency_key_reused`). The short key is refused too — since step 6 by the pattern the API document states, so as a general `invalid_request` naming the header, before the API's own check runs. And without a key, two requests make two different sessions.

@@ 924-927
**Rate limits.** A key allowed a burst of 2 and almost no refill (one token every 100 seconds) makes three requests in a row.

@@ 928-930
Two get through, the third gets `429 rate_limited`, with a `Retry-After` of at least one second.

@@ 949-951
**Pagination.** Five sessions are listed two at a time.

@@ 952
Create five sessions, remembering their IDs in the order they were made.

@@ 953-960
Read the pages the way a client would: ask for 2, then keep asking `starting_after` the cursor of the last page until `has_more` is false. (`|` joins two dictionaries; with no cursor yet, the second one is empty.)

@@ 961
Ask for more than the largest allowed page.

@@ 962-966
All the listed IDs together: pages of 2, 2 and 1; exactly the five sessions, **newest first** (`reversed(made)`), none repeated, none missed; no `age_token` anywhere in the list; and the oversized page refused with `422`.

@@ 969-975
**Scopes.** A key with only `sessions:read` can't create a session (`403 insufficient_scope`), but can list them.

@@ 978-981
**Rotation and revocation.**

@@ 982-985
Rotate the harness's key with a one-hour grace period. The key id is characters 8 to 19 of the key.

@@ 986
During the grace period, the old key and its replacement both work.

@@ 987-989
Rotate the replacement with **no** grace at all, then try the key just replaced and its own replacement.

@@ 990-991
Revoke the newest key (`revoke_key` reports that it found one), and try it once more.

@@ 992-995
The verdicts: both keys worked during the grace period; a key whose grace has ended gets `401 api_key_expired`; its replacement works; a revoked key gets the plain `401 invalid_api_key`.

@@ 998-1001
**Versioned policies.** A session keeps the policy version it started with, even after a new version is added.

@@ 1002-1004
Add version 1 of the project's own policy `shop_18`.

@@ 1005
Create a session with it.

@@ 1006-1008
Add version 2, which allows only one face attempt.

@@ 1009
Create another session, which gets version 2.

@@ 1010
Start the **first** session's flow: its answer says how many attempts remain.

@@ 1011
List the policies.

@@ 1012-1014
Three refusals to check: a custom policy named like a preset, one for age 19 (the model has no thresholds for it), and a session asking for a policy nobody made.

@@ 1015-1016
The two versions were numbered `shop_18@1` and `shop_18@2`, and each session names the version it got.

@@ 1017
The first session still has **3** attempts — version 1's rules — although version 2, with only one, now exists.

@@ 1018
The list shows both versions of the project's own policy, oldest first.

@@ 1019-1021
And the three refusals: `invalid_policy_name`, `policy_not_supported`, `unknown_policy`.

@@ 1145-1148
**Immutability.** Add one policy version through the API.

@@ 1149-1156
Then, as the API's own role, try to change it and to delete it with plain SQL. The migration gave the role only `SELECT` and `INSERT` on this table, so PostgreSQL answers "**permission denied**" to both: no bug in our code could rewrite the rules a past check followed. Close the engine at the end, whatever happened.

@@ 1159-1161
**The webhook tests (Phase 4).** `Receiver` — a website's webhook receiver, kept in memory: no network, no server.

@@ 1163-1164
The statuses it will answer with, in order, and every request it has received.

@@ 1166-1168
**`handle`** — record the request, and answer with the next status in line (`pop(0)` takes the first), or `200` once the list is used up.

@@ 1171-1172
**`deliverer`** — the delivery worker, set up as in production: as the tables' owner.

@@ 1173-1174
An owner engine, and an HTTP client whose **transport** is `httpx.MockTransport(receiver.handle)`: every request the worker sends is handed straight to the receiver's function instead of going over a network.

@@ 1175
The development master key — the same one the API in the harness uses, so the worker can open the secrets the API sealed.

@@ 1176
Return the worker and its engine (so the test can close it). The clock is `lambda: clock[0]`: a function reading a one-item list, so the test can move time forward by changing `clock[0]` — and test a 24-hour retry without waiting 24 hours.

@@ 1179-1183
**`pass_one_session`** — create a session, start it, and pass one face attempt: a session that has just completed.

@@ 1186-1189
**Test — a delivery.** A completed session reaches the website, signed so that the website can check it.

@@ 1190
An empty receiver (it will answer `200`), and a clock.

@@ 1191
The harness allows private addresses: the receiver's address is never really contacted.

@@ 1192-1194
Register an endpoint for completed sessions.

@@ 1195
Complete one session: the event and its delivery are written in the same transaction.

@@ 1196
Set the worker's clock just past now, so the delivery is due.

@@ 1197-1199
Run the worker once, then close its engine.

@@ 1200-1201
Read the endpoint's deliveries, and the list of endpoints.

@@ 1202-1203
The secret was shown once, at creation, with its `whsec_` prefix, and never again.

@@ 1204
Exactly one delivery was sent, and it arrived.

@@ 1205-1210
The body is the completed event: it names the session and its outcome, it carries **no token**, and the `Dwarpal-Event-Id` header matches the event's ID.

@@ 1211-1214
Check the signature exactly as a receiver would: split the header into `t` and `v1`, recompute the HMAC of `"<t>.<body>"` with the secret, and compare in constant time (`compare_digest`).

@@ 1215
The delivery is recorded as delivered, on its first attempt, with the receiver's `200`.

@@ 1218-1221
**Test — retries.** A failing receiver is retried on the schedule until the delivery is dead; then it can be replayed.

@@ 1222
This receiver answers `500` eight times.

@@ 1223-1229
Register an endpoint, send it a **test event** (which goes to this endpoint whatever it subscribes to), and set the clock just past now.

@@ 1230-1233
Eight rounds. In each, the worker sends one delivery, and an immediate second run finds nothing due: the failure has pushed the next attempt into the future.

@@ 1234-1235
Read the delivery's state.

@@ 1236-1239
While it is still pending, measure the wait the worker chose, and move the clock forward to exactly that moment.

@@ 1240
Replay the dead delivery.

@@ 1241-1242
With the clock at now, the worker sends it again — and the receiver, out of failures, answers `200`.

@@ 1243-1244
Close the engine and read the final state.

@@ 1245
The test event was accepted (`202`, "accepted for later").

@@ 1246
The waits were exactly the schedule: 1 minute, 5 minutes, 30 minutes, 2, 6, 12 and 24 hours.

@@ 1247
After the eighth failure the delivery was dead, with the receiver's last `500` recorded.

@@ 1248-1249
Replaying put it back to pending with a fresh count, and it was then delivered.

@@ 1252-1257
**Test — the SSRF guard through the API.** With private addresses not allowed (the normal setting), an endpoint on `127.0.0.1` — this very computer — is refused.

@@ 1258-1260
So is an endpoint asking for an event type that doesn't exist.

@@ 1261-1262
`422 unsafe_webhook_url` and `422 unknown_event_type`.

@@ 1265-1270
**Test — introspection.** Pass a session and read its age token.

@@ 1271-1272
Seed a second website, with its own key.

@@ 1274-1276
**`ask`** — introspect a token with a given key. A function defined inside the test, because only this test needs it.

@@ 1278-1281
Ask four times: with the other website's key; with a **forged** token (its last four characters changed, which breaks the signature); and twice with the right key.

@@ 1282-1285
The other website and the forger both get only `{"active": false}`; the first genuine question gets `active` with the token's claims; the second gets `false` — a token is spent once introspected.

@@ 1288-1290
**Test — expiry is announced once.** A session lifetime of 0 seconds makes every new session expire at once.

@@ 1291-1293
Register an endpoint for expired sessions.

@@ 1294-1295
Create a session, and read it twice.

@@ 1296
Read the endpoint's deliveries.

@@ 1297-1298
Both reads say `expired`, but there is exactly **one** delivery: the first read saved the change and its event together, and the second found nothing to change.

@@ 1301-1308
**`org_of`** — the organisation that owns a seeded project, read as the tables' owner: the audit log is kept per organisation.

@@ 1311-1312
**Test — the audit chain.** Real changes are chained in the log, and tampering of either kind is found.

@@ 1313-1318
Through the API: add a policy version, register a webhook endpoint, and delete it. With the key `seed_dev` created, that makes four audited actions.

@@ 1319-1322
The organisation's ID; an engine as the owner, and one as the API's role.

@@ 1323
From here on, whatever happens, both engines are closed at the end (`try` … `finally`).

@@ 1324-1326
Read the organisation's entries, and verify the chain as it stands.

@@ 1327-1329
**The API can't rewrite history**: as the API's role, changing any entry is refused with "permission denied" — the role may only add entries (migration `0006`).

@@ 1330-1334
But someone with the **owner's** rights — a database administrator, or an attacker who stole that login — can. Change entry 2's facts (as if the policy had been for age 13) and verify again.

@@ 1335-1339
Put entry 2 back, then quietly **delete the last entry**, and verify once more.

@@ 1340-1342
Close both engines, whatever happened.

@@ 1343-1348
The four entries, in order: the key's creation, the policy version, the endpoint created, the endpoint deleted.

@@ 1349-1350
Changes made with the API key name it by its **id** (characters 8 to 19), and the key itself appears in no entry's facts.

@@ 1351
Before any tampering: four entries, intact.

@@ 1352
After the edit: broken, **at entry 2** — the exact entry that was changed.

@@ 1353
After the deletion: broken at entry 4, the missing one. The chain itself still checks out, but the head (`audit_heads`) remembers that there should be four.

@@ 1356-1360
**Test — counting.** Pass two sessions.

@@ 1361-1362
Read the last week's counts, and ask for more than a year.

@@ 1363-1366
Two passes in total, in one row for today under `uk_osa_18`; both face checks decided, as passes, with the median in the first band (under 5 seconds — the test is quick); and a request for 366 days refused with `422`.

@@ 1369-1373
**Test — the sweep and the purge.** Settings for calling the operator's command directly.

@@ 1374-1378
Sessions in this harness expire at once. Register an endpoint for expired sessions, and create a session that nobody will ever read.

@@ 1379-1380
Run the scheduled jobs, then read the endpoint's deliveries.

@@ 1381-1386
As the owner, give this project a retention of **one day**.

@@ 1387-1388
Run the jobs as if it were 23 hours later: within the day, so the session is kept.

@@ 1389-1390
Run them as if it were two days later: past the day, so it is purged.

@@ 1391
Read the project's counts.

@@ 1392-1394
Verify every organisation's audit chain.

@@ 1395-1396
The sweep expired at least one session (other tests leave theirs too), and the website was told, by one delivery, although nobody read the session.

@@ 1397-1399
After 23 hours nothing of this project's was purged and the session still exists; after two days it is gone (`404`).

@@ 1400
The count of one expired session outlives the session itself.

@@ 1401
And this organisation's audit chain is intact.

@@ 1404-1406
**The console tests (Phase 4, step 2).** The console's address; settings for its tests — a cookie that may travel over plain HTTP, and a generous sign-in allowance, because every test signs in from the same address; and a throwaway password.

@@ 1409-1411
**`person`** — a separate browser for one person: a new client on the same transport, with its own cookie jar, so several people can be signed in at once in one test.

@@ 1414-1418
**`sign_up`** — create an account and organisation through the console, insist it worked, and return the answer (which includes the CSRF token).

@@ 1421-1422
**`unique`** — a fresh e-mail address each time, so tests sharing the database never collide.

@@ 1425-1429
**Test — signing up, in and out.**

@@ 1430-1432
Sign up, and look at the cookie the browser received.

@@ 1433-1438
Try to sign up again with the same address, and with a five-character password.

@@ 1439-1441
Sign in with a wrong password; with an address nobody has; and correctly, typed in capitals.

@@ 1442-1445
Sign out without the CSRF token, then with it; then ask who is signed in.

@@ 1446-1447
The new person owns the new organisation; the cookie is a long, unguessable token.

@@ 1448-1449
The repeated address and the weak password are refused.

@@ 1450-1451
A wrong password and an unknown account get the **same** status and the **same** sentence: an attacker can't use sign-in to find out who has an account.

@@ 1452
Addresses match whatever their capitals.

@@ 1453-1455
Signing out needs the CSRF token like any change; with it, the session ends, and the cookie no longer works.

@@ 1458-1460
**Test — CSRF.**

@@ 1461-1465
Sign up, then try a change three ways: with a guessed token, with the real token but from another site's origin, and genuinely.

@@ 1466-1468
The guess fails (`csrf_failed`), another origin fails (`bad_origin`), and only the genuine request works.

@@ 1471-1474
**Test — one-time codes.**

@@ 1475-1476
Sign up, and ask to set up one-time codes: the answer holds the secret and its `otpauth://` address.

@@ 1477-1481
Work out the current 30-second step. A wrong code is refused; the right one, computed from the secret as an authenticator app would, switches codes on.

@@ 1482-1483
Sign in with only the password.

@@ 1484-1486
Sign in with the **next** step's code — what a phone whose clock runs a little fast shows — and then try exactly the same code again.

@@ 1487-1492
The offer was a proper `otpauth://` address; the wrong code failed and the right one worked — and came with ten recovery codes; a password alone is no longer enough; the code worked once — and a second time it is refused.

@@ 1564-1566
**Test — roles.** Three addresses: an owner, an analyst and a developer.

@@ 1567-1573
Inside one harness, four browsers — the fourth for an outsider. `async with ( … ):` opens several at once, and closes them all at the end.

@@ 1574-1576
The owner signs up; note the organisation and the owner's CSRF token.

@@ 1577-1580
The analyst and the developer sign up (each gets an organisation of their own), and so does the outsider.

@@ 1581-1585
The owner adds the analyst and the developer to the owner's organisation, each with their role.

@@ 1586-1588
The analyst lists the organisation's projects — any member may — and the test builds the address for creating API keys in the first one.

@@ 1589-1591
The analyst and the developer each try to create a read-only key.

@@ 1592-1596
The developer tries to make the analyst an owner.

@@ 1597-1601
The analyst lists the members; the outsider tries to; the developer's new key is used on the API; and the owner and the analyst read the audit log.

@@ 1602-1604
The analyst may not create keys (`403 forbidden_for_role`); the developer may; and the developer may not manage members.

@@ 1605-1606
The analyst sees all three members; the outsider gets `404`, exactly as if the organisation didn't exist.

@@ 1607
The key made in the console works on the API.

@@ 1608-1611
The owner's audit log, oldest first: the organisation's creation, two members added, a key created; the chain is intact; and the key itself appears nowhere in it.

@@ 1612
The analyst may not read the audit log.

@@ 1859-1861
A browser at an address of its own. `ASGITransport(…, client=…)` sets the address the API sees the request coming from; `192.0.2.x` is a range reserved for documentation and tests. Without it, every other test's sign-ins would already have used up this address's allowance.

@@ 1862-1867
Sign up, then try a wrong password three times.

@@ 1868-1869
Two ordinary refusals, then `429 too_many_sign_ins`, with a `Retry-After` of at least a second.

@@ 1906-1908
**The contract test (Phase 4, step 6).** `live_api` — Schemathesis sends real HTTP, so the API runs as a real server for these tests. `scope="module"` starts it once for the whole file rather than once per test.

@@ 1909-1918
Its settings: the test databases; webhook addresses never looked up (the fuzzer invents host names); a cookie allowed over plain HTTP; and limits so high that the fuzzer's many requests aren't simply refused with `429`. Since 9 Nov the verify page's per-address limit too (`flow_burst`).

@@ 1919
Seed a project and a key for it.

@@ 1920
A uvicorn server for the API, on `127.0.0.1` and **port 0**, which asks the operating system for any free port, so the test never collides with something already running.

@@ 1921-1922
Run it in a background **thread**: `daemon=True` means the thread won't keep Python alive if the tests end without stopping it.

@@ 1923-1924
Wait, a twentieth of a second at a time, until the server says it has started.

@@ 1925
Read which port it was given.

@@ 1926
Hand the tests the server's address and the key.

@@ 1927-1928
Afterwards, ask the server to stop, and wait up to ten seconds for its thread to finish.

@@ 1931-1933
**`live_document`** — Schemathesis reads the API's document from the running server, exactly as a website's developer would.

@@ 1936
`contract` — tells Schemathesis to take the document from that fixture. A document known only once the server runs can't be read while pytest is still collecting tests, so it is fetched lazily, from the fixture.

@@ 1939-1940
`@contract.parametrize()` turns the test into one sub-test per operation in the document: 31 of them. `@settings` gives each 25 generated requests, no time limit per request (`deadline=None`), and turns off Hypothesis's health checks, which would complain that each example is slow (it is a real HTTP request).

@@ 1941-1942
**Test — the contract.** For each generated request (`case`):

@@ 1943-1945
Every check but one. `positive_data_acceptance` insists that a request the document allows must succeed. But some of the API's rules depend on data, not just shape: whether the age model is calibrated for an age, whether an address is among the project's allowed origins. Refusing such a request with `422` is correct.

@@ 1946
Send it to the server with the website's key, and check the answer: never a server error, a status code the document lists for this operation, a content type it lists, a body that matches the schema for that status, and the headers HTTP requires (such as `Allow` on a `405`). Any failure prints the exact request, as a `curl` command to reproduce it.

@@ 1949-1951
**Test — no drift.** `docs/api/openapi.json` is what websites read; the docstring says how to refresh it.

@@ 1952
The file must equal, byte for byte, what the code produces now. A change to the API without refreshing the document fails here.

@@ 1955-1957
**Fail-closed tests (Phase 7).** Valkey unreachable. "Gone" is simulated by an address where nothing listens: port 1 on this computer.

@@ 1958-1961
Settings with that Valkey and the real database; a key; and an API started with them (its inference client is never reached).

@@ 1962-1965
Try to create a session — the API key's rate limit needs Valkey — and ask whether the API is ready.

@@ 1966-1968
The session request gets `503 service_unavailable` with `Retry-After: 5` (not a crash, not a pass), and readiness reports exactly what is wrong: the database is fine, Valkey isn't.

@@ 1971-1972
**`unreachable`** — an inference service that is down: every request fails to connect.

@@ 1975-1976
**`broken`** — an inference service that answers, but with nonsense: valid JSON that isn't an analysis.

@@ 1979-1984
**Fail closed when inference fails.** The test runs twice, once with each broken service (`parametrize`).

@@ 1985-1991
An API whose inference client sends every request to the broken service, and a harness around it.

@@ 1992-1995
Create a session, start it, and make two attempts with a real face.

@@ 1996-1997
Neither attempt passes — the face would have passed with a working service — and the first is a `retry`: the person may try again, but nobody is let in on a failure.

@@ 2000
**Chaos tests** (Phase 7). The roadmap asks for *fail-closed chaos tests*: services killed in the middle of a check. They were first done by hand, stopping containers during a load test (§5.7.6); these tests do it on every run, so a change can't quietly break it. Each asks two questions: while a service is down, does anything pass? And once it is back, can a person finish their check?

@@ 2003-2006
**`Cutter`** — a small **TCP relay**: the API connects to it instead of to the real PostgreSQL or Valkey, and it passes the bytes on both ways. *Cutting* it drops every open connection at once and hangs up on new ones — to the API, exactly as if the service had died. *Restoring* lets connections through again, as after a restart. The containers themselves are never touched, so the other tests sharing them are safe.

@@ 2008-2012
Where to relay to; not cut yet; the open connections (both ends of each), so they can all be dropped; and the listening server, once started.

@@ 2014-2016
Entering the `async with`: listen on a free port on this computer (port `0` asks the system to choose one); each new connection runs `relay`.

@@ 2018-2021
Leaving it: drop everything, and stop listening.

@@ 2023-2026
**`port`** — the port the system chose. `@property` lets it be read like a field (`cutter.port`) though it is worked out each time.

@@ 2028-2031
**`relay`** — one connection from the API. While cut, hang up at once: `abort` closes the connection without the usual polite goodbye, as a dead service would.

@@ 2032-2034
Otherwise, connect to the real service, and remember both ends.

@@ 2035-2036
Copy both ways at the same time (`gather` runs the two copies together) until the connection ends; then forget it.

@@ 2038-2041
**`cut`** — from now on, refuse; and drop every open connection. `list(…)` takes a copy first, because dropping them changes the set.

@@ 2043-2044
**`restore`** — let connections through again.

@@ 2047-2048
**`pipe`** — copy one direction of a connection.

@@ 2049-2052
Read up to 64 KB at a time and pass it on, until the source ends (an empty read). `:=` (the "walrus") reads and tests in one go. `drain` waits while the other side is slow. A connection that is cut raises a connection error — expected here, so `suppress` ignores it.

@@ 2053
When one direction ends, drop the other side too, so neither half is left hanging.

@@ 2056-2058
**`chaos`** — the test databases, reached through two cutters: it hands back the new addresses (to give to the harness), and the cutters for PostgreSQL and Valkey.

@@ 2059-2061
Take both addresses apart, and check they have a host and a port.

@@ 2062-2065
Start one cutter for each service.

@@ 2066-2067
Build the addresses that lead through them — the same database, but on this computer at the cutter's port — and hand everything to the test. `hide_password=False`: the address must keep the (throwaway) password to work.

@@ 2070-2071
**`Switch`** — the same idea for the inference service, which the tests reach through httpx rather than a socket: a **transport** (what httpx sends requests through) put in front of the real one.

@@ 2073-2076
The real transport, set later; not down; and `on_call`, something to do on every call — nothing by default (`lambda: None` is a function that does nothing).

@@ 2078-2080
**`around`** — the function given to the harness as `inference_via`: keep the real transport, and use the switch in its place.

@@ 2082-2086
Every call: first run `on_call`; then, if the switch is down, fail exactly as an unreachable service does (`ConnectError`); otherwise pass the request on.

@@ 2089-2090
**`unavailable`** — the three things a "try again shortly" answer must have: status `503`, the code `service_unavailable`, and `Retry-After`.

@@ 2093-2095
**`outcome_of`** — what the website would see: the session's status and outcome, read with its API key.

@@ 2098-2102
**Valkey dies in the middle of a check.** Everything goes through the cutters. A session is created and started, and a challenge fetched while all is well.

@@ 2103-2106
Valkey dies. The person sends their frames; then the readiness check is asked.

@@ 2107-2109
Valkey comes back. The person tries again, and the website reads the result.

@@ 2110-2112
While Valkey was down: "try again shortly", and readiness names Valkey. Afterwards: the same connection pool recovered on its own, the face passes, and the session is complete — passed once.

@@ 2115-2122
**The database dies between two steps** — the same story with PostgreSQL.

@@ 2123-2128
The database dies before the frames arrive; readiness is asked; the database comes back; the person tries again.

@@ 2129-2131
While it was down, nothing was decided ("try again shortly", readiness names the database); afterwards the pool's *pre-ping* (`db.py`) noticed the dropped connections and made new ones, and the check passed.

@@ 2134-2138
**The database dies while a face is being analysed** — the hardest moment: after the attempt was accepted and its challenge used up, before the decision is written. The switch in front of inference makes that moment happen.

@@ 2139-2142
On the inference call, cut the database (`on_call`).

@@ 2143-2145
The attempt; then the switch is cleared, and the database comes back.

@@ 2146-2148
What the website sees now; a new attempt; and what it sees after.

@@ 2149-2151
The attempt answered "try again shortly" — the analysis is thrown away, never half-recorded. The session was untouched (still `in_progress`, no outcome), and the next attempt passed.

@@ 2154-2157
**Inference dies and comes back.** (The fail-closed test above has it dead throughout.)

@@ 2158-2164
Inference goes down; an attempt; it comes back; another attempt; the result.

@@ 2165-2166
While down: a `retry`, with 2 tries left — the person loses one try but isn't let in. Afterwards: a pass.

@@ 2169-2174
**Security headers (Phase 7).** A refusal (no key), the public key set, and the interactive documentation.

@@ 2175-2180
Every answer carries `nosniff`, the strict content policy, `no-referrer` and (since Phase 7) `Cross-Origin-Resource-Policy: same-origin`. HSTS isn't sent outside production: over plain HTTP it would mean nothing.

@@ 2181-2183
Answers are `no-store` unless their route says otherwise: the key set keeps its own five-minute public caching. The documentation page has no content policy, which would stop its scripts.

@@ 2186-2194
**Production.** Settings a production deployment would accept: a real-looking master key and HTTPS addresses. The app isn't started, because `/livez` needs no database.

@@ 2195-2198
Ask for `/livez`, the documentation page and the API document.

@@ 2199-2200
HSTS is sent (two years); the interactive documentation doesn't exist (`404`); the API document is still published.

@@ 2203-2209
**Test — the console's project pages (Phase 5).** An owner and an analyst, each with their own browser.

@@ 2210-2215
The owner signs up; the analyst signs up; the owner adds the analyst to the organisation.

@@ 2216-2219
The owner finds the organisation's project and creates a key for it in the console.

@@ 2220
A website using that key: the harness, copied with the key changed (`replace`).

@@ 2221-2223
The website creates a session — without a return address, because this new project hasn't allowed any yet — and a person passes it.

@@ 2225-2227
The analyst reads the project's sessions, the passed session's trace, and the last week's counts.

@@ 2228-2231
The analyst and then the owner try to add a policy version; the analyst lists the policies.

@@ 2232
The analyst tries the harness's own project — which belongs to another organisation — under this organisation's address.

@@ 2233-2234
The one session is listed; its trace has one attempt, and it passed.

@@ 2235-2236
The attempt carries its numbers: the age probability, the line it met, and the liveness evidence.

@@ 2237
Reading a trace made no token.

@@ 2238
The counts show one pass.

@@ 2239-2241
An analyst may not add a policy version; the owner may, and it is listed as `console_18@1`.

@@ 2242
Another organisation's project, named under this organisation, is not found — the check that the project belongs to the organisation in the address.

@@ 2245-2248
**Test — the console's webhooks (Phase 5).** An owner and an analyst. Private addresses are allowed, so the endpoint can point at this computer (`localhost:9`, where nothing listens — nothing is sent in this test).

@@ 2249-2255
The owner signs up, the analyst signs up and is added, and the owner finds the project.

@@ 2256-2257
The project's webhook address, and an endpoint for finished sessions.

@@ 2259-2262
The analyst tries to add it; the owner adds it; the analyst tries to list them; the owner lists the live ones.

@@ 2263-2267
The owner sends a test event, reads the endpoint's deliveries, and replays the first.

@@ 2268-2271
The owner tries to delete it as a live endpoint, then deletes it as the test one it is; lists again; and reads the audit log.

@@ 2272
An analyst may not add one.

@@ 2273
The owner's new endpoint came with its secret, and is a test endpoint.

@@ 2274
An analyst may not even list them; and the live mode has none — modes never mix.

@@ 2275-2276
The test event is waiting to be delivered (no worker runs here); the replay is accepted.

@@ 2277
The wrong mode is "not found"; the deletion worked, and the list is empty.

@@ 2278-2279
The audit log names a person (`user:…`), not a key, for both the creation and the deletion.

@@ 2282-2289
**Test — the owner rules for members (Phase 5).** Three people, each with their own browser: an owner, an admin, and one more.

@@ 2290-2294
All three sign up.

@@ 2295-2297
The owner adds the admin as an admin, and the third person as an analyst.

@@ 2298-2299
Everyone's IDs: the third person's from the answer, the owner's from `/me`, the admin's from the member list.

@@ 2301-2303
The admin promotes the analyst to developer, then tries to make them an owner; the only owner tries to step down to admin.

@@ 2304-2305
The owner makes the third person an owner, and then steps down — allowed now, since there are two.

@@ 2306-2308
The admin tries to remove the new owner; the new owner removes the admin; and tries to remove an ID that isn't anyone's.

@@ 2309-2310
What remains, and the audit log.

@@ 2311
An admin may change a member who isn't an owner.

@@ 2312
An admin may not make an owner.

@@ 2313
The last owner may not step down.

@@ 2314
With two owners, one may.

@@ 2315
An admin may not remove an owner; an owner may remove an admin; an unknown member is not found.

@@ 2316
Left: the first owner (now an admin) and the new owner.

@@ 2317-2318
The audit log holds exactly the four changes that happened — refusals leave no trace.

@@ 2321-2326
**Test — unstorable text is refused (Phase 5).** Sign in with an address containing NUL — the kind of input the contract tests found: `422 invalid_text`, not a server error.

@@ 2329-2332
**Test — the model page** (§5.5.2): anyone signed in can read which model is deciding and how it was made, and nothing about its build.

@@ 2333-2334
Run the API with the trained model's manifest — the one with sources and measured bounds — rather than the stub.

@@ 2335-2337
Ask before signing in, then sign up and ask again.

@@ 2338
Signed out, the answer is the usual 401.

@@ 2339-2341
Signed in: the version, that it isn't calibrated for live use, its permitted use, the faces it learnt from and the number it was calibrated on.

@@ 2342-2343
The line for 18: its 7.5 % risk budget, and a measured worst case for minors within it.

@@ 2344-2345
And the line's adult outcomes: the youngest band, 18 to 20, measured on 330 faces — most of whom, as the comment says, a line this careful sends to a stronger check.

@@ 2346-2347
And none of the internal details of the file — the checksum, the build's commit, the file's name or the note that it was built from uncommitted code — is in the answer.

@@ 2350-2354
**Test — the model's performance is published to anyone, without its scores** (§5.5.9). With the trained model, ask `/v1/model` with no key and no sign-in…

@@ 2355-2357
…and it answers, cacheable for five minutes, with the model's version and the fact that it isn't calibrated.

@@ 2358-2359
The 18+ line carries its bounds (the minors' under its budget) and its adults' outcomes, starting with 18 to 20.

@@ 2360
But neither of each line's two scores: they would only help someone tuning an attack.

@@ 2363-2367
**Test — the production session cookie (Phase 5).** The browser tests now run with a plain cookie (WebKit drops `Secure` ones on plain HTTP), so this test checks the real one: with the production setting, sign up and read the `Set-Cookie` header.

@@ 2368-2369
Sign up.

@@ 2370-2371
The cookie's name starts with `__Host-`, so browsers insist it is `Secure`, for path `/`, with no `Domain`: no other site can set or read it.

@@ 2372-2373
Its attributes include `HttpOnly` (no script can read it), `Secure` (HTTPS only), `Path=/` and `SameSite=Lax`.

@@ 2374
And no `Domain`, which would share it with other hosts.

@@ 2377-2383
**Test — switching an endpoint off and on** (Phase 5). A website registers an endpoint.

@@ 2384-2386
Switch it off, send a test event, and read its deliveries.

@@ 2387-2389
Switch it back on, and do the same.

@@ 2390
And try to switch an endpoint that doesn't exist.

@@ 2391
The answers said off, then on.

@@ 2392
While off, nothing was queued for it.

@@ 2393
Back on, the test event waits to be delivered.

@@ 2394
An unknown endpoint is not found.

@@ 2397-2399
**Test — listing sessions by outcome and by reference** (Phase 5).

@@ 2400-2402
A session with the website's reference `order-1`, which a person passes.

@@ 2403
Another, `order-2`, not yet started.

@@ 2404-2408
List the passed ones; the one for `order-2`; one for a reference nobody used; and ask for an outcome that doesn't exist.

@@ 2409-2411
Exactly the passed session; exactly `order-2`'s; and nothing.

@@ 2412
An unknown outcome is refused, not silently ignored.

@@ 2415-2420
**Test — recovery codes, and switching codes off** (Phase 5).

@@ 2421-2425
Sign up, ask for a secret, and confirm the current code: the answer holds the recovery codes.

@@ 2426-2429
Sign in with the first recovery code, typed as someone might copy it from paper — capitals, a space instead of the dash. Keep the new session's CSRF token.

@@ 2430
Try the same recovery code again.

@@ 2431-2432
Ask for a fresh set, then try one of the old set.

@@ 2433-2439
Try to switch codes off with a wrong password, then with the right password and the next code.

@@ 2440
Sign in with the password alone.

@@ 2441
Ten different codes, each of the shape `abcde-fghij`.

@@ 2442
The recovery code signed in, and nine are left.

@@ 2443
Each works once.

@@ 2444
The fresh set shares nothing with the old, and the old no longer works.

@@ 2445
A wrong password is refused.

@@ 2446-2447
With the right password and code, codes are off — and the password alone signs in again.

@@ 495-496
The face check's count: nothing in the totals, one step-up among the decided face checks.

@@ 85-86
For the document checks (§5.6.2): `Tesseract`, to find out whether OCR is available, and `specimen_jpeg`, which draws a photographed specimen passport.

@@ 91-99
`TESSERACT` — how to run Tesseract here: installed, or in the project's OCR container; `None` if neither answers, and then the document tests are skipped.

@@ 332-335
**`specimen`** — a photographed specimen passport (ICAO's Utopia) with the test portrait's face and the given date of birth, expiring in 2036.

@@ 361-369
**`document_attempt`** — the step-up's document check, as the verify page will send it: a new challenge; selfie frames whose labels follow its poses; the document's photo as one more file; all posted to `/stepup/mrz`.

@@ 425-432
**Test — after a step-up, a document decides**, run twice: an adult's passport (born 1990), which must pass, and a 12-year-old's (born 2014), which must fail.

@@ 433-437
Its docstring says what is proved. Without Tesseract the test is skipped, not failed.

@@ 438-442
A face check at 16 for an 18+ policy can't decide (`step_up`); then the document check.

@@ 443
Afterwards, ask for another challenge: a decided session must refuse it.

@@ 444-446
Read the session as the website would, and the public signing keys.

@@ 448-456
And read, straight from the database, what was kept of the document check.

@@ 457-460
The face check stepped up; the document decided; no further check is possible; the session is completed with the document's outcome.

@@ 461-464
The token says the age, and **how** it was decided — a face estimate, a document's MRZ and a face match — at `basic` assurance.

@@ 465-466
Something was kept; of the document, the year and month of birth — and **no name and no document number** appear anywhere in what was kept.

@@ 471-478
**Test — the document check is open only to a session sent there.** Straight after starting, with no face attempt, it's refused with `session_not_awaiting_step_up`.

@@ 281-284
**Test — the Python SDK runs a whole check against the real API** (§5.9.1), as a Python website would.

@@ 285-291
Through the API's own test transport, the SDK's `AsyncClient` creates a session; the person's side (start, face attempt) runs as in the other tests, with the session's secret taken from its link; and the SDK reads the result.

@@ 292-295
The API's public keys, served to the SDK through a fake address (the SDK fetches them itself, but this test has no network).

@@ 296-305
The SDK verifies the token itself — issuer, audience, age, session — and the session is completed with a pass that allows entry at 18, under the policy asked for.

@@ 42
Since Phase 9, the software passkey device (`passkey_device.py`), shared with `test_webauthn.py`.

@@ 1495-1502
**`add_passkey`** — ask for the options, let the device answer, and send that with a name and the password (a test may change any field); the device's own ID isn't part of a registration's body.

@@ 1505-1507
**`passkey_sign_in`** — get a challenge and send the device's signed answer.

@@ 1510-1516
**Test — a passkey is added with the password, then signs in alone, once per challenge** (Phase 9, §5.9.2). One device, and a second that was never registered.

@@ 1517-1522
In one browser: sign up; try adding the passkey with a wrong password; add it; add it again; list.

@@ 1523-1529
In a second, fresh browser: sign in with the passkey; use one answer twice; try the unregistered device; and an answer made on another site.

@@ 1530-1533
Remove the passkey, try to sign in with it, remove it again, and read the audit log.

@@ 1534-1547
A wrong password is refused; the passkey is added once (`409` the second time); it is listed, unused. The passkey alone signs in, with a session cookie. The reused answer, the unregistered passkey and the other site's answer are refused, each with its code. Once removed, it signs nobody in, and removing it again is `404`. The audit log has the additions, removals and sign-ins.

@@ 1550-1557
**Test — with one-time codes on, adding a passkey needs a code too.** Switch them on, then add a passkey without a code and with the next one.

@@ 1558-1561
Without a code: refused. With one: added.

@@ 32
Since Phase 9 also the software Age Pass holder (`age_pass_holder.py`), shared with `test_agepass.py`.

@@ 1024-1034
**`passed_with_age_passes`** — a session under a policy, passed by the face check, then asking for a batch of passes for the holder's keys; the holder keeps them if they came.

@@ 1037-1048
**`present_age_pass`** — a new session answered with one of the holder's passes: start, ask for a nonce, present.

@@ 1051-1055
**Test — an Age Pass from one check completes the next without a camera, once** (Phase 9, §5.9.3).

@@ 1056-1065
A policy that accepts passes; a passed check that gives out twenty; and a second request for the same check.

@@ 1066-1070
A new session answered with pass 0; its result and the public keys; pass 0 again on a third session; pass 1 on a fourth.

@@ 1071-1080
The pass-decided session asking for passes of its own; a session under a preset asking for a nonce; that session's view; and the issuer metadata.

@@ 1081-1093
Passes come once, twenty, stating 13, 16 and 18; a pass completes a session whose token says `age_pass`; a used pass is refused but the next works; a pass can't renew itself; no preset takes passes; and the issuer metadata points at the keys.

@@ 1096-1103
**Test — a pass must reach the session's age and be made for this session.** Two policies that take passes, at 18 and 21, and a batch from an 18+ check.

@@ 1104-1117
An 18+ pass for a 21+ session; a proof naming another session; and a second presentation on a nonce already used.

@@ 1118-1133
A check that passed twenty minutes ago (its completion time moved back in the database) asking for passes.

@@ 1134-1137
A key with a private part.

@@ 1138-1142
Each refused with its own code: line too low, wrong audience, nonce used, too late; and the private part refused by the request's own schema.

@@ 579-585
**Sessions refuse foreign return addresses and unknown policies**, each with its own code. (Until 8 Nov this test also checked that live sessions were refused with the stand-in model; since D24 they are decided by an ID document — the next test.)

@@ 588-591
**`anti_spoofing_verdict`**: the real inference service, with one thing stood in for — the anti-spoofing networks' verdict on the selfie. A live session requires it, and the test service, which trusts the frames' labels, can't give it. The OCR, the face match and every other check stay real.

@@ 593-600
A transport that passes each request to the real service and, for the document check only, rewrites its answer as if the networks had measured the selfie from the images and found it real (0.99).

@@ 602
The wrapped transport, for `harness(inference_via=…)`.

@@ 605-610
**D24 end to end**: with the stand-in age model, a live session is created, says it is document-only, refuses face attempts, and is decided by the passport and the selfie alone; its token says so. Test sessions are unchanged.

@@ 611-612
Reading the passport needs Tesseract; without it the test is skipped.

@@ 613-615
A test session first: its start says it is *not* document-only.

@@ 616-620
Then a live one, with the stood-in verdict: created, and started.

@@ 621-622
A face attempt, and a document attempt with a specimen passport of someone born in 1990.

@@ 623-625
What the website sees afterwards, and the keys to check the token's signature.

@@ 627-630
The test session isn't document-only; the live one was created (`201`), started in progress and document-only, and its face attempt was refused with `document_required`.

@@ 631-632
The document passed it, and the session completed, live.

@@ 633-635
The token's `methods` are the document and the face match only — no `face_estimation` — and its `model` is `null`: no age model decided.

@@ 668-679
**Discovery and readiness.** The configuration document names Ed25519 and admits the model is uncalibrated; the key set may be cached for 5 minutes and holds only Ed25519 keys; and `/readyz` reports both databases as `ok`. And it says live checks are decided by a document (`live_checks`, D24).

@@ 1615-1620
**Test — a project made in the console** (decisions D28, D29, and deploy step 7): an owner makes a project with its website's origin, a key for it, and a session that returns there; origins are checked and written one way; changes are audited; developers can't make projects.

@@ 1621-1627
An owner signs up; a second person signs up and is added as a developer.

@@ 1628-1633
A project with two spellings of the same origin…

@@ 1634-1637
…four origins that aren't allowed: a path, `http` for another computer, a wildcard, another scheme…

@@ 1638-1640
…and a project the developer tries to make.

@@ 1641-1646
The owner renames the project and replaces its origins, adding this computer's demo shop.

@@ 1647-1649
A key for the project.

@@ 1650-1659
A session returning to the shop's origin — written in capitals, with a path and a query — and one returning to another website.

@@ 1660
The audit log.

@@ 1661-1663
The project was made, its origins written one way with the duplicate dropped; the four others were refused.

@@ 1664-1666
The developer was refused; the rename and the new origins took.

@@ 1667-1668
The session was accepted — only the origin counts — and the other website's refused.

@@ 1669-1672
The audit log ends with the project made, changed and given a key; the change records the name from and to.

@@ 1675-1676
**Test — at most 20 projects** (decision D28).

@@ 1677-1682
An owner makes 20 more projects, one after another.

@@ 1683-1684
Nineteen are made — the one made at sign-up counts too — and the twentieth is refused with `too_many_projects`.

@@ 1687-1691
**Test — keys listed and stopped** (decision D30): the console lists a project's keys, never their secrets, and stops one at once.

@@ 1692-1700
An owner, and an analyst added to the organisation; the default project's keys address.

@@ 1701-1703
Two keys; the first works.

@@ 1704-1705
The owner lists the keys; the analyst tries to.

@@ 1706-1708
The first key is stopped, then stopped again, and an unknown key is stopped.

@@ 1709-1712
Both keys are tried, the states listed, and the audit log read.

@@ 1713-1716
The first key worked before; the list is newest first and holds no secret; the analyst was refused.

@@ 1717-1718
Stopping twice is fine both times; an unknown key isn't found.

@@ 1719-1721
The stopped key is refused at once, the other still works, and the states say so.

@@ 1722
Stopping twice is recorded once.

@@ 1725-1728
**Test — invitations** (decision D44): no e-mail is sent; the invitation waits, can be cancelled, and is taken when that address signs up.

@@ 1729-1733
An address without an account; an owner and their organisation's members address.

@@ 1734-1735
The address is invited as a developer — in capitals — and then again.

@@ 1736-1738
The waiting invitation is listed, cancelled, and the list is empty.

@@ 1739-1742
Invited again, as an analyst; the person signs up; the list and the audit log are read.

@@ 1743-1747
The first invitation was pending, written in lower case; the second was refused; the list showed the developer invitation, and cancelling emptied it.

@@ 1748-1750
The new person belongs to their own organisation and to the one that invited them, as an analyst; the invitation was taken.

@@ 1751-1754
The audit log tells the story in order, never names the address, and its chain is intact.

@@ 1757-1760
**Test — a new password** (decision D31): every other session ends; this browser carries on with a new cookie.

@@ 1761-1766
A person signs up in one browser and signs in from another.

@@ 1767-1772
A change with a wrong current password, and one with too short a new password…

@@ 1773-1775
…and a proper change.

@@ 1776-1780
Both browsers try again; the old and the new password are tried; the audit log is read.

@@ 1781-1783
The other browser had signed in; the wrong password and the weak one were refused.

@@ 1784-1786
The change gave a new CSRF token; this browser is still signed in, the other is not.

@@ 1787-1788
The old password no longer works, the new one does, and the change is in the audit log.

@@ 1791-1796
**Test — deleting an account** (decision D32): an organisation of one closes, a shared one loses a member, an only owner with others must hand over first, and the address is free again.

@@ 1797-1804
Four people, each in their own browser.

@@ 1805-1812
The leaving person signs up — their organisation of one — and makes a key.

@@ 1813-1819
Another person's organisation adds them as a developer.

@@ 1820-1821
A deletion with a wrong password, then a proper one.

@@ 1822-1825
Afterwards: their browser, their key, the shared organisation's members and its audit log.

@@ 1826
The same address signs up again.

@@ 1828-1834
An owner whose organisation has another member tries to delete their account…

@@ 1835-1841
…makes the other member an owner, and tries again.

@@ 1842
The organisation's members afterwards.

@@ 1843-1846
The wrong password was refused; the deletion worked; the browser is signed out; the organisation of one was closed, so its key stopped at once.

@@ 1847-1849
The shared organisation lost the member, recorded it with an intact chain — and the audit log never names the address.

@@ 1850
Nothing of the address was kept: it signed up again.

@@ 1851-1853
The only owner was refused until ownership was handed over; then the organisation stayed, with the other person as its owner.

@@ 1856-1858
**Test — sign-in limits.** At most 2 attempts at once, then one every two minutes.

@@ 933-936
**Test — the verify page's calls are limited per network address** (Phase 4, open item 5, 9 Nov): a flood from one address is refused before it reaches the database, while another address carries on.

@@ 937-939
A tiny limit — three calls, then one every 100 seconds — and four quick calls from the test's address.

@@ 940-942
Another address calls once.

@@ 943-946
Three were answered and the fourth refused, with `rate_limited` and a `Retry-After`; the other address was answered.

@@ 447
The project's counts, to check the ID-document figures (9 Nov).

@@ 467-468
The ID-document check, reached once and ended once with the document's outcome (9 Nov): the dashboard's step-up conversion.

@@ 497-498
It reached the ID-document check (`opened`), and hasn't ended it: the dashboard counts it as reached, with no ending (9 Nov).

@@ 626
The live counts, to check the ID-document figures (9 Nov).

@@ 636-638
Started at the ID-document check — counted when the page opened — and ended there with a pass, in the live counts; no face check was decided (9 Nov).

@@ 641-646
**Test — a live check that starts at the document can end with an Age Pass, and is counted as ended** (9 Nov; D24 and D26).

@@ 647-648
The passport check needs Tesseract: skipped without it, as the other document tests are.

@@ 649-653
A holder of Age Passes, a live harness whose inference answers with an anti-spoofing verdict, and a policy that accepts passes.

@@ 654-660
The first live check, under that policy: it opens on the passport check (counted as reached), the passport passes it, and the browser takes a batch of passes.

@@ 661-662
A second live check — reached too, the moment its page opens — answered with a pass instead; then the live counts.

@@ 663-665
The passport passed, the pass was accepted, and the counts say both checks were reached and both ended: one by the document, one by a pass.

@@ 1872-1877
**Test — wrong passwords lock the account to that address, and nowhere else** (9 Nov): the design's lock-out back-off, through the API. The lock's growing length is checked without a database (`test_console_rules.py`).

@@ 1878-1879
The console's test settings, with a smaller free count — two — and a one-minute first lock.

@@ 1881-1883
**`browser_at`** — a browser at a network address of the test's choosing, talking to the same API.

@@ 1885-1888
Two addresses from the ranges kept for documentation (RFC 5737), random so no other test shares them; a browser at each; an account; and an address with none.

@@ 1890-1891
**`login`** — one sign-in attempt, from the first browser unless another is given.

@@ 1893-1897
One wrong try, then the right password (which starts the count afresh); three wrong tries (two free, then the third locks); the right password from the same address; the right password from the other one; and four wrong tries for the address with no account.

@@ 1898-1903
The right password after one wrong one signs in; the next three wrong ones are refused as wrong; the right one is then refused as locked, for about a minute (`Retry-After` 55–60 seconds, allowing for the test's own time); the other address signs in; and the account that doesn't exist locks the same way — so a lock doesn't tell anyone that an account exists.
