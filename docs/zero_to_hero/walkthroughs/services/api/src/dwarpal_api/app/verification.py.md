---
fingerprint: 6b44e4928f80b480
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

@@ 5-10
From the standard library: `uuid`, `Callable` (the type of a function that makes IDs), `dataclass`, date-and-time types (`timedelta` is a length of time, such as "30 minutes"), `Any`, and two helpers for web addresses: `urlsplit` and `urlencode`.

@@ 12-14
SQLAlchemy's `select` (build a query) and `func` (database functions such as `count`, added in Phase 3); PostgreSQL's own `insert`, which can say what to do when a row already exists (Phase 4); and the async session types.

@@ 16
The two tenant helpers (`db.py`, Phase 4): `tenant` confines a unit of work to a project, and `session_tenant` to whichever project owns a verification session. Every database session in this file is opened through one of them, so each use case sees only its own customer's rows.

@@ 17-31
Our own pieces from every layer: the adapters (inference client, key ring and master key, Valkey store, tables — including the daily counts), the webhook use cases and the policy look-ups (`app/webhooks.py`, `app/policies.py`, Phase 4), the domain (IDs, challenges, decisions, keys, policies, the state machine), the error type, the settings, and the shared contracts. `new_challenge` (Phase 3) picks a random liveness challenge.

@@ 33
`FLOW_STATUSES` — the statuses in which the verify page may (re)start a flow: in progress, awaiting a step-up, or completed. Including the finished states matters for real people: someone who reloads the page *after* finishing gets their result shown again and can still continue back to the website, instead of meeting an error.

@@ 34
`MAX_PAGE` — the most sessions one page of the list may hold (Phase 4).

@@ 35
`CHALLENGES_PER_ATTEMPT = 2` — each allowed attempt comes with two challenges, the spare covering a reload or a lost connection. With 3 attempts, a session gets at most 6 challenges (`adapters/store.py`).

@@ 36
`HOUR_S` — an hour, in seconds: the window of the per-device budgets.

@@ 39-46
**`Services`** — one object that carries everything a use case needs: the settings, the database session factory, the Valkey store, the inference client, the key ring and the model manifest. The app builds it once at start-up (`main.py`), and every request receives the same one.

Passing one "toolbox" in, instead of having each function create its own connections, is called **dependency injection**. Tests build a toolbox around test containers, and the use cases never know the difference.

@@ 47-48
`idempotency_secret` — the secret that seals stored idempotent replies (`app/idempotency.py`), derived from the master key at start-up. The default, empty bytes, is only for code that builds a toolbox without one.

@@ 49-50
`master` — the master key, which seals webhook endpoints' secrets (`app/webhooks.py`). Optional only so that code building a toolbox without webhooks needn't supply one.

@@ 52-53
**`now`** — the one place the use cases read the clock, always in UTC. Being a method of `Services`, it could be replaced in a test that needs to travel in time.

@@ 55-56
**`new_id`** — a fresh UUIDv7 (`domain/ids.py`) for the current moment. `.timestamp()` gives seconds since 1970 as a decimal number; times 1000, then `int`, gives whole milliseconds.

@@ 59-61
**`origin_of`** — the **origin** of an address: its scheme, host and port, such as `https://shop.example` or `http://localhost:3100`. Browsers use exactly this unit to decide what counts as "the same website" (§4.13). `urlsplit` cuts the address into parts; `netloc` is the host with its port.

@@ 64-65
**`public_id`** — a session's ID as the outside world sees it: `vs_` plus 26 characters.

@@ 68-69
**`policy_label`** — how a session names its policy in every answer: the preset's name, or the project policy's `name@version` (the same as `Policy.label`, worked out from the row alone).

@@ 72
**`load_session`** — fetch a session's row by ID. The `*` in the parameter list makes everything after it **keyword-only**: callers must write `lock=True`, never just `True`, so a reader always knows what the `True` means.

@@ 73
Build the query: `SELECT … FROM verification_sessions WHERE id = …`.

@@ 74
Run it. With `lock=True`, `.with_for_update()` adds `FOR UPDATE`: PostgreSQL **locks the row** until this transaction ends, and any other transaction that wants to change the same row waits its turn (§4.10). That is how two simultaneous attempts on one session are processed one after the other, never interleaved.

@@ 75-77
Not found? Refuse with `404`. Otherwise return the row.

@@ 80-84
**`parse_session_id`** — turn `vs_…` text into a UUID. A malformed ID gets *exactly the same* `404` as an ID that doesn't exist, so a stranger poking at the API learns nothing from the difference.

@@ 87-89
**`expire_if_due`** — if the session is open and past its expiry time, move it to `expired`. This is **lazy expiry**: nothing watches the clock in the background; a session's status is corrected the next time anyone looks at it. Every use case calls this before trusting a status.

Since Phase 4 it is `async` and is given the toolbox and the database session: an expiry is news a website may want, so it is announced.

@@ 90
Write the `expired` event, in the same transaction that saves the new status.

@@ 93-94
**`announce`** — what a use case calls when its session has just completed or expired: `record_final`, with the toolbox's ID maker.

@@ 97-102
**`record_final`** — the record of a finished session, written **inside the transaction** that saves the change. It takes only what it needs (a database session, an ID maker, the row and the time), so that the operator's sweep (`app/maintenance.py`) can call it too, without a toolbox. The docstring says why it is inside the transaction. Sent separately after the commit, the event could be lost in a crash between the two; sent before, a failed commit would announce an outcome that never happened. Saved together, both are kept or neither is.

@@ 103-105
Choose the event type, and write the event (`app/webhooks.py`) with a summary of the session as its data — never a token.

@@ 106-112
The day's count it belongs to: project, mode, today's date, the policy's label, and the outcome — `expired`, or the decision (`pass`, `fail`, `reject`).

@@ 113-115
**Add one to that count**, in a single statement. `insert(…).on_conflict_do_update(…)` means: insert a row with `sessions=1`, but if a row with the same five key values already exists, add one to its `sessions` instead. Two sessions finishing at the same moment can't lose a count, because the database does the adding.

@@ 118-120
**`create_session`** — step 1, called by a website's server with its API key. It receives the toolbox, the caller's project, the key's mode (live or test), the policy's name, and two optional values: where to send the person afterwards, and the website's own reference. It returns the new row *and* the client secret in plain form — the only moment it exists.

@@ 121-123
Open a unit of work **confined to this project** (`tenant`), and find the policy: a preset, or the **newest** version of the project's own policy of that name (`latest`, which refuses an unknown name with `422 unknown_policy`). From now on the session follows that exact version, whatever is added later.

@@ 124-127
Make sure the age model has thresholds for this policy's age and risk budget; if not, refuse with `422 policy_not_supported`.

@@ 128-129
A **live** key may only be used once the model is calibrated (Phase 2). Until then, live sessions are refused with `409`.

@@ 130-131
If a return address was given, its **origin** must be one of the project's allowed origins. Otherwise refuse with `422`: a stolen key can't be used to send people to an attacker's site.

@@ 132-133
Read the clock and make the session's ID once. Then make the client secret, built on the session's public ID.

@@ 134-150
The row: its ID, project and mode; the policy's name **and version** (Phase 4); the starting status `created` and no outcome yet; only the secret's **digest**; the return address and the website's reference; no attempts and no model yet; created now, expiring after the session lifetime from the settings (30 minutes by default); not completed.

@@ 151-152
Add the row and commit. `async with` closes the database session afterwards, even if an error happens. Had the row carried another project's ID, the database itself would refuse it: the policy lets a tenant write only rows it is allowed to see.

@@ 153
Return the row and the plain-text secret.

@@ 156
**`start_flow`** — step 2, called by the verify page when the person opens the link. The page sends the client secret, which it found in the link.

@@ 157-159
Turn the public ID into a UUID, then open a unit of work confined to the session's own project (`session_tenant`), and load the session **with a lock**, because its status may change.

@@ 160-161
**Check the secret first, before revealing anything.** Without the right secret, the caller learns nothing — not even whether the session is finished.

@@ 162
Correct the status if the session has expired, announcing the expiry if so.

@@ 163-164
A fresh session moves from `created` to `in_progress`. For any other status, nothing changes.

@@ 165
Load the session's project, for its display name.

@@ 166
Look up the session's **pinned** policy version before the transaction ends: its minimum age and attempts appear in the answer.

@@ 167
Commit: save the status change and release the lock.

@@ 168-169
Only the statuses in `FLOW_STATUSES` may have a flow. An expired or canceled session gets `409`, with its status in the message.

@@ 170
Open a flow token in Valkey, valid for 15 minutes. From now on, the page proves who it is with this token rather than the secret.

@@ 171-178
The page's view of the session — exactly what the verify page needs to draw itself, and nothing more:

- its ID, status and outcome (if any);
- the project's name, for "*Amber Cellars* asks you to confirm you are 18 or over";
- the minimum age;
- the attempts left — `max(..., 0)` makes sure it never shows a negative number.

@@ 179
Return the token and the view.

@@ 182-184
**`issue_challenge`** — step 3, before each face attempt. It now also receives the browser's device ID and network address (either may be missing), for the per-device budgets.

@@ 185-186
Load the session, inside its own project (no lock needed: nothing is changed in the database).

@@ 187
Load the session's pinned policy too, for its attempts budget.

@@ 188-189
Challenges only for sessions in progress.

@@ 190
Spend one challenge from this device's and this address's hourly budgets — before the session's own budget, so starting fresh sessions can't get around them.

@@ 191
The challenge budget: the pinned policy's attempts × 2.

@@ 192-195
Ask the store to save a fresh random challenge — `new_challenge()` picks its poses and colours — for this session. `settings = svc.settings` gives a short local name, only to keep the next line within the line-length limit.

@@ 196-198
Budget used up? Refuse with `429 Too Many Requests`. Otherwise return the challenge.

@@ 201
**`spend_device_budgets`** — the per-device budgets.

@@ 202-203
The docstring gives the reason: stop endless trial and error. Someone testing photo after photo against the check could otherwise start session after session; these budgets count across all of a project's sessions.

@@ 204-208
The two budgets as (key, limit) pairs: one for the device ID and one for the network address, each scoped to the project. A missing ID or address gives `None` instead of a pair.

@@ 209-211
Spend one use from each budget that exists (`filter(None, …)` skips the `None`s). If either is spent, refuse with `429 too_many_attempts`; the verify page then tells the person to wait a while.

@@ 214
**`attempt_scores`** — the numbers kept with each attempt, so any decision can be explained later. It is a plain function: no database, no waiting.

@@ 215-216
No analysis at all? Record just that.

@@ 217
Every quality problem that occurred in any frame. The braces build a **set**, which drops duplicates; `sorted` turns it into a list in alphabetical order, so the stored value is always the same for the same problems.

@@ 218-228
The scores: the model's version, how many frames were sent and how many were usable, the problems, the probability and the threshold used, and how long the analysis took (rounded to a tenth of a millisecond). No picture, and no age.

Phase 3 adds `liveness`: the full liveness result — which pose problems were found, the light measurements, any injection signs — turned into a plain dict by `model_dump()`. As the comment says, this is where the *detail* lives. The person sees only the vague reason; the operator can read here which check fired, and the `liveness-report` command (`cli.py`) summarises it.

@@ 231-233
**`submit_face_attempt`** — step 4, the heart of the check. It receives the session (from the flow token), the challenge's ID, the frames' description and the frames themselves. It returns the decision and the number of attempts left.

The function uses **two separate transactions**, with the AI call in between:

```
transaction 1: quick look — is the session in progress?
               use up the challenge (Valkey)
               ask the inference service (≈ 0.1 s, no database held)
transaction 2: lock the row — check again — decide — record — commit
```

Holding a database connection and a row lock while the AI works would make every other request for the same session wait, and could exhaust the connection pool under load.

@@ 234-236
**A quick look first**, without a lock: if the session isn't accepting attempts, stop right away — before using up a challenge or the AI's time.

@@ 237-239
Use up the challenge. Unknown, expired, already used, or belonging to another session: `409`. On success `challenge` is the server's stored copy.

@@ 240-241
Ask the inference service. Before sending, `model_copy(update=…)` makes a copy of the request description with its `challenge` **replaced by the stored one** (Phase 3). Whatever challenge the browser put there — perhaps an easier one — is thrown away, as the comment says. The result may be `None`, which the decision engine treats safely.

@@ 242-243
Now the second transaction, again confined to the session's project: load the row again, this time **locked**.

@@ 244-248
**Check again.** While the AI was working, the session may have expired, or a simultaneous attempt may have finished it. If it is no longer in progress, commit (to save an expiry and its event) and refuse.

@@ 249-267
Decide. `model_ok` is true only if an analysis exists *and* came from a model the manifest covers. `row.attempts_count` is the index of this attempt: 0 for the first.

Phase 3 adds two inputs:

- `failures` — how many of this session's earlier attempts failed the liveness check. The query counts the attempt rows whose `reasons` list **contains** `liveness_check_failed` (`.contains([…])` becomes PostgreSQL's array operator `@>`). `or 0` turns a missing answer into 0.
- `livemode=row.livemode` — so the engine can refuse the test-only liveness evidence in a real session.

Since Phase 4, `policy` is the session's **pinned** version, loaded in the same transaction (`pinned`).

@@ 268-278
Record the attempt: a new row with its ID, its session, the kind (`face`), the outcome, the reasons (as a list, because the column is an array) and the scores.

@@ 279-280
Count the attempt, and move the session to the status the outcome requires (`STATUS_AFTER`). `move` refuses any illegal jump.

@@ 281-282
Store the outcome on the session — except for a retry, which isn't an outcome of the session, only of this attempt.

@@ 283-284
Remember which model produced the analysis.

@@ 285-286
If the session is now finished, record when.

@@ 287
A completed session is announced, in the same transaction.

@@ 288
How many attempts are left. The HTTP layer never shows a negative number.

@@ 289-290
Commit everything at once — the attempt, the new status, the outcome — and return.

@@ 293
**`finish`** — step 5: where should the page send the person now?

@@ 294-295
Load the session, inside its own project.

@@ 296-297
Only a finished session (completed, or waiting for a step-up) can be left.

@@ 298-299
No return address? Return `None`; the page then simply shows the result.

@@ 300-301
Add `session_id=vs_…` to the return address, so the website knows which check just ended. If the address already has a query (`?…`), the new value joins it with `&` instead. `urlencode` makes sure the value is written safely. Only the session's ID travels through the browser — never the outcome, which the website must fetch itself, using its key.

@@ 304-314
**`created_view`** — what the website receives after creating a session: the ID, an `object` label (a convention that tells programs what kind of thing a JSON object is), the status, mode and policy, the client secret, the expiry time in standard ISO 8601 form, and the **link** for the person:

```
http://localhost:3000/v/vs_01JA8XQ2…#cs=vs_01JA8XQ2…_secret_…
```

The secret sits after the `#`, in the link's **fragment**. Browsers never send the fragment to any server — not to the verify page's server, and not in the `Referer` header to other sites. Only the page's own code, running in the browser, can read it.

`policy` is the label of the pinned version (`policy_label`).

@@ 317
**`result_view`** — step 6: the website's server asks for the result, with its API key.

@@ 318-319
Load the session in a unit of work confined to the **caller's** project — the one its API key belongs to. Another customer's session is simply invisible here: `load_session` finds nothing and answers `404`.

@@ 320-321
**Only the project that created a session may read it**, and only with a key of the same mode. A test key can't read live sessions. The project comparison is now a second, redundant guard: the database has already hidden other projects' sessions. Keeping it costs nothing and protects against a mistake in a policy. Anything else gets the same `404` as a session that doesn't exist.

@@ 322-323
Correct the status if the session has expired, announcing the expiry if so.

@@ 324-325
Load the pinned policy (for the token's lifetime and the age in its claim name), and give a completed session a **freshly signed token**. Others get none.

@@ 326
Commit: save any expiry, and the record of the token just issued.

@@ 327-332
**`summary_view`** — what a website may see of a session **without** a token being made: the list shows this for every session, and the result view adds to it. Making a token is an event (it is recorded in `issued_tokens`), so listing a hundred sessions must not make a hundred tokens. A session past its expiry time is shown as `expired`, even if no request has yet saved that change.

@@ 333-345
The summary: the ID and `object` label; the status (corrected for expiry); the outcome, mode and policy label; the number of attempts; the website's own reference; and three times in ISO 8601 form (`completed_at` only once there is one).

@@ 348-350
**`list_sessions`** — one page of a project's sessions, for one mode (Phase 4). It takes the page size and the cursor.

@@ 351-353
The docstring explains the **cursor**. The obvious way to page through a list is "skip the first 40, give me 20" (an *offset*). But if three sessions are created while someone is reading page 2, everything moves along by three, and page 3 repeats rows. A cursor says instead "the 20 sessions older than this one". Because a UUIDv7 begins with the time it was made, "older" is just "has a smaller ID", and new sessions can't disturb pages already read.

@@ 354-356
The query: sessions of this project, in this mode only. A test key never sees live sessions.

@@ 357-358
With a cursor, only sessions **older** than it. `parse_session_id` turns `vs_…` back into a UUID, and refuses a malformed one with `404`.

@@ 359
Newest first, and **one more** than the page size (never more than `MAX_PAGE` + 1). The extra row is a cheap way to find out whether another page exists, without counting every row.

@@ 360-361
Run the query in a unit of work confined to the project.

@@ 362-363
The page is the first `limit` rows; if the extra one came back, there is more.

@@ 364-369
The answer: a list object with the page's summaries, whether there is more, and the cursor for the next page — the ID of the page's last session — or `None` at the end. A client simply repeats the request with `starting_after` set to `next_cursor` until `has_more` is false.

@@ 372
**`mint_token`** — make the signed age token for a completed session. Since Phase 4 the caller passes in the session's pinned policy.

@@ 373-374
Make a new ID for the token (`jti`), write the project's public ID as the **audience**, and work out when the token expires: after the policy's token lifetime (10 minutes for the presets).

@@ 375
Record that this token was issued — its facts, not the token itself.

@@ 376-391
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

The `policy` claim is the pinned version's label: `uk_osa_18`, or `shop_18@2`, so a website can tell exactly which rules a token followed.

@@ 392
Sign the claims with the active key, and return the token.

@@ 395-398
**`introspect`** — check an age token on a website's behalf (Phase 4). Some websites would rather ask than verify signatures themselves: this is the idea of RFC 7662, "token introspection". The answer is `{"active": true, …claims}` the first time, and `{"active": false}` for everything else, with no reason given, so a forger learns nothing from trying.

@@ 399-400
Read the clock once; prepare the one refusal.

@@ 401-403
Verify the signature (`KeyRing.verify`). Then the token must be from this issuer, and addressed to **this** website's project: another website's token is just as inactive as a forged one.

@@ 404-405
It must not have expired. (`isinstance` guards against a genuine but odd token without a whole-number `exp`.)

@@ 406-409
Its ID (`jti`) must be a UUID.

@@ 410-414
In the website's own tenant, find the record made when the token was issued, **locked**, so that two simultaneous introspections can't both be first. A token never issued, or already introspected, is inactive. Otherwise note the time and commit: from now on, this token is spent.

@@ 415
The first, genuine introspection: active, with the token's claims.
