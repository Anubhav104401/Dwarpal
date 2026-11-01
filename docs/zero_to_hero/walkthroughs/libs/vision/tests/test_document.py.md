---
fingerprint: f55c75d05a8af539
---
Tests for **reading documents** (Phase 6, §5.6.2): the MRZ band finder, Tesseract, and the face matcher, on specimen passports drawn for the purpose (`specimen.py`). No real document is ever used.

@@ 1-5
The module's docstring: what is tested, that the documents are always specimens, and that the tests needing Tesseract find it installed or in the OCR container, or are skipped.

@@ 7
The project-wide type-hint setting.

@@ 9-15
`json` and `os` (to read a configured Tesseract command), `Path`, OpenCV, NumPy and pytest.

@@ 17-20
The code under test: decoding and the face detector; the MRZ reader; the face matcher and its threshold; and the specimen maker.

@@ 22-24
The public-domain test portrait, the folder of third-party models, and the portrait as pixels.

@@ 27-33
**`tesseract_command`** — how to run Tesseract here: as configured for the inference service (a JSON list in its environment variable), else installed, else in the OCR container. The first that answers, or `None`.

@@ 36-41
**`ocr`** — a pytest *fixture*: tests that ask for it get a working Tesseract, or are skipped with the reason. `scope="module"` looks it up once for the whole file.

@@ 44-45
**`photo`** — a photographed specimen passport, decoded as the inference service would decode it, for the given birth date and random seed.

@@ 48-52
**Test — the specimen's zone carries ICAO's check digits**: given the dates of ICAO's own specimen, it is exactly the zone ICAO prints. So the drawing starts from a valid zone.

@@ 55-60
**Test — OCR text becomes MRZ lines with the names blanked**: spaces and short stray lines dropped, the passport's names line reduced to `P<UTO` and fillers, and a TD1 card's third line all fillers.

@@ 63-68
**Test — the band is found on a photographed page, and not on a face**: on the tilted, blurred specimen, a band more than five times as wide as tall; on the portrait alone, nothing.

@@ 71-79
**Test — Tesseract reads the data line** of three different photographs of the specimen: the birth date and expiry are both there. (Whether the whole line is perfect is the parser's business: it repairs a character more or less.)

@@ 82-86
**Test — a Tesseract that can't run is reported, not guessed around**: a program that doesn't exist raises `TesseractError`.

@@ 89-96
**Test — the same face matches itself on a printed page**: the face on the photographed specimen and the original portrait score at or above the threshold.

@@ 97-102
And the same picture **scrambled** — cut into 64 blocks and shuffled, so it has the same colours and textures but no face's arrangement — scores below it. (No second person's face is used: the tests keep to the one public-domain portrait.)
