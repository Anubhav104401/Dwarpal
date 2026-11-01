---
fingerprint: 0c40c7d752c49107
---
The inference service's side of the **document check** (Phase 6, §5.6.2). It does three things with a photo of a document page and the selfie frames taken with it: reads the MRZ, finds the face printed on the page, and measures how alike that face and the selfie's are. It decides nothing — that is the API's job (`domain/stepup.py`).

@@ 1-2
The module's docstring: the document check's analysis — read the MRZ, find the printed face, compare it with the selfie — and the selfie itself analysed as any face attempt is.

@@ 4
The project-wide type-hint setting.

@@ 6-7
`statistics` (for the median) and `time` (to measure how long it took).

@@ 9-13
The contracts and limits; the face pipeline; from the vision library, decoding, the face detector, the MRZ reader and Tesseract, and the face matcher.

@@ 15
`DOCUMENT_SIDE` — a document photo may be up to 2400 pixels on a side, larger than a face frame's 1920: the MRZ's small print needs the detail.

@@ 18-23
**`DocumentReader`** — holds what a document check needs: the face pipeline, the face detector, the matcher and Tesseract.

@@ 25-27
**`analyze`** — first the selfie, through the ordinary face pipeline: quality, liveness and all.

@@ 28-38
Decode the document's photo, with its own size limits. If it isn't an image we're willing to decode, answer at once: no zone, and why.

@@ 39-40
Read the zone (below), and find the faces printed on the page.

@@ 41-43
Compare faces only if the page shows exactly **one** face: turn it into its embedding — the reference.

@@ 44-52
For each selfie frame that decodes and shows exactly one face, compute how alike it is to the reference.

@@ 53
The **median** of those similarities, kept within −1 to 1 (rounding can stray a hair outside): one odd frame can't swing the result either way. No usable frame: `None`.

@@ 54-61
The answer: the zone lines (names already blanked), any problem, the number of faces on the page, the similarity, the selfie's analysis, and the time taken.

@@ 63-66
**`read_zone`** — find the band; none means `mrz_not_found`.

@@ 67-70
Read it with Tesseract and make it into lines. If Tesseract couldn't run, say `ocr_unavailable` — the service's fault, not the person's.

@@ 71
Lines read: return them. Nothing long enough to be an MRZ line: `mrz_not_found`.
