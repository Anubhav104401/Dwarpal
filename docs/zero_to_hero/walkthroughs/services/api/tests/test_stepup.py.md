---
fingerprint: 0d279c7caca46546
---
Tests for the **document check's rules** (§5.6.2, `domain/stepup.py`). Like the face decision's tests, they build analyses by hand — no camera, no OCR, no database — and check that each kind of evidence leads where it must: good evidence to a pass or a fail by age, doubtful evidence to a retry and then a fail, never a pass.

@@ 1
The module's docstring: the document check's rules, with good, missing and doubtful evidence.

@@ 3
The project-wide type-hint setting.

@@ 5-7
`date`, and pytest.

@@ 9-13
The code under test (the outcomes, the check-digit function, the policies, and the step-up's rules with their limits) and the contracts, to build analyses by hand.

@@ 15-17
A fixed "today" (1 November 2026), the UK's 18+ policy, and a liveness result that passed.

@@ 20-26
**`zone`** — a passport's zone as the inference service returns it: the names line already blanked, and an empty personal number. Every check digit is computed, so it's valid for any dates given.

@@ 29-42
**`selfie`** — a face analysis with four usable frames and the given liveness result. (A document check doesn't use the face's age, so there is none.)

@@ 45-59
**`analysis`** — a document analysis, by default a good one: a valid zone for someone born on 1 January 1990, one face on the document, a similarity of 0.7, and a live selfie. Each test changes one thing.

@@ 62-66
**Test — an adult whose face matches a valid document passes**, and of the document only the year and month of birth come out.

@@ 69-75
**Test — a minor (born 2014) or an expired document fails**, saying which.

@@ 78-91
Nine kinds of doubtful evidence, with the reason each must give:
- no analysis at all;
- no MRZ found, or OCR unavailable;
- a birth date its check digit refutes;
- no face on the document, or two;
- no face in the selfie;
- faces just below the match threshold;
- no liveness evidence.

@@ 92-98
**Test — doubtful evidence is retried, then fails, and never passes**: a retry on the first attempt, and a fail on the last, for the same reason.

@@ 101-105
**Test — a failed pose challenge is retried once, then rejected**, as at the face check.

@@ 108-113
**Test — doubtful liveness can't step up again.** At the face check, signs of injection (here a virtual camera) lead to the step-up; inside it, they lead to a retry, and after the last attempt a fail.
