---
fingerprint: 606b063e724266a7
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

@@ 17-39
Our own pieces from every layer: the adapters (inference client, key ring and master key, Valkey store, tables — including both kinds of daily count), the webhook use cases and the policy look-ups (`app/webhooks.py`, `app/policies.py`, Phase 4), the domain (IDs, challenges, decisions, keys, policies, the state machine, bands of time), the error type, the settings, and the shared contracts. `new_challenge` (Phase 3) picks a random liveness challenge.

@@ 41
`FLOW_STATUSES` — the statuses in which the verify page may (re)start a flow: in progress, awaiting a step-up, or completed. Including the finished states matters for real people: someone who reloads the page *after* finishing gets their result shown again and can still continue back to the website, instead of meeting an error.

@@ 42
`MAX_PAGE` — the most sessions one page of the list may hold (Phase 4).

@@ 43
`CHALLENGES_PER_ATTEMPT = 2` — each allowed attempt comes with two challenges, the spare covering a reload or a lost connection. With 3 attempts, a session gets at most 6 challenges (`adapters/store.py`).

@@ 44
`HOUR_S` — an hour, in seconds: the window of the per-device budgets.

@@ 47-54
**`Services`** — one object that carries everything a use case needs: the settings, the database session factory, the Valkey store, the inference client, the key ring and the model manifest. The app builds it once at start-up (`main.py`), and every request receives the same one.

Passing one "toolbox" in, instead of having each function create its own connections, is called **dependency injection**. Tests build a toolbox around test containers, and the use cases never know the difference.

@@ 55-56
`idempotency_secret` — the secret that seals stored idempotent replies (`app/idempotency.py`), derived from the master key at start-up. The default, empty bytes, is only for code that builds a toolbox without one.

@@ 57-58
`master` — the master key, which seals webhook endpoints' secrets (`app/webhooks.py`). Optional only so that code building a toolbox without webhooks needn't supply one.

@@ 60-61
**`now`** — the one place the use cases read the clock, always in UTC. Being a method of `Services`, it could be replaced in a test that needs to travel in time.

@@ 63-64
**`new_id`** — a fresh UUIDv7 (`domain/ids.py`) for the current moment. `.timestamp()` gives seconds since 1970 as a decimal number; times 1000, then `int`, gives whole milliseconds.

@@ 67-69
**`origin_of`** — the **origin** of an address: its scheme, host and port, such as `https://shop.example` or `http://localhost:3100`. Browsers use exactly this unit to decide what counts as "the same website" (§4.13). `urlsplit` cuts the address into parts; `netloc` is the host with its port.

@@ 72-73
**`public_id`** — a session's ID as the outside world sees it: `vs_` plus 26 characters.

@@ 76-77
**`policy_label`** — how a session names its policy in every answer: the preset's name, or the project policy's `name@version` (the same as `Policy.label`, worked out from the row alone).

@@ 80
**`load_session`** — fetch a session's row by ID. The `*` in the parameter list makes everything after it **keyword-only**: callers must write `lock=True`, never just `True`, so a reader always knows what the `True` means.

@@ 81
Build the query: `SELECT … FROM verification_sessions WHERE id = …`.

@@ 82
Run it. With `lock=True`, `.with_for_update()` adds `FOR UPDATE`: PostgreSQL **locks the row** until this transaction ends, and any other transaction that wants to change the same row waits its turn (§4.10). That is how two simultaneous attempts on one session are processed one after the other, never interleaved.

@@ 83-85
Not found? Refuse with `404`. Otherwise return the row.

@@ 88-92
**`parse_session_id`** — turn `vs_…` text into a UUID. A malformed ID gets *exactly the same* `404` as an ID that doesn't exist, so a stranger poking at the API learns nothing from the difference.

@@ 95-97
**`expire_if_due`** — if the session is open and past its expiry time, move it to `expired`. This is **lazy expiry**: nothing watches the clock in the background; a session's status is corrected the next time anyone looks at it. Every use case calls this before trusting a status.

Since Phase 4 it is `async` and is given the toolbox and the database session: an expiry is news a website may want, so it is announced.

@@ 98
Write the `expired` event, in the same transaction that saves the new status.

@@ 101-102
**`announce`** — what a use case calls when its session has just completed or expired: `record_final`, with the toolbox's ID maker.

@@ 105-110
**`record_final`** — the record of a finished session, written **inside the transaction** that saves the change. It takes only what it needs (a database session, an ID maker, the row and the time), so that the operator's sweep (`app/maintenance.py`) can call it too, without a toolbox. The docstring says why it is inside the transaction. Sent separately after the commit, the event could be lost in a crash between the two; sent before, a failed commit would announce an outcome that never happened. Saved together, both are kept or neither is.

@@ 111-113
Choose the event type, and write the event (`app/webhooks.py`) with a summary of the session as its data — never a token.

@@ 114-120
The day's count it belongs to: project, mode, today's date, the policy's label, and the outcome — `expired`, or the decision (`pass`, `fail`, `reject`).

@@ 121-123
**Add one to that count**, in a single statement. `insert(…).on_conflict_do_update(…)` means: insert a row with `sessions=1`, but if a row with the same five key values already exists, add one to its `sessions` instead. Two sessions finishing at the same moment can't lose a count, because the database does the adding.

@@ 143-145
**`create_session`** — step 1, called by a website's server with its API key. It receives the toolbox, the caller's project, the key's mode (live or test), the policy's name, and two optional values: where to send the person afterwards, and the website's own reference. It returns the new row *and* the client secret in plain form — the only moment it exists.

@@ 146-148
Open a unit of work **confined to this project** (`tenant`), and find the policy: a preset, or the **newest** version of the project's own policy of that name (`latest`, which refuses an unknown name with `422 unknown_policy`). From now on the session follows that exact version, whatever is added later.

@@ 149-152
Make sure the age model has thresholds for this policy's age and risk budget; if not, refuse with `422 policy_not_supported`.

@@ 153-154
A **live** key may only be used once the model is calibrated (Phase 2). Until then, live sessions are refused with `409`.

@@ 155-156
If a return address was given, its **origin** must be one of the project's allowed origins. Otherwise refuse with `422`: a stolen key can't be used to send people to an attacker's site.

@@ 157-158
Read the clock and make the session's ID once. Then make the client secret, built on the session's public ID.

@@ 159-176
The row: its ID, project and mode; the policy's name **and version** (Phase 4); the starting status `created` and no outcome yet; only the secret's **digest**; the return address and the website's reference; no attempts and no model yet; created now, not yet started, expiring after the session lifetime from the settings (30 minutes by default); not completed.

@@ 177-178
Add the row and commit. `async with` closes the database session afterwards, even if an error happens. Had the row carried another project's ID, the database itself would refuse it: the policy lets a tenant write only rows it is allowed to see.

@@ 179
Return the row and the plain-text secret.

@@ 182
**`start_flow`** — step 2, called by the verify page when the person opens the link. The page sends the client secret, which it found in the link.

@@ 183-185
Turn the public ID into a UUID, then open a unit of work confined to the session's own project (`session_tenant`), and load the session **with a lock**, because its status may change.

@@ 186-187
**Check the secret first, before revealing anything.** Without the right secret, the caller learns nothing — not even whether the session is finished.

@@ 188
Correct the status if the session has expired, announcing the expiry if so.

@@ 189-190
A fresh session moves from `created` to `in_progress`. For any other status, nothing changes.

@@ 192
Load the session's project, for its display name.

@@ 193
Look up the session's **pinned** policy version before the transaction ends: its minimum age and attempts appear in the answer.

@@ 194
Commit: save the status change and release the lock.

@@ 195-196
Only the statuses in `FLOW_STATUSES` may have a flow. An expired or canceled session gets `409`, with its status in the message.

@@ 197
Open a flow token in Valkey, valid for 15 minutes. From now on, the page proves who it is with this token rather than the secret.

@@ 198-205
The page's view of the session — exactly what the verify page needs to draw itself, and nothing more:

- its ID, status and outcome (if any);
- the project's name, for "*Amber Cellars* asks you to confirm you are 18 or over";
- the minimum age;
- the attempts left — `max(..., 0)` makes sure it never shows a negative number.

@@ 206
Return the token and the view.

@@ 209-211
**`issue_challenge`** — step 3, before each face attempt. It now also receives the browser's device ID and network address (either may be missing), for the per-device budgets.

@@ 212-213
Load the session, inside its own project (no lock needed: nothing is changed in the database).

@@ 214
Load the session's pinned policy too, for its attempts budget.

@@ 215-216
Challenges only for sessions in progress.

@@ 217
Spend one challenge from this device's and this address's hourly budgets — before the session's own budget, so starting fresh sessions can't get around them.

@@ 218
The challenge budget: the pinned policy's attempts × 2.

@@ 219-222
Ask the store to save a fresh random challenge — `new_challenge()` picks its poses and colours — for this session. `settings = svc.settings` gives a short local name, only to keep the next line within the line-length limit.

@@ 223-225
Budget used up? Refuse with `429 Too Many Requests`. Otherwise return the challenge.

@@ 228
**`spend_device_budgets`** — the per-device budgets.

@@ 229-230
The docstring gives the reason: stop endless trial and error. Someone testing photo after photo against the check could otherwise start session after session; these budgets count across all of a project's sessions.

@@ 231-235
The two budgets as (key, limit) pairs: one for the device ID and one for the network address, each scoped to the project. A missing ID or address gives `None` instead of a pair.

@@ 236-238
Spend one use from each budget that exists (`filter(None, …)` skips the `None`s). If either is spent, refuse with `429 too_many_attempts`; the verify page then tells the person to wait a while.

@@ 241
**`attempt_scores`** — the numbers kept with each attempt, so any decision can be explained later. It is a plain function: no database, no waiting.

@@ 242-243
No analysis at all? Record just that.

@@ 244
Every quality problem that occurred in any frame. The braces build a **set**, which drops duplicates; `sorted` turns it into a list in alphabetical order, so the stored value is always the same for the same problems.

@@ 245-255
The scores: the model's version, how many frames were sent and how many were usable, the problems, the probability and the threshold used, and how long the analysis took (rounded to a tenth of a millisecond). No picture, and no age.

Phase 3 adds `liveness`: the full liveness result — which pose problems were found, the light measurements, any injection signs — turned into a plain dict by `model_dump()`. As the comment says, this is where the *detail* lives. The person sees only the vague reason; the operator can read here which check fired, and the `liveness-report` command (`cli.py`) summarises it.

@@ 258-260
**`submit_face_attempt`** — step 4, the heart of the check. It receives the session (from the flow token), the challenge's ID, the frames' description and the frames themselves. It returns the decision and the number of attempts left.

The function uses **two separate transactions**, with the AI call in between:

```
transaction 1: quick look — is the session in progress?
               use up the challenge (Valkey)
               ask the inference service (≈ 0.1 s, no database held)
transaction 2: lock the row — check again — decide — record — commit
```

Holding a database connection and a row lock while the AI works would make every other request for the same session wait, and could exhaust the connection pool under load.

@@ 261-263
**A quick look first**, without a lock: if the session isn't accepting attempts, stop right away — before using up a challenge or the AI's time.

@@ 264-266
Use up the challenge. Unknown, expired, already used, or belonging to another session: `409`. On success `challenge` is the server's stored copy.

@@ 267-268
Ask the inference service. Before sending, `model_copy(update=…)` makes a copy of the request description with its `challenge` **replaced by the stored one** (Phase 3). Whatever challenge the browser put there — perhaps an easier one — is thrown away, as the comment says. The result may be `None`, which the decision engine treats safely.

@@ 269-270
Now the second transaction, again confined to the session's project: load the row again, this time **locked**.

@@ 271-275
**Check again.** While the AI was working, the session may have expired, or a simultaneous attempt may have finished it. If it is no longer in progress, commit (to save an expiry and its event) and refuse.

@@ 276-294
Decide. `model_ok` is true only if an analysis exists *and* came from a model the manifest covers. `row.attempts_count` is the index of this attempt: 0 for the first.

Phase 3 adds two inputs:

- `failures` — how many of this session's earlier attempts failed the liveness check. The query counts the attempt rows whose `reasons` list **contains** `liveness_check_failed` (`.contains([…])` becomes PostgreSQL's array operator `@>`). `or 0` turns a missing answer into 0.
- `livemode=row.livemode` — so the engine can refuse the test-only liveness evidence in a real session.

Since Phase 4, `policy` is the session's **pinned** version, loaded in the same transaction (`pinned`).

@@ 295-305
Record the attempt: a new row with its ID, its session, the kind (`face`), the outcome, the reasons (as a list, because the column is an array) and the scores.

@@ 306-307
Count the attempt, and move the session to the status the outcome requires (`STATUS_AFTER`). `move` refuses any illegal jump.

@@ 308-309
Store the outcome on the session — except for a retry, which isn't an outcome of the session, only of this attempt.

@@ 310-311
Remember which model produced the analysis.

@@ 314-315
If the session is now finished, record when.

@@ 316
A completed session is announced, in the same transaction.

@@ 317
How many attempts are left. The HTTP layer never shows a negative number.

@@ 318-319
Commit everything at once — the attempt, the new status, the outcome — and return.

@@ 322
**`finish`** — step 5: where should the page send the person now?

@@ 323-324
Load the session, inside its own project.

@@ 325-326
Only a finished session (completed, or waiting for a step-up) can be left.

@@ 327-328
No return address? Return `None`; the page then simply shows the result.

@@ 329-330
Add `session_id=vs_…` to the return address, so the website knows which check just ended. If the address already has a query (`?…`), the new value joins it with `&` instead. `urlencode` makes sure the value is written safely. Only the session's ID travels through the browser — never the outcome, which the website must fetch itself, using its key.

@@ 333-343
**`created_view`** — what the website receives after creating a session: the ID, an `object` label (a convention that tells programs what kind of thing a JSON object is), the status, mode and policy, the client secret, the expiry time in standard ISO 8601 form, and the **link** for the person:

```
http://localhost:3000/v/vs_01JA8XQ2…#cs=vs_01JA8XQ2…_secret_…
```

The secret sits after the `#`, in the link's **fragment**. Browsers never send the fragment to any server — not to the verify page's server, and not in the `Referer` header to other sites. Only the page's own code, running in the browser, can read it.

`policy` is the label of the pinned version (`policy_label`).

@@ 346
**`result_view`** — step 6: the website's server asks for the result, with its API key.

@@ 347-348
Load the session in a unit of work confined to the **caller's** project — the one its API key belongs to. Another customer's session is simply invisible here: `load_session` finds nothing and answers `404`.

@@ 349-350
**Only the project that created a session may read it**, and only with a key of the same mode. A test key can't read live sessions. The project comparison is now a second, redundant guard: the database has already hidden other projects' sessions. Keeping it costs nothing and protects against a mistake in a policy. Anything else gets the same `404` as a session that doesn't exist.

@@ 351-352
Correct the status if the session has expired, announcing the expiry if so.

@@ 353-354
Load the pinned policy (for the token's lifetime and the age in its claim name), and give a completed session a **freshly signed token**. Others get none.

@@ 355
Commit: save any expiry, and the record of the token just issued.

@@ 356-361
**`summary_view`** — what a website may see of a session **without** a token being made: the list shows this for every session, and the result view adds to it. Making a token is an event (it is recorded in `issued_tokens`), so listing a hundred sessions must not make a hundred tokens. A session past its expiry time is shown as `expired`, even if no request has yet saved that change.

@@ 362-374
The summary: the ID and `object` label; the status (corrected for expiry); the outcome, mode and policy label; the number of attempts; the website's own reference; and three times in ISO 8601 form (`completed_at` only once there is one).

@@ 377-383
**`SessionFilter`** (Phase 5, §5.5.2) — which sessions to list: those with this **outcome**, and with this **reference** of the website's own (`external_ref`, such as an order number); `None` means any. There is deliberately no status filter: "expired" isn't stored but worked out when a session is read, so filtering on the stored status would miss expired sessions and list them under their old status. `frozen=True` makes it unchangeable.

@@ 386-393
**`list_sessions`** — one page of a project's sessions, for one mode (Phase 4). It takes the page size, the cursor, and (since Phase 5) a filter — no filter by default. A function's default value is made once and shared by every call, which is a classic trap with changeable values; this one is frozen, so sharing it is safe, as the comment tells the linter (`B008`).

@@ 394-396
The docstring explains the **cursor**. The obvious way to page through a list is "skip the first 40, give me 20" (an *offset*). But if three sessions are created while someone is reading page 2, everything moves along by three, and page 3 repeats rows. A cursor says instead "the 20 sessions older than this one". Because a UUIDv7 begins with the time it was made, "older" is just "has a smaller ID", and new sessions can't disturb pages already read.

@@ 397-399
The query: sessions of this project, in this mode only. A test key never sees live sessions.

@@ 400-401
With a cursor, only sessions **older** than it. `parse_session_id` turns `vs_…` back into a UUID, and refuses a malformed one with `404`.

@@ 402-405
Keep only the sessions with the chosen outcome, and with the chosen reference — exactly equal.

@@ 406
Newest first, and **one more** than the page size (never more than `MAX_PAGE` + 1). The extra row is a cheap way to find out whether another page exists, without counting every row.

@@ 407-408
Run the query in a unit of work confined to the project.

@@ 409-410
The page is the first `limit` rows; if the extra one came back, there is more.

@@ 411-416
The answer: a list object with the page's summaries, whether there is more, and the cursor for the next page — the ID of the page's last session — or `None` at the end. A client simply repeats the request with `starting_after` set to `next_cursor` until `has_more` is false.

@@ 419
**`mint_token`** — make the signed age token for a completed session. Since Phase 4 the caller passes in the session's pinned policy.

@@ 420-421
Make a new ID for the token (`jti`), write the project's public ID as the **audience**, and work out when the token expires: after the policy's token lifetime (10 minutes for the presets).

@@ 422
Record that this token was issued — its facts, not the token itself.

@@ 423-438
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

@@ 439
Sign the claims with the active key, and return the token.

@@ 442-445
**`introspect`** — check an age token on a website's behalf (Phase 4). Some websites would rather ask than verify signatures themselves: this is the idea of RFC 7662, "token introspection". The answer is `{"active": true, …claims}` the first time, and `{"active": false}` for everything else, with no reason given, so a forger learns nothing from trying.

@@ 446-447
Read the clock once; prepare the one refusal.

@@ 448-450
Verify the signature (`KeyRing.verify`). Then the token must be from this issuer, and addressed to **this** website's project: another website's token is just as inactive as a forged one.

@@ 451-452
It must not have expired. (`isinstance` guards against a genuine but odd token without a whole-number `exp`.)

@@ 453-456
Its ID (`jti`) must be a UUID.

@@ 457-461
In the website's own tenant, find the record made when the token was issued, **locked**, so that two simultaneous introspections can't both be first. A token never issued, or already introspected, is inactive. Otherwise note the time and commit: from now on, this token is spent.

@@ 462
The first, genuine introspection: active, with the token's claims.

@@ 126-129
**`record_face_stage`** — count a face check that has reached a decision (anything but a retry), for the dashboard: its outcome, and the band of time from opening the verify page to the decision. Only the band is kept, never the exact time, and the count is not tied to the session.

@@ 130
When the person began. A session opened before `started_at` existed has none, so its time is counted from when it was created.

@@ 131-137
Which cell of the day's counts this check belongs in: the project, test or live, today, the outcome, and the band its time falls in (`band_of`).

@@ 138-140
Add one to that cell, or create it with one — the same *upsert* as the outcome counts in `record_final`.

@@ 191
The first time the verify page opens the session, note the moment: the face check's time is counted from here.

@@ 312-313
Once the face check has decided — anything but a retry — count it. A step-up counts here at once, though the session itself isn't finished.
