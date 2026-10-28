---
fingerprint: 6c1bf11114c645d5
---
Tests for how a database error becomes an answer (Phase 7, §5.7.6): text the database can't store is the request's fault (`422`); a database that has gone away is a dependency down (`503`, try again); anything else is a fault of ours (`500`). No database is needed: the errors are made by hand.

@@ 1
What these tests are about.

@@ 3
Newer type-hint syntax on older Pythons.

@@ 5-7
pytest; SQLAlchemy's database error; and Starlette's request type.

@@ 9
The error answers under test.

@@ 12-17
**`DriverError`** — a stand-in for the error the database driver raises, carrying PostgreSQL's five-character code (`sqlstate`), as the real one does.

@@ 20-23
**`a_request`** — the smallest request the handler can answer, with the request ID every answer carries.

@@ 26-35
**The cases**, each run as its own test: text that can't be stored, `422`; a server shutting down (the one the load test met) and a lost connection, `503`; an unknown table, `500`.

@@ 36-38
Wrap the driver's error as SQLAlchemy would, and let the handler answer it.

@@ 39-40
The status is as expected, and `Retry-After` is there exactly when the answer is `503`.
