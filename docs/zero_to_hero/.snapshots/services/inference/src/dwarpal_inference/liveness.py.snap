"""Liveness evidence from one attempt: did the head turn as asked, did the skin reflect the screen, and does anything
suggest the frames came from somewhere other than a live camera. Evidence only: the API decides (ADR-0007)."""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from dwarpal_contracts import Challenge, ClientSignals, FrameMeta, FrameReport, LightCheck, Pose, PoseCheck
from dwarpal_vision import Image

# Provisional limits, set from the owner's genuine attempts. The ratios come from the 5 landmarks: a turned head moves
# its nose sideways against its eyes; a raised head moves its nose towards its eyes. Each pose is measured from the
# person's own frontal frames, so camera height and face shape cancel out. Genuine turns moved the nose 0.23-0.69
# eye-widths, every time. Chins lifted until the page's meter was full moved it anywhere from -0.03 to 0.12 of the
# eyes-to-mouth distance: five landmarks can't measure looking up reliably, so it is recorded but never decides, and
# the turns carry the proof. A flat photo, turned or tilted, moves neither.
FRONTAL_YAW = 0.2
TURN_SHIFT = 0.18
RAISE_SHIFT = 0.03
DECIDING: frozenset[Pose] = frozenset({"turn_left", "turn_right"})
MIN_BASELINE = 3
# Grey levels: consecutive frames from a live camera always differ a little, if only by sensor noise.
STILL_FRAMES = 0.75
# Where to sample skin and background on a 224 x 224 aligned face (rows, columns): both cheeks and the forehead,
# and the top corners, beyond the hair line.
SKIN = ((slice(120, 150), slice(50, 80)), (slice(120, 150), slice(144, 174)), (slice(40, 60), slice(92, 132)))
BACKGROUND = ((slice(0, 16), slice(0, 16)), (slice(0, 16), slice(208, 224)))


@dataclass(frozen=True)
class Seen:
    """One frame, as the liveness checks see it."""

    meta: FrameMeta
    report: FrameReport
    aligned: Image | None


type Angles = tuple[float, float]


def frontal_angles(frames: list[Seen]) -> Angles | None:
    """The person's own yaw and pitch when facing the camera: the median over the baseline frames with one face."""
    faced = [frame.report for frame in frames if frame.report.faces == 1]
    if not faced:
        return None
    return float(np.median([r.yaw_ratio for r in faced])), float(np.median([r.pitch_ratio for r in faced]))


def shift(pose: Pose, report: FrameReport, baseline: Angles) -> float:
    """How far a frame has moved from the baseline in the pose's direction; negative when it moved the other way."""
    yaw, pitch = baseline
    if pose == "turn_left":
        return report.yaw_ratio - yaw
    if pose == "turn_right":
        return yaw - report.yaw_ratio
    return pitch - report.pitch_ratio


def shows(pose: Pose, report: FrameReport, baseline: Angles) -> bool:
    if report.faces != 1:
        return False
    return shift(pose, report, baseline) >= (RAISE_SHIFT if pose == "look_up" else TURN_SHIFT)


def segments(frames: list[Seen]) -> list[tuple[str, list[Seen]]]:
    runs: list[tuple[str, list[Seen]]] = []
    for frame in frames:
        if runs and runs[-1][0] == frame.meta.phase:
            runs[-1][1].append(frame)
        else:
            runs.append((frame.meta.phase, [frame]))
    return runs


def pose_check(frames: list[Seen], challenge: Challenge, trust_labels: bool = False) -> PoseCheck:
    ordered = sorted(frames, key=lambda frame: frame.meta.t_ms)
    problems = []
    if [frame.meta.index for frame in ordered] != sorted(frame.meta.index for frame in frames):
        problems.append("timing")
    runs = segments(ordered)
    baseline = [frame for phase, run in runs if phase == "baseline" for frame in run]
    if len(baseline) < MIN_BASELINE:
        problems.append("baseline_missing")
    elif not trust_labels and any(
        frame.report.faces != 1 or abs(frame.report.yaw_ratio) > FRONTAL_YAW for frame in baseline
    ):
        problems.append("baseline_not_frontal")
    if runs and runs[0][0] != "baseline":
        problems.append("baseline_not_first")
    reference = frontal_angles(baseline)
    reached: list[tuple[Pose, float | None]] = []
    steps = [(phase, run) for phase, run in runs if phase != "baseline"]
    if [phase for phase, _ in steps] != list(challenge.poses):
        problems.append("wrong_order")
    elif not trust_labels:
        for pose, (_, run) in zip(challenge.poses, steps, strict=True):
            faced = [frame.report for frame in run if frame.report.faces == 1]
            furthest = max((shift(pose, r, reference) for r in faced), default=None) if reference else None
            reached.append((pose, None if furthest is None else round(furthest, 3)))
            missed = reference is None or not any(shows(pose, r, reference) for r in faced)
            if missed and pose in DECIDING:
                problems.append(f"not_shown:{pose}")
    return PoseCheck(
        passed=not problems,
        problems=problems,
        baseline_yaw=None if reference is None else round(reference[0], 3),
        baseline_pitch=None if reference is None else round(reference[1], 3),
        reached=reached,
    )


def chromaticity(image: Image, patches: tuple[tuple[slice, slice], ...]) -> NDArray[np.float64]:
    pixels = np.concatenate([image[rows, cols].reshape(-1, 3) for rows, cols in patches]).astype(np.float64)
    blue, green, red = pixels.mean(axis=0)
    total = max(red + green + blue, 1.0)
    return np.array([red / total, blue / total])


def emitted(colour: str) -> NDArray[np.float64]:
    red, green, blue = (int(colour[i : i + 2], 16) for i in (1, 3, 5))
    total = max(red + green + blue, 1)
    return np.array([red / total, blue / total])


def correlation(measured: list[NDArray[np.float64]], shown: list[NDArray[np.float64]]) -> float | None:
    a = np.array(measured) - np.mean(measured, axis=0)
    b = np.array(shown) - np.mean(shown, axis=0)
    spread = float(np.linalg.norm(a) * np.linalg.norm(b))
    return None if spread == 0 else float(np.clip((a * b).sum() / spread, -1.0, 1.0))


def light_check(
    frames: list[Seen], challenge: Challenge, started_ms: float | None, signals: ClientSignals
) -> LightCheck:
    if started_ms is None or not signals.light_shown:
        return LightCheck(usable=False)
    skin, background, shown = [], [], []
    for frame in frames:
        step = int((frame.meta.t_ms - started_ms) // challenge.step_ms)
        if frame.meta.phase != "baseline" or frame.aligned is None or not 0 <= step < len(challenge.colours):
            continue
        skin.append(chromaticity(frame.aligned, SKIN))
        background.append(chromaticity(frame.aligned, BACKGROUND))
        shown.append(emitted(challenge.colours[step]))
    if len(shown) < MIN_BASELINE or len({tuple(colour) for colour in shown}) < 2:
        return LightCheck(usable=False)
    return LightCheck(usable=True, r_skin=correlation(skin, shown), r_background=correlation(background, shown))


def injection_signs(frames: list[Seen], signals: ClientSignals, trust_labels: bool = False) -> list[str]:
    signs = []
    if signals.automation:
        signs.append("automation")
    if signals.virtual_camera:
        signs.append("virtual_camera")
    if signals.hidden_ms > 0:
        signs.append("page_hidden")
    faces = [frame.aligned for frame in sorted(frames, key=lambda f: f.meta.t_ms) if frame.aligned is not None]
    grey = [cv2.cvtColor(face, cv2.COLOR_BGR2GRAY).astype(np.float64) for face in faces]
    changes = [float(np.abs(a - b).mean()) for a, b in itertools.pairwise(grey)]
    if not trust_labels and len(changes) >= 2 and max(changes) < STILL_FRAMES:
        signs.append("identical_frames")
    return signs
