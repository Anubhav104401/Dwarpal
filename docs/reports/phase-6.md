# Phase 6 report — step-up verifiers

**Dates:** from 26 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Design:** [03_implementation_design.md §9](../design/03_implementation_design.md) · **Status:** 🟡 in progress — the MRZ route works end to end in the API (1 Nov): reading from a photo, face match, rules, token; and on the verify page (§5.6.3), with a browser test from step-up to token; Aadhaar is deferred (D8/O7) ([pending decisions](pending-decisions.md)).

**Exit (from the roadmap):** parsers pass specimen and test vectors; end-to-end step-up flows pass with fake-camera inputs.

## What is built

| Area | Delivered |
| :-- | :-- |
| MRZ parser (`domain/mrz.py`) | TD1, TD2, TD3 layouts; ICAO 9303 check digits (7-3-1) on number, birth date, expiry, personal number and composite; TD1 long document numbers continued in the optional field; OCR-confusion repair only when exactly one repair makes a failing check pass, reported per field; two-digit years resolved against today (birth: latest century not in the future; expiry: this century unless > 50 years ahead) |
| Age rule | expired → fail; age ≥ N → pass, else fail; whole years from the birthday (29 February → 1 March); repairs listed as reasons |
| Privacy | only type, issuer, dates and repairs leave the parser; of the birth date, only year and month is kept |
| Book | §5.6, §5.6.1, §5.6.2; eleven walkthroughs |
| Reading from a photo (1 Nov) | `dwarpal_vision.document`: MRZ band by black-hat → Sobel → closing → Otsu → contour shape; levelled by its angle; Tesseract 5.3 (Debian, in the `ocr` container: no network, read-only, no privileges) with the MRZ alphabet only and no dictionary; names line blanked before the text leaves the service |
| Repairs (1 Nov) | `read_ocr`: fewest changes first (0, 1, 2 characters dropped or 1 added; an empty optional field tried), accepted only when exactly one document passes every check digit; repairs reported (`line_length`, `optional_fields_read_as_empty`); `T`↔`7` added to the confusions |
| Face match (1 Nov) | SFace int8 (D7b) on YuNet's landmarks; cosine similarity, median over the selfie frames; OpenCV's threshold 0.363 |
| API (1 Nov) | `POST /v1/flow/sessions/{id}/stepup/mrz` (document photo ≤ 1 MB + selfie frames of a new challenge); `domain/stepup.py` rules: analysis → liveness (the face check's rule) → zone → one printed face → match → age; 3 attempts; token `methods` = face_estimation, document_mrz, face_match, assurance `basic`; kept: type, issuer, birth year-month, expiry, repairs, similarity |
| Specimens | `dwarpal_vision.specimen`: ICAO's Utopia passport with any dates, photographed (perspective, blur, noise) — no real documents |

## What was measured

| Check | Result |
| :-- | :-- |
| ICAO Doc 9303 specimens (Utopia, TD3/TD2/TD1) | all read; dates 1974-08-12 / 2012-04-15; no repairs |
| Hypothesis: 100 generated valid passports | all read back exactly |
| Hypothesis: single-digit changes in the birth date | all caught |
| Tampering, OCR repair, broken zones, age arithmetic | as expected (13 tests) |
| 40 photographed specimen passports, random dates (1 Nov) | **31 right, 0 wrong, 9 refused**; 11 of the 31 needed a repair; median 0.43 s per reading (Tesseract through `docker exec`) |
| Specimen TD2 cards (10) / TD1 cards (10) | 9 / 1 read; TD1 lines lose their ends in Tesseract |
| Dropped character anywhere (Hypothesis) | the reading is always the true dates, or none |
| End to end through the API, real OCR | adult's specimen passes, 12-year-old's fails; no name or document number kept |

## Open items

1. ~~The verify page's screens~~ — **done 1 Nov** (§5.6.3): consent before capture, the photo prepared in the browser, the selfie with the face check's challenge; a browser test drives it from step-up to token. ~~Left: a live document camera~~ — **done 9 Nov** (D43, §5.6.5): on a computer the webcam comes first, inside a passport-shaped guide with a box for the machine-readable lines, and the photo is looked at before it is used; the file chooser stays beside it, and phones are unchanged. Whether a typical laptop camera reads the lines reliably is not measured yet (the browser tests' fake camera shows a portrait).
2. **ID cards (TD1)** read poorly with Tesseract's English model; an OCR-B model would have to be trained (no licensed one exists, D6c).
3. **Real-world accuracy** is unmeasured: the specimens are drawn in an ordinary font and photographed by a program. The face-match threshold (OpenCV's 0.363) isn't measured for printed photos against webcams.
4. **SFace's training data** was collected without consent (accepted, D7b; recorded in `models/third_party.json`).
5. **Aadhaar Secure QR** — deferred by the owner (1 Nov) until UIDAI's specification and certificate are found and OVSE registration is clear (D8, O7).
6. ~~Production image~~ — **done in Phase 8** (§5.8.2): the inference service's image installs Tesseract and its English data; the `ocr` container is for development only.
