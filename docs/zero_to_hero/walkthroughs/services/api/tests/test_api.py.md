---
fingerprint: ac9d5cfcb8b51788
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

@@ 5-19
Standard-library tools: `asyncio`, `base64` (a test master key), `hashlib` and `hmac` (to check a webhook's signature as a receiver would), `json`, `logging`, `threading` and `time` (to run a real server beside the tests), `uuid` (fresh IDs), the iterator types for fixtures, `asynccontextmanager`, `dataclass` and `replace` (a copy of a dataclass with one field changed), `UTC`, `datetime` and `timedelta` (a length of time, for key rotation and webhook retries), `Path`, `Any` — and `Literal`, for the harness's liveness option (Phase 3).

@@ 21-25
OpenCV and NumPy (to make a test picture), the `docker` client (to ask whether Docker is running), `httpx` (to call the apps) and `pytest`.

@@ 26-27
`schemathesis`, the contract tester (step 6), and `uvicorn`, the server program, to serve the API on a real port for it.

@@ 28-29
Alembic's `compare_metadata` and `MigrationContext`, for the drift test at the end.

@@ 30
Hypothesis's `settings` and `HealthCheck`, to tell Schemathesis (which uses Hypothesis inside) how many requests to make per operation.

@@ 31-32
joserfc's `jwt` and `KeySet`: the tests verify tokens exactly as a website would.

@@ 33
Pydantic's `SecretStr`, to give production settings a master key.

@@ 34
An async Valkey client, so a test can look at what the API stored there (Phase 4).

@@ 35-36
Schemathesis's `Case` — one generated request — and `positive_data_acceptance`, the one check the contract test leaves out (explained there).

@@ 37
SQLAlchemy's query builders, for the Phase 4 tests: `delete` (to remove a row on purpose), `select` and `func` (to count rows), `text` (raw SQL), and `update` (to try changing rows).

@@ 38-40
SQLAlchemy types: `Connection` for the drift test, `DBAPIError` — the error SQLAlchemy raises when the database itself refuses a statement — and `create_async_engine`.

@@ 41-43
Testcontainers: a ready-made PostgreSQL container, a general container for Valkey, and a **wait strategy** — "the container is ready when this line appears in its log".

@@ 45-73
The code under test: the database helpers (`make_engine`, `make_sessions`, `tenant`), the master key, the table catalogue and the fifteen tables that belong to tenants, the audit and maintenance modules, the delivery worker, the CLI's `API_DOCUMENT`, `api_document`, `maintain`, `migrate`, `seed_dev`, `rotate_key` and `revoke_key`, both apps' factories (renamed with `as` so the two `create_app`s can't be confused), the ID and one-time-code helpers, both settings classes, and the contracts for frames, challenges and browser signals. The brackets let one `import` span several lines.

@@ 75-76
The repository folder, and the public-domain portrait from the vision library's tests — a real face, so the real face detector finds it.

@@ 77
The demo shop's return address, which the seeded project allows.

@@ 80-83
**`blank_frame`** — a plain grey 320 × 240 picture, saved as JPEG: a valid image with no face in it. `np.full` fills an array with one value (128, middle grey). `cv2.imencode` returns two values — whether it worked, and the encoded bytes.

@@ 86-87
**The `databases` fixture.** A **fixture** is something a test needs, prepared by pytest and passed in by name. `scope="session"` means it is built **once for the whole test run** and shared: starting two containers takes seconds, so doing it once matters. It provides the two addresses.

@@ 88-91
Is Docker running? Ask it, giving up after 5 seconds. If not, skip every test that needs this fixture, with the reason.

@@ 92-97
A PostgreSQL container, using exactly the image the local Compose file uses. The password is a throwaway for a throwaway container; the comment explains why the linter's warning about a hard-coded password doesn't apply.

@@ 98-102
A Valkey container, with its port exposed, considered ready when Valkey logs `Ready to accept connections`.

@@ 103-104
Start both. Each `start()` waits until its container is ready.

@@ 105-107
Docker maps each container's port to a random free port on this computer, so the addresses are built from what the containers report. Random ports mean tests never clash with a database already running locally.

@@ 108
Apply the migrations — the same function a developer runs from the command line.

@@ 109
`yield` hands the addresses to the tests. Everything after it runs when the whole test run is over…

@@ 110-111
…stopping (and removing) both containers.

@@ 114-118
**`Harness`** — what each test gets to work with: an HTTP client connected to the API, the seeded project's test API key, and the project's public ID.

@@ 119
`transport` — the in-process connection to the API (step 2): a test can open more clients on it, one per person, each with its own cookies.

@@ 122-130
**`harness`** — sets up a complete, fresh API for one test. Its options: the age the stand-in model should "see" (30 by default — clearly an adult), whether the seeded key is live, how liveness gets its evidence (Phase 3) — `"labels"` by default, because the tests' portrait is a still photo that can't turn its head — the seeded key's scopes (every scope by default), and any other API settings to change (`**overrides`: extra named arguments, collected into a dict), such as a smaller device budget or rate limit.

@@ 131
Unpack the two database addresses.

@@ 132
Create an inference app whose stand-in model reports the chosen age, with the chosen liveness evidence.

@@ 133-137
Start the inference app's lifespan (loading its face detector), and open an HTTP client wired to it through **`ASGITransport`** — httpx calls the app's Python code directly, with no network and no server. One `async with` with two parts, in brackets, opens both and closes both.

@@ 138-139
Create the API with test settings — the test databases' addresses, plus any overrides — and the in-process inference client. The settings' default `database_role` applies, so **every test in this file runs as the restricted role**, under row-level security, exactly as the API will in production.

@@ 140
Run the API's lifespan: connect, load the signing key, read the manifest.

@@ 141
Seed a project and a key, exactly as a developer would with `seed-dev`, with the scopes asked for.

@@ 142-144
Open a client wired to the API the same way, and hand the harness to the test, with the transport. When the test ends, every `async with` closes in reverse order.

@@ 147-150
**`create`** — create a session as the demo shop would, with the API key, plus any extra headers (`headers_extra`, such as an `Idempotency-Key`). Any keyword arguments replace the body's defaults, so a test can write `create(h, policy="anything_goes")`.

@@ 153-154
**`secret`** — the body for `/start`: the session's client secret.

@@ 157-160
**`start`** — start the flow and return the `Authorization` header with the flow token, ready for the next calls. The `assert` includes the response text, so if starting fails, the test report shows why.

@@ 163-164
**`following`** (Phase 3) — the labels for a burst whose head follows the given poses: frontal **baseline** frames first, then one frame per pose, in order. With 6 frames and 3 poses: baseline, baseline, baseline, then the three poses.

@@ 165
`["baseline"] * n` makes a list of n copies; `+ poses` adds the poses after them.

@@ 166
One `FrameMeta` per phase, numbered from 0, taken 120 ms apart. `enumerate` gives each item with its position.

The comment at the end, `# type: ignore[arg-type]`, silences one complaint of the type checker: it can't know that the plain texts in `poses` are valid `Phase` names. Pydantic checks them anyway when the `FrameMeta` is created.

@@ 169-177
**`attempt`** — one complete face attempt, as the verify page makes it. Besides the frames, three optional inputs let a test play an attacker (Phase 3):

- `poses` — label the frames with these poses instead of the ones asked for;
- `signals` — report these browser signals;
- `claimed` — put a challenge of the browser's own choosing into the request.

@@ 178-179
The docstring says the same, in short.

@@ 180
Get a challenge — the server picks its random poses and colours.

@@ 181-183
Label the frames: by default they follow the challenge's own poses (an honest attempt), otherwise the poses the test gave. A challenge has 3 or 4 poses, so first make sure there are enough frames — at least 3 frontal ones, then one per pose — by repeating the last frame as many times as needed (`frames[-1:] * n`: a list of the last frame, `n` times; `max(0, …)` keeps `n` from going negative).

@@ 184
Describe the attempt: the frames' labels, the signals (normal ones unless given), and any claimed challenge.

@@ 185-187
Package the frames as files `frame_0`, `frame_1`, …, add the description and the challenge's ID, and upload everything as a multipart form.

@@ 190-191
**The main story: an adult passes, and the website can verify the token.** `@pytest.mark.anyio` lets pytest run an `async` test function.

@@ 192-198
Create, start, attempt with six portraits — the stand-in model says 30, so it passes — then finish: the redirect goes back to the shop with the session's ID.

@@ 199
Start the flow *again*, as if the person reloaded the page afterwards.

@@ 200-202
As the shop's server: read the result with the API key, and fetch the public keys.

@@ 203-204
The reloaded page sees the completed session and its outcome — no error for the person.

@@ 205-206
The result says completed, and passed.

@@ 207
**Verify the token** exactly as a website would: with the published key set, accepting only Ed25519. If the signature didn't match, this line would raise an error.

@@ 208-213
The token is an age token, says pass, says `age_over_18: true` (the literal `True`, checked with `is`), and is addressed to this project, about this session, in test mode.

@@ 214
**No age inside.** None of these names appears among the claims: the set of forbidden names and the set of claim names have nothing in common (`&` is set intersection; an empty set counts as false).

@@ 217-229
**A clear child is refused, unmistakably.** With the stand-in model at 12, the attempt fails, and the signed token says `outcome: fail` *and* `age_over_18: false` — so even a website that read only the age claim would refuse entry.

@@ 232-238
**A teenager near the limit must use a stronger check.** At 16, the probability of being 18 or over is neither high enough to pass nor low enough to fail, so the answer is step up, with the reason `age_uncertain`.

@@ 241-253
**Poor frames: retry, retry, then step up.** Three attempts with blank grey frames: each finds no face. The first two are retries — the first saying `no_face` and that 2 attempts remain — and the third becomes a step-up. The session waits for a stronger check, and has no token.

@@ 256-271
**Credentials are checked, and errors are problem details.** No API key at all: `401`, with the problem-details media type, the stable code, the type reference, and a request ID that matches the response header. A wrong client secret and a missing flow token each get their own code.

@@ 274-278
**Each request is logged once, with its ID, and never with secrets.** `caplog` is pytest's log-capturing fixture; `set_level` makes it collect `INFO` lines from `dwarpal.api`.

@@ 279-280
Create one session. (Setting up the harness makes no HTTP requests, so this is the only request.)

@@ 281-284
Exactly one request log line, with the right method, path and status, and the same ID the response carried. `vars(record)` reads a log record's fields as a dict.

@@ 285-286
Neither the API key nor the new client secret appears anywhere in the captured logs.

@@ 289-303
**A challenge can be used only once.** The same challenge, sent twice: the first attempt is accepted, the second gets `409 challenge_invalid`.

@@ 306-314
**A session gets a limited number of challenges.** Seven requests in a row: six are granted (3 attempts × 2), the seventh gets `429 too_many_challenges`.

@@ 317-320
**Oversized and unmeasured bodies are refused before they are read.** `stream` is an async generator: given as a body, it makes httpx send the request in chunks of unknown total size.

@@ 322-325
A JSON body of about 100 KB (over the 64 KiB limit), and a chunked body.

@@ 326-330
`413 request_too_large` — still with a request ID — and `411 length_required`.

@@ 333-345
**Sessions refuse foreign return addresses, unknown policies, and live mode with a stand-in model.** A return address on another website, a policy that doesn't exist, and a session created with a *live* key while the model is uncalibrated: each gets its own code.

@@ 348-358
**Discovery and readiness.** The configuration document names Ed25519 and admits the model is uncalibrated; the key set may be cached for 5 minutes and holds only Ed25519 keys; and `/readyz` reports both databases as `ok`.

@@ 361
**The drift test: the migrations build exactly the tables the code describes.** It is not `async`, so it starts the async engine itself (line 305).

@@ 362-363
**`differences`** — Alembic's `compare_metadata` compares the real database (migrated by the fixture) with `METADATA`, the tables described in `tables.py`, and lists every difference: a missing table, an extra column, a different type.

@@ 365-370
**`check`** — connect to the test database and run the comparison through `run_sync`, because Alembic's comparison code isn't async (as in `env.py`).

@@ 372
The list of differences must be **empty**. If someone adds a column to `tables.py` but forgets the migration — or the other way round — this test fails, long before a real database meets the mismatch.

@@ 375-377
**Red team, from here on** (Phase 3): tests that play the attacker. **Red-teaming** means attacking your own system on purpose, to find its weaknesses before someone else does.

The first: **a printed photo**. The "person" is the still test portrait, and here liveness measures the images for real (`liveness="images"`).

@@ 378-381
Two attempts with six identical portraits. The photo looks straight ahead throughout — it can't turn left, right or up when asked.

@@ 382-383
The first attempt gets a retry, with the vague `liveness_check_failed` (a real person may just have been slow). The second gets **rejected** — and from outside the reason is only `verification_failed`, which doesn't even say liveness was involved.

@@ 386-391
**Poses in the wrong order.** Labels mode is on, so the frames' labels are believed — but the attacker labels them `turn_right` three times, whatever the challenge asked. A challenge never repeats a pose twice in a row, so this can never match it.

@@ 392
Caught: retry, `liveness_check_failed`.

@@ 395-397
**A challenge claimed by the browser.** The attacker sends an easy challenge of its own choosing — one pose, `turn_left`, two colours.

@@ 398-401
And four frames that would satisfy *that* easy challenge: three baseline frames, then `turn_left`.

@@ 402
Caught: the server judged the frames against the challenge it **issued** (three random poses), not the claimed one, so the pose check fails.

@@ 405-412
**Automation and virtual cameras.** Two fresh sessions; in each the browser honestly reports one warning sign — a program driving the browser, or a virtual camera. The frames themselves are fine and the person is a clear adult.

@@ 413
Both go to **step up** with `liveness_uncertain`: not passed on a face that may have been injected, but not rejected either, because these signs can have innocent causes. `[x] * 2` is a list of two copies of `x`.

@@ 416-419
**One device gets only so many challenges, however many sessions it starts.**

@@ 420-423
A helper that creates a fresh session, starts it, and asks for a challenge with a given device ID — the flow token's headers plus `X-Dwarpal-Device` (`|` joins two dicts).

@@ 425-427
With a budget of 2 challenges an hour: three requests from the same device, each in a new session, then one from a different device.

@@ 428-430
The same device gets two challenges and then `429 too_many_attempts` — new sessions don't reset its budget; the other device is unaffected.

@@ 433-449
**The tenancy tests (Phase 4).** `TENANT_TABLES` — the fifteen tables whose rows belong to a tenant: from organisations to the audit log, the daily counts, the console's users and their memberships. (The signing keys belong to Dwarpal itself, not to any customer.)

@@ 450
`NOT_TENANT_DATA` — the only two tables allowed to have no row-level security: Alembic's migration history and Dwarpal's own signing keys. Neither belongs to any customer.

@@ 453-470
**`a_session`** — a minimal verification session for a given project, made directly as a table row rather than through the API: just enough to be a row worth hiding or showing. It follows a preset (`policy_version=0`). `bytes(32)` is 32 zero bytes, standing in for the client secret's digest.

@@ 473-475
**`two_organisations`** — the scene for the tests, built as the tables' **owner**, whom the policies don't bind: organisation A with projects a1 and a2, organisation B with project b1, and one verification session in each project.

@@ 476-477
The time, and a fresh random ID for each name. `uuid.uuid4()` is fine here: these IDs only need to be different from everything else in the shared test database.

@@ 478-487
An engine with **no role** — the owner. Add both organisations, then (after a `flush`, so the foreign keys find them) the three projects, then one session per project, and commit. `add_all` adds a whole list at once.

@@ 488-489
Close the engine, and return the IDs by name, so each test can say `made["a1"]`.

@@ 492-493
**Test 1 — reading.** Each tenant sees only its own rows, and a unit of work that names no tenant sees nothing at all.

@@ 494-496
Build the scene, then open an engine as the API does: as `dwarpal_app`.

@@ 497-501
First, a unit of work that names **no** tenant counts the rows of every tenant table — expected: zero everywhere, although this database holds rows from every test so far. Then roll back and ask PostgreSQL who we are (`current_user`). This guards the bug the tests found while this step was built: a rollback used to undo `SET ROLE`, and the connection quietly became the owner again (`db.py`).

@@ 502-504
Named as project **a1**: which projects own the sessions it can see, and which organisations it can see.

@@ 505-506
Named as organisation **A**: which projects it can see.

@@ 507-508
`finally` closes the engine even if something above fails, so a failing test doesn't leave connections open.

@@ 509-513
The verdicts. Still the restricted role; zero rows of anything with no tenant; project a1 sees only its own sessions and its own organisation; organisation A sees both its projects, and not b1.

@@ 516-519
**Test 2 — writing.** A tenant can't create or change another tenant's rows, and can't switch the protection off.

@@ 520-522
The same scene and the same restricted engine.

@@ 523-527
Named as **a1**, try to add a session belonging to **b1**. The database must refuse at commit with "new row violates **row-level security** policy". `pytest.raises(…, match=…)` passes only if that error, with that text, happens.

@@ 528-533
Named as **a1**, try to change b1's sessions: an `update` with a `where` that picks exactly them. `.returning(…)` asks the database to send back the ID of every row it changed. b1's rows are invisible to a1, so the update finds nothing to change.

@@ 534-535
After the commit, count sessions again in the same database session. The tenant was named with `set_config(…, true)`, for **one** transaction, and this is a new one: it sees nothing.

@@ 536-538
Could the restricted role simply turn the policies off? `ALTER TABLE … DISABLE ROW LEVEL SECURITY` is allowed only to a table's owner, so PostgreSQL answers "**must be owner** of table projects".

@@ 539-540
Close the engine, whatever happened.

@@ 541-542
The verdicts: no row changed, and nothing visible once the transaction had ended.

@@ 545-546
**Test 3 — through the API.** One website's key can't read another website's session.

@@ 547-550
Inside the usual harness, the first website creates a session. Then `seed_dev` makes a **second** organisation, project and key in the same database — a second customer.

@@ 551-556
Ask for the first website's session with the second website's key, and then with its own.

@@ 557-559
A foreign key gets the same `404 session_not_found` as a session that doesn't exist — it can't even learn that the session is there — while the owner reads it normally.

@@ 562
**Test 4 — no table forgotten.** The tests above prove that the policies work; this one proves that **every** table has them. A future migration that adds a table and forgets its policy would fail here, until someone either protects the table or decides, in this file, that it holds no customer's data.

@@ 563-569
Connect as the owner, and ask PostgreSQL's own catalogue. `pg_class` lists every table the database knows; the conditions keep ordinary tables (`relkind = 'r'`) in our `public` schema (`'public'::regnamespace` turns the schema's name into its internal ID) whose row-level security is **off** (`NOT relrowsecurity`). `connection.scalars` returns the first column of each row: the names. `set(…)` collects them, and the engine is closed.

@@ 571
The unprotected tables must be exactly the two allowed ones, no more and no fewer.

@@ 574-575
**`bearer_of`** — the `Authorization` header for a given key. The tests below use several keys, so `h.key` alone won't do.

@@ 578-581
**Idempotency.** Sending the same request twice with the same `Idempotency-Key` gets the first answer, not a second session.

@@ 582-587
The same request twice with one key; the same key with a *different* request; a key that is too short; and two requests with no key at all.

@@ 588-591
Look inside Valkey itself. `scan_iter("idem:*")` walks through every stored reply. Each must exist, and none may contain the client secret in readable form: the reply is sealed (`app/idempotency.py`), so a copy of Valkey reveals no secret.

@@ 592-595
Both requests succeeded, the second answer is **identical** to the first — the same session and the same client secret — and only the repeat carries `Idempotent-Replayed`.

@@ 596-600
The same key with a different request is refused (`422 idempotency_key_reused`). The short key is refused too — since step 6 by the pattern the API document states, so as a general `invalid_request` naming the header, before the API's own check runs. And without a key, two requests make two different sessions.

@@ 603-606
**Rate limits.** A key allowed a burst of 2 and almost no refill (one token every 100 seconds) makes three requests in a row.

@@ 607-609
Two get through, the third gets `429 rate_limited`, with a `Retry-After` of at least one second.

@@ 612-614
**Pagination.** Five sessions are listed two at a time.

@@ 615
Create five sessions, remembering their IDs in the order they were made.

@@ 616-623
Read the pages the way a client would: ask for 2, then keep asking `starting_after` the cursor of the last page until `has_more` is false. (`|` joins two dictionaries; with no cursor yet, the second one is empty.)

@@ 624
Ask for more than the largest allowed page.

@@ 625-629
All the listed IDs together: pages of 2, 2 and 1; exactly the five sessions, **newest first** (`reversed(made)`), none repeated, none missed; no `age_token` anywhere in the list; and the oversized page refused with `422`.

@@ 632-638
**Scopes.** A key with only `sessions:read` can't create a session (`403 insufficient_scope`), but can list them.

@@ 641-644
**Rotation and revocation.**

@@ 645-648
Rotate the harness's key with a one-hour grace period. The key id is characters 8 to 19 of the key.

@@ 649
During the grace period, the old key and its replacement both work.

@@ 650-652
Rotate the replacement with **no** grace at all, then try the key just replaced and its own replacement.

@@ 653-654
Revoke the newest key (`revoke_key` reports that it found one), and try it once more.

@@ 655-658
The verdicts: both keys worked during the grace period; a key whose grace has ended gets `401 api_key_expired`; its replacement works; a revoked key gets the plain `401 invalid_api_key`.

@@ 661-664
**Versioned policies.** A session keeps the policy version it started with, even after a new version is added.

@@ 665-667
Add version 1 of the project's own policy `shop_18`.

@@ 668
Create a session with it.

@@ 669-671
Add version 2, which allows only one face attempt.

@@ 672
Create another session, which gets version 2.

@@ 673
Start the **first** session's flow: its answer says how many attempts remain.

@@ 674
List the policies.

@@ 675-677
Three refusals to check: a custom policy named like a preset, one for age 19 (the model has no thresholds for it), and a session asking for a policy nobody made.

@@ 678-679
The two versions were numbered `shop_18@1` and `shop_18@2`, and each session names the version it got.

@@ 680
The first session still has **3** attempts — version 1's rules — although version 2, with only one, now exists.

@@ 681
The list shows both versions of the project's own policy, oldest first.

@@ 682-684
And the three refusals: `invalid_policy_name`, `policy_not_supported`, `unknown_policy`.

@@ 687-690
**Immutability.** Add one policy version through the API.

@@ 691-698
Then, as the API's own role, try to change it and to delete it with plain SQL. The migration gave the role only `SELECT` and `INSERT` on this table, so PostgreSQL answers "**permission denied**" to both: no bug in our code could rewrite the rules a past check followed. Close the engine at the end, whatever happened.

@@ 701-703
**The webhook tests (Phase 4).** `Receiver` — a website's webhook receiver, kept in memory: no network, no server.

@@ 705-706
The statuses it will answer with, in order, and every request it has received.

@@ 708-710
**`handle`** — record the request, and answer with the next status in line (`pop(0)` takes the first), or `200` once the list is used up.

@@ 713-714
**`deliverer`** — the delivery worker, set up as in production: as the tables' owner.

@@ 715-716
An owner engine, and an HTTP client whose **transport** is `httpx.MockTransport(receiver.handle)`: every request the worker sends is handed straight to the receiver's function instead of going over a network.

@@ 717
The development master key — the same one the API in the harness uses, so the worker can open the secrets the API sealed.

@@ 718
Return the worker and its engine (so the test can close it). The clock is `lambda: clock[0]`: a function reading a one-item list, so the test can move time forward by changing `clock[0]` — and test a 24-hour retry without waiting 24 hours.

@@ 721-725
**`pass_one_session`** — create a session, start it, and pass one face attempt: a session that has just completed.

@@ 728-731
**Test — a delivery.** A completed session reaches the website, signed so that the website can check it.

@@ 732
An empty receiver (it will answer `200`), and a clock.

@@ 733
The harness allows private addresses: the receiver's address is never really contacted.

@@ 734-736
Register an endpoint for completed sessions.

@@ 737
Complete one session: the event and its delivery are written in the same transaction.

@@ 738
Set the worker's clock just past now, so the delivery is due.

@@ 739-741
Run the worker once, then close its engine.

@@ 742-743
Read the endpoint's deliveries, and the list of endpoints.

@@ 744-745
The secret was shown once, at creation, with its `whsec_` prefix, and never again.

@@ 746
Exactly one delivery was sent, and it arrived.

@@ 747-752
The body is the completed event: it names the session and its outcome, it carries **no token**, and the `Dwarpal-Event-Id` header matches the event's ID.

@@ 753-756
Check the signature exactly as a receiver would: split the header into `t` and `v1`, recompute the HMAC of `"<t>.<body>"` with the secret, and compare in constant time (`compare_digest`).

@@ 757
The delivery is recorded as delivered, on its first attempt, with the receiver's `200`.

@@ 760-763
**Test — retries.** A failing receiver is retried on the schedule until the delivery is dead; then it can be replayed.

@@ 764
This receiver answers `500` eight times.

@@ 765-771
Register an endpoint, send it a **test event** (which goes to this endpoint whatever it subscribes to), and set the clock just past now.

@@ 772-775
Eight rounds. In each, the worker sends one delivery, and an immediate second run finds nothing due: the failure has pushed the next attempt into the future.

@@ 776-777
Read the delivery's state.

@@ 778-781
While it is still pending, measure the wait the worker chose, and move the clock forward to exactly that moment.

@@ 782
Replay the dead delivery.

@@ 783-784
With the clock at now, the worker sends it again — and the receiver, out of failures, answers `200`.

@@ 785-786
Close the engine and read the final state.

@@ 787
The test event was accepted (`202`, "accepted for later").

@@ 788
The waits were exactly the schedule: 1 minute, 5 minutes, 30 minutes, 2, 6, 12 and 24 hours.

@@ 789
After the eighth failure the delivery was dead, with the receiver's last `500` recorded.

@@ 790-791
Replaying put it back to pending with a fresh count, and it was then delivered.

@@ 794-799
**Test — the SSRF guard through the API.** With private addresses not allowed (the normal setting), an endpoint on `127.0.0.1` — this very computer — is refused.

@@ 800-802
So is an endpoint asking for an event type that doesn't exist.

@@ 803-804
`422 unsafe_webhook_url` and `422 unknown_event_type`.

@@ 807-812
**Test — introspection.** Pass a session and read its age token.

@@ 813-814
Seed a second website, with its own key.

@@ 816-818
**`ask`** — introspect a token with a given key. A function defined inside the test, because only this test needs it.

@@ 820-823
Ask four times: with the other website's key; with a **forged** token (its last four characters changed, which breaks the signature); and twice with the right key.

@@ 824-827
The other website and the forger both get only `{"active": false}`; the first genuine question gets `active` with the token's claims; the second gets `false` — a token is spent once introspected.

@@ 830-832
**Test — expiry is announced once.** A session lifetime of 0 seconds makes every new session expire at once.

@@ 833-835
Register an endpoint for expired sessions.

@@ 836-837
Create a session, and read it twice.

@@ 838
Read the endpoint's deliveries.

@@ 839-840
Both reads say `expired`, but there is exactly **one** delivery: the first read saved the change and its event together, and the second found nothing to change.

@@ 843-850
**`org_of`** — the organisation that owns a seeded project, read as the tables' owner: the audit log is kept per organisation.

@@ 853-854
**Test — the audit chain.** Real changes are chained in the log, and tampering of either kind is found.

@@ 855-860
Through the API: add a policy version, register a webhook endpoint, and delete it. With the key `seed_dev` created, that makes four audited actions.

@@ 861-864
The organisation's ID; an engine as the owner, and one as the API's role.

@@ 865
From here on, whatever happens, both engines are closed at the end (`try` … `finally`).

@@ 866-868
Read the organisation's entries, and verify the chain as it stands.

@@ 869-871
**The API can't rewrite history**: as the API's role, changing any entry is refused with "permission denied" — the role may only add entries (migration `0006`).

@@ 872-876
But someone with the **owner's** rights — a database administrator, or an attacker who stole that login — can. Change entry 2's facts (as if the policy had been for age 13) and verify again.

@@ 877-881
Put entry 2 back, then quietly **delete the last entry**, and verify once more.

@@ 882-884
Close both engines, whatever happened.

@@ 885-890
The four entries, in order: the key's creation, the policy version, the endpoint created, the endpoint deleted.

@@ 891-892
Changes made with the API key name it by its **id** (characters 8 to 19), and the key itself appears in no entry's facts.

@@ 893
Before any tampering: four entries, intact.

@@ 894
After the edit: broken, **at entry 2** — the exact entry that was changed.

@@ 895
After the deletion: broken at entry 4, the missing one. The chain itself still checks out, but the head (`audit_heads`) remembers that there should be four.

@@ 898-902
**Test — counting.** Pass two sessions.

@@ 903-904
Read the last week's counts, and ask for more than a year.

@@ 905-907
Two passes in total, in one row for today under `uk_osa_18`; and a request for 366 days refused with `422`.

@@ 910-914
**Test — the sweep and the purge.** Settings for calling the operator's command directly.

@@ 915-919
Sessions in this harness expire at once. Register an endpoint for expired sessions, and create a session that nobody will ever read.

@@ 920-921
Run the scheduled jobs, then read the endpoint's deliveries.

@@ 922-927
As the owner, give this project a retention of **one day**.

@@ 928-929
Run the jobs as if it were 23 hours later: within the day, so the session is kept.

@@ 930-931
Run them as if it were two days later: past the day, so it is purged.

@@ 932
Read the project's counts.

@@ 933-935
Verify every organisation's audit chain.

@@ 936-937
The sweep expired at least one session (other tests leave theirs too), and the website was told, by one delivery, although nobody read the session.

@@ 938-940
After 23 hours nothing of this project's was purged and the session still exists; after two days it is gone (`404`).

@@ 941
The count of one expired session outlives the session itself.

@@ 942
And this organisation's audit chain is intact.

@@ 945-947
**The console tests (Phase 4, step 2).** The console's address; settings for its tests — a cookie that may travel over plain HTTP, and a generous sign-in allowance, because every test signs in from the same address; and a throwaway password.

@@ 950-952
**`person`** — a separate browser for one person: a new client on the same transport, with its own cookie jar, so several people can be signed in at once in one test.

@@ 955-959
**`sign_up`** — create an account and organisation through the console, insist it worked, and return the answer (which includes the CSRF token).

@@ 962-963
**`unique`** — a fresh e-mail address each time, so tests sharing the database never collide.

@@ 966-970
**Test — signing up, in and out.**

@@ 971-973
Sign up, and look at the cookie the browser received.

@@ 974-979
Try to sign up again with the same address, and with a five-character password.

@@ 980-982
Sign in with a wrong password; with an address nobody has; and correctly, typed in capitals.

@@ 983-986
Sign out without the CSRF token, then with it; then ask who is signed in.

@@ 987-988
The new person owns the new organisation; the cookie is a long, unguessable token.

@@ 989-990
The repeated address and the weak password are refused.

@@ 991-992
A wrong password and an unknown account get the **same** status and the **same** sentence: an attacker can't use sign-in to find out who has an account.

@@ 993
Addresses match whatever their capitals.

@@ 994-996
Signing out needs the CSRF token like any change; with it, the session ends, and the cookie no longer works.

@@ 999-1001
**Test — CSRF.**

@@ 1002-1006
Sign up, then try a change three ways: with a guessed token, with the real token but from another site's origin, and genuinely.

@@ 1007-1009
The guess fails (`csrf_failed`), another origin fails (`bad_origin`), and only the genuine request works.

@@ 1012-1015
**Test — one-time codes.**

@@ 1016-1017
Sign up, and ask to set up one-time codes: the answer holds the secret and its `otpauth://` address.

@@ 1018-1022
Work out the current 30-second step. A wrong code is refused; the right one, computed from the secret as an authenticator app would, switches codes on.

@@ 1023-1024
Sign in with only the password.

@@ 1025-1027
Sign in with the **next** step's code — what a phone whose clock runs a little fast shows — and then try exactly the same code again.

@@ 1028-1032
The offer was a proper `otpauth://` address; the wrong code failed and the right one worked; a password alone is no longer enough; the code worked once — and a second time it is refused.

@@ 1035-1037
**Test — roles.** Three addresses: an owner, an analyst and a developer.

@@ 1038-1044
Inside one harness, four browsers — the fourth for an outsider. `async with ( … ):` opens several at once, and closes them all at the end.

@@ 1045-1047
The owner signs up; note the organisation and the owner's CSRF token.

@@ 1048-1051
The analyst and the developer sign up (each gets an organisation of their own), and so does the outsider.

@@ 1052-1056
The owner adds the analyst and the developer to the owner's organisation, each with their role.

@@ 1057-1059
The analyst lists the organisation's projects — any member may — and the test builds the address for creating API keys in the first one.

@@ 1060-1062
The analyst and the developer each try to create a read-only key.

@@ 1063-1067
The developer tries to make the analyst an owner.

@@ 1068-1072
The analyst lists the members; the outsider tries to; the developer's new key is used on the API; and the owner and the analyst read the audit log.

@@ 1073-1075
The analyst may not create keys (`403 forbidden_for_role`); the developer may; and the developer may not manage members.

@@ 1076-1077
The analyst sees all three members; the outsider gets `404`, exactly as if the organisation didn't exist.

@@ 1078
The key made in the console works on the API.

@@ 1079-1082
The owner's audit log, oldest first: the organisation's creation, two members added, a key created; the chain is intact; and the key itself appears nowhere in it.

@@ 1083
The analyst may not read the audit log.

@@ 1086-1088
**Test — sign-in limits.** At most 2 attempts at once, then one every two minutes.

@@ 1089-1091
A browser at an address of its own. `ASGITransport(…, client=…)` sets the address the API sees the request coming from; `192.0.2.x` is a range reserved for documentation and tests. Without it, every other test's sign-ins would already have used up this address's allowance.

@@ 1092-1097
Sign up, then try a wrong password three times.

@@ 1098-1099
Two ordinary refusals, then `429 too_many_sign_ins`, with a `Retry-After` of at least a second.

@@ 1102-1104
**The contract test (Phase 4, step 6).** `live_api` — Schemathesis sends real HTTP, so the API runs as a real server for these tests. `scope="module"` starts it once for the whole file rather than once per test.

@@ 1105-1113
Its settings: the test databases; webhook addresses never looked up (the fuzzer invents host names); a cookie allowed over plain HTTP; and limits so high that the fuzzer's many requests aren't simply refused with `429`.

@@ 1114
Seed a project and a key for it.

@@ 1115
A uvicorn server for the API, on `127.0.0.1` and **port 0**, which asks the operating system for any free port, so the test never collides with something already running.

@@ 1116-1117
Run it in a background **thread**: `daemon=True` means the thread won't keep Python alive if the tests end without stopping it.

@@ 1118-1119
Wait, a twentieth of a second at a time, until the server says it has started.

@@ 1120
Read which port it was given.

@@ 1121
Hand the tests the server's address and the key.

@@ 1122-1123
Afterwards, ask the server to stop, and wait up to ten seconds for its thread to finish.

@@ 1126-1128
**`live_document`** — Schemathesis reads the API's document from the running server, exactly as a website's developer would.

@@ 1131
`contract` — tells Schemathesis to take the document from that fixture. A document known only once the server runs can't be read while pytest is still collecting tests, so it is fetched lazily, from the fixture.

@@ 1134-1135
`@contract.parametrize()` turns the test into one sub-test per operation in the document: 31 of them. `@settings` gives each 25 generated requests, no time limit per request (`deadline=None`), and turns off Hypothesis's health checks, which would complain that each example is slow (it is a real HTTP request).

@@ 1136-1137
**Test — the contract.** For each generated request (`case`):

@@ 1138-1140
Every check but one. `positive_data_acceptance` insists that a request the document allows must succeed. But some of the API's rules depend on data, not just shape: whether the age model is calibrated for an age, whether an address is among the project's allowed origins. Refusing such a request with `422` is correct.

@@ 1141
Send it to the server with the website's key, and check the answer: never a server error, a status code the document lists for this operation, a content type it lists, a body that matches the schema for that status, and the headers HTTP requires (such as `Allow` on a `405`). Any failure prints the exact request, as a `curl` command to reproduce it.

@@ 1144-1146
**Test — no drift.** `docs/api/openapi.json` is what websites read; the docstring says how to refresh it.

@@ 1147
The file must equal, byte for byte, what the code produces now. A change to the API without refreshing the document fails here.

@@ 1150-1152
**Fail-closed tests (Phase 7).** Valkey unreachable. "Gone" is simulated by an address where nothing listens: port 1 on this computer.

@@ 1153-1156
Settings with that Valkey and the real database; a key; and an API started with them (its inference client is never reached).

@@ 1157-1160
Try to create a session — the API key's rate limit needs Valkey — and ask whether the API is ready.

@@ 1161-1163
The session request gets `503 service_unavailable` with `Retry-After: 5` (not a crash, not a pass), and readiness reports exactly what is wrong: the database is fine, Valkey isn't.

@@ 1166-1167
**`unreachable`** — an inference service that is down: every request fails to connect.

@@ 1170-1171
**`broken`** — an inference service that answers, but with nonsense: valid JSON that isn't an analysis.

@@ 1174-1179
**Fail closed when inference fails.** The test runs twice, once with each broken service (`parametrize`).

@@ 1180-1186
An API whose inference client sends every request to the broken service, and a harness around it.

@@ 1187-1190
Create a session, start it, and make two attempts with a real face.

@@ 1191-1192
Neither attempt passes — the face would have passed with a working service — and the first is a `retry`: the person may try again, but nobody is let in on a failure.

@@ 1195-1200
**Security headers (Phase 7).** A refusal (no key), the public key set, and the interactive documentation.

@@ 1201-1205
Every answer carries `nosniff`, the strict content policy and `no-referrer`. HSTS isn't sent outside production: over plain HTTP it would mean nothing.

@@ 1206-1208
Answers are `no-store` unless their route says otherwise: the key set keeps its own five-minute public caching. The documentation page has no content policy, which would stop its scripts.

@@ 1211-1219
**Production.** Settings a production deployment would accept: a real-looking master key and HTTPS addresses. The app isn't started, because `/livez` needs no database.

@@ 1220-1223
Ask for `/livez`, the documentation page and the API document.

@@ 1224-1225
HSTS is sent (two years); the interactive documentation doesn't exist (`404`); the API document is still published.

@@ 1228-1234
**Test — the console's project pages (Phase 5).** An owner and an analyst, each with their own browser.

@@ 1235-1240
The owner signs up; the analyst signs up; the owner adds the analyst to the organisation.

@@ 1241-1244
The owner finds the organisation's project and creates a key for it in the console.

@@ 1245
A website using that key: the harness, copied with the key changed (`replace`).

@@ 1246-1248
The website creates a session — without a return address, because this new project hasn't allowed any yet — and a person passes it.

@@ 1250-1252
The analyst reads the project's sessions, the passed session's trace, and the last week's counts.

@@ 1253-1256
The analyst and then the owner try to add a policy version; the analyst lists the policies.

@@ 1257
The analyst tries the harness's own project — which belongs to another organisation — under this organisation's address.

@@ 1258-1259
The one session is listed; its trace has one attempt, and it passed.

@@ 1260-1261
The attempt carries its numbers: the age probability, the line it met, and the liveness evidence.

@@ 1262
Reading a trace made no token.

@@ 1263
The counts show one pass.

@@ 1264-1266
An analyst may not add a policy version; the owner may, and it is listed as `console_18@1`.

@@ 1267
Another organisation's project, named under this organisation, is not found — the check that the project belongs to the organisation in the address.

@@ 1270-1273
**Test — the console's webhooks (Phase 5).** An owner and an analyst. Private addresses are allowed, so the endpoint can point at this computer (`localhost:9`, where nothing listens — nothing is sent in this test).

@@ 1274-1280
The owner signs up, the analyst signs up and is added, and the owner finds the project.

@@ 1281-1282
The project's webhook address, and an endpoint for finished sessions.

@@ 1284-1287
The analyst tries to add it; the owner adds it; the analyst tries to list them; the owner lists the live ones.

@@ 1288-1292
The owner sends a test event, reads the endpoint's deliveries, and replays the first.

@@ 1293-1296
The owner tries to delete it as a live endpoint, then deletes it as the test one it is; lists again; and reads the audit log.

@@ 1297
An analyst may not add one.

@@ 1298
The owner's new endpoint came with its secret, and is a test endpoint.

@@ 1299
An analyst may not even list them; and the live mode has none — modes never mix.

@@ 1300-1301
The test event is waiting to be delivered (no worker runs here); the replay is accepted.

@@ 1302
The wrong mode is "not found"; the deletion worked, and the list is empty.

@@ 1303-1304
The audit log names a person (`user:…`), not a key, for both the creation and the deletion.
