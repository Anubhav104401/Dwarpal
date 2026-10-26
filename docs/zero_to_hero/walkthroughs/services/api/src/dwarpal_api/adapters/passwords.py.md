---
fingerprint: 0cc9049d2586ce48
---
**Passwords** for the console (Phase 4, §5.4.5). A password is never stored. What is stored is its **hash**: the output of a one-way function that is easy to compute from the password and practically impossible to turn back. At sign-in, the typed password is hashed the same way and compared.

Ordinary hash functions such as SHA-256 are the wrong tool here, because they are *fast*. An attacker who steals the table of hashes can try billions of guesses a second on graphics cards. **Argon2id**, the winner of the 2015 Password Hashing Competition and the recommendation of RFC 9106, is slow and **memory-hard** on purpose: each guess takes tens of milliseconds and 64 MiB of memory, which cripples guessing at scale while a single honest sign-in barely notices. Each hash also mixes in a random **salt**, so two people with the same password get different hashes, and precomputed tables of common passwords are useless.

!!! kid "Explain like I'm six — the slow lock"
    Imagine a lock that takes a whole second to try each key. You barely notice when you open your own door. A burglar with a sack of a million keys would need eleven days.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5
`asyncio`, to hash in a worker thread.

@@ 7-8
From `argon2-cffi`: the `PasswordHasher`, and the two errors it raises for a wrong password or a damaged hash.

@@ 10-11
**`HASHER`** — one hasher with the library's defaults, which follow RFC 9106's second recommendation: 3 passes over 64 MiB of memory, using 4 lanes, about 50 milliseconds on this machine — the design's target. The settings are written into every hash it makes, so they can be raised later without breaking existing passwords.

@@ 12-13
**`DECOY`** — a hash of a password nobody has. When someone tries to sign in with an address that has no account, this is checked instead. Otherwise the answer for an unknown address would come back 50 ms faster than for a real one, and timing alone would reveal who has an account.

@@ 16-18
**`hash_password`** — hash a new password, in a **worker thread** (`asyncio.to_thread`). Hashing is deliberately heavy work, and the API serves many requests on one thread; 50 ms of hashing there would freeze every other request meanwhile.

@@ 21-22
**`verify_password`** — whether a password matches a stored hash. With no account (`None`), check the decoy, and answer no.

@@ 24-28
The check itself: verify against the stored hash (or the decoy), and say yes only if it matched **and** there was a real account. A wrong password, or a hash that isn't a valid Argon2 hash, raises an error, which means no.

@@ 30
Run the check in a worker thread, and wait for its answer.
