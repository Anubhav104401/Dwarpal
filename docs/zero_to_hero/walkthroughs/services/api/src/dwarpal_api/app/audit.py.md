---
fingerprint: cfb6ac7c06a5c5be
---
The **audit log** (Phase 4, §5.4.4): a record of who changed what — a key created or rotated, a policy version added, a webhook endpoint registered or removed — kept so that nobody can quietly alter or remove an entry afterwards.

The trick is a **hash chain**. Each entry stores the hash of the entry before it, and its own hash is computed over that previous hash *and* its own facts:

```
entry 1: hash₁ = SHA-256(000…0 ‖ facts₁)
entry 2: hash₂ = SHA-256(hash₁ ‖ facts₂)
entry 3: hash₃ = SHA-256(hash₂ ‖ facts₃)
```

Change one fact in entry 2, and hash₂ no longer matches; recompute hash₂ to hide it, and entry 3's stored "previous hash" no longer matches; and so on to the end. To hide one edit, a forger would have to rewrite every later entry *and* the head row that remembers the latest hash. A verifier that recomputes the chain finds the first link that doesn't follow.

!!! kid "Explain like I'm six — the paper chain"
    Each paper ring is closed through the ring before it. You can't take a ring out of the middle, or swap one for a different colour, without opening the rings next to it — and an opened ring is easy to spot.

!!! honest "Honest limitation"
    A chain proves an entry was changed *after* it was written; it doesn't stop someone who controls the database from rewriting the whole chain consistently. Publishing the latest hash somewhere outside the database (a daily signed note, say) would close that gap; it is not done yet.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-10
`hashlib` (SHA-256), `json`, `uuid`, `dataclass`, `datetime` and `Any`.

@@ 12-14
SQLAlchemy's `select`, PostgreSQL's `insert` (which can be told what to do when a row already exists), and the session type.

@@ 16
The two tables.

@@ 18
`GENESIS` — 32 zero bytes: the "previous hash" of each organisation's first entry, where every chain begins.

@@ 21-22
**`canonical`** — an entry's facts as one exact string of bytes. A hash covers bytes, so the same entry must always give the same bytes.

@@ 23-31
The facts: the organisation, the number, who, what, to what, the details and when — everything except the hashes themselves.

@@ 32
As JSON with sorted keys and no spaces, so nothing about the ordering or spacing of a dictionary can change the bytes. `ensure_ascii=False` keeps characters such as `é` as themselves.

@@ 35-37
**`link`** — the chain's rule: this entry's hash is the SHA-256 of the previous hash followed by this entry's canonical bytes.

@@ 40-48
**`record`** — append one entry. It takes the caller's database session, the organisation, who is acting (a pair such as `("api_key", "x7Kp…")`), the action, its target, the facts, and the time.

@@ 49-51
Its docstring. It works **inside the caller's transaction**, so a change and its audit entry are saved together. It is also why the head row is locked: two changes in one organisation at the same moment must not both become entry 7.

@@ 52-53
Make sure the organisation has a head row: insert one (number 0, the genesis hash), and if it already exists, do nothing (`on_conflict_do_nothing`). Two first appends at the same moment can't both create one.

@@ 54-56
Read the head **locked** (`with_for_update`): any other append for this organisation now waits until this transaction ends. Other organisations are not affected. It must exist by now; if not, something is badly wrong.

@@ 57-68
The new entry: the next number, the actor's two parts, the action, target and facts, the previous hash, an empty hash for a moment, and the time.

@@ 69
Now that its facts are set, compute its hash.

@@ 70-71
Add it, and move the head along to it.

@@ 72
Return the entry.

@@ 75-79
**`ChainReport`** — the result of a check: how many entries were read, whether the chain is intact, and if not, the number of the first entry that doesn't check out.

@@ 82-84
**`verify`** — recompute an organisation's chain from the start.

@@ 85-86
Read its entries in order. Start from the genesis hash, expecting entry 1.

@@ 87-91
For each entry, three checks: is it the next number (nothing removed or inserted in the middle)? Does its stored previous hash match the hash just computed? Does its own hash follow from that? At the first failure, report that entry. Otherwise carry on from this one.

@@ 92-94
Finally, compare with the head. Deleting the **last** entries leaves a chain that checks out perfectly, but shorter than the head remembers. Then the first missing number is reported.

@@ 95
Everything followed: intact.
