# Phase 6 report — step-up verifiers

**Dates:** from 26 Oct 2026 · **Roadmap:** [05_roadmap.md](../design/05_roadmap.md) · **Design:** [03_implementation_design.md §9](../design/03_implementation_design.md) · **Status:** 🟡 in progress — the MRZ parser and age rule are built and tested; everything needing a photo, OCR, a face-match model or UIDAI material waits for approved downloads ([pending decisions](pending-decisions.md)).

**Exit (from the roadmap):** parsers pass specimen and test vectors; end-to-end step-up flows pass with fake-camera inputs.

## What is built

| Area | Delivered |
| :-- | :-- |
| MRZ parser (`domain/mrz.py`) | TD1, TD2, TD3 layouts; ICAO 9303 check digits (7-3-1) on number, birth date, expiry, personal number and composite; TD1 long document numbers continued in the optional field; OCR-confusion repair only when exactly one repair makes a failing check pass, reported per field; two-digit years resolved against today (birth: latest century not in the future; expiry: this century unless > 50 years ahead) |
| Age rule | expired → fail; age ≥ N → pass, else fail; whole years from the birthday (29 February → 1 March); repairs listed as reasons |
| Privacy | only type, issuer, dates and repairs leave the parser; of the birth date, only year and month is kept |
| Book | §5.6, §5.6.1; two walkthroughs |

## What was measured

| Check | Result |
| :-- | :-- |
| ICAO Doc 9303 specimens (Utopia, TD3/TD2/TD1) | all read; dates 1974-08-12 / 2012-04-15; no repairs |
| Hypothesis: 100 generated valid passports | all read back exactly |
| Hypothesis: single-digit changes in the birth date | all caught |
| Tampering, OCR repair, broken zones, age arithmetic | as expected (13 tests) |

## Open items

1. **Reading the MRZ from a photo** (band detection, perspective, OCR with an MRZ model) — needs Tesseract and a model (download D6).
2. **Face match** document ↔ selfie — needs a licence-checked model (D7).
3. **Aadhaar Secure QR** — needs UIDAI's specification and certificate from official sources (D8) and the owner's own QR (O3).
4. **The step-up flow** in the API and verify page (capture UI, endpoints, assurance labels) — after 1 and 2.
