---
fingerprint: c1a66e408b4d7baa
---
The **fetch command**: download an approved dataset's files, and keep each one only if its fingerprint matches the register. It works like the model downloader of Phase 1 (`infra/scripts/fetch_models.py`), with one more rule in front: **a dataset that the owner hasn't approved is refused outright**, whatever is typed.

```
uv run --package dwarpal-ml python -m dwarpal_ml.fetch fairface    →  present / fetched, file by file
uv run --package dwarpal-ml python -m dwarpal_ml.fetch utkface     →  refused  utkface: not approved
```

@@ 1-4
The docstring, with the command.

@@ 6
The project-wide type-hint setting.

@@ 8-11
`argparse` (the command line), `hashlib` (SHA-256), `sys` (the exit code) and `Path`.

@@ 13
`httpx` — the HTTP client, used for streaming downloads.

@@ 15
The register's types and lookup.

@@ 18-23
**`sha256_of`** — a file's fingerprint, reading it 1 MiB at a time (`1 << 20` bytes), so even a multi-gigabyte file never has to fit in memory at once. `iter(function, b"")` keeps calling `function` until it returns empty bytes — the end of the file.

@@ 26
**`fetch_file`** — make sure one file is present and genuine. It returns `True` on success.

@@ 27-30
If the file already exists *and* its fingerprint matches, there is nothing to do.

@@ 31-33
Only `https://` addresses are allowed: an unencrypted download could be swapped by anyone on the network path.

@@ 34
Create the dataset's folder if needed.

@@ 35
Download to a temporary name ending in `.part`, so a half-finished download can never be mistaken for a finished one.

@@ 36-40
Stream the download: `httpx.stream` reads the answer in pieces, following redirects (Google Drive redirects), giving up if the server stays silent for 120 seconds. `raise_for_status()` turns an HTTP error, such as `404`, into an exception. Each piece is written straight to the file.

@@ 41-45
Fingerprint the download. If it doesn't match the register, delete it and say so — *both* fingerprints are printed, so a person can investigate.

@@ 46-48
It matches: rename it to its real name, and report its size. A rename is instant and atomic, so the real file appears all at once.

@@ 51
**`fetch`** — a whole dataset.

@@ 52-54
**The approval rule**: refuse any dataset not approved in the register, naming its licence.

@@ 55-57
A dataset with no pinned files can't be fetched safely either.

@@ 58-59
Fetch every file. The results are collected into a list first, so that *every* file is attempted and reported even if an early one fails, and only then combined with `all(...)`.

@@ 62-66
**`main`** — read the dataset's name from the command line, fetch it, and exit with `0` for success or `1` for failure.

@@ 69-70
Run `main` when the module is started as a program.
