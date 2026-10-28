---
fingerprint: 101c2530376cfd85
---
The use cases of **events and webhooks** (Phase 4, §5.4.3): writing events, and letting a website manage the endpoints that hear about them.

An **event** is a record that something happened — "session `vs_…` completed with outcome `pass`" — kept as it was at that moment. Events are written by `emit`, always inside the same transaction as the change they describe, together with one **delivery** row for each endpoint that wants to hear. The delivery worker (`app/delivery.py`) sends those rows later.

Two event types exist today: `verification_session.completed` and `verification_session.expired`, plus a `webhook_endpoint.test` event a website can send itself.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-8
`uuid`, `Callable` (the type of a function that makes IDs), `datetime`, and from `typing`: `TYPE_CHECKING` (explained at line 19) and `Any`.

@@ 10-11
SQLAlchemy's `func` (for `count`) and `select`, and the session type.

@@ 13-18
The tenant helper, the three tables, the URL check and secret maker, the audit log (step 5), the ID helpers, and our error class.

@@ 20-21
`TYPE_CHECKING` is `False` when the program runs and `True` only while the type checker reads the code. So `Services` is imported for type hints alone. A real import would be a **circle**: `verification.py` imports this module to announce events, and this module would import `verification.py`. Python can't finish loading either. (Until the console's webhook pages, the website API's `Caller` was imported the same way; the use cases now take plain values instead, so the console can call them too.)

@@ 23-26
The event types a website may subscribe to; the test event's type; at most 16 endpoints per project; and how many recent deliveries a list shows.

@@ 29-38
**`event_view`** — an event as receivers see it: its public ID (`evt_…`), the `object` label, its type and mode, when it happened, and its data. This is the body of every webhook, and so exactly what each signature covers.

@@ 41-50
**`endpoint_view`** — an endpoint as the API shows it: ID (`whe_…`), address, events, whether it is on, its mode, and when it was made. **Never the secret.**

@@ 53-65
**`delivery_view`** — a delivery: its ID (`whd_…`), its event, its status and attempts, when it is next due (only while pending), what happened last time, and when it was made and delivered.

@@ 68-77
**`emit`** — write an event. It takes the caller's open database session (so it joins the caller's transaction), a function that makes IDs, the time, the project and mode, the type and data, and optionally `only`: one endpoint that should get it whatever it subscribes to.

@@ 78-79
Its docstring, with the reason it works inside the caller's transaction.

@@ 80-81
Make the event row and add it.

@@ 82-86
Find the endpoints to tell: this project's, in this mode, switched on.

@@ 87-89
Either just the one endpoint, or every endpoint whose `events` list contains this type. `contains([event_type])` becomes PostgreSQL's array operator `@>`, "contains all of".

@@ 90-104
For each, add a delivery: pending, no attempts yet, due **now**, nothing recorded yet.

@@ 105
Return the event (for the test endpoint's answer).

@@ 108-117
**`create_endpoint`** — register an address for a project, in test or live mode, for some event types. `actor` is who the audit log names: a website's key (`("api_key", …)`) or, since the console's webhook pages, a person (`("user", …)`). The organisation's ID is needed for its audit log.

@@ 118-120
Every requested type must exist, and at least one must be asked for.

@@ 121-124
The address must be safe (`adapters/webhooks.py`): otherwise `422 unsafe_webhook_url`, with the reason.

@@ 125-126
The toolbox must have the master key. This can't happen in the running API (`main.py` always supplies it), so it is a programming error, not a refusal.

@@ 127
A new ID, a new secret, and the time.

@@ 128-132
The endpoint's row: its ID, project, mode and address,

@@ 133-134
its secret, **sealed** under the master key with the endpoint's ID as associated data, so a sealed secret copied onto another row won't open,

@@ 135-138
its event types (without repeats, in order), switched on, made now.

@@ 139-142
In the project's tenant, count its endpoints, and refuse a seventeenth with `409`.

@@ 143-146
Save it, and record it in the organisation's audit log in the same transaction, under the actor's name: the endpoint's ID, its address, events and mode — never its secret.

@@ 147-148
Answer with the endpoint **and its secret**. This is the only time the secret is ever shown: the website must store it now.

@@ 151-159
**`load_endpoint`** — find an endpoint by its public ID, in the current tenant and mode. A malformed ID, an unknown one, another tenant's (invisible under row-level security) or one in the other mode all get the same `404`.

@@ 162-168
**`list_endpoints`** — the project's endpoints in this mode, oldest first.

@@ 171-179
**`delete_endpoint`** — for a project, in one mode, by an actor: find it, record its deletion (with its address) in the audit log, and delete it. Its deliveries go with it (the foreign key's `CASCADE`).

@@ 182-190
**`set_enabled`** (Phase 5) — switch an endpoint off or back on, for a project in one mode, by an actor.

@@ 191-192
Switched off, an endpoint keeps its address, events and secret but gets nothing: new events skip it (`emit` only queues for enabled endpoints) and the delivery worker closes any still pending without sending. Useful while a website's receiver is down for maintenance — instead of deleting it and losing the secret.

@@ 193-194
Find it, in this mode.

@@ 195-198
Only if that changes anything: set it, and record `webhook_endpoint.enabled` or `.disabled` in the audit log with its address. Switching off something already off records nothing.

@@ 199-200
Save, and answer with the endpoint as it now is.

@@ 203-204
**`send_test`** — queue a test event for one endpoint.

@@ 205-209
Find the endpoint, and emit a `webhook_endpoint.test` event with a short message, to it alone. Commit.

@@ 210
Answer with the event.

@@ 213-223
**`list_deliveries`** — an endpoint's most recent deliveries, newest first, at most 100.

@@ 226-227
**`replay`** — send a delivery again from the start of the schedule: after a receiver was fixed, or for a dead delivery.

@@ 228-231
A malformed ID is simply "not found".

@@ 232-236
In the tenant, find the delivery, **locked**, and its endpoint; it must exist and be in the caller's mode.

@@ 237-238
Make it pending again, with no attempts, due now, and clear what happened before.

@@ 239-240
Save, and answer with its new state.
