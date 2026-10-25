---
fingerprint: 27eaca8a70728339
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

@@ 20-22
`TYPE_CHECKING` is `False` when the program runs and `True` only while the type checker reads the code. So `Services` and `Caller` are imported for type hints alone. A real import would be a **circle**: `verification.py` imports this module to announce events, this module would import `verification.py`, and `deps.py` (where `Caller` lives) imports `verification.py` too. Python can't finish loading any of them first.

@@ 24-27
The event types a website may subscribe to; the test event's type; at most 16 endpoints per project; and how many recent deliveries a list shows.

@@ 30-39
**`event_view`** — an event as receivers see it: its public ID (`evt_…`), the `object` label, its type and mode, when it happened, and its data. This is the body of every webhook, and so exactly what each signature covers.

@@ 42-51
**`endpoint_view`** — an endpoint as the API shows it: ID (`whe_…`), address, events, whether it is on, its mode, and when it was made. **Never the secret.**

@@ 54-66
**`delivery_view`** — a delivery: its ID (`whd_…`), its event, its status and attempts, when it is next due (only while pending), what happened last time, and when it was made and delivered.

@@ 69-78
**`emit`** — write an event. It takes the caller's open database session (so it joins the caller's transaction), a function that makes IDs, the time, the project and mode, the type and data, and optionally `only`: one endpoint that should get it whatever it subscribes to.

@@ 79-80
Its docstring, with the reason it works inside the caller's transaction.

@@ 81-82
Make the event row and add it.

@@ 83-87
Find the endpoints to tell: this project's, in this mode, switched on.

@@ 88-90
Either just the one endpoint, or every endpoint whose `events` list contains this type. `contains([event_type])` becomes PostgreSQL's array operator `@>`, "contains all of".

@@ 91-105
For each, add a delivery: pending, no attempts yet, due **now**, nothing recorded yet.

@@ 106
Return the event (for the test endpoint's answer).

@@ 109-110
**`create_endpoint`** — register an address for the caller's project, for some event types. It takes the whole caller, for the audit log.

@@ 111-113
Every requested type must exist, and at least one must be asked for.

@@ 114-117
The address must be safe (`adapters/webhooks.py`): otherwise `422 unsafe_webhook_url`, with the reason.

@@ 118-119
The toolbox must have the master key. This can't happen in the running API (`main.py` always supplies it), so it is a programming error, not a refusal.

@@ 120
A new ID, a new secret, and the time.

@@ 121-125
The endpoint's row: its ID, project, mode and address,

@@ 126-127
its secret, **sealed** under the master key with the endpoint's ID as associated data, so a sealed secret copied onto another row won't open,

@@ 128-131
its event types (without repeats, in order), switched on, made now.

@@ 132-135
In the project's tenant, count its endpoints, and refuse a seventeenth with `409`.

@@ 136-139
Save it, and record it in the organisation's audit log in the same transaction: the endpoint's ID, its address, events and mode — never its secret.

@@ 140-141
Answer with the endpoint **and its secret**. This is the only time the secret is ever shown: the website must store it now.

@@ 144-152
**`load_endpoint`** — find an endpoint by its public ID, in the current tenant and mode. A malformed ID, an unknown one, another tenant's (invisible under row-level security) or one in the other mode all get the same `404`.

@@ 155-161
**`list_endpoints`** — the project's endpoints in this mode, oldest first.

@@ 164-170
**`delete_endpoint`** — find it, record its deletion (with its address) in the audit log, and delete it. Its deliveries go with it (the foreign key's `CASCADE`).

@@ 173-174
**`send_test`** — queue a test event for one endpoint.

@@ 175-179
Find the endpoint, and emit a `webhook_endpoint.test` event with a short message, to it alone. Commit.

@@ 180
Answer with the event.

@@ 183-193
**`list_deliveries`** — an endpoint's most recent deliveries, newest first, at most 100.

@@ 196-197
**`replay`** — send a delivery again from the start of the schedule: after a receiver was fixed, or for a dead delivery.

@@ 198-201
A malformed ID is simply "not found".

@@ 202-206
In the tenant, find the delivery, **locked**, and its endpoint; it must exist and be in the caller's mode.

@@ 207-208
Make it pending again, with no attempts, due now, and clear what happened before.

@@ 209-210
Save, and answer with its new state.
