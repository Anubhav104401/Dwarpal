---
fingerprint: 629658123d5a7ed4
---
A **device ID** for the per-device budgets: a random ID that this browser keeps for the verify page, so the API can limit how many age checks one device tries in an hour, across all the sessions it starts.

It is deliberately *not* a fingerprint. Fingerprinting would compute an ID from the device's features (screen, fonts, graphics card…) so that it can't be escaped — and it would follow people around. This ID is just a random number in the site's own storage: it says nothing about the device or the person, and clearing the site's data resets it. A determined attacker can reset it too; the API's per-address budget is the backstop for that.

@@ 1-2
The doc comment: what the ID is for, and what it is not.

@@ 4
The name it is stored under.

@@ 5
What a stored ID must look like to be reused: 16 to 64 letters, digits and hyphens — the same rule the API applies.

@@ 7
`Store` — the two methods of browser storage this file uses. Tests pass a stand-in with just these two.

@@ 9-15
**`browserStorage`** — the page's **local storage** (`localStorage`: small, per-site data that survives closing the browser), or `null` where there is none. Some browsers throw an error merely for asking, for example with storage blocked; `try … catch` turns that into `null`.

@@ 17-18
**`deviceId`** — this browser's device ID, created the first time; or `null` where nothing may be stored. The storage is a parameter with the real one as its default, so tests can pass their own.

@@ 19-21
No storage: no ID. The API then counts only the network address's budget.

@@ 22-26
If a well-formed ID is already stored, use it.

@@ 27-29
Otherwise create one — `crypto.randomUUID()` makes a random **UUID**, such as `3f6c…-…`, from the browser's secure random source — store it, and return it. A malformed stored value is replaced the same way.

@@ 30-33
If storing fails (storage full, or blocked), carry on without an ID rather than break the check.
