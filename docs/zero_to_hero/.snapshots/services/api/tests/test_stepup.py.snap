"""The step-up's document rules (Phase 6): what each check does with good, missing and doubtful evidence."""

from __future__ import annotations

from datetime import date

import pytest

from dwarpal_api.domain.decision import Outcome
from dwarpal_api.domain.mrz import check_digit
from dwarpal_api.domain.policy import get_policy
from dwarpal_api.domain.stepup import MAX_DOCUMENT_ATTEMPTS, SAME_PERSON, decide_document
from dwarpal_contracts import (
    AadhaarReading,
    DocumentAnalysis,
    FaceAnalysis,
    FrameReport,
    LightCheck,
    Liveness,
    PoseCheck,
)

TODAY = date(2026, 11, 1)
POLICY = get_policy("uk_osa_18")
LIVE = Liveness(pose=PoseCheck(passed=True, problems=[]), light=LightCheck(usable=False), injection=[])


def zone(birth: str, expiry: str = "360101") -> list[str]:
    """A passport's zone as the inference service returns it: the names line already blanked."""
    number, personal = "L898902C3", "<" * 14
    middle = f"{number}{check_digit(number)}UTO{birth}{check_digit(birth)}F{expiry}{check_digit(expiry)}"
    middle += f"{personal}<"
    composite = middle[0:10] + middle[13:20] + middle[21:43]
    return ["P<UTO".ljust(44, "<"), middle + check_digit(composite)]


def selfie(liveness: Liveness | None = LIVE) -> FaceAnalysis:
    frame = FrameReport(
        index=0,
        faces=1,
        detector_score=0.9,
        brightness=0.5,
        sharpness=100.0,
        eye_distance_px=80.0,
        yaw_ratio=0.0,
        flags=[],
    )
    return FaceAnalysis(
        model_version="stub", frames=[frame] * 4, usable_frames=4, age=None, duration_ms=5.0, liveness=liveness
    )


def analysis(
    lines: list[str] | None = None,
    similarity: float | None = 0.7,
    faces: int = 1,
    liveness: Liveness | None = LIVE,
    problem: str | None = None,
    aadhaar: AadhaarReading | None = None,
) -> DocumentAnalysis:
    return DocumentAnalysis(
        zone=zone("900101") if lines is None else lines,
        zone_problem=problem,
        aadhaar=aadhaar,
        document_faces=faces,
        similarity=similarity,
        face=selfie(liveness),
        duration_ms=50.0,
    )


def test_an_adult_whose_face_matches_a_valid_document_passes() -> None:
    decision = decide_document(POLICY, analysis(), 0, TODAY)
    assert decision.outcome == Outcome.PASS
    assert decision.reasons == ("document_over_age",)
    assert decision.document is not None and decision.document.birth_year_month == (1990, 1)


@pytest.mark.parametrize(
    ("lines", "reason"),
    [(zone("140302"), "under_age"), (zone("900101", expiry="250101"), "document_expired")],
)
def test_a_minor_or_an_expired_document_fails(lines: list[str], reason: str) -> None:
    decision = decide_document(POLICY, analysis(lines), 0, TODAY)
    assert (decision.outcome, decision.reasons[0]) == (Outcome.FAIL, reason)


@pytest.mark.parametrize(
    ("evidence", "reason"),
    [
        (None, "analysis_unavailable"),
        (analysis(lines=[], problem="mrz_not_found"), "mrz_not_found"),
        (analysis(lines=[], problem="ocr_unavailable"), "analysis_unavailable"),
        (analysis(lines=[zone("900101")[0], zone("900101")[1].replace("900101", "900102")]), "mrz_check_failed"),
        (analysis(faces=0), "document_face_not_found"),
        (analysis(faces=2), "document_face_not_found"),
        (analysis(similarity=None), "face_not_found"),
        (analysis(similarity=SAME_PERSON - 0.01), "face_mismatch"),
        (analysis(liveness=None), "liveness_unavailable"),
    ],
)
def test_doubtful_evidence_is_retried_and_then_fails_never_passes(
    evidence: DocumentAnalysis | None, reason: str
) -> None:
    first = decide_document(POLICY, evidence, 0, TODAY)
    last = decide_document(POLICY, evidence, MAX_DOCUMENT_ATTEMPTS - 1, TODAY)
    assert (first.outcome, first.reasons[0]) == (Outcome.RETRY, reason)
    assert (last.outcome, last.reasons[0]) == (Outcome.FAIL, reason)


def test_a_failed_pose_challenge_is_retried_once_then_rejected() -> None:
    failed = Liveness(pose=PoseCheck(passed=False, problems=["pose_missing"]), light=None, injection=[])
    assert decide_document(POLICY, analysis(liveness=failed), 0, TODAY).outcome == Outcome.RETRY
    rejected = decide_document(POLICY, analysis(liveness=failed), 1, TODAY, liveness_failures=1)
    assert rejected.outcome == Outcome.REJECT


def test_doubtful_liveness_cannot_step_up_again() -> None:
    """At a face check, signs of injection send a person to the step-up; here there is nothing stronger to send them
    to, so the step-up's own attempts are used, and then it fails."""
    doubtful = Liveness(pose=PoseCheck(passed=True, problems=[]), light=None, injection=["virtual_camera"])
    decision = decide_document(POLICY, analysis(liveness=doubtful), 0, TODAY)
    assert (decision.outcome, decision.reasons) == (Outcome.RETRY, ("liveness_uncertain",))


def secure_qr(
    born: str | None = "1990-01-01", signed_by: str | None = "uidai_offline_publickey_2026"
) -> AadhaarReading:
    """What the inference service passes on from an Aadhaar Secure QR."""
    return AadhaarReading(signed_by=signed_by, born=born, problem=None if born else "aadhaar_qr_unreadable")


def test_a_signed_secure_qr_of_an_adult_whose_face_matches_passes() -> None:
    decision = decide_document(POLICY, analysis(lines=[], aadhaar=secure_qr()), 0, TODAY)
    assert decision.outcome == Outcome.PASS
    assert decision.reasons == ("document_over_age", "aadhaar_qr")
    assert decision.document is None and decision.aadhaar is not None
    assert (decision.aadhaar.born, decision.aadhaar.year_only) == (date(1990, 1, 1), False)


def test_a_signed_secure_qr_of_a_minor_fails_at_once() -> None:
    decision = decide_document(POLICY, analysis(lines=[], aadhaar=secure_qr("2010-06-01")), 0, TODAY)
    assert (decision.outcome, decision.reasons) == (Outcome.FAIL, ("under_age", "aadhaar_qr"))


@pytest.mark.parametrize(
    ("born", "outcome"),
    [("2008", Outcome.FAIL), ("2007", Outcome.PASS)],  # on 1 Nov 2026: 18 only if born before 2 Nov 2008
)
def test_a_year_alone_counts_as_its_last_day(born: str, outcome: Outcome) -> None:
    decision = decide_document(POLICY, analysis(lines=[], aadhaar=secure_qr(born)), 0, TODAY)
    assert decision.outcome == outcome
    assert decision.aadhaar is not None and decision.aadhaar.year_only
    assert decision.aadhaar.born == date(int(born), 12, 31)


@pytest.mark.parametrize(
    ("evidence", "reason"),
    [
        (analysis(lines=[], aadhaar=secure_qr(signed_by=None)), "aadhaar_signature_invalid"),
        (analysis(lines=[], aadhaar=secure_qr(born=None)), "aadhaar_qr_unreadable"),
        (analysis(lines=[], aadhaar=secure_qr("1990-02-30")), "aadhaar_qr_unreadable"),  # no such day
        (analysis(lines=[], aadhaar=secure_qr("2027-01-01")), "aadhaar_qr_unreadable"),  # not born yet
        (analysis(lines=[], aadhaar=secure_qr("1850")), "aadhaar_qr_unreadable"),
        (analysis(lines=[], aadhaar=secure_qr(), faces=0), "document_face_not_found"),
        (analysis(lines=[], aadhaar=secure_qr(), similarity=None), "face_not_found"),
        (analysis(lines=[], aadhaar=secure_qr(), similarity=SAME_PERSON - 0.01), "face_mismatch"),
        (analysis(lines=[], aadhaar=secure_qr(), liveness=None), "liveness_unavailable"),
    ],
)
def test_a_doubtful_secure_qr_is_retried_and_never_passes(evidence: DocumentAnalysis, reason: str) -> None:
    first = decide_document(POLICY, evidence, 0, TODAY)
    last = decide_document(POLICY, evidence, MAX_DOCUMENT_ATTEMPTS - 1, TODAY)
    assert first.outcome == Outcome.RETRY and reason in first.reasons
    assert last.outcome == Outcome.FAIL


def test_an_unsigned_code_fails_however_old_it_claims_to_be() -> None:
    forged = analysis(lines=[], aadhaar=secure_qr("1950-01-01", signed_by=None))
    assert decide_document(POLICY, forged, MAX_DOCUMENT_ATTEMPTS - 1, TODAY).outcome == Outcome.FAIL


def test_a_live_session_does_not_take_a_secure_qr() -> None:
    decision = decide_document(POLICY, analysis(lines=[], aadhaar=secure_qr()), 0, TODAY, livemode=True)
    assert (decision.outcome, decision.reasons) == (Outcome.RETRY, ("aadhaar_test_only",))
    last = decide_document(
        POLICY, analysis(lines=[], aadhaar=secure_qr()), MAX_DOCUMENT_ATTEMPTS - 1, TODAY, livemode=True
    )
    assert last.outcome == Outcome.FAIL
