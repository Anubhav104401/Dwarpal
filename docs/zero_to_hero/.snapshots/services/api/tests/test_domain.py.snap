"""Tests for the pure rules: identifiers, keys, policies, decisions, the session state machine, settings and logs."""

from __future__ import annotations

import base64
import itertools
import json
import logging
import math
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import SecretStr, ValidationError

from dwarpal_api.cli import liveness_summary
from dwarpal_api.domain import ids
from dwarpal_api.domain.challenges import COLOUR_STEPS, MAX_LOOK_UPS, PALETTE, POSE_STEPS, new_challenge
from dwarpal_api.domain.decision import Outcome, decide
from dwarpal_api.domain.keys import generate_api_key, generate_client_secret, matches, parse_api_key
from dwarpal_api.domain.policy import (
    PRESETS,
    Thresholds,
    UncalibratedPolicyError,
    UnknownPolicyError,
    get_policy,
    load_manifest,
)
from dwarpal_api.domain.sessions import ALLOWED, IllegalTransitionError, Status, is_expired, move
from dwarpal_api.logs import JsonFormatter
from dwarpal_api.settings import Settings
from dwarpal_contracts import AgeEstimate, FaceAnalysis, FrameReport, LightCheck, Liveness, PoseCheck

REPO = Path(__file__).resolve().parents[3]
POLICY = get_policy("uk_osa_18")
THRESHOLDS = Thresholds(tau_pass=0.95, tau_fail=0.05)
RANK = {Outcome.FAIL: 0, Outcome.STEP_UP: 1, Outcome.PASS: 2}


def frame(index: int, flags: list[str] | None = None) -> FrameReport:
    return FrameReport(
        index=index,
        faces=1,
        detector_score=0.95,
        brightness=0.5,
        sharpness=120.0,
        eye_distance_px=80.0,
        yaw_ratio=0.0,
        flags=flags or [],
    )


LIVE = Liveness(pose=PoseCheck(passed=True, problems=[]), light=LightCheck(usable=False), injection=[])


def analysis(
    p_over_18: float, usable: int = 4, means: list[float] | None = None, liveness: Liveness | None = LIVE
) -> FaceAnalysis:
    p_over = {13: 1.0, 16: 1.0, 18: p_over_18, 21: 0.9, 25: 0.8}
    age = AgeEstimate(mean=30.0, std=2.0, p_over=p_over, frame_means=means or [30.0] * usable)
    frames = [frame(i) for i in range(usable)]
    return FaceAnalysis(
        model_version="stub-age-30", frames=frames, usable_frames=usable, age=age, duration_ms=10.0, liveness=liveness
    )


@given(st.integers(min_value=0, max_value=2**48 - 1))
def test_uuid7_carries_version_variant_and_time(unix_ms: int) -> None:
    value = ids.uuid7(unix_ms)
    assert value.version == 7
    assert value.variant == uuid.RFC_4122
    assert value.int >> 80 == unix_ms


def test_uuid7_values_sort_by_time() -> None:
    assert ids.uuid7(1_000) < ids.uuid7(2_000)


@given(st.uuids())
def test_identifiers_survive_a_round_trip(value: uuid.UUID) -> None:
    text = ids.encode("vs", value)
    assert text.startswith("vs_")
    assert len(text) == 29
    assert ids.decode("vs", text) == value
    assert ids.decode("vs", text.lower()) == value


@pytest.mark.parametrize("text", ["prj_01ABC", "vs_" + "U" * 26, "vs_" + "0" * 25, "vs-" + "0" * 26, "vs_" + "Z" * 26])
def test_malformed_identifiers_are_refused(text: str) -> None:
    with pytest.raises(ids.InvalidIdError):
        ids.decode("vs", text)


def test_api_keys_are_shown_once_and_kept_only_as_digests() -> None:
    key = generate_api_key(livemode=False)
    assert key.plaintext.startswith("dk_test_")
    assert parse_api_key(key.plaintext) == (False, key.lookup)
    assert matches(key.plaintext, key.digest)
    assert not matches(key.plaintext + "x", key.digest)
    assert key.plaintext.encode() not in key.digest


@pytest.mark.parametrize("text", ["", "Bearer something", "dk_prod_abcdefghijklmnop", "dk_test_short"])
def test_other_key_formats_are_refused(text: str) -> None:
    assert parse_api_key(text) is None


def test_client_secrets_name_their_session() -> None:
    secret = generate_client_secret("vs_EXAMPLE")
    assert secret.plaintext.startswith("vs_EXAMPLE_secret_")
    assert matches(secret.plaintext, secret.digest)


def test_presets_are_found_and_unknown_policies_refused() -> None:
    assert get_policy("us_21").min_age == 21
    with pytest.raises(UnknownPolicyError):
        get_policy("anything_goes")


def test_the_stub_manifest_covers_every_preset_and_admits_it_is_uncalibrated() -> None:
    manifest = load_manifest(REPO / "models" / "registry" / "age" / "stub" / "manifest.json")
    assert not manifest.calibrated
    assert manifest.serves_model("stub-age-30")
    assert not manifest.serves_model("age-v1")
    for policy in PRESETS.values():
        assert manifest.thresholds_for(policy).tau_pass > manifest.thresholds_for(policy).tau_fail


def write_manifest(path: Path, tau_pass: float, tau_fail: float) -> Path:
    rows = [{"min_age": 18, "risk_budget": 0.02, "tau_pass": tau_pass, "tau_fail": tau_fail}]
    data = {"name": "age", "version": "v", "serves": "v", "calibrated": True, "thresholds": rows}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_a_policy_the_model_was_not_calibrated_for_is_refused(tmp_path: Path) -> None:
    manifest = load_manifest(write_manifest(tmp_path / "m.json", 0.9, 0.1))
    with pytest.raises(UncalibratedPolicyError):
        manifest.thresholds_for(get_policy("us_21"))


def test_impossible_thresholds_are_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="invalid thresholds"):
        load_manifest(write_manifest(tmp_path / "m.json", 0.1, 0.9))


def test_clear_cases_pass_fail_and_step_up() -> None:
    assert decide(POLICY, THRESHOLDS, analysis(0.99), 0, True).outcome == Outcome.PASS
    assert decide(POLICY, THRESHOLDS, analysis(0.01), 0, True).outcome == Outcome.FAIL
    assert decide(POLICY, THRESHOLDS, analysis(0.50), 0, True).outcome == Outcome.STEP_UP


def test_missing_or_mismatched_analysis_never_passes() -> None:
    assert decide(POLICY, THRESHOLDS, None, 0, True).outcome == Outcome.RETRY
    assert decide(POLICY, THRESHOLDS, None, 2, True).outcome == Outcome.STEP_UP
    assert decide(POLICY, THRESHOLDS, analysis(0.99), 0, model_ok=False).reasons == ("model_mismatch",)


def test_poor_frames_ask_for_a_retry_naming_the_main_problem() -> None:
    frames = [frame(0, ["too_dark"]), frame(1, ["too_blurry", "too_dark"]), frame(2)]
    poor = FaceAnalysis(model_version="stub-age-30", frames=frames, usable_frames=1, age=None, duration_ms=5.0)
    decision = decide(POLICY, THRESHOLDS, poor, 0, True)
    assert decision.outcome == Outcome.RETRY
    assert decision.reasons == ("too_dark",)


def test_frames_that_disagree_are_not_trusted() -> None:
    decision = decide(POLICY, THRESHOLDS, analysis(0.99, means=[15.0, 40.0, 15.0, 40.0]), 0, True)
    assert decision.reasons == ("inconsistent_frames",)


def test_a_broken_probability_fails_closed() -> None:
    good = analysis(0.99)
    assert good.age is not None
    broken_age = good.age.model_copy(update={"p_over": {18: math.nan}})
    broken = good.model_copy(update={"age": broken_age})
    assert decide(POLICY, THRESHOLDS, broken, 0, True).outcome != Outcome.PASS


@given(st.floats(0.0, 1.0), st.floats(0.0, 1.0), st.integers(0, 2))
def test_more_evidence_of_adulthood_never_makes_the_outcome_worse(p: float, q: float, attempt: int) -> None:
    low, high = sorted((p, q))
    worse = decide(POLICY, THRESHOLDS, analysis(low), attempt, True).outcome
    better = decide(POLICY, THRESHOLDS, analysis(high), attempt, True).outcome
    assert RANK[worse] <= RANK[better]


@given(st.floats(0.0, 1.0), st.integers(1, 2))
def test_later_attempts_never_get_an_easier_bar(p: float, attempt: int) -> None:
    earlier = decide(POLICY, THRESHOLDS, analysis(p), attempt - 1, True)
    later = decide(POLICY, THRESHOLDS, analysis(p), attempt, True)
    assert earlier.tau_effective is not None
    assert later.tau_effective is not None
    assert later.tau_effective >= earlier.tau_effective
    if later.outcome == Outcome.PASS:
        assert earlier.outcome == Outcome.PASS


@given(st.floats(0.0, 1.0), st.integers(0, 2))
def test_every_pass_clears_the_calibrated_threshold(p: float, attempt: int) -> None:
    decision = decide(POLICY, THRESHOLDS, analysis(p), attempt, True)
    if decision.outcome == Outcome.PASS:
        assert decision.p_over is not None
        assert decision.p_over >= THRESHOLDS.tau_pass


def test_the_state_machine_allows_exactly_its_listed_moves() -> None:
    for current in Status:
        for target in Status:
            if target in ALLOWED[current]:
                assert move(current, target) == target
            else:
                with pytest.raises(IllegalTransitionError):
                    move(current, target)


def test_only_open_sessions_can_expire() -> None:
    now = datetime(2026, 10, 16, tzinfo=UTC)
    past = now - timedelta(seconds=1)
    assert is_expired(Status.IN_PROGRESS, past, now)
    assert not is_expired(Status.COMPLETED, past, now)
    assert not is_expired(Status.CREATED, now + timedelta(minutes=5), now)


def test_production_refuses_development_values() -> None:
    real_key = SecretStr(base64.b64encode(bytes(range(32))).decode())
    with pytest.raises(ValidationError, match="DWARPAL_MASTER_KEY"):
        Settings(environment="production", issuer="https://id.example", verify_url="https://verify.example")
    with pytest.raises(ValidationError, match="DWARPAL_ISSUER"):
        Settings(environment="production", master_key=real_key, verify_url="https://verify.example")
    production = Settings(
        environment="production", master_key=real_key, issuer="https://id.example", verify_url="https://verify.example"
    )
    assert production.issuer == "https://id.example"


def test_log_lines_are_json_objects_carrying_the_request_fields() -> None:
    fields = {"name": "dwarpal.api", "levelno": logging.INFO, "levelname": "INFO", "msg": "request"}
    record = logging.makeLogRecord({**fields, "request_id": "req_0123456789abcdef", "status": 201})
    line = json.loads(JsonFormatter().format(record))
    assert line["level"] == "info"
    assert line["message"] == "request"
    assert line["request_id"] == "req_0123456789abcdef"
    assert line["status"] == 201
    assert "method" not in line


def test_without_liveness_evidence_nothing_passes() -> None:
    no_challenge = Liveness(pose=None, light=None, injection=[])
    for missing in (None, no_challenge):
        decision = decide(POLICY, THRESHOLDS, analysis(0.999, liveness=missing), 0, True)
        assert (decision.outcome, decision.reasons) == (Outcome.RETRY, ("liveness_unavailable",))


def test_a_failed_pose_challenge_gets_one_retry_then_a_rejection() -> None:
    failed = Liveness(pose=PoseCheck(passed=False, problems=["wrong_order"]), light=None, injection=[])
    first = decide(POLICY, THRESHOLDS, analysis(0.999, liveness=failed), 0, True)
    second = decide(POLICY, THRESHOLDS, analysis(0.999, liveness=failed), 1, True, liveness_failures=1)
    assert (first.outcome, first.reasons) == (Outcome.RETRY, ("liveness_check_failed",))
    assert (second.outcome, second.reasons) == (Outcome.REJECT, ("liveness_check_failed",))


def test_signs_of_injection_send_even_a_clear_adult_to_step_up() -> None:
    suspicious = Liveness(pose=PoseCheck(passed=True, problems=[]), light=None, injection=["virtual_camera"])
    decision = decide(POLICY, THRESHOLDS, analysis(0.999, liveness=suspicious), 0, True)
    assert (decision.outcome, decision.reasons) == (Outcome.STEP_UP, ("liveness_uncertain",))


def test_liveness_reasons_never_say_which_check_fired() -> None:
    reasons = set()
    for live in (
        Liveness(pose=PoseCheck(passed=False, problems=["not_shown:turn_left"]), light=None, injection=[]),
        Liveness(pose=PoseCheck(passed=False, problems=["baseline_not_frontal"]), light=None, injection=[]),
        Liveness(pose=PoseCheck(passed=True, problems=[]), light=None, injection=["automation"]),
        Liveness(pose=PoseCheck(passed=True, problems=[]), light=None, injection=["identical_frames"]),
    ):
        reasons |= set(decide(POLICY, THRESHOLDS, analysis(0.999, liveness=live), 0, True).reasons)
    assert reasons == {"liveness_check_failed", "liveness_uncertain"}


def test_a_live_session_never_accepts_liveness_taken_from_labels() -> None:
    labelled = Liveness(pose=PoseCheck(passed=True, problems=[]), light=None, injection=[], evidence="labels")
    test_mode = decide(POLICY, THRESHOLDS, analysis(0.999, liveness=labelled), 0, True)
    live = decide(POLICY, THRESHOLDS, analysis(0.999, liveness=labelled), 0, True, livemode=True)
    assert test_mode.outcome == Outcome.PASS
    assert (live.outcome, live.reasons) == (Outcome.RETRY, ("liveness_unavailable",))


def test_challenges_are_random_never_repeat_a_step_and_cover_every_order() -> None:
    rng = random.Random(7)  # noqa: S311 - reproducible test draws; real challenges use secrets.SystemRandom
    drawn = [new_challenge(rng) for _ in range(2000)]
    for challenge in drawn:
        assert len(challenge.poses) in POSE_STEPS
        assert challenge.poses.count("look_up") <= MAX_LOOK_UPS
        assert len(challenge.colours) == COLOUR_STEPS
        assert set(challenge.colours) <= set(PALETTE)
        for steps in (challenge.poses, challenge.colours):
            assert all(a != b for a, b in itertools.pairwise(steps))
    assert len({tuple(challenge.poses) for challenge in drawn}) == 24


def test_the_liveness_report_counts_outcomes_problems_signs_and_light() -> None:
    def scores(passed: bool, problems: list[str], signs: list[str], r_skin: float | None) -> dict[str, Any]:
        light = {"usable": r_skin is not None, "r_skin": r_skin, "r_background": None}
        return {
            "liveness": {
                "pose": {"passed": passed, "problems": problems, "reached": [["turn_left", 0.3 if passed else 0.05]]},
                "light": light,
                "injection": signs,
                "evidence": "images",
            }
        }

    report = liveness_summary(
        [
            ("pass", scores(True, [], [], 0.8)),
            ("pass", scores(True, [], [], 0.4)),
            ("retry", scores(False, ["not_shown:turn_left"], [], None)),
            ("step_up", scores(True, [], ["automation"], 0.6)),
        ]
    )
    assert "4 face attempts: pass 2, retry 1, step_up 1" in report
    assert "pose challenge passed: 3 of 4 (75%); false-reject rate if all were genuine: 25%" in report
    assert "pose problems: not_shown:turn_left 1" in report
    assert "pose reach from frontal, median / lowest: turn_left +0.30 / +0.05" in report
    assert "injection signs: automation 1" in report
    assert "skin correlation median +0.60, range +0.40 to +0.80" in report
