---
fingerprint: c65a0953bd937f94
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

@@ 5-18
Standard-library tools: `asyncio`, `hashlib` and `hmac` (to check a webhook's signature as a receiver would), `json`, `logging`, `threading` and `time` (to run a real server beside the tests), `uuid` (fresh IDs), the iterator types for fixtures, `asynccontextmanager`, `dataclass`, `UTC`, `datetime` and `timedelta` (a length of time, for key rotation and webhook retries), `Path`, `Any` — and `Literal`, for the harness's liveness option (Phase 3).

@@ 20-24
OpenCV and NumPy (to make a test picture), the `docker` client (to ask whether Docker is running), `httpx` (to call the apps) and `pytest`.

@@ 25-26
`schemathesis`, the contract tester (step 6), and `uvicorn`, the server program, to serve the API on a real port for it.

@@ 27-28
Alembic's `compare_metadata` and `MigrationContext`, for the drift test at the end.

@@ 29
Hypothesis's `settings` and `HealthCheck`, to tell Schemathesis (which uses Hypothesis inside) how many requests to make per operation.

@@ 30-31
joserfc's `jwt` and `KeySet`: the tests verify tokens exactly as a website would.

@@ 32
An async Valkey client, so a test can look at what the API stored there (Phase 4).

@@ 33-34
Schemathesis's `Case` — one generated request — and `positive_data_acceptance`, the one check the contract test leaves out (explained there).

@@ 35
SQLAlchemy's query builders, for the Phase 4 tests: `delete` (to remove a row on purpose), `select` and `func` (to count rows), `text` (raw SQL), and `update` (to try changing rows).

@@ 36-38
SQLAlchemy types: `Connection` for the drift test, `DBAPIError` — the error SQLAlchemy raises when the database itself refuses a statement — and `create_async_engine`.

@@ 39-41
Testcontainers: a ready-made PostgreSQL container, a general container for Valkey, and a **wait strategy** — "the container is ready when this line appears in its log".

@@ 43-71
The code under test: the database helpers (`make_engine`, `make_sessions`, `tenant`), the master key, the table catalogue and the fifteen tables that belong to tenants, the audit and maintenance modules, the delivery worker, the CLI's `API_DOCUMENT`, `api_document`, `maintain`, `migrate`, `seed_dev`, `rotate_key` and `revoke_key`, both apps' factories (renamed with `as` so the two `create_app`s can't be confused), the ID and one-time-code helpers, both settings classes, and the contracts for frames, challenges and browser signals. The brackets let one `import` span several lines.

@@ 73-74
The repository folder, and the public-domain portrait from the vision library's tests — a real face, so the real face detector finds it.

@@ 75
The demo shop's return address, which the seeded project allows.

@@ 78-81
**`blank_frame`** — a plain grey 320 × 240 picture, saved as JPEG: a valid image with no face in it. `np.full` fills an array with one value (128, middle grey). `cv2.imencode` returns two values — whether it worked, and the encoded bytes.

@@ 84-85
**The `databases` fixture.** A **fixture** is something a test needs, prepared by pytest and passed in by name. `scope="session"` means it is built **once for the whole test run** and shared: starting two containers takes seconds, so doing it once matters. It provides the two addresses.

@@ 86-89
Is Docker running? Ask it, giving up after 5 seconds. If not, skip every test that needs this fixture, with the reason.

@@ 90-95
A PostgreSQL container, using exactly the image the local Compose file uses. The password is a throwaway for a throwaway container; the comment explains why the linter's warning about a hard-coded password doesn't apply.

@@ 96-100
A Valkey container, with its port exposed, considered ready when Valkey logs `Ready to accept connections`.

@@ 101-102
Start both. Each `start()` waits until its container is ready.

@@ 103-105
Docker maps each container's port to a random free port on this computer, so the addresses are built from what the containers report. Random ports mean tests never clash with a database already running locally.

@@ 106
Apply the migrations — the same function a developer runs from the command line.

@@ 107
`yield` hands the addresses to the tests. Everything after it runs when the whole test run is over…

@@ 108-109
…stopping (and removing) both containers.

@@ 112-116
**`Harness`** — what each test gets to work with: an HTTP client connected to the API, the seeded project's test API key, and the project's public ID.

@@ 117
`transport` — the in-process connection to the API (step 2): a test can open more clients on it, one per person, each with its own cookies.

@@ 120-128
**`harness`** — sets up a complete, fresh API for one test. Its options: the age the stand-in model should "see" (30 by default — clearly an adult), whether the seeded key is live, how liveness gets its evidence (Phase 3) — `"labels"` by default, because the tests' portrait is a still photo that can't turn its head — the seeded key's scopes (every scope by default), and any other API settings to change (`**overrides`: extra named arguments, collected into a dict), such as a smaller device budget or rate limit.

@@ 129
Unpack the two database addresses.

@@ 130
Create an inference app whose stand-in model reports the chosen age, with the chosen liveness evidence.

@@ 131-135
Start the inference app's lifespan (loading its face detector), and open an HTTP client wired to it through **`ASGITransport`** — httpx calls the app's Python code directly, with no network and no server. One `async with` with two parts, in brackets, opens both and closes both.

@@ 136-137
Create the API with test settings — the test databases' addresses, plus any overrides — and the in-process inference client. The settings' default `database_role` applies, so **every test in this file runs as the restricted role**, under row-level security, exactly as the API will in production.

@@ 138
Run the API's lifespan: connect, load the signing key, read the manifest.

@@ 139
Seed a project and a key, exactly as a developer would with `seed-dev`, with the scopes asked for.

@@ 140-142
Open a client wired to the API the same way, and hand the harness to the test, with the transport. When the test ends, every `async with` closes in reverse order.

@@ 145-148
**`create`** — create a session as the demo shop would, with the API key, plus any extra headers (`headers_extra`, such as an `Idempotency-Key`). Any keyword arguments replace the body's defaults, so a test can write `create(h, policy="anything_goes")`.

@@ 151-152
**`secret`** — the body for `/start`: the session's client secret.

@@ 155-158
**`start`** — start the flow and return the `Authorization` header with the flow token, ready for the next calls. The `assert` includes the response text, so if starting fails, the test report shows why.

@@ 161-162
**`following`** (Phase 3) — the labels for a burst whose head follows the given poses: frontal **baseline** frames first, then one frame per pose, in order. With 6 frames and 3 poses: baseline, baseline, baseline, then the three poses.

@@ 163
`["baseline"] * n` makes a list of n copies; `+ poses` adds the poses after them.

@@ 164
One `FrameMeta` per phase, numbered from 0, taken 120 ms apart. `enumerate` gives each item with its position.

The comment at the end, `# type: ignore[arg-type]`, silences one complaint of the type checker: it can't know that the plain texts in `poses` are valid `Phase` names. Pydantic checks them anyway when the `FrameMeta` is created.

@@ 167-175
**`attempt`** — one complete face attempt, as the verify page makes it. Besides the frames, three optional inputs let a test play an attacker (Phase 3):

- `poses` — label the frames with these poses instead of the ones asked for;
- `signals` — report these browser signals;
- `claimed` — put a challenge of the browser's own choosing into the request.

@@ 176-177
The docstring says the same, in short.

@@ 178
Get a challenge — the server picks its random poses and colours.

@@ 179-181
Label the frames: by default they follow the challenge's own poses (an honest attempt), otherwise the poses the test gave. A challenge has 3 or 4 poses, so first make sure there are enough frames — at least 3 frontal ones, then one per pose — by repeating the last frame as many times as needed (`frames[-1:] * n`: a list of the last frame, `n` times; `max(0, …)` keeps `n` from going negative).

@@ 182
Describe the attempt: the frames' labels, the signals (normal ones unless given), and any claimed challenge.

@@ 183-185
Package the frames as files `frame_0`, `frame_1`, …, add the description and the challenge's ID, and upload everything as a multipart form.

@@ 188-189
**The main story: an adult passes, and the website can verify the token.** `@pytest.mark.anyio` lets pytest run an `async` test function.

@@ 190-196
Create, start, attempt with six portraits — the stand-in model says 30, so it passes — then finish: the redirect goes back to the shop with the session's ID.

@@ 197
Start the flow *again*, as if the person reloaded the page afterwards.

@@ 198-200
As the shop's server: read the result with the API key, and fetch the public keys.

@@ 201-202
The reloaded page sees the completed session and its outcome — no error for the person.

@@ 203-204
The result says completed, and passed.

@@ 205
**Verify the token** exactly as a website would: with the published key set, accepting only Ed25519. If the signature didn't match, this line would raise an error.

@@ 206-211
The token is an age token, says pass, says `age_over_18: true` (the literal `True`, checked with `is`), and is addressed to this project, about this session, in test mode.

@@ 212
**No age inside.** None of these names appears among the claims: the set of forbidden names and the set of claim names have nothing in common (`&` is set intersection; an empty set counts as false).

@@ 215-227
**A clear child is refused, unmistakably.** With the stand-in model at 12, the attempt fails, and the signed token says `outcome: fail` *and* `age_over_18: false` — so even a website that read only the age claim would refuse entry.

@@ 230-236
**A teenager near the limit must use a stronger check.** At 16, the probability of being 18 or over is neither high enough to pass nor low enough to fail, so the answer is step up, with the reason `age_uncertain`.

@@ 239-251
**Poor frames: retry, retry, then step up.** Three attempts with blank grey frames: each finds no face. The first two are retries — the first saying `no_face` and that 2 attempts remain — and the third becomes a step-up. The session waits for a stronger check, and has no token.

@@ 254-269
**Credentials are checked, and errors are problem details.** No API key at all: `401`, with the problem-details media type, the stable code, the type reference, and a request ID that matches the response header. A wrong client secret and a missing flow token each get their own code.

@@ 272-276
**Each request is logged once, with its ID, and never with secrets.** `caplog` is pytest's log-capturing fixture; `set_level` makes it collect `INFO` lines from `dwarpal.api`.

@@ 277-278
Create one session. (Setting up the harness makes no HTTP requests, so this is the only request.)

@@ 279-282
Exactly one request log line, with the right method, path and status, and the same ID the response carried. `vars(record)` reads a log record's fields as a dict.

@@ 283-284
Neither the API key nor the new client secret appears anywhere in the captured logs.

@@ 287-301
**A challenge can be used only once.** The same challenge, sent twice: the first attempt is accepted, the second gets `409 challenge_invalid`.

@@ 304-312
**A session gets a limited number of challenges.** Seven requests in a row: six are granted (3 attempts × 2), the seventh gets `429 too_many_challenges`.

@@ 315-318
**Oversized and unmeasured bodies are refused before they are read.** `stream` is an async generator: given as a body, it makes httpx send the request in chunks of unknown total size.

@@ 320-323
A JSON body of about 100 KB (over the 64 KiB limit), and a chunked body.

@@ 324-328
`413 request_too_large` — still with a request ID — and `411 length_required`.

@@ 331-343
**Sessions refuse foreign return addresses, unknown policies, and live mode with a stand-in model.** A return address on another website, a policy that doesn't exist, and a session created with a *live* key while the model is uncalibrated: each gets its own code.

@@ 346-356
**Discovery and readiness.** The configuration document names Ed25519 and admits the model is uncalibrated; the key set may be cached for 5 minutes and holds only Ed25519 keys; and `/readyz` reports both databases as `ok`.

@@ 359
**The drift test: the migrations build exactly the tables the code describes.** It is not `async`, so it starts the async engine itself (line 305).

@@ 360-361
**`differences`** — Alembic's `compare_metadata` compares the real database (migrated by the fixture) with `METADATA`, the tables described in `tables.py`, and lists every difference: a missing table, an extra column, a different type.

@@ 363-368
**`check`** — connect to the test database and run the comparison through `run_sync`, because Alembic's comparison code isn't async (as in `env.py`).

@@ 370
The list of differences must be **empty**. If someone adds a column to `tables.py` but forgets the migration — or the other way round — this test fails, long before a real database meets the mismatch.

@@ 373-375
**Red team, from here on** (Phase 3): tests that play the attacker. **Red-teaming** means attacking your own system on purpose, to find its weaknesses before someone else does.

The first: **a printed photo**. The "person" is the still test portrait, and here liveness measures the images for real (`liveness="images"`).

@@ 376-379
Two attempts with six identical portraits. The photo looks straight ahead throughout — it can't turn left, right or up when asked.

@@ 380-381
The first attempt gets a retry, with the vague `liveness_check_failed` (a real person may just have been slow). The second gets **rejected** — and from outside the reason is only `verification_failed`, which doesn't even say liveness was involved.

@@ 384-389
**Poses in the wrong order.** Labels mode is on, so the frames' labels are believed — but the attacker labels them `turn_right` three times, whatever the challenge asked. A challenge never repeats a pose twice in a row, so this can never match it.

@@ 390
Caught: retry, `liveness_check_failed`.

@@ 393-395
**A challenge claimed by the browser.** The attacker sends an easy challenge of its own choosing — one pose, `turn_left`, two colours.

@@ 396-399
And four frames that would satisfy *that* easy challenge: three baseline frames, then `turn_left`.

@@ 400
Caught: the server judged the frames against the challenge it **issued** (three random poses), not the claimed one, so the pose check fails.

@@ 403-410
**Automation and virtual cameras.** Two fresh sessions; in each the browser honestly reports one warning sign — a program driving the browser, or a virtual camera. The frames themselves are fine and the person is a clear adult.

@@ 411
Both go to **step up** with `liveness_uncertain`: not passed on a face that may have been injected, but not rejected either, because these signs can have innocent causes. `[x] * 2` is a list of two copies of `x`.

@@ 414-417
**One device gets only so many challenges, however many sessions it starts.**

@@ 418-421
A helper that creates a fresh session, starts it, and asks for a challenge with a given device ID — the flow token's headers plus `X-Dwarpal-Device` (`|` joins two dicts).

@@ 423-425
With a budget of 2 challenges an hour: three requests from the same device, each in a new session, then one from a different device.

@@ 426-428
The same device gets two challenges and then `429 too_many_attempts` — new sessions don't reset its budget; the other device is unaffected.

@@ 431-447
**The tenancy tests (Phase 4).** `TENANT_TABLES` — the fifteen tables whose rows belong to a tenant: from organisations to the audit log, the daily counts, the console's users and their memberships. (The signing keys belong to Dwarpal itself, not to any customer.)

@@ 448
`NOT_TENANT_DATA` — the only two tables allowed to have no row-level security: Alembic's migration history and Dwarpal's own signing keys. Neither belongs to any customer.

@@ 451-468
**`a_session`** — a minimal verification session for a given project, made directly as a table row rather than through the API: just enough to be a row worth hiding or showing. It follows a preset (`policy_version=0`). `bytes(32)` is 32 zero bytes, standing in for the client secret's digest.

@@ 471-473
**`two_organisations`** — the scene for the tests, built as the tables' **owner**, whom the policies don't bind: organisation A with projects a1 and a2, organisation B with project b1, and one verification session in each project.

@@ 474-475
The time, and a fresh random ID for each name. `uuid.uuid4()` is fine here: these IDs only need to be different from everything else in the shared test database.

@@ 476-485
An engine with **no role** — the owner. Add both organisations, then (after a `flush`, so the foreign keys find them) the three projects, then one session per project, and commit. `add_all` adds a whole list at once.

@@ 486-487
Close the engine, and return the IDs by name, so each test can say `made["a1"]`.

@@ 490-491
**Test 1 — reading.** Each tenant sees only its own rows, and a unit of work that names no tenant sees nothing at all.

@@ 492-494
Build the scene, then open an engine as the API does: as `dwarpal_app`.

@@ 495-499
First, a unit of work that names **no** tenant counts the rows of every tenant table — expected: zero everywhere, although this database holds rows from every test so far. Then roll back and ask PostgreSQL who we are (`current_user`). This guards the bug the tests found while this step was built: a rollback used to undo `SET ROLE`, and the connection quietly became the owner again (`db.py`).

@@ 500-502
Named as project **a1**: which projects own the sessions it can see, and which organisations it can see.

@@ 503-504
Named as organisation **A**: which projects it can see.

@@ 505-506
`finally` closes the engine even if something above fails, so a failing test doesn't leave connections open.

@@ 507-511
The verdicts. Still the restricted role; zero rows of anything with no tenant; project a1 sees only its own sessions and its own organisation; organisation A sees both its projects, and not b1.

@@ 514-517
**Test 2 — writing.** A tenant can't create or change another tenant's rows, and can't switch the protection off.

@@ 518-520
The same scene and the same restricted engine.

@@ 521-525
Named as **a1**, try to add a session belonging to **b1**. The database must refuse at commit with "new row violates **row-level security** policy". `pytest.raises(…, match=…)` passes only if that error, with that text, happens.

@@ 526-531
Named as **a1**, try to change b1's sessions: an `update` with a `where` that picks exactly them. `.returning(…)` asks the database to send back the ID of every row it changed. b1's rows are invisible to a1, so the update finds nothing to change.

@@ 532-533
After the commit, count sessions again in the same database session. The tenant was named with `set_config(…, true)`, for **one** transaction, and this is a new one: it sees nothing.

@@ 534-536
Could the restricted role simply turn the policies off? `ALTER TABLE … DISABLE ROW LEVEL SECURITY` is allowed only to a table's owner, so PostgreSQL answers "**must be owner** of table projects".

@@ 537-538
Close the engine, whatever happened.

@@ 539-540
The verdicts: no row changed, and nothing visible once the transaction had ended.

@@ 543-544
**Test 3 — through the API.** One website's key can't read another website's session.

@@ 545-548
Inside the usual harness, the first website creates a session. Then `seed_dev` makes a **second** organisation, project and key in the same database — a second customer.

@@ 549-554
Ask for the first website's session with the second website's key, and then with its own.

@@ 555-557
A foreign key gets the same `404 session_not_found` as a session that doesn't exist — it can't even learn that the session is there — while the owner reads it normally.

@@ 560
**Test 4 — no table forgotten.** The tests above prove that the policies work; this one proves that **every** table has them. A future migration that adds a table and forgets its policy would fail here, until someone either protects the table or decides, in this file, that it holds no customer's data.

@@ 561-567
Connect as the owner, and ask PostgreSQL's own catalogue. `pg_class` lists every table the database knows; the conditions keep ordinary tables (`relkind = 'r'`) in our `public` schema (`'public'::regnamespace` turns the schema's name into its internal ID) whose row-level security is **off** (`NOT relrowsecurity`). `connection.scalars` returns the first column of each row: the names. `set(…)` collects them, and the engine is closed.

@@ 569
The unprotected tables must be exactly the two allowed ones, no more and no fewer.

@@ 572-573
**`bearer_of`** — the `Authorization` header for a given key. The tests below use several keys, so `h.key` alone won't do.

@@ 576-579
**Idempotency.** Sending the same request twice with the same `Idempotency-Key` gets the first answer, not a second session.

@@ 580-585
The same request twice with one key; the same key with a *different* request; a key that is too short; and two requests with no key at all.

@@ 586-589
Look inside Valkey itself. `scan_iter("idem:*")` walks through every stored reply. Each must exist, and none may contain the client secret in readable form: the reply is sealed (`app/idempotency.py`), so a copy of Valkey reveals no secret.

@@ 590-593
Both requests succeeded, the second answer is **identical** to the first — the same session and the same client secret — and only the repeat carries `Idempotent-Replayed`.

@@ 594-598
The same key with a different request is refused (`422 idempotency_key_reused`). The short key is refused too — since step 6 by the pattern the API document states, so as a general `invalid_request` naming the header, before the API's own check runs. And without a key, two requests make two different sessions.

@@ 601-604
**Rate limits.** A key allowed a burst of 2 and almost no refill (one token every 100 seconds) makes three requests in a row.

@@ 605-607
Two get through, the third gets `429 rate_limited`, with a `Retry-After` of at least one second.

@@ 610-612
**Pagination.** Five sessions are listed two at a time.

@@ 613
Create five sessions, remembering their IDs in the order they were made.

@@ 614-621
Read the pages the way a client would: ask for 2, then keep asking `starting_after` the cursor of the last page until `has_more` is false. (`|` joins two dictionaries; with no cursor yet, the second one is empty.)

@@ 622
Ask for more than the largest allowed page.

@@ 623-627
All the listed IDs together: pages of 2, 2 and 1; exactly the five sessions, **newest first** (`reversed(made)`), none repeated, none missed; no `age_token` anywhere in the list; and the oversized page refused with `422`.

@@ 630-636
**Scopes.** A key with only `sessions:read` can't create a session (`403 insufficient_scope`), but can list them.

@@ 639-642
**Rotation and revocation.**

@@ 643-646
Rotate the harness's key with a one-hour grace period. The key id is characters 8 to 19 of the key.

@@ 647
During the grace period, the old key and its replacement both work.

@@ 648-650
Rotate the replacement with **no** grace at all, then try the key just replaced and its own replacement.

@@ 651-652
Revoke the newest key (`revoke_key` reports that it found one), and try it once more.

@@ 653-656
The verdicts: both keys worked during the grace period; a key whose grace has ended gets `401 api_key_expired`; its replacement works; a revoked key gets the plain `401 invalid_api_key`.

@@ 659-662
**Versioned policies.** A session keeps the policy version it started with, even after a new version is added.

@@ 663-665
Add version 1 of the project's own policy `shop_18`.

@@ 666
Create a session with it.

@@ 667-669
Add version 2, which allows only one face attempt.

@@ 670
Create another session, which gets version 2.

@@ 671
Start the **first** session's flow: its answer says how many attempts remain.

@@ 672
List the policies.

@@ 673-675
Three refusals to check: a custom policy named like a preset, one for age 19 (the model has no thresholds for it), and a session asking for a policy nobody made.

@@ 676-677
The two versions were numbered `shop_18@1` and `shop_18@2`, and each session names the version it got.

@@ 678
The first session still has **3** attempts — version 1's rules — although version 2, with only one, now exists.

@@ 679
The list shows both versions of the project's own policy, oldest first.

@@ 680-682
And the three refusals: `invalid_policy_name`, `policy_not_supported`, `unknown_policy`.

@@ 685-688
**Immutability.** Add one policy version through the API.

@@ 689-696
Then, as the API's own role, try to change it and to delete it with plain SQL. The migration gave the role only `SELECT` and `INSERT` on this table, so PostgreSQL answers "**permission denied**" to both: no bug in our code could rewrite the rules a past check followed. Close the engine at the end, whatever happened.

@@ 699-701
**The webhook tests (Phase 4).** `Receiver` — a website's webhook receiver, kept in memory: no network, no server.

@@ 703-704
The statuses it will answer with, in order, and every request it has received.

@@ 706-708
**`handle`** — record the request, and answer with the next status in line (`pop(0)` takes the first), or `200` once the list is used up.

@@ 711-712
**`deliverer`** — the delivery worker, set up as in production: as the tables' owner.

@@ 713-714
An owner engine, and an HTTP client whose **transport** is `httpx.MockTransport(receiver.handle)`: every request the worker sends is handed straight to the receiver's function instead of going over a network.

@@ 715
The development master key — the same one the API in the harness uses, so the worker can open the secrets the API sealed.

@@ 716
Return the worker and its engine (so the test can close it). The clock is `lambda: clock[0]`: a function reading a one-item list, so the test can move time forward by changing `clock[0]` — and test a 24-hour retry without waiting 24 hours.

@@ 719-723
**`pass_one_session`** — create a session, start it, and pass one face attempt: a session that has just completed.

@@ 726-729
**Test — a delivery.** A completed session reaches the website, signed so that the website can check it.

@@ 730
An empty receiver (it will answer `200`), and a clock.

@@ 731
The harness allows private addresses: the receiver's address is never really contacted.

@@ 732-734
Register an endpoint for completed sessions.

@@ 735
Complete one session: the event and its delivery are written in the same transaction.

@@ 736
Set the worker's clock just past now, so the delivery is due.

@@ 737-739
Run the worker once, then close its engine.

@@ 740-741
Read the endpoint's deliveries, and the list of endpoints.

@@ 742-743
The secret was shown once, at creation, with its `whsec_` prefix, and never again.

@@ 744
Exactly one delivery was sent, and it arrived.

@@ 745-750
The body is the completed event: it names the session and its outcome, it carries **no token**, and the `Dwarpal-Event-Id` header matches the event's ID.

@@ 751-754
Check the signature exactly as a receiver would: split the header into `t` and `v1`, recompute the HMAC of `"<t>.<body>"` with the secret, and compare in constant time (`compare_digest`).

@@ 755
The delivery is recorded as delivered, on its first attempt, with the receiver's `200`.

@@ 758-761
**Test — retries.** A failing receiver is retried on the schedule until the delivery is dead; then it can be replayed.

@@ 762
This receiver answers `500` eight times.

@@ 763-769
Register an endpoint, send it a **test event** (which goes to this endpoint whatever it subscribes to), and set the clock just past now.

@@ 770-773
Eight rounds. In each, the worker sends one delivery, and an immediate second run finds nothing due: the failure has pushed the next attempt into the future.

@@ 774-775
Read the delivery's state.

@@ 776-779
While it is still pending, measure the wait the worker chose, and move the clock forward to exactly that moment.

@@ 780
Replay the dead delivery.

@@ 781-782
With the clock at now, the worker sends it again — and the receiver, out of failures, answers `200`.

@@ 783-784
Close the engine and read the final state.

@@ 785
The test event was accepted (`202`, "accepted for later").

@@ 786
The waits were exactly the schedule: 1 minute, 5 minutes, 30 minutes, 2, 6, 12 and 24 hours.

@@ 787
After the eighth failure the delivery was dead, with the receiver's last `500` recorded.

@@ 788-789
Replaying put it back to pending with a fresh count, and it was then delivered.

@@ 792-797
**Test — the SSRF guard through the API.** With private addresses not allowed (the normal setting), an endpoint on `127.0.0.1` — this very computer — is refused.

@@ 798-800
So is an endpoint asking for an event type that doesn't exist.

@@ 801-802
`422 unsafe_webhook_url` and `422 unknown_event_type`.

@@ 805-810
**Test — introspection.** Pass a session and read its age token.

@@ 811-812
Seed a second website, with its own key.

@@ 814-816
**`ask`** — introspect a token with a given key. A function defined inside the test, because only this test needs it.

@@ 818-821
Ask four times: with the other website's key; with a **forged** token (its last four characters changed, which breaks the signature); and twice with the right key.

@@ 822-825
The other website and the forger both get only `{"active": false}`; the first genuine question gets `active` with the token's claims; the second gets `false` — a token is spent once introspected.

@@ 828-830
**Test — expiry is announced once.** A session lifetime of 0 seconds makes every new session expire at once.

@@ 831-833
Register an endpoint for expired sessions.

@@ 834-835
Create a session, and read it twice.

@@ 836
Read the endpoint's deliveries.

@@ 837-838
Both reads say `expired`, but there is exactly **one** delivery: the first read saved the change and its event together, and the second found nothing to change.

@@ 841-848
**`org_of`** — the organisation that owns a seeded project, read as the tables' owner: the audit log is kept per organisation.

@@ 851-852
**Test — the audit chain.** Real changes are chained in the log, and tampering of either kind is found.

@@ 853-858
Through the API: add a policy version, register a webhook endpoint, and delete it. With the key `seed_dev` created, that makes four audited actions.

@@ 859-862
The organisation's ID; an engine as the owner, and one as the API's role.

@@ 863
From here on, whatever happens, both engines are closed at the end (`try` … `finally`).

@@ 864-866
Read the organisation's entries, and verify the chain as it stands.

@@ 867-869
**The API can't rewrite history**: as the API's role, changing any entry is refused with "permission denied" — the role may only add entries (migration `0006`).

@@ 870-874
But someone with the **owner's** rights — a database administrator, or an attacker who stole that login — can. Change entry 2's facts (as if the policy had been for age 13) and verify again.

@@ 875-879
Put entry 2 back, then quietly **delete the last entry**, and verify once more.

@@ 880-882
Close both engines, whatever happened.

@@ 883-888
The four entries, in order: the key's creation, the policy version, the endpoint created, the endpoint deleted.

@@ 889-890
Changes made with the API key name it by its **id** (characters 8 to 19), and the key itself appears in no entry's facts.

@@ 891
Before any tampering: four entries, intact.

@@ 892
After the edit: broken, **at entry 2** — the exact entry that was changed.

@@ 893
After the deletion: broken at entry 4, the missing one. The chain itself still checks out, but the head (`audit_heads`) remembers that there should be four.

@@ 896-900
**Test — counting.** Pass two sessions.

@@ 901-902
Read the last week's counts, and ask for more than a year.

@@ 903-905
Two passes in total, in one row for today under `uk_osa_18`; and a request for 366 days refused with `422`.

@@ 908-912
**Test — the sweep and the purge.** Settings for calling the operator's command directly.

@@ 913-917
Sessions in this harness expire at once. Register an endpoint for expired sessions, and create a session that nobody will ever read.

@@ 918-919
Run the scheduled jobs, then read the endpoint's deliveries.

@@ 920-925
As the owner, give this project a retention of **one day**.

@@ 926-927
Run the jobs as if it were 23 hours later: within the day, so the session is kept.

@@ 928-929
Run them as if it were two days later: past the day, so it is purged.

@@ 930
Read the project's counts.

@@ 931-933
Verify every organisation's audit chain.

@@ 934-935
The sweep expired at least one session (other tests leave theirs too), and the website was told, by one delivery, although nobody read the session.

@@ 936-938
After 23 hours nothing of this project's was purged and the session still exists; after two days it is gone (`404`).

@@ 939
The count of one expired session outlives the session itself.

@@ 940
And this organisation's audit chain is intact.

@@ 943-945
**The console tests (Phase 4, step 2).** The console's address; settings for its tests — a cookie that may travel over plain HTTP, and a generous sign-in allowance, because every test signs in from the same address; and a throwaway password.

@@ 948-950
**`person`** — a separate browser for one person: a new client on the same transport, with its own cookie jar, so several people can be signed in at once in one test.

@@ 953-957
**`sign_up`** — create an account and organisation through the console, insist it worked, and return the answer (which includes the CSRF token).

@@ 960-961
**`unique`** — a fresh e-mail address each time, so tests sharing the database never collide.

@@ 964-968
**Test — signing up, in and out.**

@@ 969-971
Sign up, and look at the cookie the browser received.

@@ 972-977
Try to sign up again with the same address, and with a five-character password.

@@ 978-980
Sign in with a wrong password; with an address nobody has; and correctly, typed in capitals.

@@ 981-984
Sign out without the CSRF token, then with it; then ask who is signed in.

@@ 985-986
The new person owns the new organisation; the cookie is a long, unguessable token.

@@ 987-988
The repeated address and the weak password are refused.

@@ 989-990
A wrong password and an unknown account get the **same** status and the **same** sentence: an attacker can't use sign-in to find out who has an account.

@@ 991
Addresses match whatever their capitals.

@@ 992-994
Signing out needs the CSRF token like any change; with it, the session ends, and the cookie no longer works.

@@ 997-999
**Test — CSRF.**

@@ 1000-1004
Sign up, then try a change three ways: with a guessed token, with the real token but from another site's origin, and genuinely.

@@ 1005-1007
The guess fails (`csrf_failed`), another origin fails (`bad_origin`), and only the genuine request works.

@@ 1010-1013
**Test — one-time codes.**

@@ 1014-1015
Sign up, and ask to set up one-time codes: the answer holds the secret and its `otpauth://` address.

@@ 1016-1020
Work out the current 30-second step. A wrong code is refused; the right one, computed from the secret as an authenticator app would, switches codes on.

@@ 1021-1022
Sign in with only the password.

@@ 1023-1025
Sign in with the **next** step's code — what a phone whose clock runs a little fast shows — and then try exactly the same code again.

@@ 1026-1030
The offer was a proper `otpauth://` address; the wrong code failed and the right one worked; a password alone is no longer enough; the code worked once — and a second time it is refused.

@@ 1033-1035
**Test — roles.** Three addresses: an owner, an analyst and a developer.

@@ 1036-1042
Inside one harness, four browsers — the fourth for an outsider. `async with ( … ):` opens several at once, and closes them all at the end.

@@ 1043-1045
The owner signs up; note the organisation and the owner's CSRF token.

@@ 1046-1049
The analyst and the developer sign up (each gets an organisation of their own), and so does the outsider.

@@ 1050-1054
The owner adds the analyst and the developer to the owner's organisation, each with their role.

@@ 1055-1060
As the tables' owner, find the organisation's project, and build the address for creating its API keys.

@@ 1061-1063
The analyst and the developer each try to create a read-only key.

@@ 1064-1068
The developer tries to make the analyst an owner.

@@ 1069-1073
The analyst lists the members; the outsider tries to; the developer's new key is used on the API; and the owner and the analyst read the audit log.

@@ 1074-1076
The analyst may not create keys (`403 forbidden_for_role`); the developer may; and the developer may not manage members.

@@ 1077-1078
The analyst sees all three members; the outsider gets `404`, exactly as if the organisation didn't exist.

@@ 1079
The key made in the console works on the API.

@@ 1080-1083
The owner's audit log, oldest first: the organisation's creation, two members added, a key created; the chain is intact; and the key itself appears nowhere in it.

@@ 1084
The analyst may not read the audit log.

@@ 1087-1089
**Test — sign-in limits.** At most 2 attempts at once, then one every two minutes.

@@ 1090-1092
A browser at an address of its own. `ASGITransport(…, client=…)` sets the address the API sees the request coming from; `192.0.2.x` is a range reserved for documentation and tests. Without it, every other test's sign-ins would already have used up this address's allowance.

@@ 1093-1098
Sign up, then try a wrong password three times.

@@ 1099-1100
Two ordinary refusals, then `429 too_many_sign_ins`, with a `Retry-After` of at least a second.

@@ 1103-1105
**The contract test (Phase 4, step 6).** `live_api` — Schemathesis sends real HTTP, so the API runs as a real server for these tests. `scope="module"` starts it once for the whole file rather than once per test.

@@ 1106-1114
Its settings: the test databases; webhook addresses never looked up (the fuzzer invents host names); a cookie allowed over plain HTTP; and limits so high that the fuzzer's many requests aren't simply refused with `429`.

@@ 1115
Seed a project and a key for it.

@@ 1116
A uvicorn server for the API, on `127.0.0.1` and **port 0**, which asks the operating system for any free port, so the test never collides with something already running.

@@ 1117-1118
Run it in a background **thread**: `daemon=True` means the thread won't keep Python alive if the tests end without stopping it.

@@ 1119-1120
Wait, a twentieth of a second at a time, until the server says it has started.

@@ 1121
Read which port it was given.

@@ 1122
Hand the tests the server's address and the key.

@@ 1123-1124
Afterwards, ask the server to stop, and wait up to ten seconds for its thread to finish.

@@ 1127-1129
**`live_document`** — Schemathesis reads the API's document from the running server, exactly as a website's developer would.

@@ 1132
`contract` — tells Schemathesis to take the document from that fixture. A document known only once the server runs can't be read while pytest is still collecting tests, so it is fetched lazily, from the fixture.

@@ 1135-1136
`@contract.parametrize()` turns the test into one sub-test per operation in the document: 31 of them. `@settings` gives each 25 generated requests, no time limit per request (`deadline=None`), and turns off Hypothesis's health checks, which would complain that each example is slow (it is a real HTTP request).

@@ 1137-1138
**Test — the contract.** For each generated request (`case`):

@@ 1139-1141
Every check but one. `positive_data_acceptance` insists that a request the document allows must succeed. But some of the API's rules depend on data, not just shape: whether the age model is calibrated for an age, whether an address is among the project's allowed origins. Refusing such a request with `422` is correct.

@@ 1142
Send it to the server with the website's key, and check the answer: never a server error, a status code the document lists for this operation, a content type it lists, a body that matches the schema for that status, and the headers HTTP requires (such as `Allow` on a `405`). Any failure prints the exact request, as a `curl` command to reproduce it.

@@ 1145-1147
**Test — no drift.** `docs/api/openapi.json` is what websites read; the docstring says how to refresh it.

@@ 1148
The file must equal, byte for byte, what the code produces now. A change to the API without refreshing the document fails here.
