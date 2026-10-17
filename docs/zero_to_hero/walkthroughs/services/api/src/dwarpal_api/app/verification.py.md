---
fingerprint: 67726c8d0fc0bc4b
---
The **use cases**: each step of a verification, written once as an ordinary function. This is where the pieces meet — the domain's rules, the database, Valkey, the inference service and the signing keys.

Here is the whole journey of one check, with the function that handles each step:

```
website's server ── create_session ──► session "created"; returns a link to the verify page
      ⋮  (the person opens the link)
verify page ─────── start_flow ──────► "in_progress"; returns a flow token
verify page ─────── issue_challenge ─► a one-time challenge
verify page ─────── submit_face_attempt ► decision: retry (go round again) · step up · pass · fail
verify page ─────── finish ──────────► the address to send the person back to
      ⋮  (the person returns to the website)
website's server ── result_view ─────► the outcome, plus a signed age token (mint_token)
```

Every function follows the same pattern: **check** (refuse anything wrong with an `ApiError`), **act** (inside a database transaction), **answer** (a plain dict that the HTTP layer sends as JSON).

@@ 1
The docstring lists the steps.

@@ 3
The project-wide type-hint setting.

@@ 5-9
From the standard library: `uuid`, `dataclass`, date-and-time types (`timedelta` is a length of time, such as "30 minutes"), `Any`, and two helpers for web addresses: `urlsplit` cuts an address into its parts, and `urlencode` builds a safe `?name=value` query.

@@ 11-12
SQLAlchemy's `select` (build a query) and `func` (database functions such as `count`, added in Phase 3), and the async session types.

@@ 14-26
Our own pieces from every layer: the adapters (inference client, key ring, Valkey store, tables), the domain (IDs, challenges, decisions, keys, policies, the state machine), the error type, the settings, and the shared contracts. `new_challenge` (Phase 3) picks a random liveness challenge.

@@ 28
`FLOW_STATUSES` — the statuses in which the verify page may (re)start a flow: in progress, awaiting a step-up, or completed. Including the finished states matters for real people: someone who reloads the page *after* finishing gets their result shown again and can still continue back to the website, instead of meeting an error.

@@ 29
`CHALLENGES_PER_ATTEMPT = 2` — each allowed attempt comes with two challenges, the spare covering a reload or a lost connection. With 3 attempts, a session gets at most 6 challenges (`adapters/store.py`).

@@ 32-39
**`Services`** — one object that carries everything a use case needs: the settings, the database session factory, the Valkey store, the inference client, the key ring and the model manifest. The app builds it once at start-up (`main.py`), and every request receives the same one.

Passing one "toolbox" in, instead of having each function create its own connections, is called **dependency injection**. Tests build a toolbox around test containers, and the use cases never know the difference.

@@ 41-42
**`now`** — the one place the use cases read the clock, always in UTC. Being a method of `Services`, it could be replaced in a test that needs to travel in time.

@@ 44-45
**`new_id`** — a fresh UUIDv7 (`domain/ids.py`) for the current moment. `.timestamp()` gives seconds since 1970 as a decimal number; times 1000, then `int`, gives whole milliseconds.

@@ 48-50
**`origin_of`** — the **origin** of an address: its scheme, host and port, such as `https://shop.example` or `http://localhost:3100`. Browsers use exactly this unit to decide what counts as "the same website" (§4.13). `urlsplit` cuts the address into parts; `netloc` is the host with its port.

@@ 53-54
**`public_id`** — a session's ID as the outside world sees it: `vs_` plus 26 characters.

@@ 57
**`load_session`** — fetch a session's row by ID. The `*` in the parameter list makes everything after it **keyword-only**: callers must write `lock=True`, never just `True`, so a reader always knows what the `True` means.

@@ 58
Build the query: `SELECT … FROM verification_sessions WHERE id = …`.

@@ 59
Run it. With `lock=True`, `.with_for_update()` adds `FOR UPDATE`: PostgreSQL **locks the row** until this transaction ends, and any other transaction that wants to change the same row waits its turn (§4.10). That is how two simultaneous attempts on one session are processed one after the other, never interleaved.

@@ 60-62
Not found? Refuse with `404`. Otherwise return the row.

@@ 65-69
**`parse_session_id`** — turn `vs_…` text into a UUID. A malformed ID gets *exactly the same* `404` as an ID that doesn't exist, so a stranger poking at the API learns nothing from the difference.

@@ 72-74
**`expire_if_due`** — if the session is open and past its expiry time, move it to `expired`. This is **lazy expiry**: nothing watches the clock in the background; a session's status is corrected the next time anyone looks at it. Every use case calls this before trusting a status.

@@ 77-79
**`create_session`** — step 1, called by a website's server with its API key. It receives the toolbox, the caller's project, the key's mode (live or test), the policy's name, and two optional values: where to send the person afterwards, and the website's own reference. It returns the new row *and* the client secret in plain form — the only moment it exists.

@@ 80-86
Find the policy, and make sure the model has thresholds for it. Each failure becomes a `422` with its own code. `{policy_id!r}` puts the requested name in quotes in the message.

@@ 87-88
**Live sessions need a calibrated model.** While the age model is only a stand-in, a live key is refused with `409` — the system must never make real decisions about real people with placeholder thresholds. Test keys keep working.

@@ 89-90
**The return address must belong to the project.** If it didn't, someone with a stolen API key could send people to a look-alike site after the check. This kind of hole is called an **open redirect**.

@@ 91
Read the clock once and make the session's ID. Two names can be set in one line: `a, b = x, y`.

@@ 92
Make the client secret, which names the session.

@@ 93-108
Build the row: every column of `verification_sessions` with its starting value. It starts `created`, with no outcome, no attempts and no model yet. It expires `session_ttl_s` seconds (30 minutes) from now. Only the secret's *digest* is stored.

@@ 109-111
Open a database session, add the row, and commit. `async with` closes the database session afterwards, even if an error happens.

@@ 112
Return the row and the plain-text secret.

@@ 115
**`start_flow`** — step 2, called by the verify page when the person opens the link. The page sends the client secret, which it found in the link.

@@ 116-117
Load the session **with a lock**, because its status may change.

@@ 118-119
**Check the secret first, before revealing anything.** Without the right secret, the caller learns nothing — not even whether the session is finished.

@@ 120
Correct the status if the session has expired.

@@ 121-122
A fresh session moves from `created` to `in_progress`. For any other status, nothing changes.

@@ 123
Load the session's project, for its display name.

@@ 124
Commit: save the status change and release the lock.

@@ 125-126
Only the statuses in `FLOW_STATUSES` may have a flow. An expired or canceled session gets `409`, with its status in the message.

@@ 127
Look up the policy, for its minimum age.

@@ 128
Open a flow token in Valkey, valid for 15 minutes. From now on, the page proves who it is with this token rather than the secret.

@@ 129-136
The page's view of the session — exactly what the verify page needs to draw itself, and nothing more:

- its ID, status and outcome (if any);
- the project's name, for "*Amber Cellars* asks you to confirm you are 18 or over";
- the minimum age;
- the attempts left — `max(..., 0)` makes sure it never shows a negative number.

@@ 137
Return the token and the view.

@@ 140
**`issue_challenge`** — step 3, before each face attempt.

@@ 141-142
Load the session (no lock needed: nothing is changed in the database).

@@ 143-144
Challenges only for sessions in progress.

@@ 145
The challenge budget: the policy's attempts × 2.

@@ 146-149
Ask the store to save a fresh random challenge — `new_challenge()` picks its poses and colours — for this session. `settings = svc.settings` gives a short local name, only to keep the next line within the line-length limit.

@@ 150-152
Budget used up? Refuse with `429 Too Many Requests`. Otherwise return the challenge.

@@ 155
**`attempt_scores`** — the numbers kept with each attempt, so any decision can be explained later. It is a plain function: no database, no waiting.

@@ 156-157
No analysis at all? Record just that.

@@ 158
Every quality problem that occurred in any frame. The braces build a **set**, which drops duplicates; `sorted` turns it into a list in alphabetical order, so the stored value is always the same for the same problems.

@@ 159-169
The scores: the model's version, how many frames were sent and how many were usable, the problems, the probability and the threshold used, and how long the analysis took (rounded to a tenth of a millisecond). No picture, and no age.

Phase 3 adds `liveness`: the full liveness result — which pose problems were found, the light measurements, any injection signs — turned into a plain dict by `model_dump()`. As the comment says, this is where the *detail* lives. The person sees only the vague reason; the operator can read here which check fired, and the `liveness-report` command (`cli.py`) summarises it.

@@ 172-174
**`submit_face_attempt`** — step 4, the heart of the check. It receives the session (from the flow token), the challenge's ID, the frames' description and the frames themselves. It returns the decision and the number of attempts left.

The function uses **two separate transactions**, with the AI call in between:

```
transaction 1: quick look — is the session in progress?
               use up the challenge (Valkey)
               ask the inference service (≈ 0.1 s, no database held)
transaction 2: lock the row — check again — decide — record — commit
```

Holding a database connection and a row lock while the AI works would make every other request for the same session wait, and could exhaust the connection pool under load.

@@ 175-177
**A quick look first**, without a lock: if the session isn't accepting attempts, stop right away — before using up a challenge or the AI's time.

@@ 178-180
Use up the challenge. Unknown, expired, already used, or belonging to another session: `409`. On success `challenge` is the server's stored copy.

@@ 181-182
Ask the inference service. Before sending, `model_copy(update=…)` makes a copy of the request description with its `challenge` **replaced by the stored one** (Phase 3). Whatever challenge the browser put there — perhaps an easier one — is thrown away, as the comment says. The result may be `None`, which the decision engine treats safely.

@@ 183-184
Now the second transaction: load the row again, this time **locked**.

@@ 185-189
**Check again.** While the AI was working, the session may have expired, or a simultaneous attempt may have finished it. If it is no longer in progress, commit (to save an expiry) and refuse.

@@ 190-208
Decide. `model_ok` is true only if an analysis exists *and* came from a model the manifest covers. `row.attempts_count` is the index of this attempt: 0 for the first.

Phase 3 adds two inputs:

- `failures` — how many of this session's earlier attempts failed the liveness check. The query counts the attempt rows whose `reasons` list **contains** `liveness_check_failed` (`.contains([…])` becomes PostgreSQL's array operator `@>`). `or 0` turns a missing answer into 0.
- `livemode=row.livemode` — so the engine can refuse the test-only liveness evidence in a real session.

@@ 209-219
Record the attempt: a new row with its ID, its session, the kind (`face`), the outcome, the reasons (as a list, because the column is an array) and the scores.

@@ 220-221
Count the attempt, and move the session to the status the outcome requires (`STATUS_AFTER`). `move` refuses any illegal jump.

@@ 222-223
Store the outcome on the session — except for a retry, which isn't an outcome of the session, only of this attempt.

@@ 224-225
Remember which model produced the analysis.

@@ 226-227
If the session is now finished, record when.

@@ 228
How many attempts are left. The HTTP layer never shows a negative number.

@@ 229-230
Commit everything at once — the attempt, the new status, the outcome — and return.

@@ 233
**`finish`** — step 5: where should the page send the person now?

@@ 234-235
Load the session.

@@ 236-237
Only a finished session (completed, or waiting for a step-up) can be left.

@@ 238-239
No return address? Return `None`; the page then simply shows the result.

@@ 240-241
Add `session_id=vs_…` to the return address, so the website knows which check just ended. If the address already has a query (`?…`), the new value joins it with `&` instead. `urlencode` makes sure the value is written safely. Only the session's ID travels through the browser — never the outcome, which the website must fetch itself, using its key.

@@ 244-254
**`created_view`** — what the website receives after creating a session: the ID, an `object` label (a convention that tells programs what kind of thing a JSON object is), the status, mode and policy, the client secret, the expiry time in standard ISO 8601 form, and the **link** for the person:

```
http://localhost:3000/v/vs_01JA8XQ2…#cs=vs_01JA8XQ2…_secret_…
```

The secret sits after the `#`, in the link's **fragment**. Browsers never send the fragment to any server — not to the verify page's server, and not in the `Referer` header to other sites. Only the page's own code, running in the browser, can read it.

@@ 257
**`result_view`** — step 6: the website's server asks for the result, with its API key.

@@ 258-259
Load the session.

@@ 260-261
**Only the project that created a session may read it**, and only with a key of the same mode. A test key can't read live sessions, and one customer can never read another's. Anything else gets the same `404` as a session that doesn't exist.

@@ 262-263
Correct the status if the session has expired.

@@ 264
A completed session gets a **freshly signed token**. Others get none.

@@ 265
Commit: save any expiry, and the record of the token just issued.

@@ 266-280
The result: the session's facts, including the policy's minimum age, the number of attempts, the website's own reference, three times in ISO 8601 form (`completed_at` only once there is one), and the token.

@@ 283
**`mint_token`** — make the signed age token for a completed session.

@@ 284-286
Look up the policy, make a new ID for the token (`jti`), write the project's public ID as the **audience**, and work out when the token expires: 10 minutes from now.

@@ 287
Record that this token was issued — its facts, not the token itself.

@@ 288-303
The **claims** — the facts inside the token. Most names are standard JWT claims (RFC 7519):

| Claim | Meaning |
| :-- | :-- |
| `iss` | the **issuer**: this API |
| `aud` | the **audience**: the one project this token is for |
| `iat`, `nbf`, `exp` | issued at, not valid before, expires at — whole seconds since 1970 |
| `jti` | the token's own unique ID |
| `sid` | the session it reports on |
| `outcome` | `pass`, `fail` or `reject` |
| `age_over_18` | **`true` or `false`**: the answer itself, named after the policy's age (ADR-0020) |
| `assurance` | how strong the check was: `basic` for face estimation alone |
| `methods` | which methods were used |
| `policy`, `model` | which policy and which model version decided |
| `livemode` | whether this was a live check |

Line 274 builds the age claim's *name* from the policy: `f"age_over_{policy.min_age}"` gives `age_over_18` for an 18+ policy and `age_over_16` for a 16+ one. Its value is `True` only for a pass. A website checking for 18+ looks for `age_over_18: true` — so a token from a 13+ check simply doesn't contain the claim it needs, and can't be misused.

!!! key "What is never in a token"
    No estimated age, no picture, no name, and nothing that could identify the person across websites. The token answers one yes-or-no question, for one website, for ten minutes.

@@ 304
Sign the claims with the active key, and return the token.
