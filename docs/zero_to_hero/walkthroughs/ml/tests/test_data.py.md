---
fingerprint: 9ab81f5974703f0b
---
Tests for the data side: the licence register, the fetch command's refusals, and the manifest. None of them downloads anything or needs the real dataset: where face images are needed, the test builds a tiny fake zip whose "images" are four bytes of text.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-6
`zipfile` (to build a fake image archive) and `Path`.

@@ 8
`pytest`.

@@ 10-12
The code under test: the `manifest` and `register` modules themselves (so the test can swap a setting inside `register`), the `fetch` function, and the register's types.

@@ 15
**The real register is checked**, not a copy: the test reads `ml/datasets.toml` itself.

@@ 16-17
FairFace is approved.

@@ 18
Every one of its files is pinned with a full fingerprint (64 hexadecimal characters) and an `https://` address.

@@ 19-20
UTKFace is *not* approved, and its licence is recorded as non-commercial. If someone flipped its approval without the owner's decision, this test would catch it in review.

@@ 23
**Refusals.** `capsys` is a pytest **fixture** that captures what the code prints, so the test can read it.

@@ 24
Fetching the unapproved UTKFace fails — before any network request is made.

@@ 25-26
A dataset that is approved but has no pinned files also fails: approval alone is not enough.

@@ 27
And the printed output says `refused`.

@@ 30-32
**One test, run four times.** `parametrize` gives the test a list of `(text, expected)` pairs: the dash form, a two-digit band, both open-band spellings.

@@ 33-34
Each spelling is read as expected.

@@ 37
**The split.**

@@ 38-39
Split 20,000 made-up image names.

@@ 40
Splitting them again gives exactly the same result — the split is fixed.

@@ 41-42
About 80 % land in `train` and 10 % in `calib`, within a small allowance (the fingerprints only *behave* like random numbers, so the shares aren't exact).

@@ 43
Anything from the official validation set goes to `test`.

@@ 46-48
**FairFace's adapter, on a fake FairFace.** `tmp_path` is a fresh, empty folder for this test; `monkeypatch` changes a setting for the duration of the test, then puts it back.

@@ 49-51
Point the raw-data folder at the temporary folder, and create the dataset's folder inside it.

@@ 52-54
A zip holding two "images" — one from the training set, one from the validation set.

@@ 55-58
A training label file with two rows. The second row's image, `train/2.jpg`, is *not* in the zip.

@@ 59-61
A validation label file using FairFace's real spelling of its top band, `more than 70`.

@@ 62
A `Dataset` describing the fake FairFace.

@@ 63
Run the adapter.

@@ 64-67
Exactly two rows come out — the missing image was skipped — with the age bands read, the sex lower-cased, and the right splits: the training image's split is whatever `split_for` gives, and the validation image's is `test`.

@@ 68
Write them to a manifest.

@@ 69-71
The manifest's third line (the second row) ends as expected: `70` and an empty `age_high`, an empty `age_exact`, then `male`, `Black`, the licence and `test`. Unknown values are written as empty cells.

@@ 72
And `write_manifest` returns both rows.
