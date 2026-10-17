---
fingerprint: 5e582ef8b13964b5
---
The API's **short-term memory**, kept in **Valkey** (§4.11). Some facts only need to exist for minutes: "this browser may work on session X for the next 15 minutes", "this challenge may be used once in the next 2 minutes". Putting them in PostgreSQL would fill the database with rows that need cleaning up. Valkey stores each value with a **time to live** and deletes it by itself when the time runs out.

Three kinds of entry live here:

| Key | Value | Expires after | Purpose |
| :-- | :-- | :-- | :-- |
| `flow:<SHA-256 of token>` | the session's ID | 15 minutes | a **flow token**: the browser's permission to work on one session |
| `challenge:<challenge ID>` | the challenge, as JSON | 2 minutes | a one-time ticket for one face attempt |
| `challenges:<session ID>` | a counter | 30 minutes | how many challenges this session has had |

@@ 1
The docstring: short-lived state that expires on its own.

@@ 3
The project-wide type-hint setting.

@@ 5-9
The tools: `hashlib` (SHA-256), `json` (storing challenges as text), `secrets` (random tokens), `uuid` (session IDs) and `Any`.

@@ 11
`Redis` — the **asyncio** client from the `redis` library. Valkey speaks exactly the same language as Redis, so the same client works.

@@ 13
`Challenge` — the contract for what the person is asked to do (added in Phase 3). The store saves one and gives it back.

@@ 16-17
**`_hashed`** — the SHA-256 fingerprint of a token, written as 64 hexadecimal characters. The leading underscore marks a **private** helper, meant only for this file.

Flow tokens are stored **hashed**, for the same reason as API keys: someone who could read Valkey's memory would find only fingerprints, which are useless for calling the API.

@@ 20
**`FlowStore`** — the class that holds every Valkey operation the API needs. The rest of the code never talks to Valkey directly, so all the key names and expiry rules are in one file.

@@ 21-22
It keeps the client it was given. Receiving the client from outside, instead of creating it here, lets tests and the app decide which Valkey to use.

@@ 24-25
**`ping`** — Valkey's "are you there?" command. The readiness check uses it (`http/health.py`).

@@ 27
**`open_flow`** — start a flow for a session, and return its token.

@@ 28
32 secure random bytes as URL-safe text: the token the browser will send back with every flow request.

@@ 29
Store "fingerprint → session ID" with `ex=ttl_s`: Valkey's `SET` command with an expiry in seconds. The `await` waits for Valkey's reply without blocking other requests.

@@ 30
Return the token itself. It exists in plain form only in this reply and in the browser's memory.

@@ 32
**`session_for`** — which session does this token belong to? `None` if the token is unknown or has expired.

@@ 33-35
Look up the token's fingerprint. Nothing found means no access.

@@ 36
Turn the stored text back into a UUID. The client may return the value as raw bytes or as text, depending on how it was configured, and `isinstance` handles both.

@@ 38-40
**`issue_challenge`** — store a one-time challenge for a session's next face attempt. It receives the `Challenge` to store (Phase 3: the poses and colours were chosen at random by `domain/challenges.py`), the challenge's lifetime, a **budget** — the most challenges this session may ever get — and how long to remember the count. It returns the issued challenge, or `None` when the budget is used up.

@@ 41
The counter's key, one per session.

@@ 42
Create the counter at 0, with its expiry — but only if it doesn't exist yet: `nx=True` is Valkey's `NX` option, "only if Not eXists". Later calls leave the existing counter, and its expiry, alone.

@@ 43-44
`INCR` adds 1 and returns the new value, as a single **atomic** step: even if two requests arrive at the same instant, each sees a different number. Over budget? Return `None`.

!!! why "Why a budget?"
    Each challenge allows one face attempt, and each attempt makes the inference service analyse up to 16 pictures. Without a limit, one session could request thousands of challenges and keep the AI busy for everyone else. The budget allows twice the policy's attempts (see `issue_challenge` in `app/verification.py`), which leaves room for a page reload or a lost connection.

@@ 45-50
The issued challenge:

- `challenge_id` — 16 random bytes as text: the ticket's number;
- `nonce` — another random value. "Nonce" means "number used once". Nothing checks it yet; it is there so that a later phase can tie the captured frames to this exact challenge;
- `**challenge.model_dump()` — the challenge's own fields (`poses`, `colours`, `step_ms`). `model_dump()` turns a Pydantic model into a plain dict, and `**` copies every key and value into this one;
- `expires_in` — how many seconds the browser has to use it.

@@ 51
The stored version adds the session's ID, so a challenge can't be used with a different session. `**issued` copies the issued challenge's keys in.

@@ 52
Store it under its ID, with its expiry.

@@ 53
Return the challenge, without the session ID: the browser already knows its session. The browser needs the poses and colours to show the prompts — knowing them in advance doesn't help an attacker much, because they are random and change every attempt.

@@ 55
**`take_challenge`** — use a challenge up. It returns the stored `Challenge` only if it existed, hadn't expired, and belongs to this session; otherwise `None`.

@@ 56
`GETDEL` reads the value **and deletes it in one atomic step**. If the same challenge arrives twice at the same instant, only one request can get it — the other finds nothing. Reading first and deleting later would leave a tiny gap in which both could succeed.

@@ 57-62
Accept only if something was found *and* its session matches. The challenge is gone either way: a wrong guess burns it. Then rebuild the `Challenge` from what was stored — the *server's* copy, which is what the frames will be checked against, whatever the browser claims.
