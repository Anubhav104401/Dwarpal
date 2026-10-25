---
fingerprint: d8d83b57686e02ad
---
The two kinds of **secret** the API hands out:

| Secret | Looks like | Who holds it | What it unlocks |
| :-- | :-- | :-- | :-- |
| **API key** | `dk_test_…` or `dk_live_…` | the website's *server* — never a browser | creating sessions and reading their results |
| **Client secret** | `vs_…_secret_…` | the person's *browser*, for one session only | taking part in that one verification |

The API never stores either secret itself. It stores only a **digest** — a fingerprint made by SHA-256 (§X.5, §4.12). When a secret comes back, the API makes a fresh fingerprint and compares the two. A thief who steals the database gets fingerprints, which can't be turned back into keys.

!!! why "Why plain SHA-256, and not a slow password hash?"
    Passwords chosen by people are guessable, so they need deliberately *slow* hashes such as Argon2id (the console's users get exactly that in Phase 4). These secrets are different: 32 or 24 bytes from a secure random generator. Guessing a 256-bit random value is hopeless even at a billion guesses per second for the age of the universe, so a fast hash is safe — and keeps every API call fast.

**Test and live keys.** Following a convention from payment APIs, every key says in its prefix whether it is a **test** key (`dk_test_`) or a **live** key (`dk_live_`). Test keys work only with test sessions, which may use the stand-in age model. The prefixes also let secret-scanning tools — such as the one on GitHub — recognise a leaked key at a glance.

@@ 1
The docstring names both kinds of secret.

@@ 3
The project-wide type-hint setting.

@@ 5-8
The tools:

- `hashlib` — hash functions; SHA-256 lives here;
- `hmac` — here only for `compare_digest`, explained below;
- `secrets` — Python's module for **secure** random values (never use `random` for secrets: its output can be predicted);
- `dataclass` — the class-writing helper (§X.8).

@@ 10
`LOOKUP_LENGTH = 12` — how many characters of a key are stored *in plain text* as its **lookup**: a label that finds the key's row in the database quickly. The rest of the key stays secret.

@@ 11-13
`SCOPES` — every scope a key can have: read sessions' results, create sessions, add policy versions, and manage webhooks. A key gets a subset of these; each endpoint asks for the one it needs (`http/deps.py`, `needs`).

@@ 16-20
**`NewSecret`** — what generating a secret produces:

- `plaintext` — the secret itself, shown to its owner **once** and never stored;
- `lookup` — the plain-text label for finding the row;
- `digest` — the SHA-256 fingerprint, which *is* stored.

`frozen=True` makes it read-only once made.

@@ 23-24
**`digest`** — encode the text as UTF-8 bytes, run SHA-256 over them, and return the 32-byte result.

@@ 27-28
**`matches`** — does a secret that just arrived match a stored digest? It fingerprints the arrival and compares with `hmac.compare_digest`, which takes the **same time** whether the first byte differs or the last.

!!! kid "Explain like I'm six — the slow and the careful guard"
    A guard checks a password letter by letter and says "wrong!" the moment a letter is wrong. A sneaky visitor times him: a quick "wrong!" means the first letter was wrong, a slower one means the first letter was right. Letter by letter, the visitor learns the password. A careful guard always checks *every* letter before answering, so his answer takes the same time and gives nothing away.

That trick is called a **timing attack**. Comparing digests instead of the secrets themselves already blunts it, and constant-time comparison closes it completely — the standard habit for anything secret.

@@ 31
**`generate_api_key`** — make a new key; `livemode` chooses between test and live.

@@ 32
32 secure random bytes, written as **URL-safe Base64**: 43 characters using only `A`–`Z`, `a`–`z`, `0`–`9`, `-` and `_`, so a key can be pasted anywhere without escaping.

@@ 33
Put the prefix in front: `dk_live_` or `dk_test_`. The expression `'live' if livemode else 'test'` chooses one of two values in a single line.

@@ 34
Package it all: the full key, the first 12 characters of the random part as the lookup, and the digest of the *whole* key. Knowing the lookup doesn't help an attacker: the other 31 characters still hold about 186 bits of randomness.

@@ 37
**`parse_api_key`** — read the mode and the lookup from a key that arrived, *before* any database work. It returns `None` for anything that isn't shaped like one of our keys. `tuple[bool, str] | None` says: either a (mode, lookup) pair, or nothing.

@@ 38
Try each known prefix, with the mode it stands for.

@@ 39-40
If the text starts with this prefix and is long enough to hold more than a lookup, return the mode and the 12 lookup characters. `text[a : b]` is a **slice**: the characters from position `a` up to (not including) `b`.

@@ 41
No prefix matched: not one of our keys.

@@ 44
**`generate_client_secret`** — make the one-time secret for a session. It receives the session's public ID.

@@ 45
The secret is `vs_…_secret_` followed by 24 random bytes (32 characters). It **names its session**, which helps a person debugging a problem, and binds the secret to exactly one session — the digest covers the ID too.

@@ 46
Package it. For client secrets the session ID itself is the lookup: the session's row is found by its ID, and then the digest is checked.
