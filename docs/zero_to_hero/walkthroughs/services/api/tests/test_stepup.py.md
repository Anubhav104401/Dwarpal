---
fingerprint: 129ff21e439becbf
---
Tests for the **document check's rules** (§5.6.2, `domain/stepup.py`). Like the face decision's tests, they build analyses by hand — no camera, no OCR, no database — and check that each kind of evidence leads where it must: good evidence to a pass or a fail by age, doubtful evidence to a retry and then a fail, never a pass.

@@ 1
The module's docstring: the document check's rules, with good, missing and doubtful evidence.

@@ 3
The project-wide type-hint setting.

@@ 5-7
`date`, and pytest.

@@ 9-21
The code under test (the outcomes, the check-digit function, the policies, and the step-up's rules with their limits) and the contracts, to build analyses by hand. Since Part 7 also `AadhaarReading`, so the list is written one name per line.

@@ 23-25
A fixed "today" (1 November 2026), the UK's 18+ policy, and a liveness result that passed.

@@ 28-34
**`zone`** — a passport's zone as the inference service returns it: the names line already blanked, and an empty personal number. Every check digit is computed, so it's valid for any dates given.

@@ 37-50
**`selfie`** — a face analysis with four usable frames and the given liveness result. (A document check doesn't use the face's age, so there is none.)

@@ 53-69
**`analysis`** — a document analysis, by default a good one: a valid zone for someone born on 1 January 1990, one face on the document, a similarity of 0.7, and a live selfie. Each test changes one thing. Since Part 7 it can also carry what was read from an Aadhaar Secure QR (`aadhaar`).

@@ 72-76
**Test — an adult whose face matches a valid document passes**, and of the document only the year and month of birth come out.

@@ 79-85
**Test — a minor (born 2014) or an expired document fails**, saying which.

@@ 88-101
Nine kinds of doubtful evidence, with the reason each must give:
- no analysis at all;
- no MRZ found, or OCR unavailable;
- a birth date its check digit refutes;
- no face on the document, or two;
- no face in the selfie;
- faces just below the match threshold;
- no liveness evidence.

@@ 102-108
**Test — doubtful evidence is retried, then fails, and never passes**: a retry on the first attempt, and a fail on the last, for the same reason.

@@ 111-115
**Test — a failed pose challenge is retried once, then rejected**, as at the face check.

@@ 118-123
**Test — doubtful liveness can't step up again.** At the face check, signs of injection (here a virtual camera) lead to the step-up; inside it, they lead to a retry, and after the last attempt a fail.

@@ 126-130
**`secure_qr`** (Part 7) — what the inference service passes on from an Aadhaar Secure QR; by default a good one: born on 1 January 1990, signed with UIDAI's newest key. Without a date, it carries the reason.

@@ 133-138
**The good case passes**: signed, an adult, the face matching. The reasons are `document_over_age` and `aadhaar_qr`, and the decision carries the date read — as an Aadhaar document, not an MRZ one.

@@ 141-143
**A signed code of a child fails at once**: no retry, because nothing about a signed date is in doubt.

@@ 146-154
**A year alone counts as its last day.** "Today" in these tests is 1 November 2026. Someone whose code says only `2008` may have been born on 31 December 2008 and still be 17: fail. `2007` is 18 whichever day it was: pass.

@@ 157-175
**Every doubt is retried, and none passes** (Part 7): an unsigned code; no date; a date that doesn't exist (30 February); a date in the future; a year before 1900; no face in the code's photo; no face in the selfie; faces that don't match; no liveness evidence. Each gives its reason on the first attempt, and **fail** on the last.

@@ 178-180
**An unsigned code fails however old it claims to be** — the forgery test: a home-made code that says 1950.

@@ 183-189
**A live session doesn't take a Secure QR**: `aadhaar_test_only`, said alone and first, and after the last attempt, fail.
