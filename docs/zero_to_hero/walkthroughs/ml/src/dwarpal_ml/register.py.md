---
fingerprint: bdeb83ad20c81de8
---
Reads the licence register (`ml/datasets.toml`) into typed Python objects, so the rest of the ML code asks questions like "is this dataset approved?" of an object with known fields, rather than poking at raw text.

@@ 1
The docstring.

@@ 3
The project-wide type-hint setting.

@@ 5-7
`tomllib` — Python's built-in TOML reader (since Python 3.11); `dataclass`; `Path`.

@@ 9
`ROOT` — the repository's top folder. `resolve()` makes the file's path absolute; `.parents` lists the folders that contain it, nearest first, counting from 0 — `dwarpal_ml` (0), `src` (1), `ml` (2), and the repository itself (3).

@@ 10
`REGISTER` — where the licence register lives.

@@ 11
`RAW` — where downloaded datasets go: `.datasets/raw/`, a folder Git ignores. Images of real people's faces must never be committed to a repository (§0.15).

@@ 14-19
**`DatasetFile`** — one pinned file: its name, address, fingerprint and size.

@@ 22-33
**`Dataset`** — one register entry: name, title, licence, permitted use, citation, the kind of age labels and where they came from (`age_source`), how to find the labelled person in a photo (`subject`), whether it is approved, and its files as a **tuple** (which can't be changed, matching `frozen=True`).

@@ 35-37
**`folder`** — a computed property: the dataset's own folder under `.datasets/raw/`, such as `.datasets/raw/fairface`.

@@ 40-41
`UnknownDatasetError` — asked for a name the register doesn't have.

@@ 44
**`load_register`** — read the whole register; every dataset, by name.

@@ 45
Read the file, parse it, and take the list under `dataset`.

@@ 46-47
Start an empty dictionary, and go through the entries.

@@ 48
The entry's files, each made into a `DatasetFile`. `entry.get("files", [])` gives an empty list for entries without files (the unapproved ones).

@@ 49-60
Build the `Dataset` and store it under its name. `bool(...)` and `int(...)` make sure the values have exactly the expected types, whatever the file contains. `entry.get(…, default)` gives the two newer fields a value for entries that don't set them.

@@ 61
Return them all.

@@ 64-68
**`dataset`** — one dataset by name, or `UnknownDatasetError` (with Python's own `KeyError` hidden by `from None`, as in the API's `policy.py`).
