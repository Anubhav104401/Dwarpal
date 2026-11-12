"""The step-up check with an ID document (Phase 6, MRZ): pure rules, checked in a fixed order, that turn the document's
analysis into an outcome. As with faces, only the last rule can say "pass", and doubt never does.

The assurance is `basic`: a browser can't read a passport's chip, and nothing here tests a document's security printing.
What the check does establish is that a live person, whose face matches the document's photo, holds a document whose
machine-readable zone is internally consistent and says they are old enough.

An Aadhaar Secure QR code is a second kind of document (Part 7), in test sessions only. There the date of birth is not
read off print but taken from data that UIDAI signed, and the face is matched against the photo inside the code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from dwarpal_api.domain.decision import Outcome, liveness_problem
from dwarpal_api.domain.mrz import MrzDocument, MrzError, age_on, age_outcome, read_ocr
from dwarpal_api.domain.policy import Policy
from dwarpal_contracts import AadhaarReading, DocumentAnalysis

MAX_DOCUMENT_ATTEMPTS = 3
# SFace's cosine similarity at which OpenCV calls two faces the same person (99.4 % on LFW). A document's printed photo
# against a webcam is harder than LFW's pairs, and this threshold isn't yet measured for that (Phase 6 report).
SAME_PERSON = 0.363


@dataclass(frozen=True)
class AadhaarDocument:
    born: date  # when the code gives only a year, its last day: the youngest the holder can be
    year_only: bool
    signed_by: str  # the UIDAI certificate whose key signed the code


@dataclass(frozen=True)
class DocumentDecision:
    outcome: Outcome  # pass, fail, retry or reject: never another step-up
    reasons: tuple[str, ...]
    document: MrzDocument | None = None
    aadhaar: AadhaarDocument | None = None


def decide_document(
    policy: Policy,
    analysis: DocumentAnalysis | None,
    attempt_index: int,
    today: date,
    liveness_failures: int = 0,
    livemode: bool = False,
) -> DocumentDecision:
    """The checks, in order: an analysis at all; no Aadhaar code in a live session; a live selfie; a readable zone
    that passes its check digits; one face on the document, and the selfie's face matching it; then the age rule (not
    expired, old enough). A doubtful step is retried while attempts remain, and then fails. An Aadhaar code in a test
    session takes its own path after the selfie (`decide_aadhaar`)."""
    try_again = Outcome.FAIL if attempt_index + 1 >= MAX_DOCUMENT_ATTEMPTS else Outcome.RETRY
    if analysis is None:
        return DocumentDecision(try_again, ("analysis_unavailable",))
    if analysis.aadhaar is not None and livemode:
        # Said before anything else, so the person is told plainly to use a passport or ID card.
        return DocumentDecision(try_again, ("aadhaar_test_only",))
    live = liveness_problem(analysis.face, liveness_failures, try_again, livemode)
    if live is not None:
        # Uncertain liveness can't step up again: there is nothing stronger to send the person to.
        outcome = try_again if live.outcome == Outcome.STEP_UP else live.outcome
        return DocumentDecision(outcome, live.reasons)
    if analysis.aadhaar is not None:
        return decide_aadhaar(policy, analysis, analysis.aadhaar, try_again, today)
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


def aadhaar_birth(born: str, today: date) -> tuple[date, bool] | None:
    """The date of birth a Secure QR gives, and whether it gave only the year; None if it isn't a date that can be.
    A year alone is taken as its last day, so nobody is counted older than they may be."""
    try:
        if len(born) == 4:
            birth, year_only = date(int(born), 12, 31), True
        else:
            birth, year_only = date.fromisoformat(born), False
    except ValueError:
        return None
    if birth.year < 1900 or birth.year > today.year or (birth > today and not year_only):
        return None
    return birth, year_only


def decide_aadhaar(
    policy: Policy, analysis: DocumentAnalysis, reading: AadhaarReading, try_again: Outcome, today: date
) -> DocumentDecision:
    """The checks for an Aadhaar Secure QR in a test session, in order, once the selfie is known to be live: a code
    that could be read; UIDAI's signature on it; one face in the code's photo, and the selfie's face matching it; then
    the age. A code has no expiry date: what UIDAI signed about a date of birth stays true."""
    if reading.born is None:
        return DocumentDecision(try_again, (reading.problem or "aadhaar_qr_unreadable",))
    if reading.signed_by is None:
        return DocumentDecision(try_again, ("aadhaar_signature_invalid",))
    birth = aadhaar_birth(reading.born, today)
    if birth is None:
        return DocumentDecision(try_again, ("aadhaar_qr_unreadable",))
    document = AadhaarDocument(birth[0], birth[1], reading.signed_by)
    if analysis.document_faces != 1:
        return DocumentDecision(try_again, ("document_face_not_found",), aadhaar=document)
    if analysis.similarity is None:
        return DocumentDecision(try_again, ("face_not_found",), aadhaar=document)
    if analysis.similarity < SAME_PERSON:
        return DocumentDecision(try_again, ("face_mismatch",), aadhaar=document)
    if age_on(document.born, today) >= policy.min_age:
        return DocumentDecision(Outcome.PASS, ("document_over_age", "aadhaar_qr"), aadhaar=document)
    return DocumentDecision(Outcome.FAIL, ("under_age", "aadhaar_qr"), aadhaar=document)
