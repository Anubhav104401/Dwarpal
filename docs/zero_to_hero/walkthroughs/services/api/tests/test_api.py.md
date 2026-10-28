---
fingerprint: fd8860b9c0486438
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

@@ 5-20
Standard-library tools: `asyncio`, `base64` (a test master key), `hashlib` and `hmac` (to check a webhook's signature as a receiver would), `json`, `logging`, `re` (to check a recovery code's shape), `threading` and `time` (to run a real server beside the tests), `uuid` (fresh IDs), the iterator types for fixtures, `asynccontextmanager`, `dataclass` and `replace` (a copy of a dataclass with one field changed), `UTC`, `datetime` and `timedelta` (a length of time, for key rotation and webhook retries), `Path`, `Any` — and `Literal`, for the harness's liveness option (Phase 3).

@@ 22-26
OpenCV and NumPy (to make a test picture), the `docker` client (to ask whether Docker is running), `httpx` (to call the apps) and `pytest`.

@@ 27-28
`schemathesis`, the contract tester (step 6), and `uvicorn`, the server program, to serve the API on a real port for it.

@@ 29-30
Alembic's `compare_metadata` and `MigrationContext`, for the drift test at the end.

@@ 31
Hypothesis's `settings` and `HealthCheck`, to tell Schemathesis (which uses Hypothesis inside) how many requests to make per operation.

@@ 32-33
joserfc's `jwt` and `KeySet`: the tests verify tokens exactly as a website would.

@@ 34
Pydantic's `SecretStr`, to give production settings a master key.

@@ 35
An async Valkey client, so a test can look at what the API stored there (Phase 4).

@@ 36-37
Schemathesis's `Case` — one generated request — and `positive_data_acceptance`, the one check the contract test leaves out (explained there).

@@ 38
SQLAlchemy's query builders, for the Phase 4 tests: `delete` (to remove a row on purpose), `select` and `func` (to count rows), `text` (raw SQL), and `update` (to try changing rows).

@@ 39-41
SQLAlchemy types: `Connection` for the drift test, `DBAPIError` — the error SQLAlchemy raises when the database itself refuses a statement — and `create_async_engine`.

@@ 42-44
Testcontainers: a ready-made PostgreSQL container, a general container for Valkey, and a **wait strategy** — "the container is ready when this line appears in its log".

@@ 46-74
The code under test: the database helpers (`make_engine`, `make_sessions`, `tenant`), the master key, the table catalogue and the fifteen tables that belong to tenants, the audit and maintenance modules, the delivery worker, the CLI's `API_DOCUMENT`, `api_document`, `maintain`, `migrate`, `seed_dev`, `rotate_key` and `revoke_key`, both apps' factories (renamed with `as` so the two `create_app`s can't be confused), the ID and one-time-code helpers, both settings classes, and the contracts for frames, challenges and browser signals. The brackets let one `import` span several lines.

@@ 76-77
The repository folder, and the public-domain portrait from the vision library's tests — a real face, so the real face detector finds it.

@@ 78
The demo shop's return address, which the seeded project allows.

@@ 81-84
**`blank_frame`** — a plain grey 320 × 240 picture, saved as JPEG: a valid image with no face in it. `np.full` fills an array with one value (128, middle grey). `cv2.imencode` returns two values — whether it worked, and the encoded bytes.

@@ 87-88
**The `databases` fixture.** A **fixture** is something a test needs, prepared by pytest and passed in by name. `scope="session"` means it is built **once for the whole test run** and shared: starting two containers takes seconds, so doing it once matters. It provides the two addresses.

@@ 89-92
Is Docker running? Ask it, giving up after 5 seconds. If not, skip every test that needs this fixture, with the reason.

@@ 93-98
A PostgreSQL container, using exactly the image the local Compose file uses. The password is a throwaway for a throwaway container; the comment explains why the linter's warning about a hard-coded password doesn't apply.

@@ 99-103
A Valkey container, with its port exposed, considered ready when Valkey logs `Ready to accept connections`.

@@ 104-105
Start both. Each `start()` waits until its container is ready.

@@ 106-108
Docker maps each container's port to a random free port on this computer, so the addresses are built from what the containers report. Random ports mean tests never clash with a database already running locally.

@@ 109
Apply the migrations — the same function a developer runs from the command line.

@@ 110
`yield` hands the addresses to the tests. Everything after it runs when the whole test run is over…

@@ 111-112
…stopping (and removing) both containers.

@@ 115-119
**`Harness`** — what each test gets to work with: an HTTP client connected to the API, the seeded project's test API key, and the project's public ID.

@@ 120
`transport` — the in-process connection to the API (step 2): a test can open more clients on it, one per person, each with its own cookies.

@@ 123-131
**`harness`** — sets up a complete, fresh API for one test. Its options: the age the stand-in model should "see" (30 by default — clearly an adult), whether the seeded key is live, how liveness gets its evidence (Phase 3) — `"labels"` by default, because the tests' portrait is a still photo that can't turn its head — the seeded key's scopes (every scope by default), and any other API settings to change (`**overrides`: extra named arguments, collected into a dict), such as a smaller device budget or rate limit.

@@ 132
Unpack the two database addresses.

@@ 133
Create an inference app whose stand-in model reports the chosen age, with the chosen liveness evidence.

@@ 134-138
Start the inference app's lifespan (loading its face detector), and open an HTTP client wired to it through **`ASGITransport`** — httpx calls the app's Python code directly, with no network and no server. One `async with` with two parts, in brackets, opens both and closes both.

@@ 139-140
Create the API with test settings — the test databases' addresses, plus any overrides — and the in-process inference client. The settings' default `database_role` applies, so **every test in this file runs as the restricted role**, under row-level security, exactly as the API will in production.

@@ 141
Run the API's lifespan: connect, load the signing key, read the manifest.

@@ 142
Seed a project and a key, exactly as a developer would with `seed-dev`, with the scopes asked for.

@@ 143-145
Open a client wired to the API the same way, and hand the harness to the test, with the transport. When the test ends, every `async with` closes in reverse order.

@@ 148-151
**`create`** — create a session as the demo shop would, with the API key, plus any extra headers (`headers_extra`, such as an `Idempotency-Key`). Any keyword arguments replace the body's defaults, so a test can write `create(h, policy="anything_goes")`.

@@ 154-155
**`secret`** — the body for `/start`: the session's client secret.

@@ 158-161
**`start`** — start the flow and return the `Authorization` header with the flow token, ready for the next calls. The `assert` includes the response text, so if starting fails, the test report shows why.

@@ 164-165
**`following`** (Phase 3) — the labels for a burst whose head follows the given poses: frontal **baseline** frames first, then one frame per pose, in order. With 6 frames and 3 poses: baseline, baseline, baseline, then the three poses.

@@ 166
`["baseline"] * n` makes a list of n copies; `+ poses` adds the poses after them.

@@ 167
One `FrameMeta` per phase, numbered from 0, taken 120 ms apart. `enumerate` gives each item with its position.

The comment at the end, `# type: ignore[arg-type]`, silences one complaint of the type checker: it can't know that the plain texts in `poses` are valid `Phase` names. Pydantic checks them anyway when the `FrameMeta` is created.

@@ 170-178
**`attempt`** — one complete face attempt, as the verify page makes it. Besides the frames, three optional inputs let a test play an attacker (Phase 3):

- `poses` — label the frames with these poses instead of the ones asked for;
- `signals` — report these browser signals;
- `claimed` — put a challenge of the browser's own choosing into the request.

@@ 179-180
The docstring says the same, in short.

@@ 181
Get a challenge — the server picks its random poses and colours.

@@ 182-184
Label the frames: by default they follow the challenge's own poses (an honest attempt), otherwise the poses the test gave. A challenge has 3 or 4 poses, so first make sure there are enough frames — at least 3 frontal ones, then one per pose — by repeating the last frame as many times as needed (`frames[-1:] * n`: a list of the last frame, `n` times; `max(0, …)` keeps `n` from going negative).

@@ 185
Describe the attempt: the frames' labels, the signals (normal ones unless given), and any claimed challenge.

@@ 186-188
Package the frames as files `frame_0`, `frame_1`, …, add the description and the challenge's ID, and upload everything as a multipart form.

@@ 191-192
**The main story: an adult passes, and the website can verify the token.** `@pytest.mark.anyio` lets pytest run an `async` test function.

@@ 193-199
Create, start, attempt with six portraits — the stand-in model says 30, so it passes — then finish: the redirect goes back to the shop with the session's ID.

@@ 200
Start the flow *again*, as if the person reloaded the page afterwards.

@@ 201-203
As the shop's server: read the result with the API key, and fetch the public keys.

@@ 204-205
The reloaded page sees the completed session and its outcome — no error for the person.

@@ 206-207
The result says completed, and passed.

@@ 208
**Verify the token** exactly as a website would: with the published key set, accepting only Ed25519. If the signature didn't match, this line would raise an error.

@@ 209-214
The token is an age token, says pass, says `age_over_18: true` (the literal `True`, checked with `is`), and is addressed to this project, about this session, in test mode.

@@ 215
**No age inside.** None of these names appears among the claims: the set of forbidden names and the set of claim names have nothing in common (`&` is set intersection; an empty set counts as false).

@@ 218-230
**A clear child is refused, unmistakably.** With the stand-in model at 12, the attempt fails, and the signed token says `outcome: fail` *and* `age_over_18: false` — so even a website that read only the age claim would refuse entry.

@@ 233-239
**A teenager near the limit must use a stronger check.** At 16, the probability of being 18 or over is neither high enough to pass nor low enough to fail, so the answer is step up, with the reason `age_uncertain`.

@@ 242-254
**Poor frames: retry, retry, then step up.** Three attempts with blank grey frames: each finds no face. The first two are retries — the first saying `no_face` and that 2 attempts remain — and the third becomes a step-up. The session waits for a stronger check, and has no token.

@@ 257-272
**Credentials are checked, and errors are problem details.** No API key at all: `401`, with the problem-details media type, the stable code, the type reference, and a request ID that matches the response header. A wrong client secret and a missing flow token each get their own code.

@@ 275-279
**Each request is logged once, with its ID, and never with secrets.** `caplog` is pytest's log-capturing fixture; `set_level` makes it collect `INFO` lines from `dwarpal.api`.

@@ 280-281
Create one session. (Setting up the harness makes no HTTP requests, so this is the only request.)

@@ 282-285
Exactly one request log line, with the right method, path and status, and the same ID the response carried. `vars(record)` reads a log record's fields as a dict.

@@ 286-287
Neither the API key nor the new client secret appears anywhere in the captured logs.

@@ 290-304
**A challenge can be used only once.** The same challenge, sent twice: the first attempt is accepted, the second gets `409 challenge_invalid`.

@@ 307-315
**A session gets a limited number of challenges.** Seven requests in a row: six are granted (3 attempts × 2), the seventh gets `429 too_many_challenges`.

@@ 318-321
**Oversized and unmeasured bodies are refused before they are read.** `stream` is an async generator: given as a body, it makes httpx send the request in chunks of unknown total size.

@@ 323-326
A JSON body of about 100 KB (over the 64 KiB limit), and a chunked body.

@@ 327-331
`413 request_too_large` — still with a request ID — and `411 length_required`.

@@ 334-346
**Sessions refuse foreign return addresses, unknown policies, and live mode with a stand-in model.** A return address on another website, a policy that doesn't exist, and a session created with a *live* key while the model is uncalibrated: each gets its own code.

@@ 349-359
**Discovery and readiness.** The configuration document names Ed25519 and admits the model is uncalibrated; the key set may be cached for 5 minutes and holds only Ed25519 keys; and `/readyz` reports both databases as `ok`.

@@ 362
**The drift test: the migrations build exactly the tables the code describes.** It is not `async`, so it starts the async engine itself (line 305).

@@ 363-364
**`differences`** — Alembic's `compare_metadata` compares the real database (migrated by the fixture) with `METADATA`, the tables described in `tables.py`, and lists every difference: a missing table, an extra column, a different type.

@@ 366-371
**`check`** — connect to the test database and run the comparison through `run_sync`, because Alembic's comparison code isn't async (as in `env.py`).

@@ 373
The list of differences must be **empty**. If someone adds a column to `tables.py` but forgets the migration — or the other way round — this test fails, long before a real database meets the mismatch.

@@ 376-378
**Red team, from here on** (Phase 3): tests that play the attacker. **Red-teaming** means attacking your own system on purpose, to find its weaknesses before someone else does.

The first: **a printed photo**. The "person" is the still test portrait, and here liveness measures the images for real (`liveness="images"`).

@@ 379-382
Two attempts with six identical portraits. The photo looks straight ahead throughout — it can't turn left, right or up when asked.

@@ 383-384
The first attempt gets a retry, with the vague `liveness_check_failed` (a real person may just have been slow). The second gets **rejected** — and from outside the reason is only `verification_failed`, which doesn't even say liveness was involved.

@@ 387-392
**Poses in the wrong order.** Labels mode is on, so the frames' labels are believed — but the attacker labels them `turn_right` three times, whatever the challenge asked. A challenge never repeats a pose twice in a row, so this can never match it.

@@ 393
Caught: retry, `liveness_check_failed`.

@@ 396-398
**A challenge claimed by the browser.** The attacker sends an easy challenge of its own choosing — one pose, `turn_left`, two colours.

@@ 399-402
And four frames that would satisfy *that* easy challenge: three baseline frames, then `turn_left`.

@@ 403
Caught: the server judged the frames against the challenge it **issued** (three random poses), not the claimed one, so the pose check fails.

@@ 406-413
**Automation and virtual cameras.** Two fresh sessions; in each the browser honestly reports one warning sign — a program driving the browser, or a virtual camera. The frames themselves are fine and the person is a clear adult.

@@ 414
Both go to **step up** with `liveness_uncertain`: not passed on a face that may have been injected, but not rejected either, because these signs can have innocent causes. `[x] * 2` is a list of two copies of `x`.

@@ 417-420
**One device gets only so many challenges, however many sessions it starts.**

@@ 421-424
A helper that creates a fresh session, starts it, and asks for a challenge with a given device ID — the flow token's headers plus `X-Dwarpal-Device` (`|` joins two dicts).

@@ 426-428
With a budget of 2 challenges an hour: three requests from the same device, each in a new session, then one from a different device.

@@ 429-431
The same device gets two challenges and then `429 too_many_attempts` — new sessions don't reset its budget; the other device is unaffected.

@@ 434-450
**The tenancy tests (Phase 4).** `TENANT_TABLES` — the fifteen tables whose rows belong to a tenant: from organisations to the audit log, the daily counts, the console's users and their memberships. (The signing keys belong to Dwarpal itself, not to any customer.)

@@ 451
`NOT_TENANT_DATA` — the only two tables allowed to have no row-level security: Alembic's migration history and Dwarpal's own signing keys. Neither belongs to any customer.

@@ 454-471
**`a_session`** — a minimal verification session for a given project, made directly as a table row rather than through the API: just enough to be a row worth hiding or showing. It follows a preset (`policy_version=0`). `bytes(32)` is 32 zero bytes, standing in for the client secret's digest.

@@ 474-476
**`two_organisations`** — the scene for the tests, built as the tables' **owner**, whom the policies don't bind: organisation A with projects a1 and a2, organisation B with project b1, and one verification session in each project.

@@ 477-478
The time, and a fresh random ID for each name. `uuid.uuid4()` is fine here: these IDs only need to be different from everything else in the shared test database.

@@ 479-488
An engine with **no role** — the owner. Add both organisations, then (after a `flush`, so the foreign keys find them) the three projects, then one session per project, and commit. `add_all` adds a whole list at once.

@@ 489-490
Close the engine, and return the IDs by name, so each test can say `made["a1"]`.

@@ 493-494
**Test 1 — reading.** Each tenant sees only its own rows, and a unit of work that names no tenant sees nothing at all.

@@ 495-497
Build the scene, then open an engine as the API does: as `dwarpal_app`.

@@ 498-502
First, a unit of work that names **no** tenant counts the rows of every tenant table — expected: zero everywhere, although this database holds rows from every test so far. Then roll back and ask PostgreSQL who we are (`current_user`). This guards the bug the tests found while this step was built: a rollback used to undo `SET ROLE`, and the connection quietly became the owner again (`db.py`).

@@ 503-505
Named as project **a1**: which projects own the sessions it can see, and which organisations it can see.

@@ 506-507
Named as organisation **A**: which projects it can see.

@@ 508-509
`finally` closes the engine even if something above fails, so a failing test doesn't leave connections open.

@@ 510-514
The verdicts. Still the restricted role; zero rows of anything with no tenant; project a1 sees only its own sessions and its own organisation; organisation A sees both its projects, and not b1.

@@ 517-520
**Test 2 — writing.** A tenant can't create or change another tenant's rows, and can't switch the protection off.

@@ 521-523
The same scene and the same restricted engine.

@@ 524-528
Named as **a1**, try to add a session belonging to **b1**. The database must refuse at commit with "new row violates **row-level security** policy". `pytest.raises(…, match=…)` passes only if that error, with that text, happens.

@@ 529-534
Named as **a1**, try to change b1's sessions: an `update` with a `where` that picks exactly them. `.returning(…)` asks the database to send back the ID of every row it changed. b1's rows are invisible to a1, so the update finds nothing to change.

@@ 535-536
After the commit, count sessions again in the same database session. The tenant was named with `set_config(…, true)`, for **one** transaction, and this is a new one: it sees nothing.

@@ 537-539
Could the restricted role simply turn the policies off? `ALTER TABLE … DISABLE ROW LEVEL SECURITY` is allowed only to a table's owner, so PostgreSQL answers "**must be owner** of table projects".

@@ 540-541
Close the engine, whatever happened.

@@ 542-543
The verdicts: no row changed, and nothing visible once the transaction had ended.

@@ 546-547
**Test 3 — through the API.** One website's key can't read another website's session.

@@ 548-551
Inside the usual harness, the first website creates a session. Then `seed_dev` makes a **second** organisation, project and key in the same database — a second customer.

@@ 552-557
Ask for the first website's session with the second website's key, and then with its own.

@@ 558-560
A foreign key gets the same `404 session_not_found` as a session that doesn't exist — it can't even learn that the session is there — while the owner reads it normally.

@@ 563
**Test 4 — no table forgotten.** The tests above prove that the policies work; this one proves that **every** table has them. A future migration that adds a table and forgets its policy would fail here, until someone either protects the table or decides, in this file, that it holds no customer's data.

@@ 564-570
Connect as the owner, and ask PostgreSQL's own catalogue. `pg_class` lists every table the database knows; the conditions keep ordinary tables (`relkind = 'r'`) in our `public` schema (`'public'::regnamespace` turns the schema's name into its internal ID) whose row-level security is **off** (`NOT relrowsecurity`). `connection.scalars` returns the first column of each row: the names. `set(…)` collects them, and the engine is closed.

@@ 572
The unprotected tables must be exactly the two allowed ones, no more and no fewer.

@@ 575-576
**`bearer_of`** — the `Authorization` header for a given key. The tests below use several keys, so `h.key` alone won't do.

@@ 579-582
**Idempotency.** Sending the same request twice with the same `Idempotency-Key` gets the first answer, not a second session.

@@ 583-588
The same request twice with one key; the same key with a *different* request; a key that is too short; and two requests with no key at all.

@@ 589-592
Look inside Valkey itself. `scan_iter("idem:*")` walks through every stored reply. Each must exist, and none may contain the client secret in readable form: the reply is sealed (`app/idempotency.py`), so a copy of Valkey reveals no secret.

@@ 593-596
Both requests succeeded, the second answer is **identical** to the first — the same session and the same client secret — and only the repeat carries `Idempotent-Replayed`.

@@ 597-601
The same key with a different request is refused (`422 idempotency_key_reused`). The short key is refused too — since step 6 by the pattern the API document states, so as a general `invalid_request` naming the header, before the API's own check runs. And without a key, two requests make two different sessions.

@@ 604-607
**Rate limits.** A key allowed a burst of 2 and almost no refill (one token every 100 seconds) makes three requests in a row.

@@ 608-610
Two get through, the third gets `429 rate_limited`, with a `Retry-After` of at least one second.

@@ 613-615
**Pagination.** Five sessions are listed two at a time.

@@ 616
Create five sessions, remembering their IDs in the order they were made.

@@ 617-624
Read the pages the way a client would: ask for 2, then keep asking `starting_after` the cursor of the last page until `has_more` is false. (`|` joins two dictionaries; with no cursor yet, the second one is empty.)

@@ 625
Ask for more than the largest allowed page.

@@ 626-630
All the listed IDs together: pages of 2, 2 and 1; exactly the five sessions, **newest first** (`reversed(made)`), none repeated, none missed; no `age_token` anywhere in the list; and the oversized page refused with `422`.

@@ 633-639
**Scopes.** A key with only `sessions:read` can't create a session (`403 insufficient_scope`), but can list them.

@@ 642-645
**Rotation and revocation.**

@@ 646-649
Rotate the harness's key with a one-hour grace period. The key id is characters 8 to 19 of the key.

@@ 650
During the grace period, the old key and its replacement both work.

@@ 651-653
Rotate the replacement with **no** grace at all, then try the key just replaced and its own replacement.

@@ 654-655
Revoke the newest key (`revoke_key` reports that it found one), and try it once more.

@@ 656-659
The verdicts: both keys worked during the grace period; a key whose grace has ended gets `401 api_key_expired`; its replacement works; a revoked key gets the plain `401 invalid_api_key`.

@@ 662-665
**Versioned policies.** A session keeps the policy version it started with, even after a new version is added.

@@ 666-668
Add version 1 of the project's own policy `shop_18`.

@@ 669
Create a session with it.

@@ 670-672
Add version 2, which allows only one face attempt.

@@ 673
Create another session, which gets version 2.

@@ 674
Start the **first** session's flow: its answer says how many attempts remain.

@@ 675
List the policies.

@@ 676-678
Three refusals to check: a custom policy named like a preset, one for age 19 (the model has no thresholds for it), and a session asking for a policy nobody made.

@@ 679-680
The two versions were numbered `shop_18@1` and `shop_18@2`, and each session names the version it got.

@@ 681
The first session still has **3** attempts — version 1's rules — although version 2, with only one, now exists.

@@ 682
The list shows both versions of the project's own policy, oldest first.

@@ 683-685
And the three refusals: `invalid_policy_name`, `policy_not_supported`, `unknown_policy`.

@@ 688-691
**Immutability.** Add one policy version through the API.

@@ 692-699
Then, as the API's own role, try to change it and to delete it with plain SQL. The migration gave the role only `SELECT` and `INSERT` on this table, so PostgreSQL answers "**permission denied**" to both: no bug in our code could rewrite the rules a past check followed. Close the engine at the end, whatever happened.

@@ 702-704
**The webhook tests (Phase 4).** `Receiver` — a website's webhook receiver, kept in memory: no network, no server.

@@ 706-707
The statuses it will answer with, in order, and every request it has received.

@@ 709-711
**`handle`** — record the request, and answer with the next status in line (`pop(0)` takes the first), or `200` once the list is used up.

@@ 714-715
**`deliverer`** — the delivery worker, set up as in production: as the tables' owner.

@@ 716-717
An owner engine, and an HTTP client whose **transport** is `httpx.MockTransport(receiver.handle)`: every request the worker sends is handed straight to the receiver's function instead of going over a network.

@@ 718
The development master key — the same one the API in the harness uses, so the worker can open the secrets the API sealed.

@@ 719
Return the worker and its engine (so the test can close it). The clock is `lambda: clock[0]`: a function reading a one-item list, so the test can move time forward by changing `clock[0]` — and test a 24-hour retry without waiting 24 hours.

@@ 722-726
**`pass_one_session`** — create a session, start it, and pass one face attempt: a session that has just completed.

@@ 729-732
**Test — a delivery.** A completed session reaches the website, signed so that the website can check it.

@@ 733
An empty receiver (it will answer `200`), and a clock.

@@ 734
The harness allows private addresses: the receiver's address is never really contacted.

@@ 735-737
Register an endpoint for completed sessions.

@@ 738
Complete one session: the event and its delivery are written in the same transaction.

@@ 739
Set the worker's clock just past now, so the delivery is due.

@@ 740-742
Run the worker once, then close its engine.

@@ 743-744
Read the endpoint's deliveries, and the list of endpoints.

@@ 745-746
The secret was shown once, at creation, with its `whsec_` prefix, and never again.

@@ 747
Exactly one delivery was sent, and it arrived.

@@ 748-753
The body is the completed event: it names the session and its outcome, it carries **no token**, and the `Dwarpal-Event-Id` header matches the event's ID.

@@ 754-757
Check the signature exactly as a receiver would: split the header into `t` and `v1`, recompute the HMAC of `"<t>.<body>"` with the secret, and compare in constant time (`compare_digest`).

@@ 758
The delivery is recorded as delivered, on its first attempt, with the receiver's `200`.

@@ 761-764
**Test — retries.** A failing receiver is retried on the schedule until the delivery is dead; then it can be replayed.

@@ 765
This receiver answers `500` eight times.

@@ 766-772
Register an endpoint, send it a **test event** (which goes to this endpoint whatever it subscribes to), and set the clock just past now.

@@ 773-776
Eight rounds. In each, the worker sends one delivery, and an immediate second run finds nothing due: the failure has pushed the next attempt into the future.

@@ 777-778
Read the delivery's state.

@@ 779-782
While it is still pending, measure the wait the worker chose, and move the clock forward to exactly that moment.

@@ 783
Replay the dead delivery.

@@ 784-785
With the clock at now, the worker sends it again — and the receiver, out of failures, answers `200`.

@@ 786-787
Close the engine and read the final state.

@@ 788
The test event was accepted (`202`, "accepted for later").

@@ 789
The waits were exactly the schedule: 1 minute, 5 minutes, 30 minutes, 2, 6, 12 and 24 hours.

@@ 790
After the eighth failure the delivery was dead, with the receiver's last `500` recorded.

@@ 791-792
Replaying put it back to pending with a fresh count, and it was then delivered.

@@ 795-800
**Test — the SSRF guard through the API.** With private addresses not allowed (the normal setting), an endpoint on `127.0.0.1` — this very computer — is refused.

@@ 801-803
So is an endpoint asking for an event type that doesn't exist.

@@ 804-805
`422 unsafe_webhook_url` and `422 unknown_event_type`.

@@ 808-813
**Test — introspection.** Pass a session and read its age token.

@@ 814-815
Seed a second website, with its own key.

@@ 817-819
**`ask`** — introspect a token with a given key. A function defined inside the test, because only this test needs it.

@@ 821-824
Ask four times: with the other website's key; with a **forged** token (its last four characters changed, which breaks the signature); and twice with the right key.

@@ 825-828
The other website and the forger both get only `{"active": false}`; the first genuine question gets `active` with the token's claims; the second gets `false` — a token is spent once introspected.

@@ 831-833
**Test — expiry is announced once.** A session lifetime of 0 seconds makes every new session expire at once.

@@ 834-836
Register an endpoint for expired sessions.

@@ 837-838
Create a session, and read it twice.

@@ 839
Read the endpoint's deliveries.

@@ 840-841
Both reads say `expired`, but there is exactly **one** delivery: the first read saved the change and its event together, and the second found nothing to change.

@@ 844-851
**`org_of`** — the organisation that owns a seeded project, read as the tables' owner: the audit log is kept per organisation.

@@ 854-855
**Test — the audit chain.** Real changes are chained in the log, and tampering of either kind is found.

@@ 856-861
Through the API: add a policy version, register a webhook endpoint, and delete it. With the key `seed_dev` created, that makes four audited actions.

@@ 862-865
The organisation's ID; an engine as the owner, and one as the API's role.

@@ 866
From here on, whatever happens, both engines are closed at the end (`try` … `finally`).

@@ 867-869
Read the organisation's entries, and verify the chain as it stands.

@@ 870-872
**The API can't rewrite history**: as the API's role, changing any entry is refused with "permission denied" — the role may only add entries (migration `0006`).

@@ 873-877
But someone with the **owner's** rights — a database administrator, or an attacker who stole that login — can. Change entry 2's facts (as if the policy had been for age 13) and verify again.

@@ 878-882
Put entry 2 back, then quietly **delete the last entry**, and verify once more.

@@ 883-885
Close both engines, whatever happened.

@@ 886-891
The four entries, in order: the key's creation, the policy version, the endpoint created, the endpoint deleted.

@@ 892-893
Changes made with the API key name it by its **id** (characters 8 to 19), and the key itself appears in no entry's facts.

@@ 894
Before any tampering: four entries, intact.

@@ 895
After the edit: broken, **at entry 2** — the exact entry that was changed.

@@ 896
After the deletion: broken at entry 4, the missing one. The chain itself still checks out, but the head (`audit_heads`) remembers that there should be four.

@@ 899-903
**Test — counting.** Pass two sessions.

@@ 904-905
Read the last week's counts, and ask for more than a year.

@@ 906-908
Two passes in total, in one row for today under `uk_osa_18`; and a request for 366 days refused with `422`.

@@ 911-915
**Test — the sweep and the purge.** Settings for calling the operator's command directly.

@@ 916-920
Sessions in this harness expire at once. Register an endpoint for expired sessions, and create a session that nobody will ever read.

@@ 921-922
Run the scheduled jobs, then read the endpoint's deliveries.

@@ 923-928
As the owner, give this project a retention of **one day**.

@@ 929-930
Run the jobs as if it were 23 hours later: within the day, so the session is kept.

@@ 931-932
Run them as if it were two days later: past the day, so it is purged.

@@ 933
Read the project's counts.

@@ 934-936
Verify every organisation's audit chain.

@@ 937-938
The sweep expired at least one session (other tests leave theirs too), and the website was told, by one delivery, although nobody read the session.

@@ 939-941
After 23 hours nothing of this project's was purged and the session still exists; after two days it is gone (`404`).

@@ 942
The count of one expired session outlives the session itself.

@@ 943
And this organisation's audit chain is intact.

@@ 946-948
**The console tests (Phase 4, step 2).** The console's address; settings for its tests — a cookie that may travel over plain HTTP, and a generous sign-in allowance, because every test signs in from the same address; and a throwaway password.

@@ 951-953
**`person`** — a separate browser for one person: a new client on the same transport, with its own cookie jar, so several people can be signed in at once in one test.

@@ 956-960
**`sign_up`** — create an account and organisation through the console, insist it worked, and return the answer (which includes the CSRF token).

@@ 963-964
**`unique`** — a fresh e-mail address each time, so tests sharing the database never collide.

@@ 967-971
**Test — signing up, in and out.**

@@ 972-974
Sign up, and look at the cookie the browser received.

@@ 975-980
Try to sign up again with the same address, and with a five-character password.

@@ 981-983
Sign in with a wrong password; with an address nobody has; and correctly, typed in capitals.

@@ 984-987
Sign out without the CSRF token, then with it; then ask who is signed in.

@@ 988-989
The new person owns the new organisation; the cookie is a long, unguessable token.

@@ 990-991
The repeated address and the weak password are refused.

@@ 992-993
A wrong password and an unknown account get the **same** status and the **same** sentence: an attacker can't use sign-in to find out who has an account.

@@ 994
Addresses match whatever their capitals.

@@ 995-997
Signing out needs the CSRF token like any change; with it, the session ends, and the cookie no longer works.

@@ 1000-1002
**Test — CSRF.**

@@ 1003-1007
Sign up, then try a change three ways: with a guessed token, with the real token but from another site's origin, and genuinely.

@@ 1008-1010
The guess fails (`csrf_failed`), another origin fails (`bad_origin`), and only the genuine request works.

@@ 1013-1016
**Test — one-time codes.**

@@ 1017-1018
Sign up, and ask to set up one-time codes: the answer holds the secret and its `otpauth://` address.

@@ 1019-1023
Work out the current 30-second step. A wrong code is refused; the right one, computed from the secret as an authenticator app would, switches codes on.

@@ 1024-1025
Sign in with only the password.

@@ 1026-1028
Sign in with the **next** step's code — what a phone whose clock runs a little fast shows — and then try exactly the same code again.

@@ 1029-1034
The offer was a proper `otpauth://` address; the wrong code failed and the right one worked — and came with ten recovery codes; a password alone is no longer enough; the code worked once — and a second time it is refused.

@@ 1037-1039
**Test — roles.** Three addresses: an owner, an analyst and a developer.

@@ 1040-1046
Inside one harness, four browsers — the fourth for an outsider. `async with ( … ):` opens several at once, and closes them all at the end.

@@ 1047-1049
The owner signs up; note the organisation and the owner's CSRF token.

@@ 1050-1053
The analyst and the developer sign up (each gets an organisation of their own), and so does the outsider.

@@ 1054-1058
The owner adds the analyst and the developer to the owner's organisation, each with their role.

@@ 1059-1061
The analyst lists the organisation's projects — any member may — and the test builds the address for creating API keys in the first one.

@@ 1062-1064
The analyst and the developer each try to create a read-only key.

@@ 1065-1069
The developer tries to make the analyst an owner.

@@ 1070-1074
The analyst lists the members; the outsider tries to; the developer's new key is used on the API; and the owner and the analyst read the audit log.

@@ 1075-1077
The analyst may not create keys (`403 forbidden_for_role`); the developer may; and the developer may not manage members.

@@ 1078-1079
The analyst sees all three members; the outsider gets `404`, exactly as if the organisation didn't exist.

@@ 1080
The key made in the console works on the API.

@@ 1081-1084
The owner's audit log, oldest first: the organisation's creation, two members added, a key created; the chain is intact; and the key itself appears nowhere in it.

@@ 1085
The analyst may not read the audit log.

@@ 1088-1090
**Test — sign-in limits.** At most 2 attempts at once, then one every two minutes.

@@ 1091-1093
A browser at an address of its own. `ASGITransport(…, client=…)` sets the address the API sees the request coming from; `192.0.2.x` is a range reserved for documentation and tests. Without it, every other test's sign-ins would already have used up this address's allowance.

@@ 1094-1099
Sign up, then try a wrong password three times.

@@ 1100-1101
Two ordinary refusals, then `429 too_many_sign_ins`, with a `Retry-After` of at least a second.

@@ 1104-1106
**The contract test (Phase 4, step 6).** `live_api` — Schemathesis sends real HTTP, so the API runs as a real server for these tests. `scope="module"` starts it once for the whole file rather than once per test.

@@ 1107-1115
Its settings: the test databases; webhook addresses never looked up (the fuzzer invents host names); a cookie allowed over plain HTTP; and limits so high that the fuzzer's many requests aren't simply refused with `429`.

@@ 1116
Seed a project and a key for it.

@@ 1117
A uvicorn server for the API, on `127.0.0.1` and **port 0**, which asks the operating system for any free port, so the test never collides with something already running.

@@ 1118-1119
Run it in a background **thread**: `daemon=True` means the thread won't keep Python alive if the tests end without stopping it.

@@ 1120-1121
Wait, a twentieth of a second at a time, until the server says it has started.

@@ 1122
Read which port it was given.

@@ 1123
Hand the tests the server's address and the key.

@@ 1124-1125
Afterwards, ask the server to stop, and wait up to ten seconds for its thread to finish.

@@ 1128-1130
**`live_document`** — Schemathesis reads the API's document from the running server, exactly as a website's developer would.

@@ 1133
`contract` — tells Schemathesis to take the document from that fixture. A document known only once the server runs can't be read while pytest is still collecting tests, so it is fetched lazily, from the fixture.

@@ 1136-1137
`@contract.parametrize()` turns the test into one sub-test per operation in the document: 31 of them. `@settings` gives each 25 generated requests, no time limit per request (`deadline=None`), and turns off Hypothesis's health checks, which would complain that each example is slow (it is a real HTTP request).

@@ 1138-1139
**Test — the contract.** For each generated request (`case`):

@@ 1140-1142
Every check but one. `positive_data_acceptance` insists that a request the document allows must succeed. But some of the API's rules depend on data, not just shape: whether the age model is calibrated for an age, whether an address is among the project's allowed origins. Refusing such a request with `422` is correct.

@@ 1143
Send it to the server with the website's key, and check the answer: never a server error, a status code the document lists for this operation, a content type it lists, a body that matches the schema for that status, and the headers HTTP requires (such as `Allow` on a `405`). Any failure prints the exact request, as a `curl` command to reproduce it.

@@ 1146-1148
**Test — no drift.** `docs/api/openapi.json` is what websites read; the docstring says how to refresh it.

@@ 1149
The file must equal, byte for byte, what the code produces now. A change to the API without refreshing the document fails here.

@@ 1152-1154
**Fail-closed tests (Phase 7).** Valkey unreachable. "Gone" is simulated by an address where nothing listens: port 1 on this computer.

@@ 1155-1158
Settings with that Valkey and the real database; a key; and an API started with them (its inference client is never reached).

@@ 1159-1162
Try to create a session — the API key's rate limit needs Valkey — and ask whether the API is ready.

@@ 1163-1165
The session request gets `503 service_unavailable` with `Retry-After: 5` (not a crash, not a pass), and readiness reports exactly what is wrong: the database is fine, Valkey isn't.

@@ 1168-1169
**`unreachable`** — an inference service that is down: every request fails to connect.

@@ 1172-1173
**`broken`** — an inference service that answers, but with nonsense: valid JSON that isn't an analysis.

@@ 1176-1181
**Fail closed when inference fails.** The test runs twice, once with each broken service (`parametrize`).

@@ 1182-1188
An API whose inference client sends every request to the broken service, and a harness around it.

@@ 1189-1192
Create a session, start it, and make two attempts with a real face.

@@ 1193-1194
Neither attempt passes — the face would have passed with a working service — and the first is a `retry`: the person may try again, but nobody is let in on a failure.

@@ 1197-1202
**Security headers (Phase 7).** A refusal (no key), the public key set, and the interactive documentation.

@@ 1203-1208
Every answer carries `nosniff`, the strict content policy, `no-referrer` and (since Phase 7) `Cross-Origin-Resource-Policy: same-origin`. HSTS isn't sent outside production: over plain HTTP it would mean nothing.

@@ 1209-1211
Answers are `no-store` unless their route says otherwise: the key set keeps its own five-minute public caching. The documentation page has no content policy, which would stop its scripts.

@@ 1214-1222
**Production.** Settings a production deployment would accept: a real-looking master key and HTTPS addresses. The app isn't started, because `/livez` needs no database.

@@ 1223-1226
Ask for `/livez`, the documentation page and the API document.

@@ 1227-1228
HSTS is sent (two years); the interactive documentation doesn't exist (`404`); the API document is still published.

@@ 1231-1237
**Test — the console's project pages (Phase 5).** An owner and an analyst, each with their own browser.

@@ 1238-1243
The owner signs up; the analyst signs up; the owner adds the analyst to the organisation.

@@ 1244-1247
The owner finds the organisation's project and creates a key for it in the console.

@@ 1248
A website using that key: the harness, copied with the key changed (`replace`).

@@ 1249-1251
The website creates a session — without a return address, because this new project hasn't allowed any yet — and a person passes it.

@@ 1253-1255
The analyst reads the project's sessions, the passed session's trace, and the last week's counts.

@@ 1256-1259
The analyst and then the owner try to add a policy version; the analyst lists the policies.

@@ 1260
The analyst tries the harness's own project — which belongs to another organisation — under this organisation's address.

@@ 1261-1262
The one session is listed; its trace has one attempt, and it passed.

@@ 1263-1264
The attempt carries its numbers: the age probability, the line it met, and the liveness evidence.

@@ 1265
Reading a trace made no token.

@@ 1266
The counts show one pass.

@@ 1267-1269
An analyst may not add a policy version; the owner may, and it is listed as `console_18@1`.

@@ 1270
Another organisation's project, named under this organisation, is not found — the check that the project belongs to the organisation in the address.

@@ 1273-1276
**Test — the console's webhooks (Phase 5).** An owner and an analyst. Private addresses are allowed, so the endpoint can point at this computer (`localhost:9`, where nothing listens — nothing is sent in this test).

@@ 1277-1283
The owner signs up, the analyst signs up and is added, and the owner finds the project.

@@ 1284-1285
The project's webhook address, and an endpoint for finished sessions.

@@ 1287-1290
The analyst tries to add it; the owner adds it; the analyst tries to list them; the owner lists the live ones.

@@ 1291-1295
The owner sends a test event, reads the endpoint's deliveries, and replays the first.

@@ 1296-1299
The owner tries to delete it as a live endpoint, then deletes it as the test one it is; lists again; and reads the audit log.

@@ 1300
An analyst may not add one.

@@ 1301
The owner's new endpoint came with its secret, and is a test endpoint.

@@ 1302
An analyst may not even list them; and the live mode has none — modes never mix.

@@ 1303-1304
The test event is waiting to be delivered (no worker runs here); the replay is accepted.

@@ 1305
The wrong mode is "not found"; the deletion worked, and the list is empty.

@@ 1306-1307
The audit log names a person (`user:…`), not a key, for both the creation and the deletion.

@@ 1310-1317
**Test — the owner rules for members (Phase 5).** Three people, each with their own browser: an owner, an admin, and one more.

@@ 1318-1322
All three sign up.

@@ 1323-1325
The owner adds the admin as an admin, and the third person as an analyst.

@@ 1326-1327
Everyone's IDs: the third person's from the answer, the owner's from `/me`, the admin's from the member list.

@@ 1329-1331
The admin promotes the analyst to developer, then tries to make them an owner; the only owner tries to step down to admin.

@@ 1332-1333
The owner makes the third person an owner, and then steps down — allowed now, since there are two.

@@ 1334-1336
The admin tries to remove the new owner; the new owner removes the admin; and tries to remove an ID that isn't anyone's.

@@ 1337-1338
What remains, and the audit log.

@@ 1339
An admin may change a member who isn't an owner.

@@ 1340
An admin may not make an owner.

@@ 1341
The last owner may not step down.

@@ 1342
With two owners, one may.

@@ 1343
An admin may not remove an owner; an owner may remove an admin; an unknown member is not found.

@@ 1344
Left: the first owner (now an admin) and the new owner.

@@ 1345-1346
The audit log holds exactly the four changes that happened — refusals leave no trace.

@@ 1349-1354
**Test — unstorable text is refused (Phase 5).** Sign in with an address containing NUL — the kind of input the contract tests found: `422 invalid_text`, not a server error.

@@ 1357-1361
**Test — the production session cookie (Phase 5).** The browser tests now run with a plain cookie (WebKit drops `Secure` ones on plain HTTP), so this test checks the real one: with the production setting, sign up and read the `Set-Cookie` header.

@@ 1362-1363
Sign up.

@@ 1364-1365
The cookie's name starts with `__Host-`, so browsers insist it is `Secure`, for path `/`, with no `Domain`: no other site can set or read it.

@@ 1366-1367
Its attributes include `HttpOnly` (no script can read it), `Secure` (HTTPS only), `Path=/` and `SameSite=Lax`.

@@ 1368
And no `Domain`, which would share it with other hosts.

@@ 1371-1377
**Test — switching an endpoint off and on** (Phase 5). A website registers an endpoint.

@@ 1378-1380
Switch it off, send a test event, and read its deliveries.

@@ 1381-1383
Switch it back on, and do the same.

@@ 1384
And try to switch an endpoint that doesn't exist.

@@ 1385
The answers said off, then on.

@@ 1386
While off, nothing was queued for it.

@@ 1387
Back on, the test event waits to be delivered.

@@ 1388
An unknown endpoint is not found.

@@ 1391-1393
**Test — listing sessions by outcome and by reference** (Phase 5).

@@ 1394-1396
A session with the website's reference `order-1`, which a person passes.

@@ 1397
Another, `order-2`, not yet started.

@@ 1398-1402
List the passed ones; the one for `order-2`; one for a reference nobody used; and ask for an outcome that doesn't exist.

@@ 1403-1405
Exactly the passed session; exactly `order-2`'s; and nothing.

@@ 1406
An unknown outcome is refused, not silently ignored.

@@ 1409-1414
**Test — recovery codes, and switching codes off** (Phase 5).

@@ 1415-1419
Sign up, ask for a secret, and confirm the current code: the answer holds the recovery codes.

@@ 1420-1423
Sign in with the first recovery code, typed as someone might copy it from paper — capitals, a space instead of the dash. Keep the new session's CSRF token.

@@ 1424
Try the same recovery code again.

@@ 1425-1426
Ask for a fresh set, then try one of the old set.

@@ 1427-1433
Try to switch codes off with a wrong password, then with the right password and the next code.

@@ 1434
Sign in with the password alone.

@@ 1435
Ten different codes, each of the shape `abcde-fghij`.

@@ 1436
The recovery code signed in, and nine are left.

@@ 1437
Each works once.

@@ 1438
The fresh set shares nothing with the old, and the old no longer works.

@@ 1439
A wrong password is refused.

@@ 1440-1441
With the right password and code, codes are off — and the password alone signs in again.
