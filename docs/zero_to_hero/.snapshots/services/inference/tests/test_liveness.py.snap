"""Tests for the liveness evidence: the pose challenge, the light challenge and the signs of injected frames."""

from __future__ import annotations

import numpy as np
import pytest

from dwarpal_contracts import Challenge, ClientSignals, FrameMeta, FrameReport, Phase
from dwarpal_inference.liveness import (
    FRONTAL_YAW,
    RAISE_SHIFT,
    TURN_SHIFT,
    Seen,
    emitted,
    injection_signs,
    light_check,
    pose_check,
    shows,
)

CHALLENGE = Challenge(
    poses=["turn_left", "look_up", "turn_right"], colours=["#3c78ff", "#ffd23c", "#20c8a0"], step_ms=600
)


def report(
    index: int, yaw: float = 0.0, pitch: float = 0.55, faces: int = 1, mesh: tuple[float, float] | None = None
) -> FrameReport:
    return FrameReport(
        index=index,
        faces=faces,
        detector_score=0.9,
        brightness=0.5,
        sharpness=100.0,
        eye_distance_px=60.0,
        yaw_ratio=yaw,
        pitch_ratio=pitch,
        mesh_yaw=None if mesh is None else mesh[0],
        mesh_pitch=None if mesh is None else mesh[1],
        flags=[],
    )


def frame(
    index: int,
    phase: Phase = "baseline",
    t_ms: float | None = None,
    aligned: np.ndarray | None = None,
    yaw: float = 0.0,
    pitch: float = 0.55,
    mesh: tuple[float, float] | None = None,
) -> Seen:
    meta = FrameMeta(index=index, t_ms=t_ms if t_ms is not None else 200.0 * index, phase=phase)
    return Seen(meta, report(index, yaw, pitch, mesh=mesh), aligned)


def genuine() -> list[Seen]:
    return [
        frame(0),
        frame(1),
        frame(2),
        frame(3, "turn_left", yaw=0.5),
        frame(4, "look_up", pitch=0.25),
        frame(5, "turn_right", yaw=-0.5),
    ]


def test_each_pose_is_measured_from_the_persons_own_frontal_angles() -> None:
    front = (0.0, 0.55)
    assert shows("turn_left", report(0, yaw=TURN_SHIFT), front)
    assert not shows("turn_left", report(0, yaw=-TURN_SHIFT), front)
    assert shows("turn_right", report(0, yaw=-0.3), front)
    assert shows("look_up", report(0, pitch=0.55 - 2 * RAISE_SHIFT), front)
    assert not shows("look_up", report(0, pitch=0.55), front)
    assert not shows("turn_left", report(0, yaw=0.6, faces=2), front)
    # A camera below the face: frontal pitch 0.7. Lifting the chin to 0.6 counts, though it would not from 0.55.
    assert shows("look_up", report(0, pitch=0.6), (0.0, 0.7))
    assert not shows("look_up", report(0, pitch=0.6), front)


def test_the_poses_asked_for_in_the_order_asked_pass() -> None:
    assert pose_check(genuine(), CHALLENGE).passed


def test_the_check_records_how_far_each_pose_got() -> None:
    check = pose_check(genuine(), CHALLENGE)
    assert (check.baseline_yaw, check.baseline_pitch) == (0.0, 0.55)
    assert check.reached == [("turn_left", 0.5), ("look_up", 0.3), ("turn_right", 0.5)]


def test_the_face_mesh_measures_the_poses_when_it_saw_every_frontal_frame() -> None:
    frames = [
        frame(0, mesh=(0.0, 0.75)),
        frame(1, mesh=(0.02, 0.76)),
        frame(2, mesh=(-0.01, 0.74)),
        frame(3, "turn_left", yaw=0.3, mesh=(0.4, 0.75)),
        frame(4, "look_up", mesh=(0.0, 0.6)),
        frame(5, "turn_right", yaw=-0.3, mesh=(-0.4, 0.75)),
    ]
    check = pose_check(frames, CHALLENGE)
    assert check.passed
    assert check.measured_by == "mesh"
    assert check.reached[1] == ("look_up", 0.15)


def test_without_the_mesh_on_every_frontal_frame_the_five_points_measure_everything() -> None:
    frames = genuine()
    frames[0] = frame(0, mesh=(0.0, 0.75))
    check = pose_check(frames, CHALLENGE)
    assert check.passed
    assert check.measured_by == "five_points"


def test_poses_in_another_order_fail() -> None:
    frames = genuine()
    frames[3], frames[5] = frame(3, "turn_right", yaw=-0.5), frame(5, "turn_left", yaw=0.5)
    assert pose_check(frames, CHALLENGE).problems == ["wrong_order"]


def test_a_pose_that_is_named_but_not_shown_fails() -> None:
    frames = genuine()
    frames[3] = frame(3, "turn_left", yaw=0.05)
    assert pose_check(frames, CHALLENGE).problems == ["not_shown:turn_left"]


def test_a_photo_that_never_turns_fails_every_turn() -> None:
    phases: list[Phase] = ["baseline", "baseline", "baseline", "turn_left", "look_up", "turn_right"]
    still = [frame(i, phase) for i, phase in enumerate(phases)]
    assert pose_check(still, CHALLENGE).problems == ["not_shown:turn_left", "not_shown:turn_right"]


def test_looking_up_is_recorded_but_does_not_decide() -> None:
    frames = genuine()
    frames[4] = frame(4, "look_up", pitch=0.56)
    check = pose_check(frames, CHALLENGE)
    assert check.passed
    assert check.reached[1] == ("look_up", -0.01)


def test_the_baseline_must_come_first_be_frontal_and_be_long_enough() -> None:
    turned = genuine()
    turned[1] = frame(1, yaw=FRONTAL_YAW + 0.1)
    assert "baseline_not_frontal" in pose_check(turned, CHALLENGE).problems
    assert "baseline_missing" in pose_check(genuine()[2:], CHALLENGE).problems
    late = [*genuine()[3:], frame(6, t_ms=2000), frame(7, t_ms=2200), frame(8, t_ms=2400)]
    assert "baseline_not_first" in pose_check(late, CHALLENGE).problems


def test_frames_whose_clock_runs_backwards_fail() -> None:
    frames = genuine()
    frames[1] = frame(1, t_ms=900.0)
    assert "timing" in pose_check(frames, CHALLENGE).problems


def face_lit_by(colour: str, strength: float, rng: np.random.Generator) -> np.ndarray:
    blue, green, red = (int(colour[i : i + 2], 16) for i in (5, 3, 1))
    skin = np.array([110.0, 140.0, 190.0]) * (1 - strength) + np.array([blue, green, red]) * strength
    return np.clip(skin + rng.normal(0, 2, (224, 224, 3)), 0, 255).astype(np.uint8)


def lit_frames(strength: float) -> list[Seen]:
    rng = np.random.default_rng(0)
    return [frame(i, t_ms=600.0 * i + 100, aligned=face_lit_by(CHALLENGE.colours[i], strength, rng)) for i in range(3)]


def test_skin_that_follows_the_screen_correlates_strongly() -> None:
    light = light_check(lit_frames(0.2), CHALLENGE, started_ms=0.0, signals=ClientSignals())
    assert light.usable
    assert light.r_skin is not None
    assert light.r_skin > 0.9


def test_skin_that_ignores_the_screen_does_not_correlate() -> None:
    light = light_check(lit_frames(0.0), CHALLENGE, started_ms=0.0, signals=ClientSignals())
    assert light.usable
    assert light.r_skin is not None
    assert abs(light.r_skin) < 0.9


def test_without_the_screen_colours_there_is_no_light_evidence() -> None:
    assert not light_check(lit_frames(0.2), CHALLENGE, None, ClientSignals()).usable
    calm = light_check(lit_frames(0.2), CHALLENGE, 0.0, ClientSignals(light_shown=False))
    assert (calm.usable, calm.shown) == (False, False)
    too_few = light_check(lit_frames(0.2)[:2], CHALLENGE, 0.0, ClientSignals())
    assert (too_few.usable, too_few.shown) == (False, True)


def test_a_colour_is_read_as_its_share_of_red_and_blue() -> None:
    assert emitted("#ff0000") == pytest.approx([1.0, 0.0])
    assert emitted("#f0f0f0") == pytest.approx([1 / 3, 1 / 3])


def test_browser_reports_and_frozen_frames_are_signs_of_injection() -> None:
    rng = np.random.default_rng(1)
    face = rng.integers(0, 256, (224, 224, 3), dtype=np.uint8)
    frozen = [frame(i, aligned=face) for i in range(3)]
    alive = [frame(i, aligned=np.clip(face + rng.normal(0, 3, face.shape), 0, 255).astype(np.uint8)) for i in range(3)]
    signals = ClientSignals(automation=True, virtual_camera=True, hidden_ms=50.0)
    assert injection_signs(frozen, signals) == ["automation", "virtual_camera", "page_hidden", "identical_frames"]
    assert injection_signs(alive, ClientSignals()) == []


def test_a_hand_beside_the_face_in_more_than_one_photo_is_a_sign_of_a_held_phone() -> None:
    def held(hands: list[int]) -> list[str]:
        frames = [
            Seen(FrameMeta(index=i, t_ms=200.0 * i), report(i).model_copy(update={"hands_near_face": n}), None)
            for i, n in enumerate(hands)
        ]
        return injection_signs(frames, ClientSignals())

    assert held([0, 1, 0, 1]) == ["hand_near_face"]
    assert held([0, 1, 0, 0]) == []


def test_a_photo_on_the_way_into_a_pose_shows_the_movement_was_gradual() -> None:
    frames = genuine()
    frames.insert(3, frame(3, "turn_left", t_ms=550.0, yaw=0.2))
    check = pose_check(frames, CHALLENGE)
    assert check.gradual == [("turn_left", True), ("look_up", False), ("turn_right", False)]
