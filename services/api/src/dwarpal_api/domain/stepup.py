"""The step-up check with an ID document (Phase 6, MRZ): pure rules, checked in a fixed order, that turn the document's
analysis into an outcome. As with faces, only the last rule can say "pass", and doubt never does.

The assurance is `basic`: a browser can't read a passport's chip, and nothing here tests a document's security printing.
What the check does establish is that a live person, whose face matches the document's photo, holds a document whose
machine-readable zone is internally consistent and says they are old enough.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from dwarpal_api.domain.decision import Outcome, liveness_problem
from dwarpal_api.domain.mrz import MrzDocument, MrzError, age_outcome, read_ocr
from dwarpal_api.domain.policy import Policy
from dwarpal_contracts import DocumentAnalysis

MAX_DOCUMENT_ATTEMPTS = 3
# SFace's cosine similarity at which OpenCV calls two faces the same person (99.4 % on LFW). A document's printed photo
# against a webcam is harder than LFW's pairs, and this threshold isn't yet measured for that (Phase 6 report).
SAME_PERSON = 0.363


@dataclass(frozen=True)
class DocumentDecision:
    outcome: Outcome  # pass, fail, retry or reject: never another step-up
    reasons: tuple[str, ...]
    document: MrzDocument | None = None


def decide_document(
    policy: Policy,
    analysis: DocumentAnalysis | None,
    attempt_index: int,
    today: date,
    liveness_failures: int = 0,
    livemode: bool = False,
) -> DocumentDecision:
    """The checks, in order: an analysis at all; a live selfie; a readable zone that passes its check digits; one face
    on the document, and the selfie's face matching it; then the age rule (not expired, old enough). A doubtful step
    is retried while attempts remain, and then fails."""
    try_again = Outcome.FAIL if attempt_index + 1 >= MAX_DOCUMENT_ATTEMPTS else Outcome.RETRY
    if analysis is None:
        return DocumentDecision(try_again, ("analysis_unavailable",))
    live = liveness_problem(analysis.face, liveness_failures, try_again, livemode)
    if live is not None:
        # Uncertain liveness can't step up again: there is nothing stronger to send the person to.
        outcome = try_again if live.outcome == Outcome.STEP_UP else live.outcome
        return DocumentDecision(outcome, live.reasons)
    if not analysis.zone:
        problem = analysis.zone_problem or "mrz_not_found"
        return DocumentDecision(try_again, ("analysis_unavailable" if problem == "ocr_unavailable" else problem,))
    try:
        document = read_ocr(analysis.zone, today)
    except MrzError as error:
        return DocumentDecision(try_again, (error.code,))
    if analysis.document_faces != 1:
        return DocumentDecision(try_again, ("document_face_not_found",), document)
    if analysis.similarity is None:
        return DocumentDecision(try_again, ("face_not_found",), document)
    if analysis.similarity < SAME_PERSON:
        return DocumentDecision(try_again, ("face_mismatch",), document)
    verdict, reasons = age_outcome(document, policy.min_age, today)
    if verdict == "pass":
        return DocumentDecision(Outcome.PASS, ("document_over_age", *reasons), document)
    return DocumentDecision(Outcome.FAIL, tuple(reasons), document)
