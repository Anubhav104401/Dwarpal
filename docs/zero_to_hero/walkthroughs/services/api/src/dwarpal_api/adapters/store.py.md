---
fingerprint: c124a0043dd74227
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

@@ 14-15
**`_hashed`** — the SHA-256 fingerprint of a token, written as 64 hexadecimal characters. The leading underscore marks a **private** helper, meant only for this file.

Flow tokens are stored **hashed**, for the same reason as API keys: someone who could read Valkey's memory would find only fingerprints, which are useless for calling the API.

@@ 18
**`FlowStore`** — the class that holds every Valkey operation the API needs. The rest of the code never talks to Valkey directly, so all the key names and expiry rules are in one file.

@@ 19-20
It keeps the client it was given. Receiving the client from outside, instead of creating it here, lets tests and the app decide which Valkey to use.

@@ 22-23
**`ping`** — Valkey's "are you there?" command. The readiness check uses it (`http/health.py`).

@@ 25
**`open_flow`** — start a flow for a session, and return its token.

@@ 26
32 secure random bytes as URL-safe text: the token the browser will send back with every flow request.

@@ 27
Store "fingerprint → session ID" with `ex=ttl_s`: Valkey's `SET` command with an expiry in seconds. The `await` waits for Valkey's reply without blocking other requests.

@@ 28
Return the token itself. It exists in plain form only in this reply and in the browser's memory.

@@ 30
**`session_for`** — which session does this token belong to? `None` if the token is unknown or has expired.

@@ 31-33
Look up the token's fingerprint. Nothing found means no access.

@@ 34
Turn the stored text back into a UUID. The client may return the value as raw bytes or as text, depending on how it was configured, and `isinstance` handles both.

@@ 36-38
**`issue_challenge`** — create a one-time challenge for a session's next face attempt. Besides the session and the challenge's lifetime, it receives a **budget** — the most challenges this session may ever get — and how long to remember the count. It returns the challenge, or `None` when the budget is used up.

@@ 39
The counter's key, one per session.

@@ 40
Create the counter at 0, with its expiry — but only if it doesn't exist yet: `nx=True` is Valkey's `NX` option, "only if Not eXists". Later calls leave the existing counter, and its expiry, alone.

@@ 41-42
`INCR` adds 1 and returns the new value, as a single **atomic** step: even if two requests arrive at the same instant, each sees a different number. Over budget? Return `None`.

!!! why "Why a budget?"
    Each challenge allows one face attempt, and each attempt makes the inference service analyse up to 16 pictures. Without a limit, one session could request thousands of challenges and keep the AI busy for everyone else. The budget allows twice the policy's attempts (see `issue_challenge` in `app/verification.py`), which leaves room for a page reload or a lost connection.

@@ 43-49
The challenge itself:

- `challenge_id` — 16 random bytes as text: the ticket's number;
- `nonce` — another random value. "Nonce" means "number used once"; Phase 3 uses it to tie captured frames to this exact challenge;
- `poses` and `colours` — empty for now. Phase 3 fills them with head movements to perform and screen colours to flash, which make replaying a video much harder. Sending the empty fields already means the verify page and the API agree on the shape from day one;
- `expires_in` — how many seconds the challenge is valid.

@@ 50
The stored version adds the session's ID, so a challenge can't be used with a different session. `**challenge` copies every key and value of the challenge into the new dict.

@@ 51
Store it under its ID, with its expiry.

@@ 52
Return the challenge, without the session ID: the browser already knows its session.

@@ 54
**`take_challenge`** — use a challenge up. True only if it existed, hadn't expired, and belongs to this session.

@@ 55
`GETDEL` reads the value **and deletes it in one atomic step**. If the same challenge arrives twice at the same instant, only one request can get it — the other finds nothing. Reading first and deleting later would leave a tiny gap in which both could succeed.

@@ 56
Accept only if something was found *and* its session matches. The challenge is gone either way: a wrong guess burns it.
