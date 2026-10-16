---
fingerprint: 2839f92d27ce279d
---
Two **health endpoints**, asked by whatever runs the service (Docker, a load balancer, Kubernetes) rather than by people:

| Address | Question | Answer |
| :-- | :-- | :-- |
| `GET /livez` | "Is the program alive at all?" | always `200`, if it can answer |
| `GET /readyz` | "Can it do real work right now?" | `200` if PostgreSQL and Valkey both respond, otherwise `503` |

Why two? If `/livez` fails, the program is stuck, and the right fix is to **restart** it. If `/readyz` fails, the program is fine but something it needs is down — restarting won't help, but traffic should go elsewhere until it recovers. Mixing the two up leads to a classic outage: the database blinks, every copy of the API is restarted at once, and the restart storm makes everything worse. (The `z` at the end is an old Google naming habit, kept by Kubernetes, that makes these paths unlikely to clash with real ones.)

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5
`Annotated`.

@@ 7-8
The router, `Depends`, `Response`, and SQLAlchemy's `text` for a raw SQL query.

@@ 10-11
The toolbox type and its dependency.

@@ 13
The router, with no path prefix.

@@ 16-18
**`/livez`** — if this code runs at all, the program is alive. It touches nothing else, so it can't fail because of anything else.

@@ 21-23
**`/readyz`** — it may need to change the status code, so it asks for the `response`. The checks are collected in a dict.

@@ 24-29
**The database check:** open a database session and run `SELECT 1` — the smallest possible query. Success means PostgreSQL is reachable and answering. Any error at all counts as `unavailable`. Catching every kind of error is usually a bad habit; here it is exactly right, because the question is simply "did it work?".

@@ 30-34
**The Valkey check:** `PING`, in the same way.

@@ 35-36
If any check isn't `ok`, answer `503 Service Unavailable`.

@@ 37
Return the checks, so a person looking at the answer sees *which* dependency is down, for example `{"database": "ok", "valkey": "unavailable"}`.
