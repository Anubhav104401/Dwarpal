---
fingerprint: a84d45a2748e4a75
---
The **document check's rules** (Phase 6, §5.6.2): the decision engine for the step-up, as `decision.py` is for faces. A person the face check couldn't decide shows their passport or ID card and takes a selfie; this turns the inference service's analysis into pass, fail, retry or reject.

!!! key "Key idea — the same principles, a different kind of evidence"
    The rules run in a fixed order, and only the last can pass. Missing or doubtful evidence leads to another try, then a fail — never a pass. And the liveness rule is the face check's own, reused: a document is only worth something if a live person, who looks like its photo, is holding it.

@@ 1-7
The module's docstring: pure rules in a fixed order, where only the last can say "pass" — and the plain statement of what the check does and doesn't establish. It does **not** prove a document genuine: a browser can't read a passport's chip, and nothing checks its security printing. That is why its assurance is `basic`.

@@ 9
The project-wide type-hint setting.

@@ 11-17
`dataclass` and `date`; from the domain, the outcome names and the face check's liveness rule (reused, not copied), the MRZ parser and age rule, and the policy; and the analysis contract.

@@ 19
`MAX_DOCUMENT_ATTEMPTS` — three tries at the document check.

@@ 20-22
`SAME_PERSON` — the face-match threshold, OpenCV's published 0.363 for SFace, with the honest note that it isn't yet measured for printed photos against webcams.

@@ 25-29
**`DocumentDecision`** — an outcome (pass, fail, retry or reject: never another step-up, since there is nothing stronger), its reasons, and the document as read, if one was.

@@ 32-42
**`decide_document`** — the rules. Its docstring lists their order.

@@ 43
What a doubtful step leads to: a retry while attempts remain, then a fail.

@@ 44-45
**1. An analysis at all.** None (the inference service failed): try again.

@@ 46-50
**2. A live selfie**, by the face check's own rule: missing evidence or a failed pose challenge are handled as for faces (a second failure is rejected). Signs of injection would normally step up — but this *is* the step-up, so they become a retry, and then a fail.

@@ 51-53
**3. A zone was read.** If not, the reason: no MRZ found, or the photo couldn't be decoded — or, if OCR itself was unavailable, the general `analysis_unavailable`, since that's the service's problem, not the photo's.

@@ 54-57
**4. The zone passes its check digits** (`read_ocr`, with its careful repairs). If not, try again, with the parser's code.

@@ 58-59
**5. Exactly one face on the document.** None or several: try again.

@@ 60-61
**6. A face in the selfie** to compare with.

@@ 62-63
**7. The faces match.** Below the threshold: try again — perhaps a poor photo — and fail after the last attempt. The person behind the camera must be the person on the document.

@@ 64-67
**8. The age rule**, only now: a document that hasn't expired and says the person is at least the policy's age passes (`document_over_age`, with any repairs as reasons); otherwise it fails, saying why (`document_expired`, `under_age`).
