---
fingerprint: 8453e945806608e7
---
The marker file of the **adapters** layer — the API's connections to everything outside itself.

@@ 1
The docstring lists what adapters talk to:

- the **database** (PostgreSQL) — `db.py` and `tables.py`;
- **Valkey**, the fast short-term memory — `store.py`;
- the **inference service** — `inference.py`;
- the **keys** that sign age tokens — `signing.py`.

An adapter is like a travel plug: the domain's rules stay the same, and the adapter fits them to one particular socket. If PostgreSQL were ever swapped for another database, only the adapters would change.
