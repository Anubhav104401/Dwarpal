---
fingerprint: a2291b8e27db8175
---
**Checking an age token** on the website's own server (§5.9.1), as the Node SDK does: signature, issuer, audience, expiry, session — and what it says about the age required.

@@ 1-2
The module's docstring: what checking an age token means.

@@ 4
The project-wide type-hint setting.

@@ 6-15
A lock (for keys shared between threads), dataclasses, dates, type helpers, httpx, joserfc's errors and JWT tools, its key-set type, and the SDK's token error.

@@ 17-20
The one algorithm Dwarpal signs with — any other is refused, which closes the classic trick of a token claiming a weaker algorithm — and the type every Dwarpal age token declares.

@@ 23-30
**`AgeVerdict`** — the answer: whether entry is allowed, the outcome, the session, the policy, live or test, and when the token expires.

@@ 33-36
**`Keys`** — an issuer's public keys, fetched once and kept. A token signed with a key not seen yet makes them be fetched again — how a rotated key is picked up — but not more often than every minute, so a flood of forged tokens can't make the website flood Dwarpal.

@@ 38-44
The address of the keys, the HTTP client, the refresh limit, the keys (none yet), when they were fetched, and the lock.

@@ 46-55
**`get`** — under the lock: fetch the keys if there are none, or if asked to refresh and the last fetch is old enough; otherwise return the ones kept.

@@ 58-64
One `Keys` per issuer, shared by the whole program.

@@ 67-72
**`_decode`** — check the signature with the keys kept, allowing only Ed25519; if the token names a key not among them, fetch again once and retry.

@@ 75-88
**`verify_age_token`** — the check, with its options named (`*`): the issuer, the audience (your project), the age you require, and optionally the session you expect and the keys to use.

@@ 89-90
The age must be a whole number of years, at least 1.

@@ 91-94
Decode and check the signature; the header must declare a Dwarpal age token.

@@ 95-104
The claims: issued by this issuer, for this project, and carrying an expiry (checked: not past), an issue time, an ID, a session and an outcome.

@@ 105-106
Any of joserfc's failures becomes an `AgeTokenError`, naming the reason's code.

@@ 107-113
The outcome must be one Dwarpal gives, and the session the expected one.

@@ 114-121
The verdict: allowed **only** for a pass that states `age_over_<min_age>: true` for exactly the age asked — a pass at 16 doesn't open an 18+ door.
