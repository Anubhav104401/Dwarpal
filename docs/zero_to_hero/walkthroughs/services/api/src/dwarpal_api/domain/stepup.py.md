---
fingerprint: 7bf099602239d7c0
---
The **document check's rules** (Phase 6, §5.6.2): the decision engine for the step-up, as `decision.py` is for faces. A person the face check couldn't decide shows their passport or ID card and takes a selfie; this turns the inference service's analysis into pass, fail, retry or reject.

!!! key "Key idea — the same principles, a different kind of evidence"
    The rules run in a fixed order, and only the last can pass. Missing or doubtful evidence leads to another try, then a fail — never a pass. And the liveness rule is the face check's own, reused: a document is only worth something if a live person, who looks like its photo, is holding it.

@@ 1-10
The module's docstring: pure rules in a fixed order, where only the last can say "pass" — and the plain statement of what the check does and doesn't establish. It does **not** prove a document genuine: a browser can't read a passport's chip, and nothing checks its security printing. That is why its assurance is `basic`. Since Part 7 a last paragraph: an Aadhaar Secure QR is a second kind of document, in test sessions only — its date of birth isn't read off print but taken from data UIDAI signed, and the face is matched against the photo inside the code.

@@ 12
The project-wide type-hint setting.

@@ 14-20
`dataclass` and `date`; from the domain, the outcome names and the face check's liveness rule (reused, not copied), the MRZ parser and age rule, and the policy; and the analysis contract. Since Part 7 also `age_on` (whole years between two dates) and the `AadhaarReading` contract.

@@ 22
`MAX_DOCUMENT_ATTEMPTS` — three tries at the document check.

@@ 23-25
`SAME_PERSON` — the face-match threshold, OpenCV's published 0.363 for SFace, with the honest note that it isn't yet measured for printed photos against webcams.

@@ 28-32
**`AadhaarDocument`** (Part 7) — an Aadhaar Secure QR as the rules see it: a date of birth, whether the code gave only the year (then the date is that year's **last day**, the youngest the holder can be), and which UIDAI certificate's key signed it. There is nothing else to hold: no name, number or address ever reached the API.

@@ 35-40
**`DocumentDecision`** — an outcome (pass, fail, retry or reject: never another step-up, since there is nothing stronger), its reasons, and the document as read, if one was: `document` for a passport or ID card, `aadhaar` for a Secure QR. At most one of the two is set.

@@ 43-54
**`decide_document`** — the rules. Its docstring lists their order. Since Part 7 the list has one rule more near the top (no Aadhaar code in a live session), and says that an Aadhaar code in a test session takes its own path after the selfie.

@@ 55
What a doubtful step leads to: a retry while attempts remain, then a fail.

@@ 56-57
**1. An analysis at all.** None (the inference service failed): try again.

@@ 58-60
**No Aadhaar in a live session.** This demo is not registered with UIDAI or cleared for real use (§7.9), so a live check never accepts one. It is said before the liveness rule on purpose: whatever else was wrong with the attempt, the person should be told plainly to use a passport or ID card.

@@ 61-65
**2. A live selfie**, by the face check's own rule: missing evidence or a failed pose challenge are handled as for faces (a second failure is rejected). Signs of injection would normally step up — but this *is* the step-up, so they become a retry, and then a fail.

@@ 66-67
The selfie is live. If the picture was an Aadhaar Secure QR, its own rules take over from here (`decide_aadhaar`, below); the MRZ rules that follow are for passports and ID cards.

@@ 68-70
**3. A zone was read.** If not, the reason: no MRZ found, or the photo couldn't be decoded — or, if OCR itself was unavailable, the general `analysis_unavailable`, since that's the service's problem, not the photo's.

@@ 71-74
**4. The zone passes its check digits** (`read_ocr`, with its careful repairs). If not, try again, with the parser's code.

@@ 75-76
**5. Exactly one face on the document.** None or several: try again.

@@ 77-78
**6. A face in the selfie** to compare with.

@@ 79-80
**7. The faces match.** Below the threshold: try again — perhaps a poor photo — and fail after the last attempt. The person behind the camera must be the person on the document.

@@ 81-84
**8. The age rule**, only now: a document that hasn't expired and says the person is at least the policy's age passes (`document_over_age`, with any repairs as reasons); otherwise it fails, saying why (`document_expired`, `under_age`).

@@ 87-89
**`aadhaar_birth`** — the code's date-of-birth text as a real date, and whether it was only a year. Its docstring gives the one judgement call: a year alone counts as its **last day**, so nobody is taken for older than they may be.

@@ 90-96
Four characters are a year: its 31 December. Anything else must be a full date in `YYYY-MM-DD` form (`date.fromisoformat`). `ValueError` is what Python raises for "30 February" or for text that isn't a date at all: then there is no date.

@@ 97-99
Refuse dates that can't be a living person's: before 1900, in a later year than this one, or — for a full date — after today. (A year-only birth in *this* year gives 31 December, which is after today; that is allowed, and makes the person 0 years old, which is the careful side.)

@@ 102-107
**`decide_aadhaar`** — the rules for an Aadhaar Secure QR, once the selfie is known to be live. The docstring lists their order, and notes what an Aadhaar code doesn't have: an expiry date. A passport's expiry matters because a passport stops being valid; what UIDAI signed about a date of birth stays true.

@@ 108-109
No date of birth came out of the code: try again, with the inference service's reason for it.

@@ 110-111
**The signature.** No key on UIDAI's ring made it: the code is home-made, or altered, or not UIDAI's. This one line is what makes the whole check worth anything — without it, anyone could draw a code that says "born in 1960".

@@ 112-115
The date must be one that can be (`aadhaar_birth`). From here on the decision carries what was read, so it can be recorded.

@@ 116-121
The same three face rules as for a passport, with the same reason codes — here about the photo **inside the code**: exactly one face in it; a face in the selfie; and the two alike enough to be the same person (`SAME_PERSON`). This is what ties the code to the person holding it: someone else's Aadhaar doesn't have their face in it.

@@ 122-124
The only line that can say **pass**: old enough on today's date. The reason `aadhaar_qr` goes with either answer; it is how the session's token later knows which kind of document decided (`methods_of`). Under age: **fail**, at once — a signed date of birth leaves no doubt to retry.
