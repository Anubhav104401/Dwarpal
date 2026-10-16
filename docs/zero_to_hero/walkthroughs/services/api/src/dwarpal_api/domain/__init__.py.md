---
fingerprint: 8637b15f73506320
---
The marker file of the **domain** layer — the innermost ring of the API (see the package overview in `dwarpal_api/__init__.py`).

@@ 1
The docstring states the layer's one strict rule: the domain is **pure Python**. It never touches a network, a database, a file or a clock.

Why be so strict? Code that only calculates is **deterministic**: the same inputs always give the same answer. That makes it easy to test exhaustively, and easy to trust. For example, `decide()` never asks "what time is it?" — whoever calls it reads the clock and passes the time in. The one place where the domain needs randomness — creating new identifiers and secrets — uses the operating system's random generator, and the tests check the *shape* of the results rather than exact values.
