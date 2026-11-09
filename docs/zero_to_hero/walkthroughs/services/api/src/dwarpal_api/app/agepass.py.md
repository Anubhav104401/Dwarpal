---
fingerprint: f87f88365843e637
---
The **Age Pass's use cases** (Phase 9, §5.9.3): giving passes out after a passed check, and accepting one in place of the camera.

@@ 1-7
The module's docstring: the two use cases — giving passes out, and accepting one — and what is never recorded.

@@ 9
The project-wide type-hint setting.

@@ 11-15
Hashing, secure random text, identifiers, times, and type helpers.

@@ 17-32
The unit of work for the verify page's session, the attempts table, the pinned policy, shared parts of the face check's use cases, the Age Pass's rules, the outcome names, the session's state machine, and our error class. Since 9 Nov also `document_only` and `record_document_stage`, to count a live check that started at the ID document and was ended by a pass.

@@ 34-35
The toolbox's type, for the type checker only.

@@ 37-38
Passes are given out within ten minutes of the check that earned them; a nonce lasts five minutes.

@@ 41-42
**`_refused`** — an `AgePassError` as the API's answer: `422`, with the rule's code after `age_pass_`.

@@ 45-48
**`issue`** — a batch of passes for the browser's keys.

@@ 49-56
One to twenty keys, each a valid public key, and no two the same: each pass has its own key, or two passes could be linked by it.

@@ 57-60
Lock the session's row, so two requests can't both give out passes, and read the policy it was created with.

@@ 61-70
The conditions, each with its own refusal: the website's policy takes passes; the session passed; it hasn't given out passes already; it wasn't itself decided by a pass (a pass can't renew itself, or one check would last forever); and it passed within the last ten minutes.

@@ 71-74
One pass per key: built by the rules, signed by Dwarpal's current key as a `dc+sd-jwt`, and joined to its disclosures.

@@ 75-76
Note when the batch was given — only when — and commit.

@@ 77-78
Answer with the passes, the lines they state, and when they expire.

@@ 81-83
**`nonce`** — a one-time number for the next presentation. Asking for one costs from the same hourly budgets as a face challenge, so nobody can ask for millions.

@@ 84-90
Only for a session whose policy takes passes, and that is still in progress.

@@ 91-94
Spend from the budgets; make 32 random bytes as text; keep them in Valkey for five minutes under this session's name (a new nonce replaces an old one); answer with the nonce and the audience — this session's ID — that the proof must name.

@@ 97-100
**`present`** — a pass in place of a face check.

@@ 101-104
Take the presentation apart, or refuse it.

@@ 105-107
Take the session's nonce: read and deleted in one step, so each nonce answers once. None there: refused, and the browser asks for a new one.

@@ 108-110
Check Dwarpal's signature on the pass, with the key ring, for the Age Pass type only.

@@ 111-118
Lock the session; the policy must take passes and the session must be in progress.

@@ 119-133
Every rule, in order: the pass's claims; the disclosures against its digests; the holder's key from the pass; and the holder's proof over this nonce, for this session, just now, covering exactly what was shown.

@@ 134-136
The pass must show a line at or above the policy's age: a pass from a 16+ check doesn't open an 18+ door.

@@ 137-141
**Each pass works once.** Its signed part's hash is stored in Valkey until the pass would expire anyway — with `claim`, which stores only if nothing is there: a second showing finds it, and is refused. Never the pass itself.

@@ 142-152
Record the decision as an attempt of kind `age_pass`, with the line it proved.

@@ 153-160
Complete the session with a pass, exactly as after a face check — its event and statistics are written by `announce`. A live check that started at the ID document (D24) also counts that check as ended, by `age_pass` (9 Nov): the person didn't leave, they had a pass. Commit, and answer.
