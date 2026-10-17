---
fingerprint: be97300f2c937e48
---
**Near-duplicate removal.** Photo collections gathered from the internet contain the same photo more than once — re-uploaded, resized, re-compressed, turned grey. If one copy lands in training and another in the test set, the model is tested on a photo it has already studied, and looks better than it is (§2.2). If two copies land in the calibration set, they count as two people when they are one, and the safety bound (§2.14) claims more evidence than it has.

Comparing every face with every other in detail would mean 4.8 billion comparisons. So the work is done in **two stages**:

```
97,645 faces ──► 1. the sieve: perceptual hashes within 10 bits of each other ──► 123,774 candidate pairs
                                (fast: bit arithmetic on whole blocks of hashes)
             ──► 2. the check: compare the pairs' fine detail; similarity ≥ 0.6 ──► 502 confirmed pairs
             ──► 3. group copies of the same photo; keep one per group, in the most protected split
             ──► .datasets/manifest/fairface.duplicates.csv: 467 copies removed
```

Both limits — 10 bits and 0.6 — were chosen by **looking at real pairs** on either side of them; §5.2.3 tells that story.

@@ 1-7
The docstring: the job, the two stages, and the command.

@@ 9
The project-wide type-hint setting.

@@ 11-19
Standard-library tools: `argparse`, `csv`, `sys`, `zipfile`, `Counter`, the types for sequences, `ExitStack` (to close several open zips safely), `dataclass` and `Path`.

@@ 21-23
OpenCV, NumPy, and NumPy's type for arrays.

@@ 24
**`DisjointSet`** from SciPy — a ready-made, well-tested way of grouping things that are linked in pairs (below).

@@ 26-29
From the ML package: manifests, rows, age labels and tables; where prepared faces are; the register. From the vision library: the careful image decoder.

@@ 31-33
**The two limits**, and a comment saying where the evidence for them is written down:

- `SIEVE_DISTANCE = 10` — two hashes are a candidate pair if at most 10 of their 64 bits differ;
- `MIN_SIMILARITY = 0.6` — a candidate pair is confirmed as the same photo if its fine-detail similarity is at least 0.6.

@@ 34-35
How fine detail is measured: on a 64×64 grey version of the face, with a blur of strength 2 (below).

@@ 36
`BLOCK = 256` — the sieve compares 256 hashes against the rest at a time.

@@ 37-38
**`SPLIT_PRIORITY`** — which copy to keep. Lower numbers win: a copy in `test` is kept over one in `calib`, `calib` over `val`, and `val` over `train`. The copy that survives is always the one in the split that matters most to keep clean, and the copies that would have leaked into it are the ones removed.

@@ 40
`Vector` — a name for "a list of decimal numbers in a NumPy array".

@@ 43-50
**`Duplicate`** — one removed copy: which image, its split, the copy that was kept and its split, how similar they were, and whether both copies had the same age label.

@@ 53
**`close_pairs`** — the sieve. It yields every pair of positions `(a, b)`, with `a` before `b`, whose hashes differ in at most `max_distance` bits.

@@ 54-56
Take the hashes 256 at a time (`block`), and compare each block only with itself and everything after it (`rest`): pairs with earlier hashes were already found by earlier blocks.

@@ 57
The heart of the sieve, in one line. `block[:, None] ^ rest[None, :]` arranges the block as a column and the rest as a row, and NumPy fills in the whole table between them: each cell is the **XOR** of two hashes, which has a 1 exactly where the two differ. `np.bitwise_count` counts those 1s — the **Hamming distance**. For a block of 256 against 97,645 hashes, that is 25 million distances, computed by NumPy's fast built-in loops in a fraction of a second. The whole sieve, over all 97,645 faces, takes well under a minute.

@@ 58-60
`np.nonzero` gives the positions of every close pair in the table. Within the block's own square of the table, each pair appears twice (and every hash is at distance 0 from itself), so only `i < j` is kept. The positions are turned back into positions in the full list.

@@ 63
**`fine_detail`** — the check's view of a face: only its *fine detail*.

@@ 64-65
Decode the aligned face, turn it grey, and shrink it to 64×64.

@@ 66
Subtract a blurred copy of the face from itself. Blurring keeps only the broad shapes; taking them away leaves only the fine detail — pores, hair strands, the edges of glasses, the texture of the background. This is the trick that makes the check work. After alignment, *every* face has its eyes, nose and mouth in the same places, so the broad shapes of two strangers can look remarkably alike. Their fine detail never matches, but two copies of one photo share it exactly, even after resizing, re-compression or conversion to grey.

@@ 67-68
Shift the numbers so they average zero, and scale them so that their length (`np.linalg.norm`, √ of the sum of squares) is 1. `max(…, 1e-6)` avoids dividing by zero for a completely flat picture.

@@ 71-72
**`similarity`** — multiply two such vectors number by number and add up (`np.dot`). Because both were shifted and scaled, the result is their **correlation**: 1 for identical detail, around 0 for unrelated detail.

@@ 75-79
**`Details`** — fine detail on demand, from the zips of prepared faces: one zip per dataset, since a search may span two (`--against`, below). Many faces take part in several candidate pairs, so each is computed once and remembered in `cache`.

@@ 81-85
`__getitem__` is what Python calls for `details[index]`: compute the detail — reading the face from its own dataset's zip — if it isn't remembered yet, then return it.

@@ 88-90
**`confirmed_pairs`** — the check: from the candidate pairs, yield the ones whose fine detail is at least `min_similarity` alike, with their score.

@@ 91-94
Score each pair, and pass on the confirmed ones.

@@ 97
**`groups_of`** — turn confirmed *pairs* into *groups* of copies. If A matches B and B matches C, then A, B and C are one group, even if A and C were never compared.

@@ 98
A `DisjointSet` starts with every face in a group of its own.

@@ 99-100
Each confirmed pair merges the two groups its faces belong to.

@@ 101
Return every group with more than one face, its members in order.

@@ 104
**`resolve`** — decide which copy of each group to keep. `seen` names a dataset that models have already learned from, if the search includes one.

@@ 105-107
For each group, first find any copies that belong to the `seen` dataset.

@@ 108-110
**If the group has a copy a model learned from**, keep that one, and remove every copy in the *other* dataset — whatever split it is in. A model trained on FairFace has already studied that photo; testing it on UTKFace's copy would measure its memory, not its judgement. Copies inside the `seen` dataset itself are never removed here: that dataset's own duplicates were handled when it was prepared, and its models are already trained.

@@ 111-113
**Otherwise**, as before: keep the copy in the highest-priority split (between copies in the same split, the one whose name sorts first, so the choice is always the same), and remove the rest.

@@ 114-125
Every removed copy is recorded as a `Duplicate`, with its similarity to the kept copy and whether their age labels agree.

@@ 126
Return the removed copies.

@@ 129
**`faces_with_hashes`** — load the rows and hashes of every successfully prepared face.

@@ 130-131
Read the preparation table, keeping each `ok` face's hash by image name.

@@ 132
The manifest's rows for those faces, in manifest order.

@@ 133
Their hashes, as one NumPy array of unsigned 64-bit numbers (`int(…, 16)` reads hexadecimal).

@@ 136-146
**`find_duplicates`** — the whole process: open every dataset's prepared faces (closing them all at the end), sieve, check, group and resolve. When a `seen` dataset is included, pairs *within* it are skipped before the costly check: they aren't this search's business. The stages are chained as **generators**, so pairs flow through one at a time and the candidates are never all held in memory at once.

@@ 149
**`summary`** — what to print.

@@ 150-152
Count the removed copies by where they were and where the kept copy is — `train -> fairface test` means a training copy of a FairFace test photo was removed — and how many disagreed about the age.

@@ 153
List those split pairs.

@@ 154-156
How many usable faces remain in each split, once duplicates are taken out.

@@ 157
Join the lines.

@@ 160-164
**`main`** — the dataset's name and, optionally, `--against`: a dataset that models learned from.

@@ 165-176
Look up the dataset and its faces. With `--against`, add the other dataset's faces and hashes to the search. Find the duplicates, write the removed copies of *this* dataset to `.datasets/manifest/<name>.duplicates.csv`, and print the summary. (Approval was checked when the faces were prepared; this step only reads what preparation wrote.)

@@ 179-180
Run `main` when the module is started as a program.
