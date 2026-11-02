---
fingerprint: 61b5bebf0525c5d3
---
The **Age Pass's rules** (Phase 9, decision D21, §5.9.3): making a pass, and checking a presentation of one. Pure functions, with no database or network.

@@ 1-12
The module's docstring: what an Age Pass is — a pass the person keeps, so the next website needs no new face check — the two standards it follows (SD-JWT's selective disclosure, and key binding), what a presentation looks like, and why passes come in batches and are used once.

@@ 14
The project-wide type-hint setting.

@@ 16-24
Base64, hashing, JSON, random bytes (`os`), regular expressions, a type for a function given as an argument, dataclasses, dates and times, and `Any`.

@@ 26-29
`ec` from `cryptography`, to check that a holder's key is a real point on its curve; and from joserfc, already used for the age tokens, JWTs, its errors, and its elliptic-curve key type.

@@ 31-34
The names the standards give: a pass's type `dc+sd-jwt`; the type of the holder's proof `kb+jwt`; the kind of credential — Dwarpal's Age Pass, version 1 — as a URN (a name that isn't an address); and the holder's signature algorithm, ES256 (ECDSA on P-256 with SHA-256), which every browser's WebCrypto can make.

@@ 35-41
The rules in numbers: passes last 90 days; 20 come at once; the standard age lines; every pass lists 6 digests, real and decoy alike, so its size gives nothing away; a proof's clock may be five minutes off ours; a presentation may be at most 4096 characters; and the pattern of base64url text.

@@ 44-49
**`AgePassError`** — a pass or a presentation that can't be trusted, with a stable `code` the API turns into its own (`age_pass_tampered`, say), and a message saying which check failed.

@@ 52-53
**`b64url_encode`** — base64url without padding, as JWTs write bytes.

@@ 56-60
**`b64url_decode`** — strictly: Python's own decoder quietly skips characters outside the alphabet, so the text is checked first; a length that leaves one character over (`% 4 == 1`) can't be base64 at all.

@@ 63-65
**`digest`** — a disclosure's fingerprint as the signed pass lists it: SHA-256 of its base64url text, in base64url.

@@ 68-71
**`lines_for`** — the lines a pass states: the age it was checked at, and each standard line below it. A pass from an 18+ check states 13, 16 and 18; nothing about 21, which the check never looked at.

@@ 74-76
**`holder_key`** — the browser's public key, checked and cleaned, before it goes into a pass.

@@ 77-80
An EC key on P-256, and no private part: if the browser sent its `d`, something is badly wrong, and it is refused rather than ignored.

@@ 81-86
Two coordinates, each 32 bytes of base64url.

@@ 87-91
And a point really on the curve: `cryptography` refuses anything else. The key is returned with only its four defining fields, so nothing else the browser sent ends up inside a pass.

@@ 94-97
**`NewPass`** — a pass before Dwarpal signs it: the claims to sign, and the disclosures the holder keeps beside it.

@@ 100-110
**`new_pass`** — one pass, for one holder key. `random` can be given, so tests could make passes repeatable; in use it is the operating system's secure random bytes.

@@ 111-114
One **disclosure** per age line: a JSON array `[salt, name, value]` — `["Qw…", "age_over_18", true]` — in base64url. The 16-byte random salt makes each disclosure unguessable: without it, anyone could hash `["age_over_18", true]` and see which digest it is.

@@ 115-116
Their digests, plus random decoy digests up to six: no one can count a pass's lines, nor tell which digests are real.

@@ 117-128
The claims Dwarpal signs: issuer; issued at midnight of the day (UTC), so passes issued on one day can't be told apart by the second; expires 90 days later; the credential type; test or live; `cnf` (*confirmation*) — the holder's key, which binds the pass to the browser; the digests, sorted so their order reveals nothing; and the hash algorithm used.

@@ 131-133
**`joined`** — a pass as the browser keeps it: the signed JWT, then every disclosure, each followed by `~`.

@@ 136-141
**`Presentation`** — a presentation taken apart: the signed pass, the disclosures shown, the holder's key-binding JWT, and everything before that JWT — the part its `sd_hash` must cover.

@@ 144-147
**`split`** — too long: refused before anything else is done with it.

@@ 148-149
Not plain ASCII: refused too. Every part is base64url, so other characters mean a forgery — and the hashing below needs ASCII; reading the code for this book found that such a presentation would have caused an error instead of a refusal.

@@ 150-154
Split at `~`: at least the pass and the key-binding JWT, with no empty parts in between. The signed part is the text up to the key-binding JWT, its last `~` included.

@@ 157-159
**`check_pass`** — the pass's own claims, once its signature has been checked.

@@ 160-163
Ours, an Age Pass, with the hash algorithm this module knows; and of the session's mode: a test pass never opens a live session, nor a live pass a test one.

@@ 164-166
Its times must be whole numbers (`bool` is excluded: in Python `True` is also `1`).

@@ 167-170
Not expired; and not dated in the future, beyond the allowed clock difference.

@@ 173-178
**`disclosed`** — what the holder chose to show. The pass must list digests.

@@ 179-182
Each disclosure must be one this pass lists by its digest — another pass's disclosure, or an invented one, is refused as tampering.

@@ 183-190
It must decode to exactly `[salt, name, value]` (a JSON object would unpack into three names otherwise), with a text salt and name, a name not shown twice and not one of the pass's plain claims — a disclosure can't overwrite `iss`.

@@ 191-193
Keep the value under its name; return them all.

@@ 196-200
**`check_key_binding`** — the holder's proof that they hold the pass's key, now, for this request.

@@ 201-205
Check its signature with the key inside the pass (`cnf`), allowing only ES256 — a JWT naming another algorithm is refused. (The type hint widens the key's dictionary for joserfc's signature.)

@@ 206-208
It must declare itself a key-binding JWT.

@@ 209-210
Its nonce and audience must be this session's: a proof made for another session, or recorded earlier, is refused.

@@ 211-213
Made within five minutes of now.

@@ 214-216
And its `sd_hash` must be the hash of exactly the pass and the disclosures it came with: nobody can add, drop or swap a disclosure after the holder signed.

@@ 219-226
**`line_proved`** — the lowest age line at or above the policy's age that the shown claims state as `true`; `None` if there is none. Other names, and values that aren't exactly `true`, count for nothing.
