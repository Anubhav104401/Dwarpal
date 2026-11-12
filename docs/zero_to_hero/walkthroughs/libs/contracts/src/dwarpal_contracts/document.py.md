---
fingerprint: 1c9c23f428411aa9
---
The **contract** for the step-up's document check (§5.6.2): what the inference service tells the API about a photo of a document and the selfie taken with it. Like the face contract, it is shared by both services, so they can never disagree about its shape.

@@ 1-6
The module's docstring: these are the messages about a document check, and — as with faces — none of them can hold an image. The MRZ lines are the only text read from a document, and their names line is blanked before they leave the inference service. Since Part 7 it says the same of an Aadhaar Secure QR: only the date of birth and the name of the key that signed it are passed on.

@@ 8
The project-wide type-hint setting.

@@ 10-14
`Annotated` and Pydantic's `Field`, for limits on values; and from the face contracts, the strict base class `Contract` (unknown fields refused, objects frozen) and `FaceAnalysis`, reused for the selfie.

@@ 16
`MAX_DOCUMENT_BYTES` — the largest document photo accepted: 1 MB, twice a face frame's limit, because the MRZ's small print needs more detail. Both services and the API's size check import it from here.

@@ 19-21
**`AadhaarReading`** — what the inference service passes on from an Aadhaar Secure QR (Part 7). Its docstring states the rule that matters: the name, address and reference number in the code never leave that service. This class is how the rule is kept — it has **no field** that could carry them, and `Contract` forbids extra fields.

@@ 23
`signed_by` — the file name of the UIDAI certificate whose key made the code's signature, or `None` if no key on the ring did. `None` here is what stops a home-made code (§7.5).

@@ 24
`born` — the date of birth as text, `"1990-01-01"`, or just `"1990"` when the code holds only a year; `None` if the code couldn't be read. Text, not a date: turning it into a real date, and refusing impossible ones, is the API's job.

@@ 25
`problem` — why there is no date. Today the only value is `aadhaar_qr_unreadable`.

@@ 28
**`DocumentAnalysis`** — the inference service's answer about a document check.

@@ 29
`zone` — the MRZ lines as read, with the names line blanked; empty when no MRZ was found or OCR failed.

@@ 30
`zone_problem` — why there are no lines: the photo couldn't be decoded, no MRZ band was found, or OCR is unavailable.

@@ 31-33
Since Part 7, `aadhaar`: set when the picture showed a Secure QR in place of an MRZ, else `None` (the default, so an older inference service that doesn't send it is still understood). When it is set, "the document's photo" in the two fields below means the photo **inside the code**.

@@ 34
`document_faces` — how many faces were found on the document's photo; exactly one is right.

@@ 35-37
`similarity` — how alike the document's face and the selfie's are, as a cosine similarity between −1 and 1 (`match.py`): the median over the selfie frames that show one face. `None` when either face is missing.

@@ 38
`face` — the selfie, analysed exactly as a face attempt is, liveness included: a document check must be done by a live person.

@@ 39
`duration_ms` — how long the whole analysis took.
