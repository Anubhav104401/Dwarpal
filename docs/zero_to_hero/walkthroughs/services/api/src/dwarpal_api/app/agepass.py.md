---
fingerprint: c82113f40b50137d
---
The **Age Pass's use cases** (Phase 9, §5.9.3): giving passes out after a passed check, and accepting one in place of the camera.

@@ 1-7
The module's docstring: the two use cases — giving passes out, and accepting one — and what is never recorded.

@@ 9
The project-wide type-hint setting.

@@ 11-15
Hashing, secure random text, identifiers, times, and type helpers.

@@ 17-24
The unit of work for the verify page's session, the attempts table, the pinned policy, shared parts of the face check's use cases, the Age Pass's rules, the outcome names, the session's state machine, and our error class.

@@ 26-27
The toolbox's type, for the type checker only.

@@ 29-30
Passes are given out within ten minutes of the check that earned them; a nonce lasts five minutes.

@@ 33-34
**`_refused`** — an `AgePassError` as the API's answer: `422`, with the rule's code after `age_pass_`.

@@ 37-40
**`issue`** — a batch of passes for the browser's keys.

@@ 41-48
One to twenty keys, each a valid public key, and no two the same: each pass has its own key, or two passes could be linked by it.

@@ 49-52
Lock the session's row, so two requests can't both give out passes, and read the policy it was created with.

@@ 53-62
The conditions, each with its own refusal: the website's policy takes passes; the session passed; it hasn't given out passes already; it wasn't itself decided by a pass (a pass can't renew itself, or one check would last forever); and it passed within the last ten minutes.

@@ 63-66
One pass per key: built by the rules, signed by Dwarpal's current key as a `dc+sd-jwt`, and joined to its disclosures.

@@ 67-68
Note when the batch was given — only when — and commit.

@@ 69-70
Answer with the passes, the lines they state, and when they expire.

@@ 73-75
**`nonce`** — a one-time number for the next presentation. Asking for one costs from the same hourly budgets as a face challenge, so nobody can ask for millions.

@@ 76-82
Only for a session whose policy takes passes, and that is still in progress.

@@ 83-86
Spend from the budgets; make 32 random bytes as text; keep them in Valkey for five minutes under this session's name (a new nonce replaces an old one); answer with the nonce and the audience — this session's ID — that the proof must name.

@@ 89-92
**`present`** — a pass in place of a face check.

@@ 93-96
Take the presentation apart, or refuse it.

@@ 97-99
Take the session's nonce: read and deleted in one step, so each nonce answers once. None there: refused, and the browser asks for a new one.

@@ 100-102
Check Dwarpal's signature on the pass, with the key ring, for the Age Pass type only.

@@ 103-110
Lock the session; the policy must take passes and the session must be in progress.

@@ 111-125
Every rule, in order: the pass's claims; the disclosures against its digests; the holder's key from the pass; and the holder's proof over this nonce, for this session, just now, covering exactly what was shown.

@@ 126-128
The pass must show a line at or above the policy's age: a pass from a 16+ check doesn't open an 18+ door.

@@ 129-133
**Each pass works once.** Its signed part's hash is stored in Valkey until the pass would expire anyway — with `claim`, which stores only if nothing is there: a second showing finds it, and is refused. Never the pass itself.

@@ 134-144
Record the decision as an attempt of kind `age_pass`, with the line it proved.

@@ 145-150
Complete the session with a pass, exactly as after a face check — its event and statistics are written by `announce` — commit, and answer.
