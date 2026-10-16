---
fingerprint: 4781862230425fc4
---
**Downloads third-party model files and refuses any that don't match their recorded fingerprint.** Every fresh machine runs it — developers' laptops, CI, the production server — so no model file ever needs to live in Git.

!!! key "Key idea — verify, then trust"
    Code we download is code we will run. A fingerprint check turns "we hope this is the right file" into "this is provably the exact file we reviewed". Package managers do the same with lockfiles; this script does it for model files.

@@ 1-4
The docstring: what the script does, and the command that runs it.

@@ 6
The project-wide type-hint setting.

@@ 8-11
`hashlib` for SHA-256, `json` to read the register, `sys` for the exit code, and `Path` for file locations.

@@ 13
`httpx` — the HTTP client (from the `dev` dependency group).

@@ 15-16
The repository root (two folders up from `infra/scripts/`) and its `models` folder.

@@ 19
**`sha256_of`** — compute a file's SHA-256 fingerprint.

@@ 20
Start an empty SHA-256 calculation.

@@ 21-23
Read the file **1 MB at a time** (`1 << 20` is 2²⁰ = 1,048,576) and feed each piece into the calculation. Reading in chunks means even a multi-gigabyte model never has to fit in memory at once.

`iter(lambda: …, b"")` keeps calling the reading function until it returns empty bytes, which means the end of the file.

@@ 24
Return the fingerprint as 64 hexadecimal characters.

@@ 27
**`fetch(entry)`** — make sure one model file is present and correct. It returns `True` on success.

@@ 28
Where the file should be.

@@ 29-31
**Already there and correct?** Then nothing to do. The fingerprint is checked even here, so a file damaged on disk is downloaded again.

@@ 32-34
**Only HTTPS.** An unencrypted `http://` download could be altered in transit. The fingerprint check would catch that, but refusing up front is clearer.

@@ 35
Create the destination folder if needed.

@@ 36
Download first to a temporary name ending in `.part`. If the download is interrupted, no half-written file ever sits under the real name.

@@ 37
**Start the download as a stream**, so the file arrives in pieces instead of all at once in memory.

- `follow_redirects=True` — Hugging Face answers with a redirect to its file-storage servers, and this follows it.
- `timeout=60.0` — give up if the server is silent for a minute.

@@ 38
If the server answered with an error (`404 Not Found`, `500`, …), stop with that error.

@@ 39-41
Write each arriving piece to the `.part` file.

@@ 42
Fingerprint what actually arrived.

@@ 43-46
**Mismatch: delete the file and fail**, printing both fingerprints so the problem can be investigated. Never keep an unverified file.

@@ 47
**Match: move the file into place.** `replace` renames it in a single step, so other programs see either no file or the complete, verified file — never a partial one.

@@ 48-49
Report success, with the path written relative to the repository and with forward slashes.

@@ 52
**`main`** — process every entry in the register.

@@ 53
Read and parse `models/third_party.json`, explicitly as UTF-8.

@@ 54
Fetch each model. A list comprehension (rather than stopping at the first failure) reports every problem in one run.

@@ 55
Exit code `0` only if every model is present and verified; otherwise `1`. That makes CI stop before any test runs.

@@ 58-59
The entry point: run `main()` when the file is executed directly, and hand its result to `sys.exit`.
