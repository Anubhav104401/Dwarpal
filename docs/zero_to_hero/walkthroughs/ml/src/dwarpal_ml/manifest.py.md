---
fingerprint: a307c7409a01e0bd
---
The **unified manifest**: one CSV table listing every image of a dataset, one row per image, in the *same* columns whatever dataset it came from. Every dataset arrives in its own shape — FairFace keeps its labels in two CSV files beside a zip of images; UTKFace hides its labels inside each file's name; others use spreadsheets or folders. A small **adapter** per dataset turns its shape into rows of one shape, and everything later (training, testing, calibration) reads only manifests.

The manifest also fixes each image's **split** — which job the image may be used for (§2.2):

| Split | Share | Used for |
| :-- | :-: | :-- |
| `train` | 80 % of FairFace's official training set | teaching the model |
| `val` | 10 % | checking progress while it learns, and choosing settings |
| `calib` | 10 % | setting the safety thresholds (`risk.py`) — never seen in training |
| `test` | FairFace's whole official validation set | the final, locked exam |

```
uv run --package dwarpal-ml python -m dwarpal_ml.manifest fairface
97,698 images
splits: calib 8,621, test 10,954, train 69,469, val 8,654
ages:   0-2 1,991, 3-9 11,764, 10-19 10,284, 20-29 28,898, …, 70+ 960
groups: Black 13,789, East Asian 13,837, …, White 18,612
```

The manifest holds only file names and labels — no pictures — and it is written under `.datasets/`, beside the images, so it is never committed either.

@@ 1-4
The docstring, with the command.

@@ 6
The project-wide type-hint setting.

@@ 8-17
Standard-library tools only: `argparse` (the command line), `csv` (reading and writing CSV tables), `hashlib` (fingerprints, used here for splitting), `re` (patterns in text), `sys` (the exit code), `zipfile` (looking inside the zip of images without unpacking it), `Counter` (counting things), the types for functions and sequences, the dataclass helpers, and `Path`.

@@ 18
`TYPE_CHECKING` — a constant that is `False` when the program runs, but treated as `True` by the type checker (mypy). Code under `if TYPE_CHECKING:` is read only by the checker.

@@ 20
From the register: the raw-data folder, the `Dataset` type, and the lookup.

@@ 22-23
`DataclassInstance` — the type checker's name for "any dataclass object". It lives in `_typeshed`, a module that exists only for type checkers and can't be imported when the program runs — hence `if TYPE_CHECKING`. (Thanks to `from __future__ import annotations` on line 6, type hints are never evaluated at run time, so using the name in a hint is safe.)

@@ 25
`MANIFESTS` — manifests are written to `.datasets/manifest/`, next to `.datasets/raw/`.

@@ 26-27
**`AGE_RANGE`** — a **regular expression**, a pattern that text is matched against. It accepts three spellings of an age band:

- `(\d+)-(\d+)` — two numbers with a dash, as in `10-19` (`\d+` means "one or more digits"; each pair of brackets **captures** the part it matches, so the code can read it afterwards);
- `(\d+)\+` — a number and a plus sign, as in `70+` (`\+` is a real plus sign: on its own, `+` means "one or more");
- `more than (\d+)` — the words FairFace actually uses.

`^` and `$` mean the pattern must cover the *whole* text, and `(?:…|…|…)` means "one of these", without capturing. The comment records why the third spelling is there: FairFace's documentation says `70+`, but its label file says `more than 70`. The first run of this code found that out by refusing the unknown spelling (see `parse_age_range`).

@@ 30-42
**`Row`** — one image in the manifest:

- `image_id` — a name unique across all datasets, such as `fairface/train/1.jpg`;
- `dataset`, `archive`, `member` — where to find the image: which dataset, which zip file, and which file inside the zip;
- `age_low` and `age_high` — the age band (`age_high` is `None` for an open band such as "70 and over");
- `age_exact` — the exact age, when the dataset has one (FairFace never does);
- `sex` and `group` — the dataset's own labels, kept so errors can be measured for each group (§2.16);
- `licence` — copied from the register onto every row, so the terms travel with the data;
- `split` — the image's job.

@@ 45
**`parse_age_range`** — turn a label such as `"10-19"` into `(10, 19)`, or `"more than 70"` into `(70, None)`.

@@ 46
Match the pattern, ignoring spaces at either end.

@@ 47-48
No match: refuse loudly, rather than guess. A label nobody expected could mean anything.

@@ 49-50
If the first capture matched, it was the dash form: return both numbers. `match[1]` is the first capture, `match[2]` the second.

@@ 51
Otherwise it was one of the open forms: the number is in capture 3 (`70+`) or capture 4 (`more than 70`). `a or b` gives `b` when `a` is `None`.

@@ 54
**`split_for`** — the split for one image.

@@ 55-56
FairFace's own validation set becomes our **test** set, untouched: it was put together by the dataset's authors, so nothing we chose can have leaked into it.

@@ 57
The rest is split by the image's **fingerprint**: take the SHA-256 of its `image_id`, read the first 4 bytes as a number, and keep the remainder after dividing by 100 — a number from 0 to 99 that looks random but is always the same for the same image. Splitting this way, rather than with a random-number generator, means the split never changes: on any computer, on any run, today or next year, an image stays in the split it started in. If a test image could ever drift into training, the test would be quietly ruined.

@@ 58
Numbers 0–79 are `train`, 80–89 `val`, and 90–99 `calib`.

@@ 61
**`fairface_rows`** — FairFace's adapter. It **yields** rows one at a time (the `Iterator` type), so the whole dataset never has to be built in memory before it is written.

@@ 62
The images' zip file: FairFace's wide-margin version (see `ml/datasets.toml`).

@@ 63-64
Open the zip and take the list of files it holds (`namelist`). Only the list is read — the zip is never unpacked.

@@ 65-66
For each of FairFace's two label files (`train` and `val`), open it as UTF-8 text. `newline=""` lets the `csv` module handle line endings itself, as its documentation asks.

@@ 67
`csv.DictReader` reads each row as a dictionary keyed by the header line: `record["age"]`, `record["race"]`, and so on.

@@ 68-70
The image's path inside the zip, such as `train/1.jpg`. A label whose image is missing from the zip is skipped: a manifest must only list images that exist.

@@ 71
Read the age band.

@@ 72
The unique name: the dataset's name in front of the path.

@@ 73-85
Build the row. `sex` is lower-cased (`Female` becomes `female`) so all datasets spell it the same way; `group` keeps FairFace's own group names.

@@ 88
**`ADAPTERS`** — the adapter for each dataset name. Adding a dataset later means writing its adapter and adding one entry here.

@@ 91
**`write_table`** — write any list of dataclass rows to a CSV file, and return them as a list. It is used for the manifest, and for the tables that face preparation and duplicate removal write (`prepare.py`, `dedup.py`). `[T: DataclassInstance]` makes it **generic**: `T` stands for whichever dataclass is passed in as `kind`, and the type checker then knows that the list returned holds that same kind of row.

@@ 92
Collect the rows into a list (they arrive one at a time from the adapter).

@@ 93
Create the folder if needed.

@@ 94-95
Open the file for writing, and a CSV writer on it.

@@ 96
The header line: the names of the dataclass's fields, in order (`fields(kind)` lists them).

@@ 97-98
One line per row. `astuple` turns a row into its values, in the same order; `None` (an unknown value) is written as an empty cell.

@@ 99
Return the list, for the summary.

@@ 102-103
**`write_manifest`** — the manifest is simply a table of `Row`s.

@@ 106-107
**`optional_int`** — the reverse of writing `None` as an empty cell: an empty cell is read back as `None`, anything else as a whole number.

@@ 110-127
**`read_manifest`** — read a manifest back into `Row`s, turning each column's text into the right type: numbers with `int`, possibly-empty numbers with `optional_int`, and everything else kept as text. Face preparation and duplicate removal both start from it.

@@ 130-131
**`age_label`** — a row's age band as text: `10-19`, or `70+` for an open band.

@@ 134
**`summary`** — the short report printed after a manifest is written. A person should *see* how much data there is, and how it divides, before anything is trained on it.

@@ 135-137
Count the images per split, per age band, and per group. The age bands are counted by `(age_low, label)` pairs, so that sorting puts them in age order — `3-9` before `10-19`, which plain text sorting would get wrong.

@@ 138
The first line: how many images. `:,` writes numbers with thousands separators (`97,698`).

@@ 139-141
One line each for splits, ages and groups. `", ".join(...)` puts commas between the parts; `for (_, label), count in …` unpacks each counted pair, ignoring the number used only for sorting (`_`).

@@ 142
Join the lines, one under another (`"\n"` is a line break).

@@ 145-148
**`main`** — read the dataset's name from the command line. `choices` means only datasets with an adapter are accepted.

@@ 149-152
Look the dataset up, and refuse it unless it is approved — the same rule as the fetch command, checked again here.

@@ 153
Run the adapter and write its manifest to `.datasets/manifest/<name>.csv`.

@@ 154-155
Print the summary, and report success.

@@ 158-159
Run `main` when the module is started as a program.
