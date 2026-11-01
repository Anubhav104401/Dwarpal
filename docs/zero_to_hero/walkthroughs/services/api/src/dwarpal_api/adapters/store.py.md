---
fingerprint: df2b3b6ce3fc7eb7
---
The API's **short-term memory**, kept in **Valkey** (§4.11). Some facts only need to exist for minutes: "this browser may work on session X for the next 15 minutes", "this challenge may be used once in the next 2 minutes". Putting them in PostgreSQL would fill the database with rows that need cleaning up. Valkey stores each value with a **time to live** and deletes it by itself when the time runs out.

Three kinds of entry live here:

| Key | Value | Expires after | Purpose |
| :-- | :-- | :-- | :-- |
| `flow:<SHA-256 of token>` | the session's ID | 15 minutes | a **flow token**: the browser's permission to work on one session |
| `challenge:<challenge ID>` | the challenge, as JSON | 2 minutes | a one-time ticket for one face attempt |
| `challenges:<session ID>` | a counter | 30 minutes | how many challenges this session has had |

@@ 1-2
The docstring: everything kept in Valkey is short-lived and expires on its own — flow tokens, challenges, budgets, and since Phase 4 the rate-limit buckets and the idempotent replies.

@@ 4
The project-wide type-hint setting.

@@ 6-10
The tools: `hashlib` (SHA-256), `json` (storing challenges as text), `secrets` (random tokens), `uuid` (session IDs) and `Any`.

@@ 12
`Redis` — the **asyncio** client from the `redis` library. Valkey speaks exactly the same language as Redis, so the same client works.

@@ 14
`Challenge` — the contract for what the person is asked to do (added in Phase 3). The store saves one and gives it back.

@@ 16-18
**The rate limit** (Phase 4). A **token bucket** is the classic way to say "about this many requests a second, with short bursts allowed". Picture a bucket that holds at most `burst` tokens and is refilled at `rate` tokens per second. Each request takes one token; with the bucket empty, the request is refused until the next token drips in. A quiet website saves up a full bucket and may then send a burst; a flooding one is held to the refill rate.

The comment explains two choices. The whole bucket is updated by **one script run inside Valkey**, which runs scripts one at a time: two API servers can never both take the last token. And it uses **Valkey's own clock**, so the API servers' clocks needn't agree.

@@ 19
`RATE_LIMIT_SCRIPT` — the script, written in **Lua**, the small language Valkey runs scripts in.

@@ 20
Read the two arguments, `rate` and `burst`, as numbers (`ARGV` holds the values passed in).

@@ 21-22
Ask Valkey the time: `TIME` returns seconds and microseconds, combined here into milliseconds.

@@ 23
Read this bucket's state: how many tokens it held, and when it was last updated (`KEYS[1]` is the bucket's name). A new bucket has neither.

@@ 24
**Refill**: the tokens it had (a full bucket if it's new), plus the time since the last update multiplied by the rate — but never more than `burst`.

@@ 25
Assume a refusal: not allowed, and the wait until one whole token is back — the missing part of a token divided by the refill rate.

@@ 26-28
If there is a whole token, take it: allowed, no wait.

@@ 29
Save the new count and the time. (`tostring` keeps the fraction of a token: a bucket refills smoothly, not in steps.)

@@ 30
Let Valkey forget the bucket once it would have refilled completely anyway, plus a second: an idle key costs no memory.

@@ 31-32
Return the two numbers, and end the script.

@@ 35-36
**`_hashed`** — the SHA-256 fingerprint of a token, written as 64 hexadecimal characters. The leading underscore marks a **private** helper, meant only for this file.

Flow tokens are stored **hashed**, for the same reason as API keys: someone who could read Valkey's memory would find only fingerprints, which are useless for calling the API.

@@ 39
**`FlowStore`** — the class that holds every Valkey operation the API needs. The rest of the code never talks to Valkey directly, so all the key names and expiry rules are in one file.

@@ 40-41
It keeps the client it was given. Receiving the client from outside, instead of creating it here, lets tests and the app decide which Valkey to use.

@@ 43-44
**`ping`** — Valkey's "are you there?" command. The readiness check uses it (`http/health.py`).

@@ 46
**`open_flow`** — start a flow for a session, and return its token.

@@ 47
32 secure random bytes as URL-safe text: the token the browser will send back with every flow request.

@@ 48
Store "fingerprint → session ID" with `ex=ttl_s`: Valkey's `SET` command with an expiry in seconds. The `await` waits for Valkey's reply without blocking other requests.

@@ 49
Return the token itself. It exists in plain form only in this reply and in the browser's memory.

@@ 51
**`session_for`** — which session does this token belong to? `None` if the token is unknown or has expired.

@@ 52-54
Look up the token's fingerprint. Nothing found means no access.

@@ 55
Turn the stored text back into a UUID. The client may return the value as raw bytes or as text, depending on how it was configured, and `isinstance` handles both.

@@ 57-59
**`issue_challenge`** — store a one-time challenge for a session's next face attempt. It receives the `Challenge` to store (Phase 3: the poses and colours were chosen at random by `domain/challenges.py`), the challenge's lifetime, a **budget** — the most challenges this session may ever get — and how long to remember the count. It returns the issued challenge, or `None` when the budget is used up.

@@ 60
The counter's key, one per session.

@@ 61
Create the counter at 0, with its expiry — but only if it doesn't exist yet: `nx=True` is Valkey's `NX` option, "only if Not eXists". Later calls leave the existing counter, and its expiry, alone.

@@ 62-63
`INCR` adds 1 and returns the new value, as a single **atomic** step: even if two requests arrive at the same instant, each sees a different number. Over budget? Return `None`.

!!! why "Why a budget?"
    Each challenge allows one face attempt, and each attempt makes the inference service analyse up to 16 pictures. Without a limit, one session could request thousands of challenges and keep the AI busy for everyone else. The budget allows twice the policy's attempts (see `issue_challenge` in `app/verification.py`), which leaves room for a page reload or a lost connection.

@@ 64-69
The issued challenge:

- `challenge_id` — 16 random bytes as text: the ticket's number;
- `nonce` — another random value. "Nonce" means "number used once". Nothing checks it yet; it is there so that a later phase can tie the captured frames to this exact challenge;
- `**challenge.model_dump()` — the challenge's own fields (`poses`, `colours`, `step_ms`). `model_dump()` turns a Pydantic model into a plain dict, and `**` copies every key and value into this one;
- `expires_in` — how many seconds the browser has to use it.

@@ 70
The stored version adds the session's ID, so a challenge can't be used with a different session. `**issued` copies the issued challenge's keys in.

@@ 71
Store it under its ID, with its expiry.

@@ 72
Return the challenge, without the session ID: the browser already knows its session. The browser needs the poses and colours to show the prompts — knowing them in advance doesn't help an attacker much, because they are random and change every attempt.

@@ 74-75
**`spend_budget`** — count one use against a budget that starts afresh every window, as the docstring says, and answer whether there was still room. Used for the per-device and per-address budgets (`app/verification.py`).

@@ 76
The counter's name: `budget:` and a fingerprint of the key. Hashing keeps device IDs and network addresses out of Valkey's key names.

@@ 77
Create the counter at 0 with its expiry — but only if it doesn't exist yet (`nx=True`): the window starts with the first use and isn't extended by later ones.

@@ 78
Add one and compare with the limit. `incr` is atomic in Valkey, so two requests arriving together can't both slip through on the same count.

@@ 80-83
**`take_token`** — run the script for the bucket called `key` (`eval` sends a script with one key name and its arguments). Return 0 when allowed; otherwise the wait in milliseconds, at least 1 so that "refused" can never look like 0.

@@ 85-88
**`claim`** — the first step of idempotency (`app/idempotency.py`): store a value **only if nothing is there yet** (`nx=True`) and, in the same command, get back what *was* there (`get=True`). One command, so two copies of a request arriving together can't both believe they came first. `None` means "it was empty, and is now ours".

@@ 90-91
**`put`** — store a value, replacing whatever was there, for `ttl_s` seconds.

@@ 93-94
**`drop`** — delete a key.

@@ 101-104
**`fetch`** — read a value and, in the same command (`GETEX`), restart its time to live. This is a **sliding expiry**: a console session lasts 12 hours *from its last use*, so someone working all day stays signed in, and an abandoned session ends on its own.

@@ 106
**`take_challenge`** — use a challenge up. It returns the stored `Challenge` only if it existed, hadn't expired, and belongs to this session; otherwise `None`.

@@ 107
`GETDEL` reads the value **and deletes it in one atomic step**. If the same challenge arrives twice at the same instant, only one request can get it — the other finds nothing. Reading first and deleting later would leave a tiny gap in which both could succeed.

@@ 108-113
Accept only if something was found *and* its session matches. The challenge is gone either way: a wrong guess burns it. Then rebuild the `Challenge` from what was stored — the *server's* copy, which is what the frames will be checked against, whatever the browser claims.

@@ 96-99
**`take`** (Phase 9) — read a value and delete it in one step (`GETDEL`), as `take_challenge` below does for liveness challenges. Passkey challenges use it: whoever takes a challenge first has it, so a device's answer can be used once.
