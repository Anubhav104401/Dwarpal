---
fingerprint: 1461cee9541ca903
---
The **contract** for the step-up's document check (§5.6.2): what the inference service tells the API about a photo of a document and the selfie taken with it. Like the face contract, it is shared by both services, so they can never disagree about its shape.

@@ 1-5
The module's docstring: these are the messages about a document check, and — as with faces — none of them can hold an image. The MRZ lines are the only text read from a document, and their names line is blanked before they leave the inference service.

@@ 7
The project-wide type-hint setting.

@@ 9-13
`Annotated` and Pydantic's `Field`, for limits on values; and from the face contracts, the strict base class `Contract` (unknown fields refused, objects frozen) and `FaceAnalysis`, reused for the selfie.

@@ 15
`MAX_DOCUMENT_BYTES` — the largest document photo accepted: 1 MB, twice a face frame's limit, because the MRZ's small print needs more detail. Both services and the API's size check import it from here.

@@ 18
**`DocumentAnalysis`** — the inference service's answer about a document check.

@@ 19
`zone` — the MRZ lines as read, with the names line blanked; empty when no MRZ was found or OCR failed.

@@ 20
`zone_problem` — why there are no lines: the photo couldn't be decoded, no MRZ band was found, or OCR is unavailable.

@@ 21
`document_faces` — how many faces were found on the document's photo; exactly one is right.

@@ 22-24
`similarity` — how alike the document's face and the selfie's are, as a cosine similarity between −1 and 1 (`match.py`): the median over the selfie frames that show one face. `None` when either face is missing.

@@ 25
`face` — the selfie, analysed exactly as a face attempt is, liveness included: a document check must be done by a live person.

@@ 26
`duration_ms` — how long the whole analysis took.
