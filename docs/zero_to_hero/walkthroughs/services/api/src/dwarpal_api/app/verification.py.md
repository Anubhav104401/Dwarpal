---
fingerprint: b1466dcb6c4b50ff
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

@@ 17-40
Our own pieces from every layer: the adapters (inference client, key ring and master key, Valkey store, tables — including both kinds of daily count), the webhook use cases and the policy look-ups (`app/webhooks.py`, `app/policies.py`), and the domain's identifiers, challenges, decisions, keys, policies, session states, the document check's rules (`domain/stepup.py`, §5.6.2) and the time bands; then our error class, the settings, and the shared contracts — including `DocumentAnalysis`.

@@ 42
`FLOW_STATUSES` — the statuses in which the verify page may (re)start a flow: in progress, awaiting a step-up, or completed. Including the finished states matters for real people: someone who reloads the page *after* finishing gets their result shown again and can still continue back to the website, instead of meeting an error.

@@ 43-44
`SHOWN_STATUSES` — the statuses in which the verify page may still be *shown*: those of a flow, and a fresh `created` session (the page opens it). `|` joins two sets. Only these may be framed by a website (`frame_ancestor`, below).

@@ 45
`MAX_PAGE` — the most sessions one page of the list may hold (Phase 4).

@@ 46
`CHALLENGES_PER_ATTEMPT = 2` — each allowed attempt comes with two challenges, the spare covering a reload or a lost connection. With 3 attempts, a session gets at most 6 challenges (`adapters/store.py`).

@@ 47
`HOUR_S` — an hour, in seconds: the window of the per-device budgets.

@@ 52-59
**`Services`** — one object that carries everything a use case needs: the settings, the database session factory, the Valkey store, the inference client, the key ring and the model manifest. The app builds it once at start-up (`main.py`), and every request receives the same one.

Passing one "toolbox" in, instead of having each function create its own connections, is called **dependency injection**. Tests build a toolbox around test containers, and the use cases never know the difference.

@@ 60-61
`idempotency_secret` — the secret that seals stored idempotent replies (`app/idempotency.py`), derived from the master key at start-up. The default, empty bytes, is only for code that builds a toolbox without one.

@@ 62-63
`master` — the master key, which seals webhook endpoints' secrets (`app/webhooks.py`). Optional only so that code building a toolbox without webhooks needn't supply one.

@@ 65-66
**`now`** — the one place the use cases read the clock, always in UTC. Being a method of `Services`, it could be replaced in a test that needs to travel in time.

@@ 68-69
**`new_id`** — a fresh UUIDv7 (`domain/ids.py`) for the current moment. `.timestamp()` gives seconds since 1970 as a decimal number; times 1000, then `int`, gives whole milliseconds.

@@ 72-74
**`origin_of`** — the **origin** of an address: its scheme, host and port, such as `https://shop.example` or `http://localhost:3100`. Browsers use exactly this unit to decide what counts as "the same website" (§4.13). `urlsplit` cuts the address into parts; `netloc` is the host with its port.

@@ 77-78
**`public_id`** — a session's ID as the outside world sees it: `vs_` plus 26 characters.

@@ 81-82
**`policy_label`** — how a session names its policy in every answer: the preset's name, or the project policy's `name@version` (the same as `Policy.label`, worked out from the row alone).

@@ 85
**`load_session`** — fetch a session's row by ID. The `*` in the parameter list makes everything after it **keyword-only**: callers must write `lock=True`, never just `True`, so a reader always knows what the `True` means.

@@ 86
Build the query: `SELECT … FROM verification_sessions WHERE id = …`.

@@ 87
Run it. With `lock=True`, `.with_for_update()` adds `FOR UPDATE`: PostgreSQL **locks the row** until this transaction ends, and any other transaction that wants to change the same row waits its turn (§4.10). That is how two simultaneous attempts on one session are processed one after the other, never interleaved.

@@ 88-90
Not found? Refuse with `404`. Otherwise return the row.

@@ 93-97
**`parse_session_id`** — turn `vs_…` text into a UUID. A malformed ID gets *exactly the same* `404` as an ID that doesn't exist, so a stranger poking at the API learns nothing from the difference.

@@ 100-102
**`expire_if_due`** — if the session is open and past its expiry time, move it to `expired`. This is **lazy expiry**: nothing watches the clock in the background; a session's status is corrected the next time anyone looks at it. Every use case calls this before trusting a status.

Since Phase 4 it is `async` and is given the toolbox and the database session: an expiry is news a website may want, so it is announced.

@@ 103
Write the `expired` event, in the same transaction that saves the new status.

@@ 106-107
**`announce`** — what a use case calls when its session has just completed or expired: `record_final`, with the toolbox's ID maker.

@@ 110-115
**`record_final`** — the record of a finished session, written **inside the transaction** that saves the change. It takes only what it needs (a database session, an ID maker, the row and the time), so that the operator's sweep (`app/maintenance.py`) can call it too, without a toolbox. The docstring says why it is inside the transaction. Sent separately after the commit, the event could be lost in a crash between the two; sent before, a failed commit would announce an outcome that never happened. Saved together, both are kept or neither is.

@@ 116-118
Choose the event type, and write the event (`app/webhooks.py`) with a summary of the session as its data — never a token.

@@ 119-125
The day's count it belongs to: project, mode, today's date, the policy's label, and the outcome — `expired`, or the decision (`pass`, `fail`, `reject`).

@@ 126-128
**Add one to that count**, in a single statement. `insert(…).on_conflict_do_update(…)` means: insert a row with `sessions=1`, but if a row with the same five key values already exists, add one to its `sessions` instead. Two sessions finishing at the same moment can't lose a count, because the database does the adding.

@@ 163-165
**`create_session`** — step 1, called by a website's server with its API key. It receives the toolbox, the caller's project, the key's mode (live or test), the policy's name, and two optional values: where to send the person afterwards, and the website's own reference. It returns the new row *and* the client secret in plain form — the only moment it exists.

@@ 166-168
Open a unit of work **confined to this project** (`tenant`), and find the policy: a preset, or the **newest** version of the project's own policy of that name (`latest`, which refuses an unknown name with `422 unknown_policy`). From now on the session follows that exact version, whatever is added later.

@@ 169-172
Unless the check is document-only, the age model will decide it: it must have thresholds for this policy's age and risk budget. (Before D24, a live session with an uncalibrated model was refused here with `409 model_not_calibrated`; now it is created, and the document decides it.)

@@ 173-174
If the model has no thresholds for the policy, the session is refused with `422 policy_not_supported`.

@@ 175-176
If a return address was given, its **origin** must be one of the project's allowed origins. Otherwise refuse with `422`: a stolen key can't be used to send people to an attacker's site.

@@ 177-178
Read the clock and make the session's ID once. Then make the client secret, built on the session's public ID.

@@ 179-196
The row: its ID, project and mode; the policy's name **and version** (Phase 4); the starting status `created` and no outcome yet; only the secret's **digest**; the return address and the website's reference; no attempts and no model yet; created now, not yet started, expiring after the session lifetime from the settings (30 minutes by default); not completed.

@@ 197-198
Add the row and commit. `async with` closes the database session afterwards, even if an error happens. Had the row carried another project's ID, the database itself would refuse it: the policy lets a tenant write only rows it is allowed to see.

@@ 199
Return the row and the plain-text secret.

@@ 202
**`start_flow`** — step 2, called by the verify page when the person opens the link. The page sends the client secret, which it found in the link.

@@ 203-205
Turn the public ID into a UUID, then open a unit of work confined to the session's own project (`session_tenant`), and load the session **with a lock**, because its status may change.

@@ 206-207
**Check the secret first, before revealing anything.** Without the right secret, the caller learns nothing — not even whether the session is finished.

@@ 208
Correct the status if the session has expired, announcing the expiry if so.

@@ 209-210
A fresh session moves from `created` to `in_progress`. For any other status, nothing changes.

@@ 212
Load the session's project, for its display name.

@@ 213
Look up the session's **pinned** policy version before the transaction ends: its minimum age and attempts appear in the answer.

@@ 214
Commit: save the status change and release the lock.

@@ 215-216
Only the statuses in `FLOW_STATUSES` may have a flow. An expired or canceled session gets `409`, with its status in the message.

@@ 217
Open a flow token in Valkey, valid for 15 minutes. From now on, the page proves who it is with this token rather than the secret.

@@ 218-231
The page's view of the session — exactly what the verify page needs to draw itself, and nothing more:

- its ID, status and outcome (if any);
- the project's name, for "*Amber Cellars* asks you to confirm you are 18 or over";
- the minimum age;
- the attempts left — `max(..., 0)` makes sure it never shows a negative number;
- the **return origin** (decision D16): the website the session returns to, as an origin (`https://shop.example`), or `None` without a return address. Inside that website's frame, it is the only page the verify page will talk to (`verify-flow.tsx`).

Since Phase 9 also whether the website's policy accepts **Age Passes**, and whether the session is live or a test: the page offers a kept pass only where one is accepted, and only a pass of the same mode (§5.9.3). And since D24, **`document_only`**: whether this check is decided by an ID document — the page then leads to the document check instead of the camera.

@@ 232
Return the token and the view.

@@ 235-238
**`frame_ancestor`** (decision D16) — which website, if any, may show this session's verify page inside a frame. *Frame ancestors* are the pages around a frame. The answer is the origin of the session's return address: the website gave it when it created the session, with its secret key, and it had to be one of the project's allowed origins (`create_session`). No session means no website.

@@ 239-242
A malformed ID: no website — no error, because the answer only goes into a header (`proxy.ts`).

@@ 243-244
Load the session in its own project's tenant. `session.get` finds a row by its key, and gives `None` when there is none, rather than a `404`.

@@ 245-246
No session, no return address, or a session that is over (expired, cancelled): no website.

@@ 247-248
The same for a session past its expiry time that nobody has marked expired yet.

@@ 249
Otherwise, the return address's origin.

@@ 252-254
**`issue_challenge`** — step 3, before each face attempt. It now also receives the browser's device ID and network address (either may be missing), for the per-device budgets.

@@ 255-256
Load the session, inside its own project (no lock needed: nothing is changed in the database).

@@ 257
Load the session's pinned policy too, for its attempts budget.

@@ 258-259
Challenges only for sessions in progress or awaiting their step-up.

@@ 260
Spend one challenge from this device's and this address's hourly budgets — before the session's own budget, so starting fresh sessions can't get around them.

@@ 261
The challenge budget: two per attempt, for the face attempts **and** the document check's attempts (§5.6.2).

@@ 262-265
Ask the store to save a fresh random challenge — `new_challenge()` picks its poses and colours — for this session. `settings = svc.settings` gives a short local name, only to keep the next line within the line-length limit.

@@ 266-268
Budget used up? Refuse with `429 Too Many Requests`. Otherwise return the challenge.

@@ 271
**`spend_device_budgets`** — the per-device budgets.

@@ 272-273
The docstring gives the reason: stop endless trial and error. Someone testing photo after photo against the check could otherwise start session after session; these budgets count across all of a project's sessions.

@@ 274-278
The two budgets as (key, limit) pairs: one for the device ID and one for the network address, each scoped to the project. A missing ID or address gives `None` instead of a pair.

@@ 279-281
Spend one use from each budget that exists (`filter(None, …)` skips the `None`s). If either is spent, refuse with `429 too_many_attempts`; the verify page then tells the person to wait a while.

@@ 284
**`attempt_scores`** — the numbers kept with each attempt, so any decision can be explained later. It is a plain function: no database, no waiting. The decision is optional since Phase 6: a document check keeps its selfie's scores too, but it has no age score or threshold.

@@ 285-286
No analysis at all? Record just that.

@@ 287
Every quality problem that occurred in any frame. The braces build a **set**, which drops duplicates; `sorted` turns it into a list in alphabetical order, so the stored value is always the same for the same problems.

@@ 288-298
The scores: the model's version, how many frames were sent and how many were usable, the problems, the probability and the threshold used (none without a face decision), and how long the analysis took (rounded to a tenth of a millisecond). No picture, and no exact age.

Phase 3 adds `liveness`: the full liveness result — which checks ran and what they found. As the comment says, it is kept for the people who run Dwarpal, and never shown to the person being checked.

@@ 301-303
**`submit_face_attempt`** — step 4, the heart of the check. It receives the session (from the flow token), the challenge's ID, the frames' description and the frames themselves. It returns the decision and the number of attempts left.

The function uses **two separate transactions**, with the AI call in between:

```
transaction 1: quick look — is the session in progress?
               use up the challenge (Valkey)
               ask the inference service (≈ 0.1 s, no database held)
transaction 2: lock the row — check again — decide — record — commit
```

Holding a database connection and a row lock while the AI works would make every other request for the same session wait, and could exhaust the connection pool under load.

@@ 304-309
**A quick look first**, without a lock: if the session isn't accepting attempts, stop right away — before using up a challenge or the AI's time. A document-only session (D24) refuses face attempts too, with `409 document_required`: its age is never estimated.

@@ 310-312
Use up the challenge. Unknown, expired, already used, or belonging to another session: `409`. On success `challenge` is the server's stored copy.

@@ 313-314
Ask the inference service. Before sending, `model_copy(update=…)` makes a copy of the request description with its `challenge` **replaced by the stored one** (Phase 3). Whatever challenge the browser put there — perhaps an easier one — is thrown away, as the comment says. The result may be `None`, which the decision engine treats safely.

@@ 315-316
Now the second transaction, again confined to the session's project: load the row again, this time **locked**.

@@ 317-321
**Check again.** While the AI was working, the session may have expired, or a simultaneous attempt may have finished it. If it is no longer in progress, commit (to save an expiry and its event) and refuse.

@@ 322-340
Decide. `model_ok` is true only if an analysis exists *and* came from a model the manifest covers. `row.attempts_count` is the index of this attempt: 0 for the first.

Phase 3 adds two inputs:

- `failures` — how many of this session's earlier attempts failed the liveness check. The query counts the attempt rows whose `reasons` list **contains** `liveness_check_failed` (`.contains([…])` becomes PostgreSQL's array operator `@>`). `or 0` turns a missing answer into 0.
- `livemode=row.livemode` — so the engine can refuse the test-only liveness evidence in a real session.

Since Phase 4, `policy` is the session's **pinned** version, loaded in the same transaction (`pinned`).

@@ 341-351
Record the attempt: a new row with its ID, its session, the kind (`face`), the outcome, the reasons (as a list, because the column is an array) and the scores.

@@ 352-353
Count the attempt, and move the session to the status the outcome requires (`STATUS_AFTER`). `move` refuses any illegal jump.

@@ 354-355
Store the outcome on the session — except for a retry, which isn't an outcome of the session, only of this attempt.

@@ 356-357
Remember which model produced the analysis.

@@ 360-361
If the session is now finished, record when.

@@ 362
A completed session is announced, in the same transaction.

@@ 363
How many attempts are left. The HTTP layer never shows a negative number.

@@ 364-365
Commit everything at once — the attempt, the new status, the outcome — and return.

@@ 479
**`finish`** — step 5: where should the page send the person now?

@@ 480-481
Load the session, inside its own project.

@@ 482-483
Only a finished session (completed, or waiting for a step-up) can be left.

@@ 484-485
No return address? Return `None`; the page then simply shows the result.

@@ 486-487
Add `session_id=vs_…` to the return address, so the website knows which check just ended. If the address already has a query (`?…`), the new value joins it with `&` instead. `urlencode` makes sure the value is written safely. Only the session's ID travels through the browser — never the outcome, which the website must fetch itself, using its key.

@@ 490-500
**`created_view`** — what the website receives after creating a session: the ID, an `object` label (a convention that tells programs what kind of thing a JSON object is), the status, mode and policy, the client secret, the expiry time in standard ISO 8601 form, and the **link** for the person:

```
http://localhost:3000/v/vs_01JA8XQ2…#cs=vs_01JA8XQ2…_secret_…
```

The secret sits after the `#`, in the link's **fragment**. Browsers never send the fragment to any server — not to the verify page's server, and not in the `Referer` header to other sites. Only the page's own code, running in the browser, can read it.

`policy` is the label of the pinned version (`policy_label`).

@@ 503
**`result_view`** — step 6: the website's server asks for the result, with its API key.

@@ 504-505
Load the session in a unit of work confined to the **caller's** project — the one its API key belongs to. Another customer's session is simply invisible here: `load_session` finds nothing and answers `404`.

@@ 506-507
**Only the project that created a session may read it**, and only with a key of the same mode. A test key can't read live sessions. The project comparison is now a second, redundant guard: the database has already hidden other projects' sessions. Keeping it costs nothing and protects against a mistake in a policy. Anything else gets the same `404` as a session that doesn't exist.

@@ 508-509
Correct the status if the session has expired, announcing the expiry if so.

@@ 510-513
Load the pinned policy (for the token's lifetime and the age in its claim name), and give a completed session a **freshly signed token**, saying how it was decided (`methods_of`). Others get none.

@@ 514
Commit: save any expiry, and the record of the token just issued.

@@ 515-520
**`summary_view`** — what a website may see of a session **without** a token being made: the list shows this for every session, and the result view adds to it. Making a token is an event (it is recorded in `issued_tokens`), so listing a hundred sessions must not make a hundred tokens. A session past its expiry time is shown as `expired`, even if no request has yet saved that change.

@@ 521-533
The summary: the ID and `object` label; the status (corrected for expiry); the outcome, mode and policy label; the number of attempts; the website's own reference; and three times in ISO 8601 form (`completed_at` only once there is one).

@@ 536-542
**`SessionFilter`** (Phase 5, §5.5.2) — which sessions to list: those with this **outcome**, and with this **reference** of the website's own (`external_ref`, such as an order number); `None` means any. There is deliberately no status filter: "expired" isn't stored but worked out when a session is read, so filtering on the stored status would miss expired sessions and list them under their old status. `frozen=True` makes it unchangeable.

@@ 545-552
**`list_sessions`** — one page of a project's sessions, for one mode (Phase 4). It takes the page size, the cursor, and (since Phase 5) a filter — no filter by default. A function's default value is made once and shared by every call, which is a classic trap with changeable values; this one is frozen, so sharing it is safe, as the comment tells the linter (`B008`).

@@ 553-555
The docstring explains the **cursor**. The obvious way to page through a list is "skip the first 40, give me 20" (an *offset*). But if three sessions are created while someone is reading page 2, everything moves along by three, and page 3 repeats rows. A cursor says instead "the 20 sessions older than this one". Because a UUIDv7 begins with the time it was made, "older" is just "has a smaller ID", and new sessions can't disturb pages already read.

@@ 556-558
The query: sessions of this project, in this mode only. A test key never sees live sessions.

@@ 559-560
With a cursor, only sessions **older** than it. `parse_session_id` turns `vs_…` back into a UUID, and refuses a malformed one with `404`.

@@ 561-564
Keep only the sessions with the chosen outcome, and with the chosen reference — exactly equal.

@@ 565
Newest first, and **one more** than the page size (never more than `MAX_PAGE` + 1). The extra row is a cheap way to find out whether another page exists, without counting every row.

@@ 566-567
Run the query in a unit of work confined to the project.

@@ 568-569
The page is the first `limit` rows; if the extra one came back, there is more.

@@ 570-575
The answer: a list object with the page's summaries, whether there is more, and the cursor for the next page — the ID of the page's last session — or `None` at the end. A client simply repeats the request with `starting_after` set to `next_cursor` until `has_more` is false.

@@ 578-585
**`mint_token`** — make the signed age token for a completed session. Since Phase 4 the caller passes in the session's pinned policy; since Phase 6, how the session was decided (`methods`), which defaults to the face alone.

@@ 586-587
Make a new ID for the token (`jti`), write the project's public ID as the **audience**, and work out when the token expires: after the policy's token lifetime (10 minutes for the presets).

@@ 588
Record that this token was issued — its facts, not the token itself.

@@ 589-604
The **claims** — the facts inside the token. Most names are standard JWT claims (RFC 7519):

| Claim | Meaning |
| :-- | :-- |
| `iss` | the **issuer**: this API |
| `aud` | the **audience**: the one project this token is for |
| `iat`, `nbf`, `exp` | issued at, not valid before, expires at — as whole seconds since 1970 |
| `jti` | the token's own unique ID (it was recorded above) |

The rest are Dwarpal's own: the session ID, the outcome, a yes/no claim named after the age (`age_over_18: true`), the **assurance** level and the **methods** used, the policy, the age model's version, and live or test mode. A document check is still `basic` assurance (§5.6.2): a browser can't read a passport's chip. No age, no birth date, no image — only the yes or no a website needs.

@@ 605
Sign the claims with the active key, and return the token.

@@ 608-611
**`introspect`** — check an age token on a website's behalf (Phase 4). Some websites would rather ask than verify signatures themselves: this is the idea of RFC 7662, "token introspection". The answer is `{"active": true, …claims}` the first time, and `{"active": false}` for everything else, with no reason given, so a forger learns nothing from trying.

@@ 612-613
Read the clock once; prepare the one refusal.

@@ 614-616
Verify the signature (`KeyRing.verify`). Then the token must be from this issuer, and addressed to **this** website's project: another website's token is just as inactive as a forged one.

@@ 617-618
It must not have expired. (`isinstance` guards against a genuine but odd token without a whole-number `exp`.)

@@ 619-622
Its ID (`jti`) must be a UUID.

@@ 623-627
In the website's own tenant, find the record made when the token was issued, **locked**, so that two simultaneous introspections can't both be first. A token never issued, or already introspected, is inactive. Otherwise note the time and commit: from now on, this token is spent.

@@ 628
The first, genuine introspection: active, with the token's claims.

@@ 131-134
**`record_face_stage`** — count a face check that has reached a decision (anything but a retry), for the dashboard: its outcome, and the band of time from opening the verify page to the decision. Only the band is kept, never the exact time, and the count is not tied to the session.

@@ 135
When the person began. A session opened before `started_at` existed has none, so its time is counted from when it was created.

@@ 136-142
Which cell of the day's counts this check belongs in: the project, test or live, today, the outcome, and the band its time falls in (`band_of`).

@@ 143-145
Add one to that cell, or create it with one — the same *upsert* as the outcome counts in `record_final`.

@@ 211
The first time the verify page opens the session, note the moment: the face check's time is counted from here.

@@ 358-359
Once the face check has decided — anything but a retry — count it. A step-up counts here at once, though the session itself isn't finished.

@@ 48-49
**`CHALLENGE_STATUSES`** (§5.6.2) — where a challenge may be issued: a session in progress (for a face attempt), or one awaiting its step-up (for the selfie of the document check, which proves liveness the same way).

@@ 368-372
**`document_scores`** (§5.6.2) — what is kept of a document check. Its docstring states the rule from the design (§9.1): the results, and of the document only its kind, issuer, the year and month of birth and its expiry. No analysis at all? Say so.

@@ 373-385
Of the document, if one was read: its layout, type and issuer; the **year and month** of birth (formatted as `1990-01`), never the day; the expiry; and the repairs its reading needed. The name, the document number and the nationality were dropped inside the parser and never reach this point.

@@ 386-390
And the check's other results: why no zone was read (if none was), how many faces the document showed, how alike the faces were (to three decimal places), the selfie's own scores — liveness included — and how long the analysis took.

@@ 393-402
**`submit_document_attempt`** (§5.6.2) — the step-up with an ID document. It takes what a face attempt takes, plus the document's photo, and returns the decision and the attempts left. It is open only to a session that the face check sent there. Since D24 it is also open from the start in a document-only session.

@@ 403-405
First a quick look, without a lock: may the document check be used now (`document_open`)? If not, `409` — before a challenge is used up or the inference service is asked anything.

@@ 406-409
Use up the challenge (once only, as for faces), and put the server's own challenge into the frames' description: the selfie is judged against what the server asked for, never against what the browser says it was asked.

@@ 410
Ask the inference service to read the document and compare the faces. `None` if it failed: the rules below turn that into a retry.

@@ 411-417
Then the decision, in one transaction holding the session's row lock — the same pattern as a face attempt: reload with a lock, expire if due, and make sure the session is still awaiting its step-up (two uploads at once can't both decide). ("May still use" is `document_open` again: awaiting its step-up, or a document-only session still in progress.)

@@ 418-425
Load the pinned policy, and the reasons of this session's earlier document checks.

@@ 426-427
Count those that failed the pose challenge (a second failure is rejected, as for faces), and decide with `decide_document`, using today's date for the age and expiry.

@@ 428-438
Record the attempt, of kind `document`, with its outcome, reasons and scores — the only trace the document leaves.

@@ 439-443
Anything but a retry ends the session: completed, with the step-up's outcome, the completion time, and the announcement (webhook event and daily count) in the same transaction. It comes from either state — awaiting a step-up, or in progress for a document-only session — and `move` checks the change is allowed.

@@ 444-446
Work out the attempts left, save everything, and return.

@@ 449-458
**`methods_of`** (§5.6.2) — how a completed session was decided, for its token's `methods` claim. First (Phase 9): a session answered with an Age Pass says just `age_pass` — no face was seen this time.

@@ 459-467
Count the session's document checks that reached a decision (not retries)…

@@ 468-476
…and if there is one, the session was decided by a document. If it also had a face attempt, by a document after a face estimate: `face_estimation`, `document_mrz` and `face_match`; a document-only session (D24) never had its age estimated: `document_mrz` and `face_match`. Otherwise it was decided by the face alone.

@@ 148-152
**`document_only`** — decision D24 (8 Nov): while no age model is certified for live use (its manifest says `calibrated: false`), a **live** check is decided by an ID document alone. The age estimate is never used for it, so the face check is skipped; the document check's own selfie, taken with the same random challenge, still shows that a live person is there and that the document is theirs. Test checks are unchanged.

@@ 155-160
**`document_open`** — whether the document check may be used now: when a face check sent the person there (`awaiting_step_up`), or, in a document-only session, from the start (`in_progress`).
