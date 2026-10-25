---
fingerprint: ea5da1858d80e91a
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

@@ 5-16
Standard-library tools: `asyncio`, `hashlib` and `hmac` (to check a webhook's signature as a receiver would), `json`, `logging`, `uuid` (fresh IDs for the tenancy tests), the iterator types for fixtures, `asynccontextmanager`, `dataclass`, `UTC`, `datetime` and `timedelta` (a length of time, for key rotation and webhook retries), `Path`, `Any` — and `Literal`, for the harness's liveness option (Phase 3).

@@ 18-22
OpenCV and NumPy (to make a test picture), the `docker` client (to ask whether Docker is running), `httpx` (to call the apps) and `pytest`.

@@ 23-24
Alembic's `compare_metadata` and `MigrationContext`, for the drift test at the end.

@@ 25-26
joserfc's `jwt` and `KeySet`: the tests verify tokens exactly as a website would.

@@ 27
An async Valkey client, so a test can look at what the API stored there (Phase 4).

@@ 28
SQLAlchemy's query builders, for the Phase 4 tests: `delete` (to remove a row on purpose), `select` and `func` (to count rows), `text` (raw SQL), and `update` (to try changing rows).

@@ 29-31
SQLAlchemy types: `Connection` for the drift test, `DBAPIError` — the error SQLAlchemy raises when the database itself refuses a statement — and `create_async_engine`.

@@ 32-34
Testcontainers: a ready-made PostgreSQL container, a general container for Valkey, and a **wait strategy** — "the container is ready when this line appears in its log".

@@ 36-62
The code under test: the database helpers (`make_engine`, `make_sessions`, `tenant`), the master key, the table catalogue and the thirteen tables that belong to tenants, the audit and maintenance modules, the delivery worker, the CLI's `maintain`, `migrate`, `seed_dev`, `rotate_key` and `revoke_key`, both apps' factories (renamed with `as` so the two `create_app`s can't be confused), the ID helpers, both settings classes, and the contracts for frames, challenges and browser signals. The brackets let one `import` span several lines.

@@ 64-65
The repository folder, and the public-domain portrait from the vision library's tests — a real face, so the real face detector finds it.

@@ 66
The demo shop's return address, which the seeded project allows.

@@ 69-72
**`blank_frame`** — a plain grey 320 × 240 picture, saved as JPEG: a valid image with no face in it. `np.full` fills an array with one value (128, middle grey). `cv2.imencode` returns two values — whether it worked, and the encoded bytes.

@@ 75-76
**The `databases` fixture.** A **fixture** is something a test needs, prepared by pytest and passed in by name. `scope="session"` means it is built **once for the whole test run** and shared: starting two containers takes seconds, so doing it once matters. It provides the two addresses.

@@ 77-80
Is Docker running? Ask it, giving up after 5 seconds. If not, skip every test that needs this fixture, with the reason.

@@ 81-86
A PostgreSQL container, using exactly the image the local Compose file uses. The password is a throwaway for a throwaway container; the comment explains why the linter's warning about a hard-coded password doesn't apply.

@@ 87-91
A Valkey container, with its port exposed, considered ready when Valkey logs `Ready to accept connections`.

@@ 92-93
Start both. Each `start()` waits until its container is ready.

@@ 94-96
Docker maps each container's port to a random free port on this computer, so the addresses are built from what the containers report. Random ports mean tests never clash with a database already running locally.

@@ 97
Apply the migrations — the same function a developer runs from the command line.

@@ 98
`yield` hands the addresses to the tests. Everything after it runs when the whole test run is over…

@@ 99-100
…stopping (and removing) both containers.

@@ 103-107
**`Harness`** — what each test gets to work with: an HTTP client connected to the API, the seeded project's test API key, and the project's public ID.

@@ 110-118
**`harness`** — sets up a complete, fresh API for one test. Its options: the age the stand-in model should "see" (30 by default — clearly an adult), whether the seeded key is live, how liveness gets its evidence (Phase 3) — `"labels"` by default, because the tests' portrait is a still photo that can't turn its head — the seeded key's scopes (every scope by default), and any other API settings to change (`**overrides`: extra named arguments, collected into a dict), such as a smaller device budget or rate limit.

@@ 119
Unpack the two database addresses.

@@ 120
Create an inference app whose stand-in model reports the chosen age, with the chosen liveness evidence.

@@ 121-125
Start the inference app's lifespan (loading its face detector), and open an HTTP client wired to it through **`ASGITransport`** — httpx calls the app's Python code directly, with no network and no server. One `async with` with two parts, in brackets, opens both and closes both.

@@ 126-127
Create the API with test settings — the test databases' addresses, plus any overrides — and the in-process inference client. The settings' default `database_role` applies, so **every test in this file runs as the restricted role**, under row-level security, exactly as the API will in production.

@@ 128
Run the API's lifespan: connect, load the signing key, read the manifest.

@@ 129
Seed a project and a key, exactly as a developer would with `seed-dev`, with the scopes asked for.

@@ 130-132
Open a client wired to the API the same way, and hand the harness to the test. When the test ends, every `async with` closes in reverse order.

@@ 135-138
**`create`** — create a session as the demo shop would, with the API key, plus any extra headers (`headers_extra`, such as an `Idempotency-Key`). Any keyword arguments replace the body's defaults, so a test can write `create(h, policy="anything_goes")`.

@@ 141-142
**`secret`** — the body for `/start`: the session's client secret.

@@ 145-148
**`start`** — start the flow and return the `Authorization` header with the flow token, ready for the next calls. The `assert` includes the response text, so if starting fails, the test report shows why.

@@ 151-152
**`following`** (Phase 3) — the labels for a burst whose head follows the given poses: frontal **baseline** frames first, then one frame per pose, in order. With 6 frames and 3 poses: baseline, baseline, baseline, then the three poses.

@@ 153
`["baseline"] * n` makes a list of n copies; `+ poses` adds the poses after them.

@@ 154
One `FrameMeta` per phase, numbered from 0, taken 120 ms apart. `enumerate` gives each item with its position.

The comment at the end, `# type: ignore[arg-type]`, silences one complaint of the type checker: it can't know that the plain texts in `poses` are valid `Phase` names. Pydantic checks them anyway when the `FrameMeta` is created.

@@ 157-165
**`attempt`** — one complete face attempt, as the verify page makes it. Besides the frames, three optional inputs let a test play an attacker (Phase 3):

- `poses` — label the frames with these poses instead of the ones asked for;
- `signals` — report these browser signals;
- `claimed` — put a challenge of the browser's own choosing into the request.

@@ 166-167
The docstring says the same, in short.

@@ 168
Get a challenge — the server picks its random poses and colours.

@@ 169-171
Label the frames: by default they follow the challenge's own poses (an honest attempt), otherwise the poses the test gave. A challenge has 3 or 4 poses, so first make sure there are enough frames — at least 3 frontal ones, then one per pose — by repeating the last frame as many times as needed (`frames[-1:] * n`: a list of the last frame, `n` times; `max(0, …)` keeps `n` from going negative).

@@ 172
Describe the attempt: the frames' labels, the signals (normal ones unless given), and any claimed challenge.

@@ 173-175
Package the frames as files `frame_0`, `frame_1`, …, add the description and the challenge's ID, and upload everything as a multipart form.

@@ 178-179
**The main story: an adult passes, and the website can verify the token.** `@pytest.mark.anyio` lets pytest run an `async` test function.

@@ 180-186
Create, start, attempt with six portraits — the stand-in model says 30, so it passes — then finish: the redirect goes back to the shop with the session's ID.

@@ 187
Start the flow *again*, as if the person reloaded the page afterwards.

@@ 188-190
As the shop's server: read the result with the API key, and fetch the public keys.

@@ 191-192
The reloaded page sees the completed session and its outcome — no error for the person.

@@ 193-194
The result says completed, and passed.

@@ 195
**Verify the token** exactly as a website would: with the published key set, accepting only Ed25519. If the signature didn't match, this line would raise an error.

@@ 196-201
The token is an age token, says pass, says `age_over_18: true` (the literal `True`, checked with `is`), and is addressed to this project, about this session, in test mode.

@@ 202
**No age inside.** None of these names appears among the claims: the set of forbidden names and the set of claim names have nothing in common (`&` is set intersection; an empty set counts as false).

@@ 205-217
**A clear child is refused, unmistakably.** With the stand-in model at 12, the attempt fails, and the signed token says `outcome: fail` *and* `age_over_18: false` — so even a website that read only the age claim would refuse entry.

@@ 220-226
**A teenager near the limit must use a stronger check.** At 16, the probability of being 18 or over is neither high enough to pass nor low enough to fail, so the answer is step up, with the reason `age_uncertain`.

@@ 229-241
**Poor frames: retry, retry, then step up.** Three attempts with blank grey frames: each finds no face. The first two are retries — the first saying `no_face` and that 2 attempts remain — and the third becomes a step-up. The session waits for a stronger check, and has no token.

@@ 244-259
**Credentials are checked, and errors are problem details.** No API key at all: `401`, with the problem-details media type, the stable code, the type reference, and a request ID that matches the response header. A wrong client secret and a missing flow token each get their own code.

@@ 262-266
**Each request is logged once, with its ID, and never with secrets.** `caplog` is pytest's log-capturing fixture; `set_level` makes it collect `INFO` lines from `dwarpal.api`.

@@ 267-268
Create one session. (Setting up the harness makes no HTTP requests, so this is the only request.)

@@ 269-272
Exactly one request log line, with the right method, path and status, and the same ID the response carried. `vars(record)` reads a log record's fields as a dict.

@@ 273-274
Neither the API key nor the new client secret appears anywhere in the captured logs.

@@ 277-291
**A challenge can be used only once.** The same challenge, sent twice: the first attempt is accepted, the second gets `409 challenge_invalid`.

@@ 294-302
**A session gets a limited number of challenges.** Seven requests in a row: six are granted (3 attempts × 2), the seventh gets `429 too_many_challenges`.

@@ 305-308
**Oversized and unmeasured bodies are refused before they are read.** `stream` is an async generator: given as a body, it makes httpx send the request in chunks of unknown total size.

@@ 310-313
A JSON body of about 100 KB (over the 64 KiB limit), and a chunked body.

@@ 314-318
`413 request_too_large` — still with a request ID — and `411 length_required`.

@@ 321-333
**Sessions refuse foreign return addresses, unknown policies, and live mode with a stand-in model.** A return address on another website, a policy that doesn't exist, and a session created with a *live* key while the model is uncalibrated: each gets its own code.

@@ 336-346
**Discovery and readiness.** The configuration document names Ed25519 and admits the model is uncalibrated; the key set may be cached for 5 minutes and holds only Ed25519 keys; and `/readyz` reports both databases as `ok`.

@@ 349
**The drift test: the migrations build exactly the tables the code describes.** It is not `async`, so it starts the async engine itself (line 305).

@@ 350-351
**`differences`** — Alembic's `compare_metadata` compares the real database (migrated by the fixture) with `METADATA`, the tables described in `tables.py`, and lists every difference: a missing table, an extra column, a different type.

@@ 353-358
**`check`** — connect to the test database and run the comparison through `run_sync`, because Alembic's comparison code isn't async (as in `env.py`).

@@ 360
The list of differences must be **empty**. If someone adds a column to `tables.py` but forgets the migration — or the other way round — this test fails, long before a real database meets the mismatch.

@@ 363-365
**Red team, from here on** (Phase 3): tests that play the attacker. **Red-teaming** means attacking your own system on purpose, to find its weaknesses before someone else does.

The first: **a printed photo**. The "person" is the still test portrait, and here liveness measures the images for real (`liveness="images"`).

@@ 366-369
Two attempts with six identical portraits. The photo looks straight ahead throughout — it can't turn left, right or up when asked.

@@ 370-371
The first attempt gets a retry, with the vague `liveness_check_failed` (a real person may just have been slow). The second gets **rejected** — and from outside the reason is only `verification_failed`, which doesn't even say liveness was involved.

@@ 374-379
**Poses in the wrong order.** Labels mode is on, so the frames' labels are believed — but the attacker labels them `turn_right` three times, whatever the challenge asked. A challenge never repeats a pose twice in a row, so this can never match it.

@@ 380
Caught: retry, `liveness_check_failed`.

@@ 383-385
**A challenge claimed by the browser.** The attacker sends an easy challenge of its own choosing — one pose, `turn_left`, two colours.

@@ 386-389
And four frames that would satisfy *that* easy challenge: three baseline frames, then `turn_left`.

@@ 390
Caught: the server judged the frames against the challenge it **issued** (three random poses), not the claimed one, so the pose check fails.

@@ 393-400
**Automation and virtual cameras.** Two fresh sessions; in each the browser honestly reports one warning sign — a program driving the browser, or a virtual camera. The frames themselves are fine and the person is a clear adult.

@@ 401
Both go to **step up** with `liveness_uncertain`: not passed on a face that may have been injected, but not rejected either, because these signs can have innocent causes. `[x] * 2` is a list of two copies of `x`.

@@ 404-407
**One device gets only so many challenges, however many sessions it starts.**

@@ 408-411
A helper that creates a fresh session, starts it, and asks for a challenge with a given device ID — the flow token's headers plus `X-Dwarpal-Device` (`|` joins two dicts).

@@ 413-415
With a budget of 2 challenges an hour: three requests from the same device, each in a new session, then one from a different device.

@@ 416-418
The same device gets two challenges and then `429 too_many_attempts` — new sessions don't reset its budget; the other device is unaffected.

@@ 421-435
**The tenancy tests (Phase 4).** `TENANT_TABLES` — the thirteen tables whose rows belong to a tenant: from organisations to the audit log and the daily counts. (The signing keys belong to Dwarpal itself, not to any customer.)

@@ 436
`NOT_TENANT_DATA` — the only two tables allowed to have no row-level security: Alembic's migration history and Dwarpal's own signing keys. Neither belongs to any customer.

@@ 439-456
**`a_session`** — a minimal verification session for a given project, made directly as a table row rather than through the API: just enough to be a row worth hiding or showing. It follows a preset (`policy_version=0`). `bytes(32)` is 32 zero bytes, standing in for the client secret's digest.

@@ 459-461
**`two_organisations`** — the scene for the tests, built as the tables' **owner**, whom the policies don't bind: organisation A with projects a1 and a2, organisation B with project b1, and one verification session in each project.

@@ 462-463
The time, and a fresh random ID for each name. `uuid.uuid4()` is fine here: these IDs only need to be different from everything else in the shared test database.

@@ 464-473
An engine with **no role** — the owner. Add both organisations, then (after a `flush`, so the foreign keys find them) the three projects, then one session per project, and commit. `add_all` adds a whole list at once.

@@ 474-475
Close the engine, and return the IDs by name, so each test can say `made["a1"]`.

@@ 478-479
**Test 1 — reading.** Each tenant sees only its own rows, and a unit of work that names no tenant sees nothing at all.

@@ 480-482
Build the scene, then open an engine as the API does: as `dwarpal_app`.

@@ 483-487
First, a unit of work that names **no** tenant counts the rows of every tenant table — expected: zero everywhere, although this database holds rows from every test so far. Then roll back and ask PostgreSQL who we are (`current_user`). This guards the bug the tests found while this step was built: a rollback used to undo `SET ROLE`, and the connection quietly became the owner again (`db.py`).

@@ 488-490
Named as project **a1**: which projects own the sessions it can see, and which organisations it can see.

@@ 491-492
Named as organisation **A**: which projects it can see.

@@ 493-494
`finally` closes the engine even if something above fails, so a failing test doesn't leave connections open.

@@ 495-499
The verdicts. Still the restricted role; zero rows of anything with no tenant; project a1 sees only its own sessions and its own organisation; organisation A sees both its projects, and not b1.

@@ 502-505
**Test 2 — writing.** A tenant can't create or change another tenant's rows, and can't switch the protection off.

@@ 506-508
The same scene and the same restricted engine.

@@ 509-513
Named as **a1**, try to add a session belonging to **b1**. The database must refuse at commit with "new row violates **row-level security** policy". `pytest.raises(…, match=…)` passes only if that error, with that text, happens.

@@ 514-519
Named as **a1**, try to change b1's sessions: an `update` with a `where` that picks exactly them. `.returning(…)` asks the database to send back the ID of every row it changed. b1's rows are invisible to a1, so the update finds nothing to change.

@@ 520-521
After the commit, count sessions again in the same database session. The tenant was named with `set_config(…, true)`, for **one** transaction, and this is a new one: it sees nothing.

@@ 522-524
Could the restricted role simply turn the policies off? `ALTER TABLE … DISABLE ROW LEVEL SECURITY` is allowed only to a table's owner, so PostgreSQL answers "**must be owner** of table projects".

@@ 525-526
Close the engine, whatever happened.

@@ 527-528
The verdicts: no row changed, and nothing visible once the transaction had ended.

@@ 531-532
**Test 3 — through the API.** One website's key can't read another website's session.

@@ 533-536
Inside the usual harness, the first website creates a session. Then `seed_dev` makes a **second** organisation, project and key in the same database — a second customer.

@@ 537-542
Ask for the first website's session with the second website's key, and then with its own.

@@ 543-545
A foreign key gets the same `404 session_not_found` as a session that doesn't exist — it can't even learn that the session is there — while the owner reads it normally.

@@ 548
**Test 4 — no table forgotten.** The tests above prove that the policies work; this one proves that **every** table has them. A future migration that adds a table and forgets its policy would fail here, until someone either protects the table or decides, in this file, that it holds no customer's data.

@@ 549-555
Connect as the owner, and ask PostgreSQL's own catalogue. `pg_class` lists every table the database knows; the conditions keep ordinary tables (`relkind = 'r'`) in our `public` schema (`'public'::regnamespace` turns the schema's name into its internal ID) whose row-level security is **off** (`NOT relrowsecurity`). `connection.scalars` returns the first column of each row: the names. `set(…)` collects them, and the engine is closed.

@@ 557
The unprotected tables must be exactly the two allowed ones, no more and no fewer.

@@ 560-561
**`bearer_of`** — the `Authorization` header for a given key. The tests below use several keys, so `h.key` alone won't do.

@@ 564-567
**Idempotency.** Sending the same request twice with the same `Idempotency-Key` gets the first answer, not a second session.

@@ 568-573
The same request twice with one key; the same key with a *different* request; a key that is too short; and two requests with no key at all.

@@ 574-577
Look inside Valkey itself. `scan_iter("idem:*")` walks through every stored reply. Each must exist, and none may contain the client secret in readable form: the reply is sealed (`app/idempotency.py`), so a copy of Valkey reveals no secret.

@@ 578-581
Both requests succeeded, the second answer is **identical** to the first — the same session and the same client secret — and only the repeat carries `Idempotent-Replayed`.

@@ 582-584
The same key with a different request is refused (`422 idempotency_key_reused`); the short key is refused; and without a key, two requests make two different sessions.

@@ 587-590
**Rate limits.** A key allowed a burst of 2 and almost no refill (one token every 100 seconds) makes three requests in a row.

@@ 591-593
Two get through, the third gets `429 rate_limited`, with a `Retry-After` of at least one second.

@@ 596-598
**Pagination.** Five sessions are listed two at a time.

@@ 599
Create five sessions, remembering their IDs in the order they were made.

@@ 600-607
Read the pages the way a client would: ask for 2, then keep asking `starting_after` the cursor of the last page until `has_more` is false. (`|` joins two dictionaries; with no cursor yet, the second one is empty.)

@@ 608
Ask for more than the largest allowed page.

@@ 609-613
All the listed IDs together: pages of 2, 2 and 1; exactly the five sessions, **newest first** (`reversed(made)`), none repeated, none missed; no `age_token` anywhere in the list; and the oversized page refused with `422`.

@@ 616-622
**Scopes.** A key with only `sessions:read` can't create a session (`403 insufficient_scope`), but can list them.

@@ 625-628
**Rotation and revocation.**

@@ 629-632
Rotate the harness's key with a one-hour grace period. The key id is characters 8 to 19 of the key.

@@ 633
During the grace period, the old key and its replacement both work.

@@ 634-636
Rotate the replacement with **no** grace at all, then try the key just replaced and its own replacement.

@@ 637-638
Revoke the newest key (`revoke_key` reports that it found one), and try it once more.

@@ 639-642
The verdicts: both keys worked during the grace period; a key whose grace has ended gets `401 api_key_expired`; its replacement works; a revoked key gets the plain `401 invalid_api_key`.

@@ 645-648
**Versioned policies.** A session keeps the policy version it started with, even after a new version is added.

@@ 649-651
Add version 1 of the project's own policy `shop_18`.

@@ 652
Create a session with it.

@@ 653-655
Add version 2, which allows only one face attempt.

@@ 656
Create another session, which gets version 2.

@@ 657
Start the **first** session's flow: its answer says how many attempts remain.

@@ 658
List the policies.

@@ 659-661
Three refusals to check: a custom policy named like a preset, one for age 19 (the model has no thresholds for it), and a session asking for a policy nobody made.

@@ 662-663
The two versions were numbered `shop_18@1` and `shop_18@2`, and each session names the version it got.

@@ 664
The first session still has **3** attempts — version 1's rules — although version 2, with only one, now exists.

@@ 665
The list shows both versions of the project's own policy, oldest first.

@@ 666-668
And the three refusals: `invalid_policy_name`, `policy_not_supported`, `unknown_policy`.

@@ 671-674
**Immutability.** Add one policy version through the API.

@@ 675-682
Then, as the API's own role, try to change it and to delete it with plain SQL. The migration gave the role only `SELECT` and `INSERT` on this table, so PostgreSQL answers "**permission denied**" to both: no bug in our code could rewrite the rules a past check followed. Close the engine at the end, whatever happened.

@@ 685-687
**The webhook tests (Phase 4).** `Receiver` — a website's webhook receiver, kept in memory: no network, no server.

@@ 689-690
The statuses it will answer with, in order, and every request it has received.

@@ 692-694
**`handle`** — record the request, and answer with the next status in line (`pop(0)` takes the first), or `200` once the list is used up.

@@ 697-698
**`deliverer`** — the delivery worker, set up as in production: as the tables' owner.

@@ 699-700
An owner engine, and an HTTP client whose **transport** is `httpx.MockTransport(receiver.handle)`: every request the worker sends is handed straight to the receiver's function instead of going over a network.

@@ 701
The development master key — the same one the API in the harness uses, so the worker can open the secrets the API sealed.

@@ 702
Return the worker and its engine (so the test can close it). The clock is `lambda: clock[0]`: a function reading a one-item list, so the test can move time forward by changing `clock[0]` — and test a 24-hour retry without waiting 24 hours.

@@ 705-709
**`pass_one_session`** — create a session, start it, and pass one face attempt: a session that has just completed.

@@ 712-715
**Test — a delivery.** A completed session reaches the website, signed so that the website can check it.

@@ 716
An empty receiver (it will answer `200`), and a clock.

@@ 717
The harness allows private addresses: the receiver's address is never really contacted.

@@ 718-720
Register an endpoint for completed sessions.

@@ 721
Complete one session: the event and its delivery are written in the same transaction.

@@ 722
Set the worker's clock just past now, so the delivery is due.

@@ 723-725
Run the worker once, then close its engine.

@@ 726-727
Read the endpoint's deliveries, and the list of endpoints.

@@ 728-729
The secret was shown once, at creation, with its `whsec_` prefix, and never again.

@@ 730
Exactly one delivery was sent, and it arrived.

@@ 731-736
The body is the completed event: it names the session and its outcome, it carries **no token**, and the `Dwarpal-Event-Id` header matches the event's ID.

@@ 737-740
Check the signature exactly as a receiver would: split the header into `t` and `v1`, recompute the HMAC of `"<t>.<body>"` with the secret, and compare in constant time (`compare_digest`).

@@ 741
The delivery is recorded as delivered, on its first attempt, with the receiver's `200`.

@@ 744-747
**Test — retries.** A failing receiver is retried on the schedule until the delivery is dead; then it can be replayed.

@@ 748
This receiver answers `500` eight times.

@@ 749-755
Register an endpoint, send it a **test event** (which goes to this endpoint whatever it subscribes to), and set the clock just past now.

@@ 756-759
Eight rounds. In each, the worker sends one delivery, and an immediate second run finds nothing due: the failure has pushed the next attempt into the future.

@@ 760-761
Read the delivery's state.

@@ 762-765
While it is still pending, measure the wait the worker chose, and move the clock forward to exactly that moment.

@@ 766
Replay the dead delivery.

@@ 767-768
With the clock at now, the worker sends it again — and the receiver, out of failures, answers `200`.

@@ 769-770
Close the engine and read the final state.

@@ 771
The test event was accepted (`202`, "accepted for later").

@@ 772
The waits were exactly the schedule: 1 minute, 5 minutes, 30 minutes, 2, 6, 12 and 24 hours.

@@ 773
After the eighth failure the delivery was dead, with the receiver's last `500` recorded.

@@ 774-775
Replaying put it back to pending with a fresh count, and it was then delivered.

@@ 778-783
**Test — the SSRF guard through the API.** With private addresses not allowed (the normal setting), an endpoint on `127.0.0.1` — this very computer — is refused.

@@ 784-786
So is an endpoint asking for an event type that doesn't exist.

@@ 787-788
`422 unsafe_webhook_url` and `422 unknown_event_type`.

@@ 791-796
**Test — introspection.** Pass a session and read its age token.

@@ 797-798
Seed a second website, with its own key.

@@ 800-802
**`ask`** — introspect a token with a given key. A function defined inside the test, because only this test needs it.

@@ 804-807
Ask four times: with the other website's key; with a **forged** token (its last four characters changed, which breaks the signature); and twice with the right key.

@@ 808-811
The other website and the forger both get only `{"active": false}`; the first genuine question gets `active` with the token's claims; the second gets `false` — a token is spent once introspected.

@@ 814-816
**Test — expiry is announced once.** A session lifetime of 0 seconds makes every new session expire at once.

@@ 817-819
Register an endpoint for expired sessions.

@@ 820-821
Create a session, and read it twice.

@@ 822
Read the endpoint's deliveries.

@@ 823-824
Both reads say `expired`, but there is exactly **one** delivery: the first read saved the change and its event together, and the second found nothing to change.

@@ 827-834
**`org_of`** — the organisation that owns a seeded project, read as the tables' owner: the audit log is kept per organisation.

@@ 837-838
**Test — the audit chain.** Real changes are chained in the log, and tampering of either kind is found.

@@ 839-844
Through the API: add a policy version, register a webhook endpoint, and delete it. With the key `seed_dev` created, that makes four audited actions.

@@ 845-848
The organisation's ID; an engine as the owner, and one as the API's role.

@@ 849
From here on, whatever happens, both engines are closed at the end (`try` … `finally`).

@@ 850-852
Read the organisation's entries, and verify the chain as it stands.

@@ 853-855
**The API can't rewrite history**: as the API's role, changing any entry is refused with "permission denied" — the role may only add entries (migration `0006`).

@@ 856-860
But someone with the **owner's** rights — a database administrator, or an attacker who stole that login — can. Change entry 2's facts (as if the policy had been for age 13) and verify again.

@@ 861-865
Put entry 2 back, then quietly **delete the last entry**, and verify once more.

@@ 866-868
Close both engines, whatever happened.

@@ 869-874
The four entries, in order: the key's creation, the policy version, the endpoint created, the endpoint deleted.

@@ 875-876
Changes made with the API key name it by its **id** (characters 8 to 19), and the key itself appears in no entry's facts.

@@ 877
Before any tampering: four entries, intact.

@@ 878
After the edit: broken, **at entry 2** — the exact entry that was changed.

@@ 879
After the deletion: broken at entry 4, the missing one. The chain itself still checks out, but the head (`audit_heads`) remembers that there should be four.

@@ 882-886
**Test — counting.** Pass two sessions.

@@ 887-888
Read the last week's counts, and ask for more than a year.

@@ 889-891
Two passes in total, in one row for today under `uk_osa_18`; and a request for 366 days refused with `422`.

@@ 894-898
**Test — the sweep and the purge.** Settings for calling the operator's command directly.

@@ 899-903
Sessions in this harness expire at once. Register an endpoint for expired sessions, and create a session that nobody will ever read.

@@ 904-905
Run the scheduled jobs, then read the endpoint's deliveries.

@@ 906-911
As the owner, give this project a retention of **one day**.

@@ 912-913
Run the jobs as if it were 23 hours later: within the day, so the session is kept.

@@ 914-915
Run them as if it were two days later: past the day, so it is purged.

@@ 916
Read the project's counts.

@@ 917-919
Verify every organisation's audit chain.

@@ 920-921
The sweep expired at least one session (other tests leave theirs too), and the website was told, by one delivery, although nobody read the session.

@@ 922-924
After 23 hours nothing of this project's was purged and the session still exists; after two days it is gone (`404`).

@@ 925
The count of one expired session outlives the session itself.

@@ 926
And this organisation's audit chain is intact.
