---
fingerprint: acdbb62ada17aa6b
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

@@ 23-25
The closing brackets of the entry, the list and the object.
