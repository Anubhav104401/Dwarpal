---
fingerprint: 645a61dc80498976
---
The inference service's side of the **document check** (Phase 6, §5.6.2). It does three things with a photo of a document page and the selfie frames taken with it: reads the MRZ, finds the face printed on the page, and measures how alike that face and the selfie's are. It decides nothing — that is the API's job (`domain/stepup.py`).

@@ 1-5
The module's docstring: the document check's analysis — read the MRZ, find the printed face, compare it with the selfie — and the selfie itself analysed as any face attempt is. Since Part 7 a second paragraph: a picture of an Aadhaar Secure QR is read too — the date of birth and the photo come out of the code, and UIDAI's signature on it is checked.

@@ 7
The project-wide type-hint setting.

@@ 9-10
`statistics` (for the median) and `time` (to measure how long it took).

@@ 12-21
The contracts and limits; the face pipeline; from the vision library, decoding, the face detector, the MRZ reader and Tesseract, and the face matcher. Since Part 7 also OpenCV and NumPy (to enlarge the code's small photo), the `AadhaarReading` contract, the key ring, and the vision library's Secure QR reader.

@@ 23
`DOCUMENT_SIDE` — a document photo may be up to 2400 pixels on a side, larger than a face frame's 1920: the MRZ's small print needs the detail.

@@ 24
`QR_PHOTO_SIDE` — the photo inside a Secure QR is tiny (ours measure 160 by 200 pixels). It is enlarged until its shorter side is 320 before a face is looked for in it: measured on the specimen, the detector missed faces at the original size that it found once enlarged.

@@ 27-40
**`DocumentReader`** — holds what a document check needs: the face pipeline, the face detector, the matcher and Tesseract, and — since Part 7 — the ring of UIDAI's public keys. Without a ring (`None`), Secure QR codes aren't looked for at all.

@@ 42-44
**`analyze`** — first the selfie, through the ordinary face pipeline: quality, liveness and all.

@@ 45-55
Decode the document's photo, with its own size limits. If it isn't an image we're willing to decode, answer at once: no zone, and why.

@@ 56-63
First, is the picture an **Aadhaar Secure QR** (`read_aadhaar`, below)? It is tried before the MRZ because a QR's dense pattern can look like lines of print to the MRZ finder. If it isn't one, read the zone as before, and the "portrait" to find a face in is the page itself. If it is one, there is no zone, and the portrait is the photo from inside the code (or `None`, if the code has none). Then find the faces in that portrait.

@@ 64-66
Compare faces only if the page shows exactly **one** face: turn it into its embedding — the reference. Since Part 7 "the page" may be the photo from inside a Secure QR.

@@ 67-75
For each selfie frame that decodes and shows exactly one face, compute how alike it is to the reference.

@@ 76
The **median** of those similarities, kept within −1 to 1 (rounding can stray a hair outside): one odd frame can't swing the result either way. No usable frame: `None`.

@@ 77-85
The answer: the zone lines (names already blanked), any problem, the number of faces on the page, the similarity, the selfie's analysis, and the time taken. Since Part 7 also what was read from an Aadhaar Secure QR, if the picture was one.

@@ 87-90
**`read_zone`** — find the band; none means `mrz_not_found`.

@@ 91-94
Read it with Tesseract and make it into lines. If Tesseract couldn't run, say `ocr_unavailable` — the service's fault, not the person's.

@@ 95
Lines read: return them. Nothing long enough to be an MRZ line: `mrz_not_found`.

@@ 97-99
**`read_aadhaar`** (Part 7) — what a Secure QR in the picture says, and the photo inside it. The docstring's second sentence is the privacy rule in action: the code's bytes — name, address and all — live only inside this function, and are dropped as it returns.

@@ 100-104
No key ring: Secure QR codes aren't read. No such code in the picture: say so, with two `None`s, and the caller goes on to the MRZ.

@@ 105-108
Turn the code's number into bytes and split them into parts. If that fails, the picture *was* a QR full of digits but not a readable Secure QR: answer with the reason, and no photo.

@@ 109
Ask the key ring who signed it, and note the date of birth. Nothing here decides: an unsigned code is passed on as `signed_by=None`, for the API's rules to refuse.

@@ 110-112
Decode the photo. A code without one (or with one that can't be decoded) still gives its reading; the API will then say `document_face_not_found`.

@@ 113-116
Enlarge a small photo so its shorter side is `QR_PHOTO_SIDE`, smoothly (`INTER_CUBIC`), and return the reading with it.
