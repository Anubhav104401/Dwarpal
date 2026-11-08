---
fingerprint: f51faacdf7c550fa
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

@@ 35
Hypothesis's `settings` and `HealthCheck`, to tell Schemathesis (which uses Hypothesis inside) how many requests to make per operation.

@@ 36-37
joserfc's `jwt` and `KeySet`: the tests verify tokens exactly as a website would.

@@ 39
Pydantic's `SecretStr`, to give production settings a master key.

@@ 40
An async Valkey client, so a test can look at what the API stored there (Phase 4).

@@ 41-42
Schemathesis's `Case` — one generated request — and `positive_data_acceptance`, the one check the contract test leaves out (explained there).

@@ 43
SQLAlchemy's query builders, for the Phase 4 tests: `delete` (to remove a row on purpose), `select` and `func` (to count rows), `text` (raw SQL), and `update` (to try changing rows).

@@ 44-46
SQLAlchemy types: `Connection` for the drift test, `make_url` (which reads a database address so a chaos test can change its host and port), `DBAPIError` — the error SQLAlchemy raises when the database itself refuses a statement — and `create_async_engine`.

@@ 47-49
Testcontainers: a ready-made PostgreSQL container, a general container for Valkey, and a **wait strategy** — "the container is ready when this line appears in its log".

@@ 51-79
The code under test: the database helpers (`make_engine`, `make_sessions`, `tenant`), the master key, the table catalogue and the fifteen tables that belong to tenants, the audit and maintenance modules, the delivery worker, the CLI's `API_DOCUMENT`, `api_document`, `maintain`, `migrate`, `seed_dev`, `rotate_key` and `revoke_key`, both apps' factories (renamed with `as` so the two `create_app`s can't be confused), the ID and one-time-code helpers, both settings classes, and the contracts for frames, challenges and browser signals. The brackets let one `import` span several lines.

@@ 83-84
The repository folder, and the public-domain portrait from the vision library's tests — a real face, so the real face detector finds it.

@@ 85
The demo shop's return address, which the seeded project allows.

@@ 97-100
**`blank_frame`** — a plain grey 320 × 240 picture, saved as JPEG: a valid image with no face in it. `np.full` fills an array with one value (128, middle grey). `cv2.imencode` returns two values — whether it worked, and the encoded bytes.

@@ 103-104
**The `databases` fixture.** A **fixture** is something a test needs, prepared by pytest and passed in by name. `scope="session"` means it is built **once for the whole test run** and shared: starting two containers takes seconds, so doing it once matters. It provides the two addresses.

@@ 105-108
Is Docker running? Ask it, giving up after 5 seconds. If not, skip every test that needs this fixture, with the reason.

@@ 109-114
A PostgreSQL container, using exactly the image the local Compose file uses. The password is a throwaway for a throwaway container; the comment explains why the linter's warning about a hard-coded password doesn't apply.

@@ 115-119
A Valkey container, with its port exposed, considered ready when Valkey logs `Ready to accept connections`.

@@ 120-121
Start both. Each `start()` waits until its container is ready.

@@ 122-124
Docker maps each container's port to a random free port on this computer, so the addresses are built from what the containers report. Random ports mean tests never clash with a database already running locally.

@@ 125
Apply the migrations — the same function a developer runs from the command line.

@@ 126
`yield` hands the addresses to the tests. Everything after it runs when the whole test run is over…

@@ 127-128
…stopping (and removing) both containers.

@@ 131-135
**`Harness`** — what each test gets to work with: an HTTP client connected to the API, the seeded project's test API key, and the project's public ID.

@@ 136
`transport` — the in-process connection to the API (step 2): a test can open more clients on it, one per person, each with its own cookies.

@@ 139-148
**`harness`** — sets up a complete, fresh API for one test. Its options: the age the stand-in model should "see" (30 by default — clearly an adult), whether the seeded key is live, how liveness gets its evidence (Phase 3) — `"labels"` by default, because the tests' portrait is a still photo that can't turn its head — the seeded key's scopes (every scope by default), something to put in front of the inference service (`inference_via`, for the chaos tests: a function that takes the connection to it and returns another), and any other API settings to change (`**overrides`: extra named arguments, collected into a dict), such as a smaller device budget or rate limit.

@@ 149
Unpack the two database addresses.

@@ 150-151
Create an inference app whose stand-in model reports the chosen age, with the chosen liveness evidence, and with Tesseract as found above (or its default, where there's none — then document checks say OCR is unavailable).

@@ 152
The connection to it: **`ASGITransport`** — httpx calls the app's Python code directly, with no network and no server. Its type is written as any async transport, so the next lines may put another in its place.

@@ 153-154
If the test asked for it, wrap the connection — in a `Switch`, below, that can make the service "die".

@@ 155-158
Start the inference app's lifespan (loading its face detector), and open an HTTP client on that connection. One `async with` with two parts, in brackets, opens both and closes both.

@@ 159-160
Create the API with test settings — the test databases' addresses, plus any overrides — and the in-process inference client. The settings' default `database_role` applies, so **every test in this file runs as the restricted role**, under row-level security, exactly as the API will in production.

@@ 161
Run the API's lifespan: connect, load the signing key, read the manifest.

@@ 162
Seed a project and a key, exactly as a developer would with `seed-dev`, with the scopes asked for.

@@ 163-168
Open a client wired to the API the same way — since 9 Nov as a visitor at an address of its own, one of the addresses kept for documentation (`198.51.100.x`, RFC 5737), so limits per address count one test's requests, not the whole run's, just as each test has its own key — and hand the harness to the test, with the transport. When the test ends, every `async with` closes in reverse order.

@@ 171-174
**`create`** — create a session as the demo shop would, with the API key, plus any extra headers (`headers_extra`, such as an `Idempotency-Key`). Any keyword arguments replace the body's defaults, so a test can write `create(h, policy="anything_goes")`.

@@ 177-178
**`secret`** — the body for `/start`: the session's client secret.

@@ 181-184
**`start`** — start the flow and return the `Authorization` header with the flow token, ready for the next calls. The `assert` includes the response text, so if starting fails, the test report shows why.

@@ 187-188
**`following`** (Phase 3) — the labels for a burst whose head follows the given poses: frontal **baseline** frames first, then one frame per pose, in order. With 6 frames and 3 poses: baseline, baseline, baseline, then the three poses.

@@ 189
`["baseline"] * n` makes a list of n copies; `+ poses` adds the poses after them.

@@ 190
One `FrameMeta` per phase, numbered from 0, taken 120 ms apart. `enumerate` gives each item with its position.

The comment at the end, `# type: ignore[arg-type]`, silences one complaint of the type checker: it can't know that the plain texts in `poses` are valid `Phase` names. Pydantic checks them anyway when the `FrameMeta` is created.

@@ 193-202
**`attempt`** — one complete face attempt, as the verify page makes it. Besides the frames, three optional inputs let a test play an attacker (Phase 3):

- `poses` — label the frames with these poses instead of the ones asked for;
- `signals` — report these browser signals;
- `claimed` — put a challenge of the browser's own choosing into the request.

And a fourth, for the chaos tests: `challenge`, one fetched earlier — so a test can fetch it while everything works, then make a service die before the frames are sent.

@@ 203-205
The docstring says the same, in short.

@@ 206-207
Unless one was given, get a challenge — the server picks its random poses and colours.

@@ 208-210
Label the frames: by default they follow the challenge's own poses (an honest attempt), otherwise the poses the test gave. A challenge has 3 or 4 poses, so first make sure there are enough frames — at least 3 frontal ones, then one per pose — by repeating the last frame as many times as needed (`frames[-1:] * n`: a list of the last frame, `n` times; `max(0, …)` keeps `n` from going negative).

@@ 211
Describe the attempt: the frames' labels, the signals (normal ones unless given), and any claimed challenge.

@@ 212-214
Package the frames as files `frame_0`, `frame_1`, …, add the description and the challenge's ID, and upload everything as a multipart form.

@@ 217-219
**Who may frame a verify page** (decision D16): only the website a session returns to.

@@ 220-222
Three sessions: one with the shop's return address (the default), one without a return address, and one to be "over". The first is started.

@@ 223-232
Make the third expire: as the tables' owner, move its expiry time a minute into the past.

@@ 234-237
**`ancestor`** — ask who may frame a page; then ask it for the three sessions, a well-formed but unknown session, and something that isn't a session at all.

@@ 238
Start the first session again: the verify page's view of it.

@@ 239-241
Every answer is a `200` — this is asked while a page is being served, so it never fails. Only the session with a return address names a website, the shop's origin; the others name none. And the verify page learns the same origin when it starts.

@@ 244-245
**The main story: an adult passes, and the website can verify the token.** `@pytest.mark.anyio` lets pytest run an `async` test function.

@@ 246-252
Create, start, attempt with six portraits — the stand-in model says 30, so it passes — then finish: the redirect goes back to the shop with the session's ID.

@@ 253
Start the flow *again*, as if the person reloaded the page afterwards.

@@ 254-256
As the shop's server: read the result with the API key, and fetch the public keys.

@@ 257-258
The reloaded page sees the completed session and its outcome — no error for the person.

@@ 259-260
The result says completed, and passed.

@@ 261
**Verify the token** exactly as a website would: with the published key set, accepting only Ed25519. If the signature didn't match, this line would raise an error.

@@ 262-267
The token is an age token, says pass, says `age_over_18: true` (the literal `True`, checked with `is`), and is addressed to this project, about this session, in test mode.

@@ 268
**No age inside.** None of these names appears among the claims: the set of forbidden names and the set of claim names have nothing in common (`&` is set intersection; an empty set counts as false).

@@ 298-310
**A clear child is refused, unmistakably.** With the stand-in model at 12, the attempt fails, and the signed token says `outcome: fail` *and* `age_over_18: false` — so even a website that read only the age claim would refuse entry.

@@ 313-319
**A teenager near the limit must use a stronger check.** At 16, the probability of being 18 or over is neither high enough to pass nor low enough to fail, so the answer is step up, with the reason `age_uncertain`.

@@ 392-405
**Poor frames: retry, retry, then step up.** Three attempts with blank grey frames: each finds no face. The first two are retries — the first saying `no_face` and that 2 attempts remain — and the third becomes a step-up. The session waits for a stronger check, and has no token. It isn't finished, so it isn't in the totals yet; but its face check has reached a decision — once, not once per attempt — and is counted as a step-up.

@@ 410-425
**Credentials are checked, and errors are problem details.** No API key at all: `401`, with the problem-details media type, the stable code, the type reference, and a request ID that matches the response header. A wrong client secret and a missing flow token each get their own code.

@@ 428-432
**Each request is logged once, with its ID, and never with secrets.** `caplog` is pytest's log-capturing fixture; `set_level` makes it collect `INFO` lines from `dwarpal.api`.

@@ 433-434
Create one session. (Setting up the harness makes no HTTP requests, so this is the only request.)

@@ 435-438
Exactly one request log line, with the right method, path and status, and the same ID the response carried. `vars(record)` reads a log record's fields as a dict.

@@ 439-440
Neither the API key nor the new client secret appears anywhere in the captured logs.

@@ 443-457
**A challenge can be used only once.** The same challenge, sent twice: the first attempt is accepted, the second gets `409 challenge_invalid`.

@@ 460-469
**A session gets a limited number of challenges.** Thirteen requests in a row: twelve are granted — two per attempt, for three face attempts and, since Phase 6, three document attempts — and the thirteenth gets `429 too_many_challenges`.

@@ 472-475
**Oversized and unmeasured bodies are refused before they are read.** `stream` is an async generator: given as a body, it makes httpx send the request in chunks of unknown total size.

@@ 477-480
A JSON body of about 100 KB (over the 64 KiB limit), and a chunked body.

@@ 481-485
`413 request_too_large` — still with a request ID — and `411 length_required`.

@@ 560
**The drift test: the migrations build exactly the tables the code describes.** It is not `async`, so it starts the async engine itself (line 305).

@@ 561-562
**`differences`** — Alembic's `compare_metadata` compares the real database (migrated by the fixture) with `METADATA`, the tables described in `tables.py`, and lists every difference: a missing table, an extra column, a different type.

@@ 564-569
**`check`** — connect to the test database and run the comparison through `run_sync`, because Alembic's comparison code isn't async (as in `env.py`).

@@ 571
The list of differences must be **empty**. If someone adds a column to `tables.py` but forgets the migration — or the other way round — this test fails, long before a real database meets the mismatch.

@@ 574-576
**Red team, from here on** (Phase 3): tests that play the attacker. **Red-teaming** means attacking your own system on purpose, to find its weaknesses before someone else does.

The first: **a printed photo**. The "person" is the still test portrait, and here liveness measures the images for real (`liveness="images"`).

@@ 577-580
Two attempts with six identical portraits. The photo looks straight ahead throughout — it can't turn left, right or up when asked.

@@ 581-582
The first attempt gets a retry, with the vague `liveness_check_failed` (a real person may just have been slow). The second gets **rejected** — and from outside the reason is only `verification_failed`, which doesn't even say liveness was involved.

@@ 585-590
**Poses in the wrong order.** Labels mode is on, so the frames' labels are believed — but the attacker labels them `turn_right` three times, whatever the challenge asked. A challenge never repeats a pose twice in a row, so this can never match it.

@@ 591
Caught: retry, `liveness_check_failed`.

@@ 594-596
**A challenge claimed by the browser.** The attacker sends an easy challenge of its own choosing — one pose, `turn_left`, two colours.

@@ 597-600
And four frames that would satisfy *that* easy challenge: three baseline frames, then `turn_left`.

@@ 601
Caught: the server judged the frames against the challenge it **issued** (three random poses), not the claimed one, so the pose check fails.

@@ 604-611
**Automation and virtual cameras.** Two fresh sessions; in each the browser honestly reports one warning sign — a program driving the browser, or a virtual camera. The frames themselves are fine and the person is a clear adult.

@@ 612
Both go to **step up** with `liveness_uncertain`: not passed on a face that may have been injected, but not rejected either, because these signs can have innocent causes. `[x] * 2` is a list of two copies of `x`.

@@ 615-618
**One device gets only so many challenges, however many sessions it starts.**

@@ 619-622
A helper that creates a fresh session, starts it, and asks for a challenge with a given device ID — the flow token's headers plus `X-Dwarpal-Device` (`|` joins two dicts).

@@ 624-626
With a budget of 2 challenges an hour: three requests from the same device, each in a new session, then one from a different device.

@@ 627-629
The same device gets two challenges and then `429 too_many_attempts` — new sessions don't reset its budget; the other device is unaffected.

@@ 632-648
**The tenancy tests (Phase 4).** `TENANT_TABLES` — the fifteen tables whose rows belong to a tenant: from organisations to the audit log, the daily counts, the console's users and their memberships. (The signing keys belong to Dwarpal itself, not to any customer.)

@@ 649
`NOT_TENANT_DATA` — the only two tables allowed to have no row-level security: Alembic's migration history and Dwarpal's own signing keys. Neither belongs to any customer.

@@ 652-669
**`a_session`** — a minimal verification session for a given project, made directly as a table row rather than through the API: just enough to be a row worth hiding or showing. It follows a preset (`policy_version=0`). `bytes(32)` is 32 zero bytes, standing in for the client secret's digest.

@@ 672-674
**`two_organisations`** — the scene for the tests, built as the tables' **owner**, whom the policies don't bind: organisation A with projects a1 and a2, organisation B with project b1, and one verification session in each project.

@@ 675-676
The time, and a fresh random ID for each name. `uuid.uuid4()` is fine here: these IDs only need to be different from everything else in the shared test database.

@@ 677-686
An engine with **no role** — the owner. Add both organisations, then (after a `flush`, so the foreign keys find them) the three projects, then one session per project, and commit. `add_all` adds a whole list at once.

@@ 687-688
Close the engine, and return the IDs by name, so each test can say `made["a1"]`.

@@ 691-692
**Test 1 — reading.** Each tenant sees only its own rows, and a unit of work that names no tenant sees nothing at all.

@@ 693-695
Build the scene, then open an engine as the API does: as `dwarpal_app`.

@@ 696-700
First, a unit of work that names **no** tenant counts the rows of every tenant table — expected: zero everywhere, although this database holds rows from every test so far. Then roll back and ask PostgreSQL who we are (`current_user`). This guards the bug the tests found while this step was built: a rollback used to undo `SET ROLE`, and the connection quietly became the owner again (`db.py`).

@@ 701-703
Named as project **a1**: which projects own the sessions it can see, and which organisations it can see.

@@ 704-705
Named as organisation **A**: which projects it can see.

@@ 706-707
`finally` closes the engine even if something above fails, so a failing test doesn't leave connections open.

@@ 708-712
The verdicts. Still the restricted role; zero rows of anything with no tenant; project a1 sees only its own sessions and its own organisation; organisation A sees both its projects, and not b1.

@@ 715-718
**Test 2 — writing.** A tenant can't create or change another tenant's rows, and can't switch the protection off.

@@ 719-721
The same scene and the same restricted engine.

@@ 722-726
Named as **a1**, try to add a session belonging to **b1**. The database must refuse at commit with "new row violates **row-level security** policy". `pytest.raises(…, match=…)` passes only if that error, with that text, happens.

@@ 727-732
Named as **a1**, try to change b1's sessions: an `update` with a `where` that picks exactly them. `.returning(…)` asks the database to send back the ID of every row it changed. b1's rows are invisible to a1, so the update finds nothing to change.

@@ 733-734
After the commit, count sessions again in the same database session. The tenant was named with `set_config(…, true)`, for **one** transaction, and this is a new one: it sees nothing.

@@ 735-737
Could the restricted role simply turn the policies off? `ALTER TABLE … DISABLE ROW LEVEL SECURITY` is allowed only to a table's owner, so PostgreSQL answers "**must be owner** of table projects".

@@ 738-739
Close the engine, whatever happened.

@@ 740-741
The verdicts: no row changed, and nothing visible once the transaction had ended.

@@ 744-745
**Test 3 — through the API.** One website's key can't read another website's session.

@@ 746-749
Inside the usual harness, the first website creates a session. Then `seed_dev` makes a **second** organisation, project and key in the same database — a second customer.

@@ 750-755
Ask for the first website's session with the second website's key, and then with its own.

@@ 756-758
A foreign key gets the same `404 session_not_found` as a session that doesn't exist — it can't even learn that the session is there — while the owner reads it normally.

@@ 761
**Test 4 — no table forgotten.** The tests above prove that the policies work; this one proves that **every** table has them. A future migration that adds a table and forgets its policy would fail here, until someone either protects the table or decides, in this file, that it holds no customer's data.

@@ 762-768
Connect as the owner, and ask PostgreSQL's own catalogue. `pg_class` lists every table the database knows; the conditions keep ordinary tables (`relkind = 'r'`) in our `public` schema (`'public'::regnamespace` turns the schema's name into its internal ID) whose row-level security is **off** (`NOT relrowsecurity`). `connection.scalars` returns the first column of each row: the names. `set(…)` collects them, and the engine is closed.

@@ 770
The unprotected tables must be exactly the two allowed ones, no more and no fewer.

@@ 773-774
**`bearer_of`** — the `Authorization` header for a given key. The tests below use several keys, so `h.key` alone won't do.

@@ 777-780
**Idempotency.** Sending the same request twice with the same `Idempotency-Key` gets the first answer, not a second session.

@@ 781-786
The same request twice with one key; the same key with a *different* request; a key that is too short; and two requests with no key at all.

@@ 787-790
Look inside Valkey itself. `scan_iter("idem:*")` walks through every stored reply. Each must exist, and none may contain the client secret in readable form: the reply is sealed (`app/idempotency.py`), so a copy of Valkey reveals no secret.

@@ 791-794
Both requests succeeded, the second answer is **identical** to the first — the same session and the same client secret — and only the repeat carries `Idempotent-Replayed`.

@@ 795-799
The same key with a different request is refused (`422 idempotency_key_reused`). The short key is refused too — since step 6 by the pattern the API document states, so as a general `invalid_request` naming the header, before the API's own check runs. And without a key, two requests make two different sessions.

@@ 802-805
**Rate limits.** A key allowed a burst of 2 and almost no refill (one token every 100 seconds) makes three requests in a row.

@@ 806-808
Two get through, the third gets `429 rate_limited`, with a `Retry-After` of at least one second.

@@ 827-829
**Pagination.** Five sessions are listed two at a time.

@@ 830
Create five sessions, remembering their IDs in the order they were made.

@@ 831-838
Read the pages the way a client would: ask for 2, then keep asking `starting_after` the cursor of the last page until `has_more` is false. (`|` joins two dictionaries; with no cursor yet, the second one is empty.)

@@ 839
Ask for more than the largest allowed page.

@@ 840-844
All the listed IDs together: pages of 2, 2 and 1; exactly the five sessions, **newest first** (`reversed(made)`), none repeated, none missed; no `age_token` anywhere in the list; and the oversized page refused with `422`.

@@ 847-853
**Scopes.** A key with only `sessions:read` can't create a session (`403 insufficient_scope`), but can list them.

@@ 856-859
**Rotation and revocation.**

@@ 860-863
Rotate the harness's key with a one-hour grace period. The key id is characters 8 to 19 of the key.

@@ 864
During the grace period, the old key and its replacement both work.

@@ 865-867
Rotate the replacement with **no** grace at all, then try the key just replaced and its own replacement.

@@ 868-869
Revoke the newest key (`revoke_key` reports that it found one), and try it once more.

@@ 870-873
The verdicts: both keys worked during the grace period; a key whose grace has ended gets `401 api_key_expired`; its replacement works; a revoked key gets the plain `401 invalid_api_key`.

@@ 876-879
**Versioned policies.** A session keeps the policy version it started with, even after a new version is added.

@@ 880-882
Add version 1 of the project's own policy `shop_18`.

@@ 883
Create a session with it.

@@ 884-886
Add version 2, which allows only one face attempt.

@@ 887
Create another session, which gets version 2.

@@ 888
Start the **first** session's flow: its answer says how many attempts remain.

@@ 889
List the policies.

@@ 890-892
Three refusals to check: a custom policy named like a preset, one for age 19 (the model has no thresholds for it), and a session asking for a policy nobody made.

@@ 893-894
The two versions were numbered `shop_18@1` and `shop_18@2`, and each session names the version it got.

@@ 895
The first session still has **3** attempts — version 1's rules — although version 2, with only one, now exists.

@@ 896
The list shows both versions of the project's own policy, oldest first.

@@ 897-899
And the three refusals: `invalid_policy_name`, `policy_not_supported`, `unknown_policy`.

@@ 1023-1026
**Immutability.** Add one policy version through the API.

@@ 1027-1034
Then, as the API's own role, try to change it and to delete it with plain SQL. The migration gave the role only `SELECT` and `INSERT` on this table, so PostgreSQL answers "**permission denied**" to both: no bug in our code could rewrite the rules a past check followed. Close the engine at the end, whatever happened.

@@ 1037-1039
**The webhook tests (Phase 4).** `Receiver` — a website's webhook receiver, kept in memory: no network, no server.

@@ 1041-1042
The statuses it will answer with, in order, and every request it has received.

@@ 1044-1046
**`handle`** — record the request, and answer with the next status in line (`pop(0)` takes the first), or `200` once the list is used up.

@@ 1049-1050
**`deliverer`** — the delivery worker, set up as in production: as the tables' owner.

@@ 1051-1052
An owner engine, and an HTTP client whose **transport** is `httpx.MockTransport(receiver.handle)`: every request the worker sends is handed straight to the receiver's function instead of going over a network.

@@ 1053
The development master key — the same one the API in the harness uses, so the worker can open the secrets the API sealed.

@@ 1054
Return the worker and its engine (so the test can close it). The clock is `lambda: clock[0]`: a function reading a one-item list, so the test can move time forward by changing `clock[0]` — and test a 24-hour retry without waiting 24 hours.

@@ 1057-1061
**`pass_one_session`** — create a session, start it, and pass one face attempt: a session that has just completed.

@@ 1064-1067
**Test — a delivery.** A completed session reaches the website, signed so that the website can check it.

@@ 1068
An empty receiver (it will answer `200`), and a clock.

@@ 1069
The harness allows private addresses: the receiver's address is never really contacted.

@@ 1070-1072
Register an endpoint for completed sessions.

@@ 1073
Complete one session: the event and its delivery are written in the same transaction.

@@ 1074
Set the worker's clock just past now, so the delivery is due.

@@ 1075-1077
Run the worker once, then close its engine.

@@ 1078-1079
Read the endpoint's deliveries, and the list of endpoints.

@@ 1080-1081
The secret was shown once, at creation, with its `whsec_` prefix, and never again.

@@ 1082
Exactly one delivery was sent, and it arrived.

@@ 1083-1088
The body is the completed event: it names the session and its outcome, it carries **no token**, and the `Dwarpal-Event-Id` header matches the event's ID.

@@ 1089-1092
Check the signature exactly as a receiver would: split the header into `t` and `v1`, recompute the HMAC of `"<t>.<body>"` with the secret, and compare in constant time (`compare_digest`).

@@ 1093
The delivery is recorded as delivered, on its first attempt, with the receiver's `200`.

@@ 1096-1099
**Test — retries.** A failing receiver is retried on the schedule until the delivery is dead; then it can be replayed.

@@ 1100
This receiver answers `500` eight times.

@@ 1101-1107
Register an endpoint, send it a **test event** (which goes to this endpoint whatever it subscribes to), and set the clock just past now.

@@ 1108-1111
Eight rounds. In each, the worker sends one delivery, and an immediate second run finds nothing due: the failure has pushed the next attempt into the future.

@@ 1112-1113
Read the delivery's state.

@@ 1114-1117
While it is still pending, measure the wait the worker chose, and move the clock forward to exactly that moment.

@@ 1118
Replay the dead delivery.

@@ 1119-1120
With the clock at now, the worker sends it again — and the receiver, out of failures, answers `200`.

@@ 1121-1122
Close the engine and read the final state.

@@ 1123
The test event was accepted (`202`, "accepted for later").

@@ 1124
The waits were exactly the schedule: 1 minute, 5 minutes, 30 minutes, 2, 6, 12 and 24 hours.

@@ 1125
After the eighth failure the delivery was dead, with the receiver's last `500` recorded.

@@ 1126-1127
Replaying put it back to pending with a fresh count, and it was then delivered.

@@ 1130-1135
**Test — the SSRF guard through the API.** With private addresses not allowed (the normal setting), an endpoint on `127.0.0.1` — this very computer — is refused.

@@ 1136-1138
So is an endpoint asking for an event type that doesn't exist.

@@ 1139-1140
`422 unsafe_webhook_url` and `422 unknown_event_type`.

@@ 1143-1148
**Test — introspection.** Pass a session and read its age token.

@@ 1149-1150
Seed a second website, with its own key.

@@ 1152-1154
**`ask`** — introspect a token with a given key. A function defined inside the test, because only this test needs it.

@@ 1156-1159
Ask four times: with the other website's key; with a **forged** token (its last four characters changed, which breaks the signature); and twice with the right key.

@@ 1160-1163
The other website and the forger both get only `{"active": false}`; the first genuine question gets `active` with the token's claims; the second gets `false` — a token is spent once introspected.

@@ 1166-1168
**Test — expiry is announced once.** A session lifetime of 0 seconds makes every new session expire at once.

@@ 1169-1171
Register an endpoint for expired sessions.

@@ 1172-1173
Create a session, and read it twice.

@@ 1174
Read the endpoint's deliveries.

@@ 1175-1176
Both reads say `expired`, but there is exactly **one** delivery: the first read saved the change and its event together, and the second found nothing to change.

@@ 1179-1186
**`org_of`** — the organisation that owns a seeded project, read as the tables' owner: the audit log is kept per organisation.

@@ 1189-1190
**Test — the audit chain.** Real changes are chained in the log, and tampering of either kind is found.

@@ 1191-1196
Through the API: add a policy version, register a webhook endpoint, and delete it. With the key `seed_dev` created, that makes four audited actions.

@@ 1197-1200
The organisation's ID; an engine as the owner, and one as the API's role.

@@ 1201
From here on, whatever happens, both engines are closed at the end (`try` … `finally`).

@@ 1202-1204
Read the organisation's entries, and verify the chain as it stands.

@@ 1205-1207
**The API can't rewrite history**: as the API's role, changing any entry is refused with "permission denied" — the role may only add entries (migration `0006`).

@@ 1208-1212
But someone with the **owner's** rights — a database administrator, or an attacker who stole that login — can. Change entry 2's facts (as if the policy had been for age 13) and verify again.

@@ 1213-1217
Put entry 2 back, then quietly **delete the last entry**, and verify once more.

@@ 1218-1220
Close both engines, whatever happened.

@@ 1221-1226
The four entries, in order: the key's creation, the policy version, the endpoint created, the endpoint deleted.

@@ 1227-1228
Changes made with the API key name it by its **id** (characters 8 to 19), and the key itself appears in no entry's facts.

@@ 1229
Before any tampering: four entries, intact.

@@ 1230
After the edit: broken, **at entry 2** — the exact entry that was changed.

@@ 1231
After the deletion: broken at entry 4, the missing one. The chain itself still checks out, but the head (`audit_heads`) remembers that there should be four.

@@ 1234-1238
**Test — counting.** Pass two sessions.

@@ 1239-1240
Read the last week's counts, and ask for more than a year.

@@ 1241-1244
Two passes in total, in one row for today under `uk_osa_18`; both face checks decided, as passes, with the median in the first band (under 5 seconds — the test is quick); and a request for 366 days refused with `422`.

@@ 1247-1251
**Test — the sweep and the purge.** Settings for calling the operator's command directly.

@@ 1252-1256
Sessions in this harness expire at once. Register an endpoint for expired sessions, and create a session that nobody will ever read.

@@ 1257-1258
Run the scheduled jobs, then read the endpoint's deliveries.

@@ 1259-1264
As the owner, give this project a retention of **one day**.

@@ 1265-1266
Run the jobs as if it were 23 hours later: within the day, so the session is kept.

@@ 1267-1268
Run them as if it were two days later: past the day, so it is purged.

@@ 1269
Read the project's counts.

@@ 1270-1272
Verify every organisation's audit chain.

@@ 1273-1274
The sweep expired at least one session (other tests leave theirs too), and the website was told, by one delivery, although nobody read the session.

@@ 1275-1277
After 23 hours nothing of this project's was purged and the session still exists; after two days it is gone (`404`).

@@ 1278
The count of one expired session outlives the session itself.

@@ 1279
And this organisation's audit chain is intact.

@@ 1282-1284
**The console tests (Phase 4, step 2).** The console's address; settings for its tests — a cookie that may travel over plain HTTP, and a generous sign-in allowance, because every test signs in from the same address; and a throwaway password.

@@ 1287-1289
**`person`** — a separate browser for one person: a new client on the same transport, with its own cookie jar, so several people can be signed in at once in one test.

@@ 1292-1296
**`sign_up`** — create an account and organisation through the console, insist it worked, and return the answer (which includes the CSRF token).

@@ 1299-1300
**`unique`** — a fresh e-mail address each time, so tests sharing the database never collide.

@@ 1303-1307
**Test — signing up, in and out.**

@@ 1308-1310
Sign up, and look at the cookie the browser received.

@@ 1311-1316
Try to sign up again with the same address, and with a five-character password.

@@ 1317-1319
Sign in with a wrong password; with an address nobody has; and correctly, typed in capitals.

@@ 1320-1323
Sign out without the CSRF token, then with it; then ask who is signed in.

@@ 1324-1325
The new person owns the new organisation; the cookie is a long, unguessable token.

@@ 1326-1327
The repeated address and the weak password are refused.

@@ 1328-1329
A wrong password and an unknown account get the **same** status and the **same** sentence: an attacker can't use sign-in to find out who has an account.

@@ 1330
Addresses match whatever their capitals.

@@ 1331-1333
Signing out needs the CSRF token like any change; with it, the session ends, and the cookie no longer works.

@@ 1336-1338
**Test — CSRF.**

@@ 1339-1343
Sign up, then try a change three ways: with a guessed token, with the real token but from another site's origin, and genuinely.

@@ 1344-1346
The guess fails (`csrf_failed`), another origin fails (`bad_origin`), and only the genuine request works.

@@ 1349-1352
**Test — one-time codes.**

@@ 1353-1354
Sign up, and ask to set up one-time codes: the answer holds the secret and its `otpauth://` address.

@@ 1355-1359
Work out the current 30-second step. A wrong code is refused; the right one, computed from the secret as an authenticator app would, switches codes on.

@@ 1360-1361
Sign in with only the password.

@@ 1362-1364
Sign in with the **next** step's code — what a phone whose clock runs a little fast shows — and then try exactly the same code again.

@@ 1365-1370
The offer was a proper `otpauth://` address; the wrong code failed and the right one worked — and came with ten recovery codes; a password alone is no longer enough; the code worked once — and a second time it is refused.

@@ 1442-1444
**Test — roles.** Three addresses: an owner, an analyst and a developer.

@@ 1445-1451
Inside one harness, four browsers — the fourth for an outsider. `async with ( … ):` opens several at once, and closes them all at the end.

@@ 1452-1454
The owner signs up; note the organisation and the owner's CSRF token.

@@ 1455-1458
The analyst and the developer sign up (each gets an organisation of their own), and so does the outsider.

@@ 1459-1463
The owner adds the analyst and the developer to the owner's organisation, each with their role.

@@ 1464-1466
The analyst lists the organisation's projects — any member may — and the test builds the address for creating API keys in the first one.

@@ 1467-1469
The analyst and the developer each try to create a read-only key.

@@ 1470-1474
The developer tries to make the analyst an owner.

@@ 1475-1479
The analyst lists the members; the outsider tries to; the developer's new key is used on the API; and the owner and the analyst read the audit log.

@@ 1480-1482
The analyst may not create keys (`403 forbidden_for_role`); the developer may; and the developer may not manage members.

@@ 1483-1484
The analyst sees all three members; the outsider gets `404`, exactly as if the organisation didn't exist.

@@ 1485
The key made in the console works on the API.

@@ 1486-1489
The owner's audit log, oldest first: the organisation's creation, two members added, a key created; the chain is intact; and the key itself appears nowhere in it.

@@ 1490
The analyst may not read the audit log.

@@ 1737-1739
A browser at an address of its own. `ASGITransport(…, client=…)` sets the address the API sees the request coming from; `192.0.2.x` is a range reserved for documentation and tests. Without it, every other test's sign-ins would already have used up this address's allowance.

@@ 1740-1745
Sign up, then try a wrong password three times.

@@ 1746-1747
Two ordinary refusals, then `429 too_many_sign_ins`, with a `Retry-After` of at least a second.

@@ 1750-1752
**The contract test (Phase 4, step 6).** `live_api` — Schemathesis sends real HTTP, so the API runs as a real server for these tests. `scope="module"` starts it once for the whole file rather than once per test.

@@ 1753-1762
Its settings: the test databases; webhook addresses never looked up (the fuzzer invents host names); a cookie allowed over plain HTTP; and limits so high that the fuzzer's many requests aren't simply refused with `429`. Since 9 Nov the verify page's per-address limit too (`flow_burst`).

@@ 1763
Seed a project and a key for it.

@@ 1764
A uvicorn server for the API, on `127.0.0.1` and **port 0**, which asks the operating system for any free port, so the test never collides with something already running.

@@ 1765-1766
Run it in a background **thread**: `daemon=True` means the thread won't keep Python alive if the tests end without stopping it.

@@ 1767-1768
Wait, a twentieth of a second at a time, until the server says it has started.

@@ 1769
Read which port it was given.

@@ 1770
Hand the tests the server's address and the key.

@@ 1771-1772
Afterwards, ask the server to stop, and wait up to ten seconds for its thread to finish.

@@ 1775-1777
**`live_document`** — Schemathesis reads the API's document from the running server, exactly as a website's developer would.

@@ 1780
`contract` — tells Schemathesis to take the document from that fixture. A document known only once the server runs can't be read while pytest is still collecting tests, so it is fetched lazily, from the fixture.

@@ 1783-1784
`@contract.parametrize()` turns the test into one sub-test per operation in the document: 31 of them. `@settings` gives each 25 generated requests, no time limit per request (`deadline=None`), and turns off Hypothesis's health checks, which would complain that each example is slow (it is a real HTTP request).

@@ 1785-1786
**Test — the contract.** For each generated request (`case`):

@@ 1787-1789
Every check but one. `positive_data_acceptance` insists that a request the document allows must succeed. But some of the API's rules depend on data, not just shape: whether the age model is calibrated for an age, whether an address is among the project's allowed origins. Refusing such a request with `422` is correct.

@@ 1790
Send it to the server with the website's key, and check the answer: never a server error, a status code the document lists for this operation, a content type it lists, a body that matches the schema for that status, and the headers HTTP requires (such as `Allow` on a `405`). Any failure prints the exact request, as a `curl` command to reproduce it.

@@ 1793-1795
**Test — no drift.** `docs/api/openapi.json` is what websites read; the docstring says how to refresh it.

@@ 1796
The file must equal, byte for byte, what the code produces now. A change to the API without refreshing the document fails here.

@@ 1799-1801
**Fail-closed tests (Phase 7).** Valkey unreachable. "Gone" is simulated by an address where nothing listens: port 1 on this computer.

@@ 1802-1805
Settings with that Valkey and the real database; a key; and an API started with them (its inference client is never reached).

@@ 1806-1809
Try to create a session — the API key's rate limit needs Valkey — and ask whether the API is ready.

@@ 1810-1812
The session request gets `503 service_unavailable` with `Retry-After: 5` (not a crash, not a pass), and readiness reports exactly what is wrong: the database is fine, Valkey isn't.

@@ 1815-1816
**`unreachable`** — an inference service that is down: every request fails to connect.

@@ 1819-1820
**`broken`** — an inference service that answers, but with nonsense: valid JSON that isn't an analysis.

@@ 1823-1828
**Fail closed when inference fails.** The test runs twice, once with each broken service (`parametrize`).

@@ 1829-1835
An API whose inference client sends every request to the broken service, and a harness around it.

@@ 1836-1839
Create a session, start it, and make two attempts with a real face.

@@ 1840-1841
Neither attempt passes — the face would have passed with a working service — and the first is a `retry`: the person may try again, but nobody is let in on a failure.

@@ 1844
**Chaos tests** (Phase 7). The roadmap asks for *fail-closed chaos tests*: services killed in the middle of a check. They were first done by hand, stopping containers during a load test (§5.7.6); these tests do it on every run, so a change can't quietly break it. Each asks two questions: while a service is down, does anything pass? And once it is back, can a person finish their check?

@@ 1847-1850
**`Cutter`** — a small **TCP relay**: the API connects to it instead of to the real PostgreSQL or Valkey, and it passes the bytes on both ways. *Cutting* it drops every open connection at once and hangs up on new ones — to the API, exactly as if the service had died. *Restoring* lets connections through again, as after a restart. The containers themselves are never touched, so the other tests sharing them are safe.

@@ 1852-1856
Where to relay to; not cut yet; the open connections (both ends of each), so they can all be dropped; and the listening server, once started.

@@ 1858-1860
Entering the `async with`: listen on a free port on this computer (port `0` asks the system to choose one); each new connection runs `relay`.

@@ 1862-1865
Leaving it: drop everything, and stop listening.

@@ 1867-1870
**`port`** — the port the system chose. `@property` lets it be read like a field (`cutter.port`) though it is worked out each time.

@@ 1872-1875
**`relay`** — one connection from the API. While cut, hang up at once: `abort` closes the connection without the usual polite goodbye, as a dead service would.

@@ 1876-1878
Otherwise, connect to the real service, and remember both ends.

@@ 1879-1880
Copy both ways at the same time (`gather` runs the two copies together) until the connection ends; then forget it.

@@ 1882-1885
**`cut`** — from now on, refuse; and drop every open connection. `list(…)` takes a copy first, because dropping them changes the set.

@@ 1887-1888
**`restore`** — let connections through again.

@@ 1891-1892
**`pipe`** — copy one direction of a connection.

@@ 1893-1896
Read up to 64 KB at a time and pass it on, until the source ends (an empty read). `:=` (the "walrus") reads and tests in one go. `drain` waits while the other side is slow. A connection that is cut raises a connection error — expected here, so `suppress` ignores it.

@@ 1897
When one direction ends, drop the other side too, so neither half is left hanging.

@@ 1900-1902
**`chaos`** — the test databases, reached through two cutters: it hands back the new addresses (to give to the harness), and the cutters for PostgreSQL and Valkey.

@@ 1903-1905
Take both addresses apart, and check they have a host and a port.

@@ 1906-1909
Start one cutter for each service.

@@ 1910-1911
Build the addresses that lead through them — the same database, but on this computer at the cutter's port — and hand everything to the test. `hide_password=False`: the address must keep the (throwaway) password to work.

@@ 1914-1915
**`Switch`** — the same idea for the inference service, which the tests reach through httpx rather than a socket: a **transport** (what httpx sends requests through) put in front of the real one.

@@ 1917-1920
The real transport, set later; not down; and `on_call`, something to do on every call — nothing by default (`lambda: None` is a function that does nothing).

@@ 1922-1924
**`around`** — the function given to the harness as `inference_via`: keep the real transport, and use the switch in its place.

@@ 1926-1930
Every call: first run `on_call`; then, if the switch is down, fail exactly as an unreachable service does (`ConnectError`); otherwise pass the request on.

@@ 1933-1934
**`unavailable`** — the three things a "try again shortly" answer must have: status `503`, the code `service_unavailable`, and `Retry-After`.

@@ 1937-1939
**`outcome_of`** — what the website would see: the session's status and outcome, read with its API key.

@@ 1942-1946
**Valkey dies in the middle of a check.** Everything goes through the cutters. A session is created and started, and a challenge fetched while all is well.

@@ 1947-1950
Valkey dies. The person sends their frames; then the readiness check is asked.

@@ 1951-1953
Valkey comes back. The person tries again, and the website reads the result.

@@ 1954-1956
While Valkey was down: "try again shortly", and readiness names Valkey. Afterwards: the same connection pool recovered on its own, the face passes, and the session is complete — passed once.

@@ 1959-1966
**The database dies between two steps** — the same story with PostgreSQL.

@@ 1967-1972
The database dies before the frames arrive; readiness is asked; the database comes back; the person tries again.

@@ 1973-1975
While it was down, nothing was decided ("try again shortly", readiness names the database); afterwards the pool's *pre-ping* (`db.py`) noticed the dropped connections and made new ones, and the check passed.

@@ 1978-1982
**The database dies while a face is being analysed** — the hardest moment: after the attempt was accepted and its challenge used up, before the decision is written. The switch in front of inference makes that moment happen.

@@ 1983-1986
On the inference call, cut the database (`on_call`).

@@ 1987-1989
The attempt; then the switch is cleared, and the database comes back.

@@ 1990-1992
What the website sees now; a new attempt; and what it sees after.

@@ 1993-1995
The attempt answered "try again shortly" — the analysis is thrown away, never half-recorded. The session was untouched (still `in_progress`, no outcome), and the next attempt passed.

@@ 1998-2001
**Inference dies and comes back.** (The fail-closed test above has it dead throughout.)

@@ 2002-2008
Inference goes down; an attempt; it comes back; another attempt; the result.

@@ 2009-2010
While down: a `retry`, with 2 tries left — the person loses one try but isn't let in. Afterwards: a pass.

@@ 2013-2018
**Security headers (Phase 7).** A refusal (no key), the public key set, and the interactive documentation.

@@ 2019-2024
Every answer carries `nosniff`, the strict content policy, `no-referrer` and (since Phase 7) `Cross-Origin-Resource-Policy: same-origin`. HSTS isn't sent outside production: over plain HTTP it would mean nothing.

@@ 2025-2027
Answers are `no-store` unless their route says otherwise: the key set keeps its own five-minute public caching. The documentation page has no content policy, which would stop its scripts.

@@ 2030-2038
**Production.** Settings a production deployment would accept: a real-looking master key and HTTPS addresses. The app isn't started, because `/livez` needs no database.

@@ 2039-2042
Ask for `/livez`, the documentation page and the API document.

@@ 2043-2044
HSTS is sent (two years); the interactive documentation doesn't exist (`404`); the API document is still published.

@@ 2047-2053
**Test — the console's project pages (Phase 5).** An owner and an analyst, each with their own browser.

@@ 2054-2059
The owner signs up; the analyst signs up; the owner adds the analyst to the organisation.

@@ 2060-2063
The owner finds the organisation's project and creates a key for it in the console.

@@ 2064
A website using that key: the harness, copied with the key changed (`replace`).

@@ 2065-2067
The website creates a session — without a return address, because this new project hasn't allowed any yet — and a person passes it.

@@ 2069-2071
The analyst reads the project's sessions, the passed session's trace, and the last week's counts.

@@ 2072-2075
The analyst and then the owner try to add a policy version; the analyst lists the policies.

@@ 2076
The analyst tries the harness's own project — which belongs to another organisation — under this organisation's address.

@@ 2077-2078
The one session is listed; its trace has one attempt, and it passed.

@@ 2079-2080
The attempt carries its numbers: the age probability, the line it met, and the liveness evidence.

@@ 2081
Reading a trace made no token.

@@ 2082
The counts show one pass.

@@ 2083-2085
An analyst may not add a policy version; the owner may, and it is listed as `console_18@1`.

@@ 2086
Another organisation's project, named under this organisation, is not found — the check that the project belongs to the organisation in the address.

@@ 2089-2092
**Test — the console's webhooks (Phase 5).** An owner and an analyst. Private addresses are allowed, so the endpoint can point at this computer (`localhost:9`, where nothing listens — nothing is sent in this test).

@@ 2093-2099
The owner signs up, the analyst signs up and is added, and the owner finds the project.

@@ 2100-2101
The project's webhook address, and an endpoint for finished sessions.

@@ 2103-2106
The analyst tries to add it; the owner adds it; the analyst tries to list them; the owner lists the live ones.

@@ 2107-2111
The owner sends a test event, reads the endpoint's deliveries, and replays the first.

@@ 2112-2115
The owner tries to delete it as a live endpoint, then deletes it as the test one it is; lists again; and reads the audit log.

@@ 2116
An analyst may not add one.

@@ 2117
The owner's new endpoint came with its secret, and is a test endpoint.

@@ 2118
An analyst may not even list them; and the live mode has none — modes never mix.

@@ 2119-2120
The test event is waiting to be delivered (no worker runs here); the replay is accepted.

@@ 2121
The wrong mode is "not found"; the deletion worked, and the list is empty.

@@ 2122-2123
The audit log names a person (`user:…`), not a key, for both the creation and the deletion.

@@ 2126-2133
**Test — the owner rules for members (Phase 5).** Three people, each with their own browser: an owner, an admin, and one more.

@@ 2134-2138
All three sign up.

@@ 2139-2141
The owner adds the admin as an admin, and the third person as an analyst.

@@ 2142-2143
Everyone's IDs: the third person's from the answer, the owner's from `/me`, the admin's from the member list.

@@ 2145-2147
The admin promotes the analyst to developer, then tries to make them an owner; the only owner tries to step down to admin.

@@ 2148-2149
The owner makes the third person an owner, and then steps down — allowed now, since there are two.

@@ 2150-2152
The admin tries to remove the new owner; the new owner removes the admin; and tries to remove an ID that isn't anyone's.

@@ 2153-2154
What remains, and the audit log.

@@ 2155
An admin may change a member who isn't an owner.

@@ 2156
An admin may not make an owner.

@@ 2157
The last owner may not step down.

@@ 2158
With two owners, one may.

@@ 2159
An admin may not remove an owner; an owner may remove an admin; an unknown member is not found.

@@ 2160
Left: the first owner (now an admin) and the new owner.

@@ 2161-2162
The audit log holds exactly the four changes that happened — refusals leave no trace.

@@ 2165-2170
**Test — unstorable text is refused (Phase 5).** Sign in with an address containing NUL — the kind of input the contract tests found: `422 invalid_text`, not a server error.

@@ 2173-2176
**Test — the model page** (§5.5.2): anyone signed in can read which model is deciding and how it was made, and nothing about its build.

@@ 2177-2178
Run the API with the trained model's manifest — the one with sources and measured bounds — rather than the stub.

@@ 2179-2181
Ask before signing in, then sign up and ask again.

@@ 2182
Signed out, the answer is the usual 401.

@@ 2183-2185
Signed in: the version, that it isn't calibrated for live use, its permitted use, the faces it learnt from and the number it was calibrated on.

@@ 2186-2187
The line for 18: its 7.5 % risk budget, and a measured worst case for minors within it.

@@ 2188-2189
And the line's adult outcomes: the youngest band, 18 to 20, measured on 330 faces — most of whom, as the comment says, a line this careful sends to a stronger check.

@@ 2190-2191
And none of the internal details of the file — the checksum, the build's commit, the file's name or the note that it was built from uncommitted code — is in the answer.

@@ 2194-2198
**Test — the model's performance is published to anyone, without its scores** (§5.5.9). With the trained model, ask `/v1/model` with no key and no sign-in…

@@ 2199-2201
…and it answers, cacheable for five minutes, with the model's version and the fact that it isn't calibrated.

@@ 2202-2203
The 18+ line carries its bounds (the minors' under its budget) and its adults' outcomes, starting with 18 to 20.

@@ 2204
But neither of each line's two scores: they would only help someone tuning an attack.

@@ 2207-2211
**Test — the production session cookie (Phase 5).** The browser tests now run with a plain cookie (WebKit drops `Secure` ones on plain HTTP), so this test checks the real one: with the production setting, sign up and read the `Set-Cookie` header.

@@ 2212-2213
Sign up.

@@ 2214-2215
The cookie's name starts with `__Host-`, so browsers insist it is `Secure`, for path `/`, with no `Domain`: no other site can set or read it.

@@ 2216-2217
Its attributes include `HttpOnly` (no script can read it), `Secure` (HTTPS only), `Path=/` and `SameSite=Lax`.

@@ 2218
And no `Domain`, which would share it with other hosts.

@@ 2221-2227
**Test — switching an endpoint off and on** (Phase 5). A website registers an endpoint.

@@ 2228-2230
Switch it off, send a test event, and read its deliveries.

@@ 2231-2233
Switch it back on, and do the same.

@@ 2234
And try to switch an endpoint that doesn't exist.

@@ 2235
The answers said off, then on.

@@ 2236
While off, nothing was queued for it.

@@ 2237
Back on, the test event waits to be delivered.

@@ 2238
An unknown endpoint is not found.

@@ 2241-2243
**Test — listing sessions by outcome and by reference** (Phase 5).

@@ 2244-2246
A session with the website's reference `order-1`, which a person passes.

@@ 2247
Another, `order-2`, not yet started.

@@ 2248-2252
List the passed ones; the one for `order-2`; one for a reference nobody used; and ask for an outcome that doesn't exist.

@@ 2253-2255
Exactly the passed session; exactly `order-2`'s; and nothing.

@@ 2256
An unknown outcome is refused, not silently ignored.

@@ 2259-2264
**Test — recovery codes, and switching codes off** (Phase 5).

@@ 2265-2269
Sign up, ask for a secret, and confirm the current code: the answer holds the recovery codes.

@@ 2270-2273
Sign in with the first recovery code, typed as someone might copy it from paper — capitals, a space instead of the dash. Keep the new session's CSRF token.

@@ 2274
Try the same recovery code again.

@@ 2275-2276
Ask for a fresh set, then try one of the old set.

@@ 2277-2283
Try to switch codes off with a wrong password, then with the right password and the next code.

@@ 2284
Sign in with the password alone.

@@ 2285
Ten different codes, each of the shape `abcde-fghij`.

@@ 2286
The recovery code signed in, and nine are left.

@@ 2287
Each works once.

@@ 2288
The fresh set shares nothing with the old, and the old no longer works.

@@ 2289
A wrong password is refused.

@@ 2290-2291
With the right password and code, codes are off — and the password alone signs in again.

@@ 406-407
The face check's count: nothing in the totals, one step-up among the decided face checks.

@@ 80-81
For the document checks (§5.6.2): `Tesseract`, to find out whether OCR is available, and `specimen_jpeg`, which draws a photographed specimen passport.

@@ 86-94
`TESSERACT` — how to run Tesseract here: installed, or in the project's OCR container; `None` if neither answers, and then the document tests are skipped.

@@ 322-325
**`specimen`** — a photographed specimen passport (ICAO's Utopia) with the test portrait's face and the given date of birth, expiring in 2036.

@@ 328-336
**`document_attempt`** — the step-up's document check, as the verify page will send it: a new challenge; selfie frames whose labels follow its poses; the document's photo as one more file; all posted to `/stepup/mrz`.

@@ 339-346
**Test — after a step-up, a document decides**, run twice: an adult's passport (born 1990), which must pass, and a 12-year-old's (born 2014), which must fail.

@@ 347-351
Its docstring says what is proved. Without Tesseract the test is skipped, not failed.

@@ 352-356
A face check at 16 for an 18+ policy can't decide (`step_up`); then the document check.

@@ 357
Afterwards, ask for another challenge: a decided session must refuse it.

@@ 358-360
Read the session as the website would, and the public signing keys.

@@ 361-369
And read, straight from the database, what was kept of the document check.

@@ 370-373
The face check stepped up; the document decided; no further check is possible; the session is completed with the document's outcome.

@@ 374-377
The token says the age, and **how** it was decided — a face estimate, a document's MRZ and a face match — at `basic` assurance.

@@ 378-379
Something was kept; of the document, the year and month of birth — and **no name and no document number** appear anywhere in what was kept.

@@ 382-389
**Test — the document check is open only to a session sent there.** Straight after starting, with no face attempt, it's refused with `session_not_awaiting_step_up`.

@@ 271-274
**Test — the Python SDK runs a whole check against the real API** (§5.9.1), as a Python website would.

@@ 275-281
Through the API's own test transport, the SDK's `AsyncClient` creates a session; the person's side (start, face attempt) runs as in the other tests, with the session's secret taken from its link; and the SDK reads the result.

@@ 282-285
The API's public keys, served to the SDK through a fake address (the SDK fetches them itself, but this test has no network).

@@ 286-295
The SDK verifies the token itself — issuer, audience, age, session — and the session is completed with a pass that allows entry at 18, under the policy asked for.

@@ 38
Since Phase 9, the software passkey device (`passkey_device.py`), shared with `test_webauthn.py`.

@@ 1373-1380
**`add_passkey`** — ask for the options, let the device answer, and send that with a name and the password (a test may change any field); the device's own ID isn't part of a registration's body.

@@ 1383-1385
**`passkey_sign_in`** — get a challenge and send the device's signed answer.

@@ 1388-1394
**Test — a passkey is added with the password, then signs in alone, once per challenge** (Phase 9, §5.9.2). One device, and a second that was never registered.

@@ 1395-1400
In one browser: sign up; try adding the passkey with a wrong password; add it; add it again; list.

@@ 1401-1407
In a second, fresh browser: sign in with the passkey; use one answer twice; try the unregistered device; and an answer made on another site.

@@ 1408-1411
Remove the passkey, try to sign in with it, remove it again, and read the audit log.

@@ 1412-1425
A wrong password is refused; the passkey is added once (`409` the second time); it is listed, unused. The passkey alone signs in, with a session cookie. The reused answer, the unregistered passkey and the other site's answer are refused, each with its code. Once removed, it signs nobody in, and removing it again is `404`. The audit log has the additions, removals and sign-ins.

@@ 1428-1435
**Test — with one-time codes on, adding a passkey needs a code too.** Switch them on, then add a passkey without a code and with the next one.

@@ 1436-1439
Without a code: refused. With one: added.

@@ 32
Since Phase 9 also the software Age Pass holder (`age_pass_holder.py`), shared with `test_agepass.py`.

@@ 902-912
**`passed_with_age_passes`** — a session under a policy, passed by the face check, then asking for a batch of passes for the holder's keys; the holder keeps them if they came.

@@ 915-926
**`present_age_pass`** — a new session answered with one of the holder's passes: start, ask for a nonce, present.

@@ 929-933
**Test — an Age Pass from one check completes the next without a camera, once** (Phase 9, §5.9.3).

@@ 934-943
A policy that accepts passes; a passed check that gives out twenty; and a second request for the same check.

@@ 944-948
A new session answered with pass 0; its result and the public keys; pass 0 again on a third session; pass 1 on a fourth.

@@ 949-958
The pass-decided session asking for passes of its own; a session under a preset asking for a nonce; that session's view; and the issuer metadata.

@@ 959-971
Passes come once, twenty, stating 13, 16 and 18; a pass completes a session whose token says `age_pass`; a used pass is refused but the next works; a pass can't renew itself; no preset takes passes; and the issuer metadata points at the keys.

@@ 974-981
**Test — a pass must reach the session's age and be made for this session.** Two policies that take passes, at 18 and 21, and a batch from an 18+ check.

@@ 982-995
An 18+ pass for a 21+ session; a proof naming another session; and a second presentation on a nonce already used.

@@ 996-1011
A check that passed twenty minutes ago (its completion time moved back in the database) asking for passes.

@@ 1012-1015
A key with a private part.

@@ 1016-1020
Each refused with its own code: line too low, wrong audience, nonce used, too late; and the private part refused by the request's own schema.

@@ 488-494
**Sessions refuse foreign return addresses and unknown policies**, each with its own code. (Until 8 Nov this test also checked that live sessions were refused with the stand-in model; since D24 they are decided by an ID document — the next test.)

@@ 497-500
**`anti_spoofing_verdict`**: the real inference service, with one thing stood in for — the anti-spoofing networks' verdict on the selfie. A live session requires it, and the test service, which trusts the frames' labels, can't give it. The OCR, the face match and every other check stay real.

@@ 502-509
A transport that passes each request to the real service and, for the document check only, rewrites its answer as if the networks had measured the selfie from the images and found it real (0.99).

@@ 511
The wrapped transport, for `harness(inference_via=…)`.

@@ 514-519
**D24 end to end**: with the stand-in age model, a live session is created, says it is document-only, refuses face attempts, and is decided by the passport and the selfie alone; its token says so. Test sessions are unchanged.

@@ 520-521
Reading the passport needs Tesseract; without it the test is skipped.

@@ 522-524
A test session first: its start says it is *not* document-only.

@@ 525-529
Then a live one, with the stood-in verdict: created, and started.

@@ 530-531
A face attempt, and a document attempt with a specimen passport of someone born in 1990.

@@ 532-534
What the website sees afterwards, and the keys to check the token's signature.

@@ 535-538
The test session isn't document-only; the live one was created (`201`), started in progress and document-only, and its face attempt was refused with `document_required`.

@@ 539-540
The document passed it, and the session completed, live.

@@ 541-543
The token's `methods` are the document and the face match only — no `face_estimation` — and its `model` is `null`: no age model decided.

@@ 546-557
**Discovery and readiness.** The configuration document names Ed25519 and admits the model is uncalibrated; the key set may be cached for 5 minutes and holds only Ed25519 keys; and `/readyz` reports both databases as `ok`. And it says live checks are decided by a document (`live_checks`, D24).

@@ 1493-1498
**Test — a project made in the console** (decisions D28, D29, and deploy step 7): an owner makes a project with its website's origin, a key for it, and a session that returns there; origins are checked and written one way; changes are audited; developers can't make projects.

@@ 1499-1505
An owner signs up; a second person signs up and is added as a developer.

@@ 1506-1511
A project with two spellings of the same origin…

@@ 1512-1515
…four origins that aren't allowed: a path, `http` for another computer, a wildcard, another scheme…

@@ 1516-1518
…and a project the developer tries to make.

@@ 1519-1524
The owner renames the project and replaces its origins, adding this computer's demo shop.

@@ 1525-1527
A key for the project.

@@ 1528-1537
A session returning to the shop's origin — written in capitals, with a path and a query — and one returning to another website.

@@ 1538
The audit log.

@@ 1539-1541
The project was made, its origins written one way with the duplicate dropped; the four others were refused.

@@ 1542-1544
The developer was refused; the rename and the new origins took.

@@ 1545-1546
The session was accepted — only the origin counts — and the other website's refused.

@@ 1547-1550
The audit log ends with the project made, changed and given a key; the change records the name from and to.

@@ 1553-1554
**Test — at most 20 projects** (decision D28).

@@ 1555-1560
An owner makes 20 more projects, one after another.

@@ 1561-1562
Nineteen are made — the one made at sign-up counts too — and the twentieth is refused with `too_many_projects`.

@@ 1565-1569
**Test — keys listed and stopped** (decision D30): the console lists a project's keys, never their secrets, and stops one at once.

@@ 1570-1578
An owner, and an analyst added to the organisation; the default project's keys address.

@@ 1579-1581
Two keys; the first works.

@@ 1582-1583
The owner lists the keys; the analyst tries to.

@@ 1584-1586
The first key is stopped, then stopped again, and an unknown key is stopped.

@@ 1587-1590
Both keys are tried, the states listed, and the audit log read.

@@ 1591-1594
The first key worked before; the list is newest first and holds no secret; the analyst was refused.

@@ 1595-1596
Stopping twice is fine both times; an unknown key isn't found.

@@ 1597-1599
The stopped key is refused at once, the other still works, and the states say so.

@@ 1600
Stopping twice is recorded once.

@@ 1603-1606
**Test — invitations** (decision D44): no e-mail is sent; the invitation waits, can be cancelled, and is taken when that address signs up.

@@ 1607-1611
An address without an account; an owner and their organisation's members address.

@@ 1612-1613
The address is invited as a developer — in capitals — and then again.

@@ 1614-1616
The waiting invitation is listed, cancelled, and the list is empty.

@@ 1617-1620
Invited again, as an analyst; the person signs up; the list and the audit log are read.

@@ 1621-1625
The first invitation was pending, written in lower case; the second was refused; the list showed the developer invitation, and cancelling emptied it.

@@ 1626-1628
The new person belongs to their own organisation and to the one that invited them, as an analyst; the invitation was taken.

@@ 1629-1632
The audit log tells the story in order, never names the address, and its chain is intact.

@@ 1635-1638
**Test — a new password** (decision D31): every other session ends; this browser carries on with a new cookie.

@@ 1639-1644
A person signs up in one browser and signs in from another.

@@ 1645-1650
A change with a wrong current password, and one with too short a new password…

@@ 1651-1653
…and a proper change.

@@ 1654-1658
Both browsers try again; the old and the new password are tried; the audit log is read.

@@ 1659-1661
The other browser had signed in; the wrong password and the weak one were refused.

@@ 1662-1664
The change gave a new CSRF token; this browser is still signed in, the other is not.

@@ 1665-1666
The old password no longer works, the new one does, and the change is in the audit log.

@@ 1669-1674
**Test — deleting an account** (decision D32): an organisation of one closes, a shared one loses a member, an only owner with others must hand over first, and the address is free again.

@@ 1675-1682
Four people, each in their own browser.

@@ 1683-1690
The leaving person signs up — their organisation of one — and makes a key.

@@ 1691-1697
Another person's organisation adds them as a developer.

@@ 1698-1699
A deletion with a wrong password, then a proper one.

@@ 1700-1703
Afterwards: their browser, their key, the shared organisation's members and its audit log.

@@ 1704
The same address signs up again.

@@ 1706-1712
An owner whose organisation has another member tries to delete their account…

@@ 1713-1719
…makes the other member an owner, and tries again.

@@ 1720
The organisation's members afterwards.

@@ 1721-1724
The wrong password was refused; the deletion worked; the browser is signed out; the organisation of one was closed, so its key stopped at once.

@@ 1725-1727
The shared organisation lost the member, recorded it with an intact chain — and the audit log never names the address.

@@ 1728
Nothing of the address was kept: it signed up again.

@@ 1729-1731
The only owner was refused until ownership was handed over; then the organisation stayed, with the other person as its owner.

@@ 1734-1736
**Test — sign-in limits.** At most 2 attempts at once, then one every two minutes.

@@ 811-814
**Test — the verify page's calls are limited per network address** (Phase 4, open item 5, 9 Nov): a flood from one address is refused before it reaches the database, while another address carries on.

@@ 815-817
A tiny limit — three calls, then one every 100 seconds — and four quick calls from the test's address.

@@ 818-820
Another address calls once.

@@ 821-824
Three were answered and the fourth refused, with `rate_limited` and a `Retry-After`; the other address was answered.
