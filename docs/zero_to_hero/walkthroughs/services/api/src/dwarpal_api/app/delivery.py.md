---
fingerprint: aa4e4e6ea1601ee7
---
The **delivery worker** (Phase 4, §5.4.3): a separate, long-running process that empties the **outbox**, the table of webhook deliveries waiting to be sent.

Why not send a webhook directly when a session completes? Because the API's request would then wait for a website's server, which may be slow or down, and because sending in the middle of a transaction would announce an outcome that might not be saved. Instead, the API writes a delivery row in the same transaction as the outcome (`app/webhooks.py`, `emit`), and the worker sends it afterwards. This pattern is called the **transactional outbox**. Nothing is ever announced that wasn't saved, and nothing saved is ever left unannounced.

Three properties make it safe to run several workers at once, and to stop one at any moment:

- **claiming** with `FOR UPDATE SKIP LOCKED`, so two workers never take the same row;
- a **lease**: a claimed row is pushed a minute into the future, so if its worker dies mid-send, another picks it up later;
- **sending outside any transaction**, so a slow receiver never holds a database lock.

@@ 1-5
The docstring: what the worker does, and why it connects as the tables' owner — it works for every project at once, as the command-line tools do.

@@ 7
The project-wide type-hint setting.

@@ 9-13
`asyncio` (to wait between rounds), `json`, `uuid`, `Callable` (the type of the clock function), and dates and lengths of time.

@@ 15-17
`httpx`, SQLAlchemy's `select`, and the session types.

@@ 19-23
The master key (to open each endpoint's sealed secret), the three tables, the sending helpers, the event's public form, and the ID helpers.

@@ 25-26
**`LEASE`** — how long a claimed row belongs to the worker that claimed it: one minute.

@@ 29-39
**`Deliverer`** — the worker. It is given everything it uses: the session factory, the master key, an HTTP client, a function that tells the time, and whether private addresses are allowed. Being given the clock and the client, rather than finding them itself, lets tests replace both: a fake receiver, and a clock they can move a day forward (`test_api.py`).

@@ 41-42
**`deliver_due`** — one round: send up to `limit` deliveries that are due, and say how many were tried.

@@ 43-44
Read the clock once, and open a unit of work.

@@ 45-52
The pending deliveries whose time has come, oldest first, at most `limit`, **locked** — and `skip_locked=True`. Rows another worker has locked at this moment are simply passed over rather than waited for, so two workers running this query at once take different rows.

@@ 53-56
Take them, push each one's next attempt a lease into the future, and commit. The rows are now claimed, and the locks are released at once.

@@ 57-59
Send each one, outside the transaction, and report how many.

@@ 61-65
**`deliver`** — send one delivery. First read the delivery, its endpoint and its event.

@@ 66-67
If any is gone — the website deleted the endpoint meanwhile, which deletes its deliveries — there is nothing to do.

@@ 68-71
A switched-off endpoint isn't sent to. Otherwise send.

@@ 72
Record the result. For a switched-off endpoint it is final: no retries.

@@ 74-79
**`_send`** — check the address **again**, now: a host name that was public when the endpoint was saved may point at a private address today. The check hands back the addresses it found, all public (9 Nov). An unsafe address is a failure, with the reason cut to 200 characters to fit the column.

@@ 80
Open the endpoint's secret. Its ID is the associated data it was sealed with, so a sealed secret copied onto another endpoint wouldn't open.

@@ 81
The body: the event's public form as compact JSON — exactly the bytes that are signed.

@@ 82-84
Sign with the current time, and send — to the addresses just checked, never to the name again: asked twice, its owner could answer with a private address the second time (**DNS rebinding**, closed 9 Nov).

@@ 86-89
**`_record`** — save the result, in a new unit of work, re-reading the row **locked**.

@@ 90-91
If it was deleted meanwhile, stop.

@@ 92-93
Count the attempt, and keep the receiver's status and the reason.

@@ 94
How long until the next try: none for a final failure; otherwise the schedule's next step, or none once it is used up.

@@ 95-96
Accepted: delivered, now.

@@ 97-98
Failed with no tries left: **dead**. A person can replay it later (`app/webhooks.py`, `replay`).

@@ 99-100
Failed, with tries left: due again after the wait.

@@ 101
Save.

@@ 103-110
**`run`** — the worker's whole life: one round after another. If a round found nothing, wait `poll_s` seconds before asking again, so an idle worker doesn't hammer the database. If a round was busy, go straight on. `once` (for the `--once` option) stops after one round.
