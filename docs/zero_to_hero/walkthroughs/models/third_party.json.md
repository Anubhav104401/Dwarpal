---
fingerprint: 7967a4f77987a5ef
---
The **register of third-party model files**: AI models made by others that Dwarpal uses. Model files are never stored in Git (they are large, and their licences vary — ADR-0014, ADR-0018). This file records *exactly* which file to fetch, from where, under which licence, and the fingerprint it must have. `infra/scripts/fetch_models.py` reads it.

@@ 1-2
A JSON object whose `models` field is a list, with one entry per model file.

@@ 3-4
The first (and so far only) entry. `name` is a short, human-friendly label used in messages.

@@ 5
`file` — where the downloaded file is stored, relative to the `models/` folder. The inference service's settings point at the same path.

@@ 6
`url` — where to download it from: the OpenCV organisation's official page on **Hugging Face**, a widely used model-hosting site. It is a mirror of the same file in OpenCV's own model zoo on GitHub.

@@ 7
`sha256` — the file's **SHA-256 fingerprint** (§X.5). A downloaded file is accepted **only** if its fingerprint matches exactly. A file that was corrupted, tampered with or swapped on the server is therefore rejected.

This value was not simply copied from our own first download. It was read from the Git LFS pointer in OpenCV's own repository — an **independent source** — and the download matched it.

@@ 8
`bytes` — the expected size (232,589 bytes, about 227 KB), recorded for humans.

@@ 9
`licence` — **MIT**, copyright Shiqi Yu, the YuNet author. It was checked in the upstream licence file before first use, as ADR-0018 requires.

@@ 10
`source` — where the model's code, documentation and licence live, for anyone who wants to check.

@@ 11-13
The closing brackets of the entry, the list and the object.
