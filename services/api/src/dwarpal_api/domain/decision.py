"""The decision engine: pure rules that turn an analysis into an outcome, checked in a fixed order.

The engine can only ever answer "pass" from its last rule, and only when every earlier rule is satisfied.
Missing, broken or doubtful evidence leads to retry, step-up or fail, never to pass (it "fails closed").
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum

from dwarpal_api.domain.policy import Policy, Thresholds
from dwarpal_contracts import FaceAnalysis

MIN_USABLE_FRAMES = 3
MAX_FRAME_SPREAD_YEARS = 8.0
RETRY_HARDENING = 0.02
ADVICE_ORDER = (
    "undecodable",
    "no_face",
    "multiple_faces",
    "face_too_small",
    "too_dark",
    "too_bright",
    "too_blurry",
    "not_frontal",
    "low_confidence",
)


class Outcome(StrEnum):
    PASS = "pass"  # noqa: S105 - an outcome's name, not a password
    FAIL = "fail"
    STEP_UP = "step_up"
    RETRY = "retry"
    REJECT = "reject"


@dataclass(frozen=True)
class Decision:
    outcome: Outcome
    reasons: tuple[str, ...]
    p_over: float | None = None
    tau_effective: float | None = None


def dominant_problem(analysis: FaceAnalysis) -> str:
    counts = Counter(flag for frame in analysis.frames for flag in frame.flags)
    return next((flag for flag in ADVICE_ORDER if counts[flag]), "no_usable_frames")


def decide(
    policy: Policy, thresholds: Thresholds, analysis: FaceAnalysis | None, attempt_index: int, model_ok: bool
) -> Decision:
    try_again = Outcome.STEP_UP if attempt_index + 1 >= policy.max_face_attempts else Outcome.RETRY
    if analysis is None:
        return Decision(try_again, ("analysis_unavailable",))
    if not model_ok:
        return Decision(try_again, ("model_mismatch",))
    if analysis.age is None or analysis.usable_frames < MIN_USABLE_FRAMES:
        return Decision(try_again, (dominant_problem(analysis),))
    means = analysis.age.frame_means
    if len(means) > 1 and statistics.pstdev(means) > MAX_FRAME_SPREAD_YEARS:
        return Decision(try_again, ("inconsistent_frames",))
    p_over = analysis.age.p_over.get(policy.min_age)
    if p_over is None or math.isnan(p_over):
        return Decision(try_again, ("analysis_incomplete",))
    tau = min(0.999, thresholds.tau_pass + attempt_index * RETRY_HARDENING)
    if p_over >= tau:
        return Decision(Outcome.PASS, ("age_over_threshold",), p_over, tau)
    if p_over <= thresholds.tau_fail:
        return Decision(Outcome.FAIL, ("age_under_threshold",), p_over, tau)
    return Decision(Outcome.STEP_UP, ("age_uncertain",), p_over, tau)
