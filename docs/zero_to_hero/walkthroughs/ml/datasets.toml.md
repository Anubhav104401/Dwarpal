---
fingerprint: 7fe203fd8cda416d
---
The **licence register**: every dataset Dwarpal may learn from, where it comes from, who made it, how to cite it, and — above all — what its licence allows (ADR-0018). An AI model carries the terms of the data it learned from: a model trained on "non-commercial research only" photos may itself only be used for non-commercial research. Writing those terms down, per dataset, is how the project keeps track.

Two safety rules are built into the file's shape:

- a dataset is downloaded only when the project owner has **approved** it (`approved = true`, with the date);
- every file is **pinned** by its SHA-256 fingerprint (§X.5), so a download that has been tampered with, or quietly changed, is thrown away.

The design planned this register as YAML; it is written in **TOML** instead, because Python reads TOML with no extra library and TOML allows comments (§5.0.2).

@@ 1-3
The comment at the top: what the file is, and its two rules.

@@ 5
`[[dataset]]` — double square brackets start one entry in a **list of tables**: each `[[dataset]]` adds another dataset.

@@ 6-9
**FairFace**: its short name (used in commands and folders), title, home page, and licence — **CC BY 4.0**, a Creative Commons licence that allows any use, including commercial, provided the creators are credited.

@@ 10
`permitted_use` — the licence's meaning in plain words.

@@ 11
`citation` — how to credit the creators, as the licence requires.

@@ 12
`age_labels = "ranges"` — FairFace gives an age *band* for each face ("10-19"), not an exact age. That limits what it can be used for (§5.2.1).

@@ 13
`age_source` — where the labels came from (added with UTKFace): FairFace's age bands are people's estimates from looking at each photo. Every result measured with a dataset carries this note.

@@ 14-15
`subject = "central"` — how to find the labelled person in a photo: FairFace centred every image on them, so preparation takes the face nearest the middle (`prepare.py`).

@@ 16-17
Approved by the project owner on 16 October 2026. TOML understands dates written like this as real dates.

@@ 19
`[[dataset.files]]` — one file belonging to the dataset above.

@@ 20-24
The face images, training and validation sets together: a comment saying why this version, then the file's name, the official download address (Google Drive, linked from the dataset's home page), its SHA-256 fingerprint, and its size in bytes (2.1 GB). The fingerprint was recorded when the owner-approved download was first made.

FairFace comes in two versions: a tight crop (25 % padding around each face) and a wide one (125 %). The project first used the tight one — until face preparation showed that our alignment needs the hair and surroundings the tight crops cut off (§5.2.3). The owner approved the wide version, and it replaced the tight one here.

@@ 26-30
The training labels: one row per image — file name, age band, sex, and race group.

@@ 32-36
The validation labels, in the same form.

@@ 38-69
**UTKFace** (approved on 17 October 2026, Phase 2): over 24,000 photos with **exact ages** — exactly what teenage thresholds need — under a licence for **non-commercial research only**, accepted under the project's research-only first version.

- The **in-the-wild** photos, not the cropped ones: alignment needs the surroundings (the lesson of FairFace's tight crops, §5.2.3).
- `age_source` — the ages are exact but *estimated*: the DEX age estimator proposed each one and a person checked it. They are not ages from documents, and every calibration result says so.
- `subject = "only"` — a photo may show other people too, and the labelled person isn't necessarily in the middle. So preparation takes the clearest face, and sets aside any photo with a second clear face rather than guess whose age the label is.
- Three pinned files, 1.39 GB together, fingerprinted on their first, owner-approved download.

@@ 71-79
**APPA-REAL**: real *and* apparent ages ("how old people think this person looks"). Its page asks only for a citation and states no licence, which is recorded honestly as "pending clarification". Not approved.

@@ 81-89
**IMDB-Clean**: a cleaned set of age labels for the large IMDB-WIKI collection of celebrity photos. Research use; not approved.
