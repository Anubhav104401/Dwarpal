---
fingerprint: 38d9174bc70e1914
---
The marker file of the **HTTP layer** — the outermost ring, the only part of the API that knows about web requests.

@@ 1
The docstring states the layer's discipline: it only **translates**. A request arrives, its data is checked and handed to a use case, and the use case's result is turned into a response. No business rule — such as "a session may only be attempted three times" — lives here. Each rule lives in the domain or the use cases, so it can't be skipped by calling the system some other way.
