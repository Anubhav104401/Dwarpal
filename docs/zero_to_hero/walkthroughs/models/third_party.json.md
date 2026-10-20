---
fingerprint: f1c5e762e2ac9327
---
The **register of third-party model files**: AI models made by others that Dwarpal uses. Model files are never stored in Git (they are large, and their licences vary — ADR-0014, ADR-0018). This file records *exactly* which file to fetch, from where, under which licence, and the fingerprint it must have. `infra/scripts/fetch_models.py` reads it.

@@ 1-2
A JSON object whose `models` field is a list, with one entry per model file.

@@ 3-4
The first entry. `name` is a short, human-friendly label used in messages.

@@ 5
`use` — what the file is for: `serving` (needed by the running services and the tests) or `training` (needed only to train models). The fetcher downloads training files only when asked (`--training`), and training accepts only `training` entries (`ml/src/dwarpal_ml/model.py`). Added in Phase 2.

@@ 6
`file` — where the downloaded file is stored, relative to the `models/` folder. The inference service's settings point at the same path.

@@ 7
`url` — where to download it from: the OpenCV organisation's official page on **Hugging Face**, a widely used model-hosting site. It is a mirror of the same file in OpenCV's own model zoo on GitHub.

@@ 8
`sha256` — the file's **SHA-256 fingerprint** (§X.5). A downloaded file is accepted **only** if its fingerprint matches exactly. A file that was corrupted, tampered with or swapped on the server is therefore rejected.

This value was not simply copied from our own first download. It was read from the Git LFS pointer in OpenCV's own repository — an **independent source** — and the download matched it.

@@ 9
`bytes` — the expected size (232,589 bytes, about 227 KB), recorded for humans.

@@ 10
`licence` — **MIT**, copyright Shiqi Yu, the YuNet author. It was checked in the upstream licence file before first use, as ADR-0018 requires.

@@ 11
`source` — where the model's code, documentation and licence live, for anyone who wants to check.

@@ 12
The end of the first entry; a comma, because another follows.

@@ 13-15
The second entry (added in Phase 2): **pretrained weights** for training (§2.10), not used by any service.

@@ 16
`timm` — the backbone's name in the timm library, which is how training finds these weights: `--backbone convnext_tiny.in12k_ft_in1k --pretrained`.

@@ 17-18
Where the file is stored, and where it comes from: timm's official page on Hugging Face. The address contains a full **revision** (`aa096f03…`), a specific saved version of that page, so it always points at exactly this file even if the page is updated later.

@@ 19-20
The fingerprint and size. As for YuNet, the fingerprint was read from an independent source first — Hugging Face's own record of the file — and the download matched it.

@@ 21
The licence, recorded with its one caveat. The model card says **Apache-2.0**, which allows any use. But the weights were learned from ImageNet, whose own terms allow non-commercial research only, and whether such terms carry over to a trained model is a question courts haven't settled. It is common practice to treat such weights as usable; the register says so honestly, so that the owner can judge before any commercial launch.

@@ 22
`source` — the model's page, with its full card.

@@ 23
The end of the second entry.

@@ 24-26
The third entry: **MediaPipe Face Landmarker**. The verify page runs it for live guidance, and since the owner's tests the inference service runs it too, through OpenCV, to measure the head's angles. `use: "serving"` — needed to serve, so the fetcher downloads it by default.

@@ 27-30
Where it is stored and fetched from — Google's model storage, where the path's `float16/1` names one fixed version — its SHA-256 fingerprint and its size (3.7 MB).

@@ 31
Its licence, Apache-2.0, when it was approved and for what, and how the download was checked: Google's server publishes an MD5 fingerprint of each stored file, and the download matched it — an independent check, as for the other entries.

@@ 32
`source` — the model's documentation page.

@@ 33
The end of the third entry.

@@ 34-40
The fourth entry: **MediaPipe Hand Landmarker** — used by the inference service, through OpenCV, to look for a hand held next to the face. Its file, address (a fixed version, `float16/1`), SHA-256 fingerprint and size (7.8 MB).

@@ 41-42
Its licence (Apache-2.0), the owner's approval and why, the independent MD5 check, and its documentation page.

@@ 43
The end of the fourth entry.

@@ 44-50
The fifth and sixth entries: the two **MiniFASNet** anti-spoofing networks, from the Silent-Face-Anti-Spoofing project. The address names one exact commit (`b6d5f04…`), so the files can't change underneath us. `use: "training"` — they are fetched only with `--training`, because serving uses the ONNX versions made from them (`ml/src/dwarpal_ml/antispoof.py`), not these files.

@@ 51-52
The licence — Apache-2.0 — the owner's approval, and a note that matters for safety: these are PyTorch files, a format that can carry code, so they are only ever read as plain numbers (`weights_only`).

@@ 53
The end of the fifth entry.

@@ 54-62
The sixth entry, the second network, in the same shape: its own file, address, fingerprint and size.

@@ 63-65
The closing brackets of the entry, the list and the object.
