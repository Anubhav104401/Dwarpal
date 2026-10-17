---
fingerprint: 152bebc735353ddc
---
**Downloads third-party model files and refuses any that don't match their recorded fingerprint.** Every fresh machine runs it — developers' laptops, CI, the production server — so no model file ever needs to live in Git.

!!! key "Key idea — verify, then trust"
    Code we download is code we will run. A fingerprint check turns "we hope this is the right file" into "this is provably the exact file we reviewed". Package managers do the same with lockfiles; this script does it for model files.

@@ 1-5
The docstring: what the script does, and its two commands. Plain `fetch_models.py` fetches what serving, the verify page and the tests need — CI runs it on every change. `--training` also fetches pretrained weights used only for training (added in Phase 2): 114 MB that CI never needs.

@@ 7
The project-wide type-hint setting.

@@ 9-13
`argparse` for the `--training` option, `hashlib` for SHA-256, `json` to read the register, `sys` for the exit code, and `Path` for file locations.

@@ 15
`httpx` — the HTTP client (from the `dev` dependency group).

@@ 17-18
The repository root (two folders up from `infra/scripts/`) and its `models` folder.

@@ 21
**`sha256_of`** — compute a file's SHA-256 fingerprint.

@@ 22
Start an empty SHA-256 calculation.

@@ 23-25
Read the file **1 MB at a time** (`1 << 20` is 2²⁰ = 1,048,576) and feed each piece into the calculation. Reading in chunks means even a multi-gigabyte model never has to fit in memory at once.

`iter(lambda: …, b"")` keeps calling the reading function until it returns empty bytes, which means the end of the file.

@@ 26
Return the fingerprint as 64 hexadecimal characters.

@@ 29
**`fetch(entry)`** — make sure one model file is present and correct. It returns `True` on success.

@@ 30
Where the file should be.

@@ 31-33
**Already there and correct?** Then nothing to do. The fingerprint is checked even here, so a file damaged on disk is downloaded again.

@@ 34-36
**Only HTTPS.** An unencrypted `http://` download could be altered in transit. The fingerprint check would catch that, but refusing up front is clearer.

@@ 37
Create the destination folder if needed.

@@ 38
Download first to a temporary name ending in `.part`. If the download is interrupted, no half-written file ever sits under the real name.

@@ 39
**Start the download as a stream**, so the file arrives in pieces instead of all at once in memory.

- `follow_redirects=True` — Hugging Face answers with a redirect to its file-storage servers, and this follows it.
- `timeout=60.0` — give up if the server is silent for a minute.

@@ 40
If the server answered with an error (`404 Not Found`, `500`, …), stop with that error.

@@ 41-43
Write each arriving piece to the `.part` file.

@@ 44
Fingerprint what actually arrived.

@@ 45-48
**Mismatch: delete the file and fail**, printing both fingerprints so the problem can be investigated. Never keep an unverified file.

@@ 49
**Match: move the file into place.** `replace` renames it in a single step, so other programs see either no file or the complete, verified file — never a partial one.

@@ 50-51
Report success, with the path written relative to the repository and with forward slashes.

@@ 54-57
**`main`** — read the one option, `--training` (`store_true`: present means true, absent means false).

@@ 58
Read and parse `models/third_party.json`, explicitly as UTF-8.

@@ 59-60
Choose the entries to fetch — every entry not marked `"training"`, and the training ones only if asked — then fetch each one. A list comprehension (rather than stopping at the first failure) reports every problem in one run.

@@ 61
Exit code `0` only if every model is present and verified; otherwise `1`. That makes CI stop before any test runs.

@@ 64-65
The entry point: run `main()` when the file is executed directly, and hand its result to `sys.exit`.
