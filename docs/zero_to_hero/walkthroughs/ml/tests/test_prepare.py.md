---
fingerprint: 06cf88fbb58063ef
---
Tests for face preparation and duplicate removal. They use the vision library's test portrait (a public-domain photo of an astronaut, §5.1.1) and pictures made from it — resized, re-saved, turned grey, mirrored — so they need neither FairFace nor the internet. They do need the face-detector model, which the project's setup downloads (`infra/scripts/fetch_models.py`).

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-6
`zipfile` (to build small test archives) and `Path`.

@@ 8-12
OpenCV, NumPy, pytest and Hypothesis.

@@ 14-18
The code under test, the manifest's `Row`, and from the vision library the detector, the decoder and the `Face` type.

@@ 20
`PORTRAIT` — the test portrait, found from this file's location: two folders up is the repository, then into the vision library's test fixtures.

@@ 23-25
A **fixture** shared by the whole file (`scope="module"`): the detector is loaded once, not once per test.

@@ 28-29
**`jpeg`** — a helper that encodes a picture as JPEG bytes, at a chosen quality.

@@ 32-33
**`row`** — a helper that makes a manifest row with only the parts a test cares about: a name, a split, and an age band.

@@ 36-42
**The portrait is prepared.** Its status is `ok`, one face was found, the fingerprint has 16 hexadecimal digits, and the saved face decodes to a 256×256 colour picture.

@@ 45-48
**Failures are recorded, not hidden.** Bytes that aren't an image are `undecodable`; a plain grey square is `no_face`, with no face saved.

@@ 51-55
**The central face wins.** Two made-up faces: a very confident one in the corner (score 0.99) and a less confident one in the middle (0.7). The middle one is chosen — confidence doesn't decide whose face it is.

@@ 58
**Both stages of duplicate detection, on real pictures.**

@@ 59-61
The portrait; a copy shrunk and re-saved at low JPEG quality; and a mirror image (`[:, ::-1]` reverses the order of the columns). `ascontiguousarray` lays the mirrored pixels out afresh in memory, which OpenCV requires.

@@ 62-64
The sieve: the re-saved copy's hash is within the sieve distance of the original's; the mirror image's is not. `bit_count` counts the 1-bits of the XOR (§5.2.3).

@@ 65-67
The check: the re-saved copy's fine detail is confirmed as the same; the mirror's is not. A mirrored photo is arguably "the same photo", but neither stage treats it as one, and this test records that limit so that nobody assumes otherwise.

@@ 70
**Preparing a whole (tiny) dataset.**

@@ 71-74
A zip with the portrait and a broken file, and their rows.

@@ 75-76
Prepare it twice, into two different zips, using one worker process.

@@ 77-78
The portrait is `ok` and the broken file `undecodable`; only the portrait's face is in the zip.

@@ 79
And the two zips are **byte-for-byte identical** — thanks to the fixed timestamp in `prepare.py`.

@@ 82-84
**The fast sieve finds exactly what a slow search finds.** Hypothesis invents lists of 2 to 40 random 64-bit hashes, and a distance limit from 0 to 12.

@@ 85-90
The slow, obviously-correct search: compare every pair with every other, one at a time.

@@ 91
The fast block-by-block sieve must find exactly the same set of pairs — no more, no fewer — for every list Hypothesis tries.

@@ 94
**The whole process, end to end.**

@@ 95-102
Four pictures: the portrait (`a`), a copy shrunk and enlarged again (`b`), a grey copy (`c`), and random noise (`d`).

@@ 103-105
Save them in a zip, as prepared faces would be.

@@ 106
Their rows: `a` in training, `b` in the test set (with a different age band), `c` in validation, `d` in training.

@@ 107
All four hashes are set to zero, so the sieve shortlists every pair, and the check alone has to decide.

@@ 108-112
Exactly two copies are removed, `a` and `c`, and both point to `b` — the copy in the test set, the most protected split. The noise is untouched. Both are marked as disagreeing about the age, because `b` was given a different band. (The faces are passed as a mapping from dataset name to zip, since duplicate removal can now read two datasets at once.)

@@ 115-117
**Copies of photos a model learned from** (added with UTKFace). Two one-photo zips: the portrait in a dataset called `seen`, and a resized copy in a dataset called `new`.

@@ 118-121
The new copy is in its dataset's test split; the original is in the other's training split.

@@ 122-123
Search with `seen` named as the dataset models learned from, with both hashes zero so the check alone decides.

@@ 124-126
The copy in `new` is removed — even though it sits in a test split, which would normally win — and it points to the original in `seen`'s training split. A model trained on `seen` has already studied this photo, so measuring it on the copy would flatter it.
