---
fingerprint: 39e1936a2d23fa1c
---
The **webhooks API** (Phase 4, §5.4.3) — six endpoints for a website's server, all needing the `webhooks:write` scope:

| Method and path | What it does |
| :-- | :-- |
| `POST /v1/webhook-endpoints` | register an address and the events it wants; the answer shows the signing secret, once |
| `GET /v1/webhook-endpoints` | list the project's endpoints (never their secrets) |
| `DELETE /v1/webhook-endpoints/{id}` | remove one, with its deliveries |
| `POST /v1/webhook-endpoints/{id}/test` | queue a test event for one endpoint |
| `GET /v1/webhook-endpoints/{id}/deliveries` | its most recent deliveries, and how each went |
| `POST /v1/webhook-deliveries/{id}/replay` | send a delivery again from the start of the schedule |

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5
`Annotated` and `Any`.

@@ 7-8
FastAPI's router, dependency marker and `Response` (for the empty answer to a delete); Pydantic's model, settings and field limits.

@@ 10-12
The webhook use cases, the toolbox type, and the gate pieces.

@@ 14
The router. Its prefix is just `/v1`, because these paths start with two different words (`webhook-endpoints` and `webhook-deliveries`).

@@ 15-16
Two **type aliases**: names for long types, written once. `Manager` means "a caller whose key has `webhooks:write`", and `Toolbox` means "the toolbox". Every endpoint below uses both, and reads more clearly for it.

@@ 19-20
**`NewEndpoint`** — the body for registering an endpoint. Unknown fields are refused.

@@ 22
`url` — 8 to 2,000 characters; the use case checks that it is safe.

@@ 23
`events` — at least one, and no more than there are event types.

@@ 26-31
**`create_endpoint`** — `201 Created`: register it for the key's project and mode, naming the key in the audit log.

@@ 34-36
**`list_endpoints`**.

@@ 39-43
**`delete_endpoint`** — the same for a deletion; answers `204 No Content`: done, and nothing to say.

@@ 46-49
**`Switch`** — the body of a switch: just `enabled`, true or false.

@@ 52-57
**`switch_endpoint`** — `PATCH /v1/webhook-endpoints/{id}`: switch it, naming the key in the audit log.

@@ 60-62
**`send_test`** — answers `202 Accepted`: the event is queued, and the worker will send it shortly.

@@ 65-67
**`list_deliveries`** — for one endpoint.

@@ 70-72
**`replay`** — also `202`: queued again.
