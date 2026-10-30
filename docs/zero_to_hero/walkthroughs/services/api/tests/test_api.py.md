---
fingerprint: cd8ca2db4c580521
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

@@ 24-28
OpenCV and NumPy (to make a test picture), the `docker` client (to ask whether Docker is running), `httpx` (to call the apps) and `pytest`.

@@ 29-30
`schemathesis`, the contract tester (step 6), and `uvicorn`, the server program, to serve the API on a real port for it.

@@ 31-32
Alembic's `compare_metadata` and `MigrationContext`, for the drift test at the end.

@@ 33
Hypothesis's `settings` and `HealthCheck`, to tell Schemathesis (which uses Hypothesis inside) how many requests to make per operation.

@@ 34-35
joserfc's `jwt` and `KeySet`: the tests verify tokens exactly as a website would.

@@ 36
Pydantic's `SecretStr`, to give production settings a master key.

@@ 37
An async Valkey client, so a test can look at what the API stored there (Phase 4).

@@ 38-39
Schemathesis's `Case` — one generated request — and `positive_data_acceptance`, the one check the contract test leaves out (explained there).

@@ 40
SQLAlchemy's query builders, for the Phase 4 tests: `delete` (to remove a row on purpose), `select` and `func` (to count rows), `text` (raw SQL), and `update` (to try changing rows).

@@ 41-43
SQLAlchemy types: `Connection` for the drift test, `make_url` (which reads a database address so a chaos test can change its host and port), `DBAPIError` — the error SQLAlchemy raises when the database itself refuses a statement — and `create_async_engine`.

@@ 44-46
Testcontainers: a ready-made PostgreSQL container, a general container for Valkey, and a **wait strategy** — "the container is ready when this line appears in its log".

@@ 48-76
The code under test: the database helpers (`make_engine`, `make_sessions`, `tenant`), the master key, the table catalogue and the fifteen tables that belong to tenants, the audit and maintenance modules, the delivery worker, the CLI's `API_DOCUMENT`, `api_document`, `maintain`, `migrate`, `seed_dev`, `rotate_key` and `revoke_key`, both apps' factories (renamed with `as` so the two `create_app`s can't be confused), the ID and one-time-code helpers, both settings classes, and the contracts for frames, challenges and browser signals. The brackets let one `import` span several lines.

@@ 78-79
The repository folder, and the public-domain portrait from the vision library's tests — a real face, so the real face detector finds it.

@@ 80
The demo shop's return address, which the seeded project allows.

@@ 83-86
**`blank_frame`** — a plain grey 320 × 240 picture, saved as JPEG: a valid image with no face in it. `np.full` fills an array with one value (128, middle grey). `cv2.imencode` returns two values — whether it worked, and the encoded bytes.

@@ 89-90
**The `databases` fixture.** A **fixture** is something a test needs, prepared by pytest and passed in by name. `scope="session"` means it is built **once for the whole test run** and shared: starting two containers takes seconds, so doing it once matters. It provides the two addresses.

@@ 91-94
Is Docker running? Ask it, giving up after 5 seconds. If not, skip every test that needs this fixture, with the reason.

@@ 95-100
A PostgreSQL container, using exactly the image the local Compose file uses. The password is a throwaway for a throwaway container; the comment explains why the linter's warning about a hard-coded password doesn't apply.

@@ 101-105
A Valkey container, with its port exposed, considered ready when Valkey logs `Ready to accept connections`.

@@ 106-107
Start both. Each `start()` waits until its container is ready.

@@ 108-110
Docker maps each container's port to a random free port on this computer, so the addresses are built from what the containers report. Random ports mean tests never clash with a database already running locally.

@@ 111
Apply the migrations — the same function a developer runs from the command line.

@@ 112
`yield` hands the addresses to the tests. Everything after it runs when the whole test run is over…

@@ 113-114
…stopping (and removing) both containers.

@@ 117-121
**`Harness`** — what each test gets to work with: an HTTP client connected to the API, the seeded project's test API key, and the project's public ID.

@@ 122
`transport` — the in-process connection to the API (step 2): a test can open more clients on it, one per person, each with its own cookies.

@@ 125-134
**`harness`** — sets up a complete, fresh API for one test. Its options: the age the stand-in model should "see" (30 by default — clearly an adult), whether the seeded key is live, how liveness gets its evidence (Phase 3) — `"labels"` by default, because the tests' portrait is a still photo that can't turn its head — the seeded key's scopes (every scope by default), something to put in front of the inference service (`inference_via`, for the chaos tests: a function that takes the connection to it and returns another), and any other API settings to change (`**overrides`: extra named arguments, collected into a dict), such as a smaller device budget or rate limit.

@@ 135
Unpack the two database addresses.

@@ 136
Create an inference app whose stand-in model reports the chosen age, with the chosen liveness evidence.

@@ 137
The connection to it: **`ASGITransport`** — httpx calls the app's Python code directly, with no network and no server. Its type is written as any async transport, so the next lines may put another in its place.

@@ 138-139
If the test asked for it, wrap the connection — in a `Switch`, below, that can make the service "die".

@@ 140-143
Start the inference app's lifespan (loading its face detector), and open an HTTP client on that connection. One `async with` with two parts, in brackets, opens both and closes both.

@@ 144-145
Create the API with test settings — the test databases' addresses, plus any overrides — and the in-process inference client. The settings' default `database_role` applies, so **every test in this file runs as the restricted role**, under row-level security, exactly as the API will in production.

@@ 146
Run the API's lifespan: connect, load the signing key, read the manifest.

@@ 147
Seed a project and a key, exactly as a developer would with `seed-dev`, with the scopes asked for.

@@ 148-150
Open a client wired to the API the same way, and hand the harness to the test, with the transport. When the test ends, every `async with` closes in reverse order.

@@ 153-156
**`create`** — create a session as the demo shop would, with the API key, plus any extra headers (`headers_extra`, such as an `Idempotency-Key`). Any keyword arguments replace the body's defaults, so a test can write `create(h, policy="anything_goes")`.

@@ 159-160
**`secret`** — the body for `/start`: the session's client secret.

@@ 163-166
**`start`** — start the flow and return the `Authorization` header with the flow token, ready for the next calls. The `assert` includes the response text, so if starting fails, the test report shows why.

@@ 169-170
**`following`** (Phase 3) — the labels for a burst whose head follows the given poses: frontal **baseline** frames first, then one frame per pose, in order. With 6 frames and 3 poses: baseline, baseline, baseline, then the three poses.

@@ 171
`["baseline"] * n` makes a list of n copies; `+ poses` adds the poses after them.

@@ 172
One `FrameMeta` per phase, numbered from 0, taken 120 ms apart. `enumerate` gives each item with its position.

The comment at the end, `# type: ignore[arg-type]`, silences one complaint of the type checker: it can't know that the plain texts in `poses` are valid `Phase` names. Pydantic checks them anyway when the `FrameMeta` is created.

@@ 175-184
**`attempt`** — one complete face attempt, as the verify page makes it. Besides the frames, three optional inputs let a test play an attacker (Phase 3):

- `poses` — label the frames with these poses instead of the ones asked for;
- `signals` — report these browser signals;
- `claimed` — put a challenge of the browser's own choosing into the request.

And a fourth, for the chaos tests: `challenge`, one fetched earlier — so a test can fetch it while everything works, then make a service die before the frames are sent.

@@ 185-187
The docstring says the same, in short.

@@ 188-189
Unless one was given, get a challenge — the server picks its random poses and colours.

@@ 190-192
Label the frames: by default they follow the challenge's own poses (an honest attempt), otherwise the poses the test gave. A challenge has 3 or 4 poses, so first make sure there are enough frames — at least 3 frontal ones, then one per pose — by repeating the last frame as many times as needed (`frames[-1:] * n`: a list of the last frame, `n` times; `max(0, …)` keeps `n` from going negative).

@@ 193
Describe the attempt: the frames' labels, the signals (normal ones unless given), and any claimed challenge.

@@ 194-196
Package the frames as files `frame_0`, `frame_1`, …, add the description and the challenge's ID, and upload everything as a multipart form.

@@ 199-200
**The main story: an adult passes, and the website can verify the token.** `@pytest.mark.anyio` lets pytest run an `async` test function.

@@ 201-207
Create, start, attempt with six portraits — the stand-in model says 30, so it passes — then finish: the redirect goes back to the shop with the session's ID.

@@ 208
Start the flow *again*, as if the person reloaded the page afterwards.

@@ 209-211
As the shop's server: read the result with the API key, and fetch the public keys.

@@ 212-213
The reloaded page sees the completed session and its outcome — no error for the person.

@@ 214-215
The result says completed, and passed.

@@ 216
**Verify the token** exactly as a website would: with the published key set, accepting only Ed25519. If the signature didn't match, this line would raise an error.

@@ 217-222
The token is an age token, says pass, says `age_over_18: true` (the literal `True`, checked with `is`), and is addressed to this project, about this session, in test mode.

@@ 223
**No age inside.** None of these names appears among the claims: the set of forbidden names and the set of claim names have nothing in common (`&` is set intersection; an empty set counts as false).

@@ 226-238
**A clear child is refused, unmistakably.** With the stand-in model at 12, the attempt fails, and the signed token says `outcome: fail` *and* `age_over_18: false` — so even a website that read only the age claim would refuse entry.

@@ 241-247
**A teenager near the limit must use a stronger check.** At 16, the probability of being 18 or over is neither high enough to pass nor low enough to fail, so the answer is step up, with the reason `age_uncertain`.

@@ 250-263
**Poor frames: retry, retry, then step up.** Three attempts with blank grey frames: each finds no face. The first two are retries — the first saying `no_face` and that 2 attempts remain — and the third becomes a step-up. The session waits for a stronger check, and has no token. It isn't finished, so it isn't in the totals yet; but its face check has reached a decision — once, not once per attempt — and is counted as a step-up.

@@ 268-283
**Credentials are checked, and errors are problem details.** No API key at all: `401`, with the problem-details media type, the stable code, the type reference, and a request ID that matches the response header. A wrong client secret and a missing flow token each get their own code.

@@ 286-290
**Each request is logged once, with its ID, and never with secrets.** `caplog` is pytest's log-capturing fixture; `set_level` makes it collect `INFO` lines from `dwarpal.api`.

@@ 291-292
Create one session. (Setting up the harness makes no HTTP requests, so this is the only request.)

@@ 293-296
Exactly one request log line, with the right method, path and status, and the same ID the response carried. `vars(record)` reads a log record's fields as a dict.

@@ 297-298
Neither the API key nor the new client secret appears anywhere in the captured logs.

@@ 301-315
**A challenge can be used only once.** The same challenge, sent twice: the first attempt is accepted, the second gets `409 challenge_invalid`.

@@ 318-326
**A session gets a limited number of challenges.** Seven requests in a row: six are granted (3 attempts × 2), the seventh gets `429 too_many_challenges`.

@@ 329-332
**Oversized and unmeasured bodies are refused before they are read.** `stream` is an async generator: given as a body, it makes httpx send the request in chunks of unknown total size.

@@ 334-337
A JSON body of about 100 KB (over the 64 KiB limit), and a chunked body.

@@ 338-342
`413 request_too_large` — still with a request ID — and `411 length_required`.

@@ 345-357
**Sessions refuse foreign return addresses, unknown policies, and live mode with a stand-in model.** A return address on another website, a policy that doesn't exist, and a session created with a *live* key while the model is uncalibrated: each gets its own code.

@@ 360-370
**Discovery and readiness.** The configuration document names Ed25519 and admits the model is uncalibrated; the key set may be cached for 5 minutes and holds only Ed25519 keys; and `/readyz` reports both databases as `ok`.

@@ 373
**The drift test: the migrations build exactly the tables the code describes.** It is not `async`, so it starts the async engine itself (line 305).

@@ 374-375
**`differences`** — Alembic's `compare_metadata` compares the real database (migrated by the fixture) with `METADATA`, the tables described in `tables.py`, and lists every difference: a missing table, an extra column, a different type.

@@ 377-382
**`check`** — connect to the test database and run the comparison through `run_sync`, because Alembic's comparison code isn't async (as in `env.py`).

@@ 384
The list of differences must be **empty**. If someone adds a column to `tables.py` but forgets the migration — or the other way round — this test fails, long before a real database meets the mismatch.

@@ 387-389
**Red team, from here on** (Phase 3): tests that play the attacker. **Red-teaming** means attacking your own system on purpose, to find its weaknesses before someone else does.

The first: **a printed photo**. The "person" is the still test portrait, and here liveness measures the images for real (`liveness="images"`).

@@ 390-393
Two attempts with six identical portraits. The photo looks straight ahead throughout — it can't turn left, right or up when asked.

@@ 394-395
The first attempt gets a retry, with the vague `liveness_check_failed` (a real person may just have been slow). The second gets **rejected** — and from outside the reason is only `verification_failed`, which doesn't even say liveness was involved.

@@ 398-403
**Poses in the wrong order.** Labels mode is on, so the frames' labels are believed — but the attacker labels them `turn_right` three times, whatever the challenge asked. A challenge never repeats a pose twice in a row, so this can never match it.

@@ 404
Caught: retry, `liveness_check_failed`.

@@ 407-409
**A challenge claimed by the browser.** The attacker sends an easy challenge of its own choosing — one pose, `turn_left`, two colours.

@@ 410-413
And four frames that would satisfy *that* easy challenge: three baseline frames, then `turn_left`.

@@ 414
Caught: the server judged the frames against the challenge it **issued** (three random poses), not the claimed one, so the pose check fails.

@@ 417-424
**Automation and virtual cameras.** Two fresh sessions; in each the browser honestly reports one warning sign — a program driving the browser, or a virtual camera. The frames themselves are fine and the person is a clear adult.

@@ 425
Both go to **step up** with `liveness_uncertain`: not passed on a face that may have been injected, but not rejected either, because these signs can have innocent causes. `[x] * 2` is a list of two copies of `x`.

@@ 428-431
**One device gets only so many challenges, however many sessions it starts.**

@@ 432-435
A helper that creates a fresh session, starts it, and asks for a challenge with a given device ID — the flow token's headers plus `X-Dwarpal-Device` (`|` joins two dicts).

@@ 437-439
With a budget of 2 challenges an hour: three requests from the same device, each in a new session, then one from a different device.

@@ 440-442
The same device gets two challenges and then `429 too_many_attempts` — new sessions don't reset its budget; the other device is unaffected.

@@ 445-461
**The tenancy tests (Phase 4).** `TENANT_TABLES` — the fifteen tables whose rows belong to a tenant: from organisations to the audit log, the daily counts, the console's users and their memberships. (The signing keys belong to Dwarpal itself, not to any customer.)

@@ 462
`NOT_TENANT_DATA` — the only two tables allowed to have no row-level security: Alembic's migration history and Dwarpal's own signing keys. Neither belongs to any customer.

@@ 465-482
**`a_session`** — a minimal verification session for a given project, made directly as a table row rather than through the API: just enough to be a row worth hiding or showing. It follows a preset (`policy_version=0`). `bytes(32)` is 32 zero bytes, standing in for the client secret's digest.

@@ 485-487
**`two_organisations`** — the scene for the tests, built as the tables' **owner**, whom the policies don't bind: organisation A with projects a1 and a2, organisation B with project b1, and one verification session in each project.

@@ 488-489
The time, and a fresh random ID for each name. `uuid.uuid4()` is fine here: these IDs only need to be different from everything else in the shared test database.

@@ 490-499
An engine with **no role** — the owner. Add both organisations, then (after a `flush`, so the foreign keys find them) the three projects, then one session per project, and commit. `add_all` adds a whole list at once.

@@ 500-501
Close the engine, and return the IDs by name, so each test can say `made["a1"]`.

@@ 504-505
**Test 1 — reading.** Each tenant sees only its own rows, and a unit of work that names no tenant sees nothing at all.

@@ 506-508
Build the scene, then open an engine as the API does: as `dwarpal_app`.

@@ 509-513
First, a unit of work that names **no** tenant counts the rows of every tenant table — expected: zero everywhere, although this database holds rows from every test so far. Then roll back and ask PostgreSQL who we are (`current_user`). This guards the bug the tests found while this step was built: a rollback used to undo `SET ROLE`, and the connection quietly became the owner again (`db.py`).

@@ 514-516
Named as project **a1**: which projects own the sessions it can see, and which organisations it can see.

@@ 517-518
Named as organisation **A**: which projects it can see.

@@ 519-520
`finally` closes the engine even if something above fails, so a failing test doesn't leave connections open.

@@ 521-525
The verdicts. Still the restricted role; zero rows of anything with no tenant; project a1 sees only its own sessions and its own organisation; organisation A sees both its projects, and not b1.

@@ 528-531
**Test 2 — writing.** A tenant can't create or change another tenant's rows, and can't switch the protection off.

@@ 532-534
The same scene and the same restricted engine.

@@ 535-539
Named as **a1**, try to add a session belonging to **b1**. The database must refuse at commit with "new row violates **row-level security** policy". `pytest.raises(…, match=…)` passes only if that error, with that text, happens.

@@ 540-545
Named as **a1**, try to change b1's sessions: an `update` with a `where` that picks exactly them. `.returning(…)` asks the database to send back the ID of every row it changed. b1's rows are invisible to a1, so the update finds nothing to change.

@@ 546-547
After the commit, count sessions again in the same database session. The tenant was named with `set_config(…, true)`, for **one** transaction, and this is a new one: it sees nothing.

@@ 548-550
Could the restricted role simply turn the policies off? `ALTER TABLE … DISABLE ROW LEVEL SECURITY` is allowed only to a table's owner, so PostgreSQL answers "**must be owner** of table projects".

@@ 551-552
Close the engine, whatever happened.

@@ 553-554
The verdicts: no row changed, and nothing visible once the transaction had ended.

@@ 557-558
**Test 3 — through the API.** One website's key can't read another website's session.

@@ 559-562
Inside the usual harness, the first website creates a session. Then `seed_dev` makes a **second** organisation, project and key in the same database — a second customer.

@@ 563-568
Ask for the first website's session with the second website's key, and then with its own.

@@ 569-571
A foreign key gets the same `404 session_not_found` as a session that doesn't exist — it can't even learn that the session is there — while the owner reads it normally.

@@ 574
**Test 4 — no table forgotten.** The tests above prove that the policies work; this one proves that **every** table has them. A future migration that adds a table and forgets its policy would fail here, until someone either protects the table or decides, in this file, that it holds no customer's data.

@@ 575-581
Connect as the owner, and ask PostgreSQL's own catalogue. `pg_class` lists every table the database knows; the conditions keep ordinary tables (`relkind = 'r'`) in our `public` schema (`'public'::regnamespace` turns the schema's name into its internal ID) whose row-level security is **off** (`NOT relrowsecurity`). `connection.scalars` returns the first column of each row: the names. `set(…)` collects them, and the engine is closed.

@@ 583
The unprotected tables must be exactly the two allowed ones, no more and no fewer.

@@ 586-587
**`bearer_of`** — the `Authorization` header for a given key. The tests below use several keys, so `h.key` alone won't do.

@@ 590-593
**Idempotency.** Sending the same request twice with the same `Idempotency-Key` gets the first answer, not a second session.

@@ 594-599
The same request twice with one key; the same key with a *different* request; a key that is too short; and two requests with no key at all.

@@ 600-603
Look inside Valkey itself. `scan_iter("idem:*")` walks through every stored reply. Each must exist, and none may contain the client secret in readable form: the reply is sealed (`app/idempotency.py`), so a copy of Valkey reveals no secret.

@@ 604-607
Both requests succeeded, the second answer is **identical** to the first — the same session and the same client secret — and only the repeat carries `Idempotent-Replayed`.

@@ 608-612
The same key with a different request is refused (`422 idempotency_key_reused`). The short key is refused too — since step 6 by the pattern the API document states, so as a general `invalid_request` naming the header, before the API's own check runs. And without a key, two requests make two different sessions.

@@ 615-618
**Rate limits.** A key allowed a burst of 2 and almost no refill (one token every 100 seconds) makes three requests in a row.

@@ 619-621
Two get through, the third gets `429 rate_limited`, with a `Retry-After` of at least one second.

@@ 624-626
**Pagination.** Five sessions are listed two at a time.

@@ 627
Create five sessions, remembering their IDs in the order they were made.

@@ 628-635
Read the pages the way a client would: ask for 2, then keep asking `starting_after` the cursor of the last page until `has_more` is false. (`|` joins two dictionaries; with no cursor yet, the second one is empty.)

@@ 636
Ask for more than the largest allowed page.

@@ 637-641
All the listed IDs together: pages of 2, 2 and 1; exactly the five sessions, **newest first** (`reversed(made)`), none repeated, none missed; no `age_token` anywhere in the list; and the oversized page refused with `422`.

@@ 644-650
**Scopes.** A key with only `sessions:read` can't create a session (`403 insufficient_scope`), but can list them.

@@ 653-656
**Rotation and revocation.**

@@ 657-660
Rotate the harness's key with a one-hour grace period. The key id is characters 8 to 19 of the key.

@@ 661
During the grace period, the old key and its replacement both work.

@@ 662-664
Rotate the replacement with **no** grace at all, then try the key just replaced and its own replacement.

@@ 665-666
Revoke the newest key (`revoke_key` reports that it found one), and try it once more.

@@ 667-670
The verdicts: both keys worked during the grace period; a key whose grace has ended gets `401 api_key_expired`; its replacement works; a revoked key gets the plain `401 invalid_api_key`.

@@ 673-676
**Versioned policies.** A session keeps the policy version it started with, even after a new version is added.

@@ 677-679
Add version 1 of the project's own policy `shop_18`.

@@ 680
Create a session with it.

@@ 681-683
Add version 2, which allows only one face attempt.

@@ 684
Create another session, which gets version 2.

@@ 685
Start the **first** session's flow: its answer says how many attempts remain.

@@ 686
List the policies.

@@ 687-689
Three refusals to check: a custom policy named like a preset, one for age 19 (the model has no thresholds for it), and a session asking for a policy nobody made.

@@ 690-691
The two versions were numbered `shop_18@1` and `shop_18@2`, and each session names the version it got.

@@ 692
The first session still has **3** attempts — version 1's rules — although version 2, with only one, now exists.

@@ 693
The list shows both versions of the project's own policy, oldest first.

@@ 694-696
And the three refusals: `invalid_policy_name`, `policy_not_supported`, `unknown_policy`.

@@ 699-702
**Immutability.** Add one policy version through the API.

@@ 703-710
Then, as the API's own role, try to change it and to delete it with plain SQL. The migration gave the role only `SELECT` and `INSERT` on this table, so PostgreSQL answers "**permission denied**" to both: no bug in our code could rewrite the rules a past check followed. Close the engine at the end, whatever happened.

@@ 713-715
**The webhook tests (Phase 4).** `Receiver` — a website's webhook receiver, kept in memory: no network, no server.

@@ 717-718
The statuses it will answer with, in order, and every request it has received.

@@ 720-722
**`handle`** — record the request, and answer with the next status in line (`pop(0)` takes the first), or `200` once the list is used up.

@@ 725-726
**`deliverer`** — the delivery worker, set up as in production: as the tables' owner.

@@ 727-728
An owner engine, and an HTTP client whose **transport** is `httpx.MockTransport(receiver.handle)`: every request the worker sends is handed straight to the receiver's function instead of going over a network.

@@ 729
The development master key — the same one the API in the harness uses, so the worker can open the secrets the API sealed.

@@ 730
Return the worker and its engine (so the test can close it). The clock is `lambda: clock[0]`: a function reading a one-item list, so the test can move time forward by changing `clock[0]` — and test a 24-hour retry without waiting 24 hours.

@@ 733-737
**`pass_one_session`** — create a session, start it, and pass one face attempt: a session that has just completed.

@@ 740-743
**Test — a delivery.** A completed session reaches the website, signed so that the website can check it.

@@ 744
An empty receiver (it will answer `200`), and a clock.

@@ 745
The harness allows private addresses: the receiver's address is never really contacted.

@@ 746-748
Register an endpoint for completed sessions.

@@ 749
Complete one session: the event and its delivery are written in the same transaction.

@@ 750
Set the worker's clock just past now, so the delivery is due.

@@ 751-753
Run the worker once, then close its engine.

@@ 754-755
Read the endpoint's deliveries, and the list of endpoints.

@@ 756-757
The secret was shown once, at creation, with its `whsec_` prefix, and never again.

@@ 758
Exactly one delivery was sent, and it arrived.

@@ 759-764
The body is the completed event: it names the session and its outcome, it carries **no token**, and the `Dwarpal-Event-Id` header matches the event's ID.

@@ 765-768
Check the signature exactly as a receiver would: split the header into `t` and `v1`, recompute the HMAC of `"<t>.<body>"` with the secret, and compare in constant time (`compare_digest`).

@@ 769
The delivery is recorded as delivered, on its first attempt, with the receiver's `200`.

@@ 772-775
**Test — retries.** A failing receiver is retried on the schedule until the delivery is dead; then it can be replayed.

@@ 776
This receiver answers `500` eight times.

@@ 777-783
Register an endpoint, send it a **test event** (which goes to this endpoint whatever it subscribes to), and set the clock just past now.

@@ 784-787
Eight rounds. In each, the worker sends one delivery, and an immediate second run finds nothing due: the failure has pushed the next attempt into the future.

@@ 788-789
Read the delivery's state.

@@ 790-793
While it is still pending, measure the wait the worker chose, and move the clock forward to exactly that moment.

@@ 794
Replay the dead delivery.

@@ 795-796
With the clock at now, the worker sends it again — and the receiver, out of failures, answers `200`.

@@ 797-798
Close the engine and read the final state.

@@ 799
The test event was accepted (`202`, "accepted for later").

@@ 800
The waits were exactly the schedule: 1 minute, 5 minutes, 30 minutes, 2, 6, 12 and 24 hours.

@@ 801
After the eighth failure the delivery was dead, with the receiver's last `500` recorded.

@@ 802-803
Replaying put it back to pending with a fresh count, and it was then delivered.

@@ 806-811
**Test — the SSRF guard through the API.** With private addresses not allowed (the normal setting), an endpoint on `127.0.0.1` — this very computer — is refused.

@@ 812-814
So is an endpoint asking for an event type that doesn't exist.

@@ 815-816
`422 unsafe_webhook_url` and `422 unknown_event_type`.

@@ 819-824
**Test — introspection.** Pass a session and read its age token.

@@ 825-826
Seed a second website, with its own key.

@@ 828-830
**`ask`** — introspect a token with a given key. A function defined inside the test, because only this test needs it.

@@ 832-835
Ask four times: with the other website's key; with a **forged** token (its last four characters changed, which breaks the signature); and twice with the right key.

@@ 836-839
The other website and the forger both get only `{"active": false}`; the first genuine question gets `active` with the token's claims; the second gets `false` — a token is spent once introspected.

@@ 842-844
**Test — expiry is announced once.** A session lifetime of 0 seconds makes every new session expire at once.

@@ 845-847
Register an endpoint for expired sessions.

@@ 848-849
Create a session, and read it twice.

@@ 850
Read the endpoint's deliveries.

@@ 851-852
Both reads say `expired`, but there is exactly **one** delivery: the first read saved the change and its event together, and the second found nothing to change.

@@ 855-862
**`org_of`** — the organisation that owns a seeded project, read as the tables' owner: the audit log is kept per organisation.

@@ 865-866
**Test — the audit chain.** Real changes are chained in the log, and tampering of either kind is found.

@@ 867-872
Through the API: add a policy version, register a webhook endpoint, and delete it. With the key `seed_dev` created, that makes four audited actions.

@@ 873-876
The organisation's ID; an engine as the owner, and one as the API's role.

@@ 877
From here on, whatever happens, both engines are closed at the end (`try` … `finally`).

@@ 878-880
Read the organisation's entries, and verify the chain as it stands.

@@ 881-883
**The API can't rewrite history**: as the API's role, changing any entry is refused with "permission denied" — the role may only add entries (migration `0006`).

@@ 884-888
But someone with the **owner's** rights — a database administrator, or an attacker who stole that login — can. Change entry 2's facts (as if the policy had been for age 13) and verify again.

@@ 889-893
Put entry 2 back, then quietly **delete the last entry**, and verify once more.

@@ 894-896
Close both engines, whatever happened.

@@ 897-902
The four entries, in order: the key's creation, the policy version, the endpoint created, the endpoint deleted.

@@ 903-904
Changes made with the API key name it by its **id** (characters 8 to 19), and the key itself appears in no entry's facts.

@@ 905
Before any tampering: four entries, intact.

@@ 906
After the edit: broken, **at entry 2** — the exact entry that was changed.

@@ 907
After the deletion: broken at entry 4, the missing one. The chain itself still checks out, but the head (`audit_heads`) remembers that there should be four.

@@ 910-914
**Test — counting.** Pass two sessions.

@@ 915-916
Read the last week's counts, and ask for more than a year.

@@ 917-920
Two passes in total, in one row for today under `uk_osa_18`; both face checks decided, as passes, with the median in the first band (under 5 seconds — the test is quick); and a request for 366 days refused with `422`.

@@ 923-927
**Test — the sweep and the purge.** Settings for calling the operator's command directly.

@@ 928-932
Sessions in this harness expire at once. Register an endpoint for expired sessions, and create a session that nobody will ever read.

@@ 933-934
Run the scheduled jobs, then read the endpoint's deliveries.

@@ 935-940
As the owner, give this project a retention of **one day**.

@@ 941-942
Run the jobs as if it were 23 hours later: within the day, so the session is kept.

@@ 943-944
Run them as if it were two days later: past the day, so it is purged.

@@ 945
Read the project's counts.

@@ 946-948
Verify every organisation's audit chain.

@@ 949-950
The sweep expired at least one session (other tests leave theirs too), and the website was told, by one delivery, although nobody read the session.

@@ 951-953
After 23 hours nothing of this project's was purged and the session still exists; after two days it is gone (`404`).

@@ 954
The count of one expired session outlives the session itself.

@@ 955
And this organisation's audit chain is intact.

@@ 958-960
**The console tests (Phase 4, step 2).** The console's address; settings for its tests — a cookie that may travel over plain HTTP, and a generous sign-in allowance, because every test signs in from the same address; and a throwaway password.

@@ 963-965
**`person`** — a separate browser for one person: a new client on the same transport, with its own cookie jar, so several people can be signed in at once in one test.

@@ 968-972
**`sign_up`** — create an account and organisation through the console, insist it worked, and return the answer (which includes the CSRF token).

@@ 975-976
**`unique`** — a fresh e-mail address each time, so tests sharing the database never collide.

@@ 979-983
**Test — signing up, in and out.**

@@ 984-986
Sign up, and look at the cookie the browser received.

@@ 987-992
Try to sign up again with the same address, and with a five-character password.

@@ 993-995
Sign in with a wrong password; with an address nobody has; and correctly, typed in capitals.

@@ 996-999
Sign out without the CSRF token, then with it; then ask who is signed in.

@@ 1000-1001
The new person owns the new organisation; the cookie is a long, unguessable token.

@@ 1002-1003
The repeated address and the weak password are refused.

@@ 1004-1005
A wrong password and an unknown account get the **same** status and the **same** sentence: an attacker can't use sign-in to find out who has an account.

@@ 1006
Addresses match whatever their capitals.

@@ 1007-1009
Signing out needs the CSRF token like any change; with it, the session ends, and the cookie no longer works.

@@ 1012-1014
**Test — CSRF.**

@@ 1015-1019
Sign up, then try a change three ways: with a guessed token, with the real token but from another site's origin, and genuinely.

@@ 1020-1022
The guess fails (`csrf_failed`), another origin fails (`bad_origin`), and only the genuine request works.

@@ 1025-1028
**Test — one-time codes.**

@@ 1029-1030
Sign up, and ask to set up one-time codes: the answer holds the secret and its `otpauth://` address.

@@ 1031-1035
Work out the current 30-second step. A wrong code is refused; the right one, computed from the secret as an authenticator app would, switches codes on.

@@ 1036-1037
Sign in with only the password.

@@ 1038-1040
Sign in with the **next** step's code — what a phone whose clock runs a little fast shows — and then try exactly the same code again.

@@ 1041-1046
The offer was a proper `otpauth://` address; the wrong code failed and the right one worked — and came with ten recovery codes; a password alone is no longer enough; the code worked once — and a second time it is refused.

@@ 1049-1051
**Test — roles.** Three addresses: an owner, an analyst and a developer.

@@ 1052-1058
Inside one harness, four browsers — the fourth for an outsider. `async with ( … ):` opens several at once, and closes them all at the end.

@@ 1059-1061
The owner signs up; note the organisation and the owner's CSRF token.

@@ 1062-1065
The analyst and the developer sign up (each gets an organisation of their own), and so does the outsider.

@@ 1066-1070
The owner adds the analyst and the developer to the owner's organisation, each with their role.

@@ 1071-1073
The analyst lists the organisation's projects — any member may — and the test builds the address for creating API keys in the first one.

@@ 1074-1076
The analyst and the developer each try to create a read-only key.

@@ 1077-1081
The developer tries to make the analyst an owner.

@@ 1082-1086
The analyst lists the members; the outsider tries to; the developer's new key is used on the API; and the owner and the analyst read the audit log.

@@ 1087-1089
The analyst may not create keys (`403 forbidden_for_role`); the developer may; and the developer may not manage members.

@@ 1090-1091
The analyst sees all three members; the outsider gets `404`, exactly as if the organisation didn't exist.

@@ 1092
The key made in the console works on the API.

@@ 1093-1096
The owner's audit log, oldest first: the organisation's creation, two members added, a key created; the chain is intact; and the key itself appears nowhere in it.

@@ 1097
The analyst may not read the audit log.

@@ 1100-1102
**Test — sign-in limits.** At most 2 attempts at once, then one every two minutes.

@@ 1103-1105
A browser at an address of its own. `ASGITransport(…, client=…)` sets the address the API sees the request coming from; `192.0.2.x` is a range reserved for documentation and tests. Without it, every other test's sign-ins would already have used up this address's allowance.

@@ 1106-1111
Sign up, then try a wrong password three times.

@@ 1112-1113
Two ordinary refusals, then `429 too_many_sign_ins`, with a `Retry-After` of at least a second.

@@ 1116-1118
**The contract test (Phase 4, step 6).** `live_api` — Schemathesis sends real HTTP, so the API runs as a real server for these tests. `scope="module"` starts it once for the whole file rather than once per test.

@@ 1119-1127
Its settings: the test databases; webhook addresses never looked up (the fuzzer invents host names); a cookie allowed over plain HTTP; and limits so high that the fuzzer's many requests aren't simply refused with `429`.

@@ 1128
Seed a project and a key for it.

@@ 1129
A uvicorn server for the API, on `127.0.0.1` and **port 0**, which asks the operating system for any free port, so the test never collides with something already running.

@@ 1130-1131
Run it in a background **thread**: `daemon=True` means the thread won't keep Python alive if the tests end without stopping it.

@@ 1132-1133
Wait, a twentieth of a second at a time, until the server says it has started.

@@ 1134
Read which port it was given.

@@ 1135
Hand the tests the server's address and the key.

@@ 1136-1137
Afterwards, ask the server to stop, and wait up to ten seconds for its thread to finish.

@@ 1140-1142
**`live_document`** — Schemathesis reads the API's document from the running server, exactly as a website's developer would.

@@ 1145
`contract` — tells Schemathesis to take the document from that fixture. A document known only once the server runs can't be read while pytest is still collecting tests, so it is fetched lazily, from the fixture.

@@ 1148-1149
`@contract.parametrize()` turns the test into one sub-test per operation in the document: 31 of them. `@settings` gives each 25 generated requests, no time limit per request (`deadline=None`), and turns off Hypothesis's health checks, which would complain that each example is slow (it is a real HTTP request).

@@ 1150-1151
**Test — the contract.** For each generated request (`case`):

@@ 1152-1154
Every check but one. `positive_data_acceptance` insists that a request the document allows must succeed. But some of the API's rules depend on data, not just shape: whether the age model is calibrated for an age, whether an address is among the project's allowed origins. Refusing such a request with `422` is correct.

@@ 1155
Send it to the server with the website's key, and check the answer: never a server error, a status code the document lists for this operation, a content type it lists, a body that matches the schema for that status, and the headers HTTP requires (such as `Allow` on a `405`). Any failure prints the exact request, as a `curl` command to reproduce it.

@@ 1158-1160
**Test — no drift.** `docs/api/openapi.json` is what websites read; the docstring says how to refresh it.

@@ 1161
The file must equal, byte for byte, what the code produces now. A change to the API without refreshing the document fails here.

@@ 1164-1166
**Fail-closed tests (Phase 7).** Valkey unreachable. "Gone" is simulated by an address where nothing listens: port 1 on this computer.

@@ 1167-1170
Settings with that Valkey and the real database; a key; and an API started with them (its inference client is never reached).

@@ 1171-1174
Try to create a session — the API key's rate limit needs Valkey — and ask whether the API is ready.

@@ 1175-1177
The session request gets `503 service_unavailable` with `Retry-After: 5` (not a crash, not a pass), and readiness reports exactly what is wrong: the database is fine, Valkey isn't.

@@ 1180-1181
**`unreachable`** — an inference service that is down: every request fails to connect.

@@ 1184-1185
**`broken`** — an inference service that answers, but with nonsense: valid JSON that isn't an analysis.

@@ 1188-1193
**Fail closed when inference fails.** The test runs twice, once with each broken service (`parametrize`).

@@ 1194-1200
An API whose inference client sends every request to the broken service, and a harness around it.

@@ 1201-1204
Create a session, start it, and make two attempts with a real face.

@@ 1205-1206
Neither attempt passes — the face would have passed with a working service — and the first is a `retry`: the person may try again, but nobody is let in on a failure.

@@ 1209
**Chaos tests** (Phase 7). The roadmap asks for *fail-closed chaos tests*: services killed in the middle of a check. They were first done by hand, stopping containers during a load test (§5.7.6); these tests do it on every run, so a change can't quietly break it. Each asks two questions: while a service is down, does anything pass? And once it is back, can a person finish their check?

@@ 1212-1215
**`Cutter`** — a small **TCP relay**: the API connects to it instead of to the real PostgreSQL or Valkey, and it passes the bytes on both ways. *Cutting* it drops every open connection at once and hangs up on new ones — to the API, exactly as if the service had died. *Restoring* lets connections through again, as after a restart. The containers themselves are never touched, so the other tests sharing them are safe.

@@ 1217-1221
Where to relay to; not cut yet; the open connections (both ends of each), so they can all be dropped; and the listening server, once started.

@@ 1223-1225
Entering the `async with`: listen on a free port on this computer (port `0` asks the system to choose one); each new connection runs `relay`.

@@ 1227-1230
Leaving it: drop everything, and stop listening.

@@ 1232-1235
**`port`** — the port the system chose. `@property` lets it be read like a field (`cutter.port`) though it is worked out each time.

@@ 1237-1240
**`relay`** — one connection from the API. While cut, hang up at once: `abort` closes the connection without the usual polite goodbye, as a dead service would.

@@ 1241-1243
Otherwise, connect to the real service, and remember both ends.

@@ 1244-1245
Copy both ways at the same time (`gather` runs the two copies together) until the connection ends; then forget it.

@@ 1247-1250
**`cut`** — from now on, refuse; and drop every open connection. `list(…)` takes a copy first, because dropping them changes the set.

@@ 1252-1253
**`restore`** — let connections through again.

@@ 1256-1257
**`pipe`** — copy one direction of a connection.

@@ 1258-1261
Read up to 64 KB at a time and pass it on, until the source ends (an empty read). `:=` (the "walrus") reads and tests in one go. `drain` waits while the other side is slow. A connection that is cut raises a connection error — expected here, so `suppress` ignores it.

@@ 1262
When one direction ends, drop the other side too, so neither half is left hanging.

@@ 1265-1267
**`chaos`** — the test databases, reached through two cutters: it hands back the new addresses (to give to the harness), and the cutters for PostgreSQL and Valkey.

@@ 1268-1270
Take both addresses apart, and check they have a host and a port.

@@ 1271-1274
Start one cutter for each service.

@@ 1275-1276
Build the addresses that lead through them — the same database, but on this computer at the cutter's port — and hand everything to the test. `hide_password=False`: the address must keep the (throwaway) password to work.

@@ 1279-1280
**`Switch`** — the same idea for the inference service, which the tests reach through httpx rather than a socket: a **transport** (what httpx sends requests through) put in front of the real one.

@@ 1282-1285
The real transport, set later; not down; and `on_call`, something to do on every call — nothing by default (`lambda: None` is a function that does nothing).

@@ 1287-1289
**`around`** — the function given to the harness as `inference_via`: keep the real transport, and use the switch in its place.

@@ 1291-1295
Every call: first run `on_call`; then, if the switch is down, fail exactly as an unreachable service does (`ConnectError`); otherwise pass the request on.

@@ 1298-1299
**`unavailable`** — the three things a "try again shortly" answer must have: status `503`, the code `service_unavailable`, and `Retry-After`.

@@ 1302-1304
**`outcome_of`** — what the website would see: the session's status and outcome, read with its API key.

@@ 1307-1311
**Valkey dies in the middle of a check.** Everything goes through the cutters. A session is created and started, and a challenge fetched while all is well.

@@ 1312-1315
Valkey dies. The person sends their frames; then the readiness check is asked.

@@ 1316-1318
Valkey comes back. The person tries again, and the website reads the result.

@@ 1319-1321
While Valkey was down: "try again shortly", and readiness names Valkey. Afterwards: the same connection pool recovered on its own, the face passes, and the session is complete — passed once.

@@ 1324-1331
**The database dies between two steps** — the same story with PostgreSQL.

@@ 1332-1337
The database dies before the frames arrive; readiness is asked; the database comes back; the person tries again.

@@ 1338-1340
While it was down, nothing was decided ("try again shortly", readiness names the database); afterwards the pool's *pre-ping* (`db.py`) noticed the dropped connections and made new ones, and the check passed.

@@ 1343-1347
**The database dies while a face is being analysed** — the hardest moment: after the attempt was accepted and its challenge used up, before the decision is written. The switch in front of inference makes that moment happen.

@@ 1348-1351
On the inference call, cut the database (`on_call`).

@@ 1352-1354
The attempt; then the switch is cleared, and the database comes back.

@@ 1355-1357
What the website sees now; a new attempt; and what it sees after.

@@ 1358-1360
The attempt answered "try again shortly" — the analysis is thrown away, never half-recorded. The session was untouched (still `in_progress`, no outcome), and the next attempt passed.

@@ 1363-1366
**Inference dies and comes back.** (The fail-closed test above has it dead throughout.)

@@ 1367-1373
Inference goes down; an attempt; it comes back; another attempt; the result.

@@ 1374-1375
While down: a `retry`, with 2 tries left — the person loses one try but isn't let in. Afterwards: a pass.

@@ 1378-1383
**Security headers (Phase 7).** A refusal (no key), the public key set, and the interactive documentation.

@@ 1384-1389
Every answer carries `nosniff`, the strict content policy, `no-referrer` and (since Phase 7) `Cross-Origin-Resource-Policy: same-origin`. HSTS isn't sent outside production: over plain HTTP it would mean nothing.

@@ 1390-1392
Answers are `no-store` unless their route says otherwise: the key set keeps its own five-minute public caching. The documentation page has no content policy, which would stop its scripts.

@@ 1395-1403
**Production.** Settings a production deployment would accept: a real-looking master key and HTTPS addresses. The app isn't started, because `/livez` needs no database.

@@ 1404-1407
Ask for `/livez`, the documentation page and the API document.

@@ 1408-1409
HSTS is sent (two years); the interactive documentation doesn't exist (`404`); the API document is still published.

@@ 1412-1418
**Test — the console's project pages (Phase 5).** An owner and an analyst, each with their own browser.

@@ 1419-1424
The owner signs up; the analyst signs up; the owner adds the analyst to the organisation.

@@ 1425-1428
The owner finds the organisation's project and creates a key for it in the console.

@@ 1429
A website using that key: the harness, copied with the key changed (`replace`).

@@ 1430-1432
The website creates a session — without a return address, because this new project hasn't allowed any yet — and a person passes it.

@@ 1434-1436
The analyst reads the project's sessions, the passed session's trace, and the last week's counts.

@@ 1437-1440
The analyst and then the owner try to add a policy version; the analyst lists the policies.

@@ 1441
The analyst tries the harness's own project — which belongs to another organisation — under this organisation's address.

@@ 1442-1443
The one session is listed; its trace has one attempt, and it passed.

@@ 1444-1445
The attempt carries its numbers: the age probability, the line it met, and the liveness evidence.

@@ 1446
Reading a trace made no token.

@@ 1447
The counts show one pass.

@@ 1448-1450
An analyst may not add a policy version; the owner may, and it is listed as `console_18@1`.

@@ 1451
Another organisation's project, named under this organisation, is not found — the check that the project belongs to the organisation in the address.

@@ 1454-1457
**Test — the console's webhooks (Phase 5).** An owner and an analyst. Private addresses are allowed, so the endpoint can point at this computer (`localhost:9`, where nothing listens — nothing is sent in this test).

@@ 1458-1464
The owner signs up, the analyst signs up and is added, and the owner finds the project.

@@ 1465-1466
The project's webhook address, and an endpoint for finished sessions.

@@ 1468-1471
The analyst tries to add it; the owner adds it; the analyst tries to list them; the owner lists the live ones.

@@ 1472-1476
The owner sends a test event, reads the endpoint's deliveries, and replays the first.

@@ 1477-1480
The owner tries to delete it as a live endpoint, then deletes it as the test one it is; lists again; and reads the audit log.

@@ 1481
An analyst may not add one.

@@ 1482
The owner's new endpoint came with its secret, and is a test endpoint.

@@ 1483
An analyst may not even list them; and the live mode has none — modes never mix.

@@ 1484-1485
The test event is waiting to be delivered (no worker runs here); the replay is accepted.

@@ 1486
The wrong mode is "not found"; the deletion worked, and the list is empty.

@@ 1487-1488
The audit log names a person (`user:…`), not a key, for both the creation and the deletion.

@@ 1491-1498
**Test — the owner rules for members (Phase 5).** Three people, each with their own browser: an owner, an admin, and one more.

@@ 1499-1503
All three sign up.

@@ 1504-1506
The owner adds the admin as an admin, and the third person as an analyst.

@@ 1507-1508
Everyone's IDs: the third person's from the answer, the owner's from `/me`, the admin's from the member list.

@@ 1510-1512
The admin promotes the analyst to developer, then tries to make them an owner; the only owner tries to step down to admin.

@@ 1513-1514
The owner makes the third person an owner, and then steps down — allowed now, since there are two.

@@ 1515-1517
The admin tries to remove the new owner; the new owner removes the admin; and tries to remove an ID that isn't anyone's.

@@ 1518-1519
What remains, and the audit log.

@@ 1520
An admin may change a member who isn't an owner.

@@ 1521
An admin may not make an owner.

@@ 1522
The last owner may not step down.

@@ 1523
With two owners, one may.

@@ 1524
An admin may not remove an owner; an owner may remove an admin; an unknown member is not found.

@@ 1525
Left: the first owner (now an admin) and the new owner.

@@ 1526-1527
The audit log holds exactly the four changes that happened — refusals leave no trace.

@@ 1530-1535
**Test — unstorable text is refused (Phase 5).** Sign in with an address containing NUL — the kind of input the contract tests found: `422 invalid_text`, not a server error.

@@ 1538-1541
**Test — the model page** (§5.5.2): anyone signed in can read which model is deciding and how it was made, and nothing about its build.

@@ 1542-1543
Run the API with the trained model's manifest — the one with sources and measured bounds — rather than the stub.

@@ 1544-1546
Ask before signing in, then sign up and ask again.

@@ 1547
Signed out, the answer is the usual 401.

@@ 1548-1550
Signed in: the version, that it isn't calibrated for live use, its permitted use, the faces it learnt from and the number it was calibrated on.

@@ 1551-1552
The line for 18: its 7.5 % risk budget, and a measured worst case for minors within it.

@@ 1553-1554
And none of the internal details of the file — the checksum, the build's commit, the file's name or the note that it was built from uncommitted code — is in the answer.

@@ 1557-1561
**Test — the production session cookie (Phase 5).** The browser tests now run with a plain cookie (WebKit drops `Secure` ones on plain HTTP), so this test checks the real one: with the production setting, sign up and read the `Set-Cookie` header.

@@ 1562-1563
Sign up.

@@ 1564-1565
The cookie's name starts with `__Host-`, so browsers insist it is `Secure`, for path `/`, with no `Domain`: no other site can set or read it.

@@ 1566-1567
Its attributes include `HttpOnly` (no script can read it), `Secure` (HTTPS only), `Path=/` and `SameSite=Lax`.

@@ 1568
And no `Domain`, which would share it with other hosts.

@@ 1571-1577
**Test — switching an endpoint off and on** (Phase 5). A website registers an endpoint.

@@ 1578-1580
Switch it off, send a test event, and read its deliveries.

@@ 1581-1583
Switch it back on, and do the same.

@@ 1584
And try to switch an endpoint that doesn't exist.

@@ 1585
The answers said off, then on.

@@ 1586
While off, nothing was queued for it.

@@ 1587
Back on, the test event waits to be delivered.

@@ 1588
An unknown endpoint is not found.

@@ 1591-1593
**Test — listing sessions by outcome and by reference** (Phase 5).

@@ 1594-1596
A session with the website's reference `order-1`, which a person passes.

@@ 1597
Another, `order-2`, not yet started.

@@ 1598-1602
List the passed ones; the one for `order-2`; one for a reference nobody used; and ask for an outcome that doesn't exist.

@@ 1603-1605
Exactly the passed session; exactly `order-2`'s; and nothing.

@@ 1606
An unknown outcome is refused, not silently ignored.

@@ 1609-1614
**Test — recovery codes, and switching codes off** (Phase 5).

@@ 1615-1619
Sign up, ask for a secret, and confirm the current code: the answer holds the recovery codes.

@@ 1620-1623
Sign in with the first recovery code, typed as someone might copy it from paper — capitals, a space instead of the dash. Keep the new session's CSRF token.

@@ 1624
Try the same recovery code again.

@@ 1625-1626
Ask for a fresh set, then try one of the old set.

@@ 1627-1633
Try to switch codes off with a wrong password, then with the right password and the next code.

@@ 1634
Sign in with the password alone.

@@ 1635
Ten different codes, each of the shape `abcde-fghij`.

@@ 1636
The recovery code signed in, and nine are left.

@@ 1637
Each works once.

@@ 1638
The fresh set shares nothing with the old, and the old no longer works.

@@ 1639
A wrong password is refused.

@@ 1640-1641
With the right password and code, codes are off — and the password alone signs in again.

@@ 264-265
The face check's count: nothing in the totals, one step-up among the decided face checks.
