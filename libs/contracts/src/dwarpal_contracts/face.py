"""Messages exchanged between the API and the inference service about a face attempt.

Nothing in these models can hold an image: only numbers, flags and short texts.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Probability = Annotated[float, Field(ge=0.0, le=1.0)]
POLICY_AGES = (13, 16, 18, 21, 25)
MAX_FRAMES = 16
MAX_FRAME_BYTES = 512 * 1024
type Pose = Literal["turn_left", "turn_right", "look_up"]
POSES: tuple[Pose, ...] = ("turn_left", "turn_right", "look_up")
type Phase = Literal["baseline", "turn_left", "turn_right", "look_up"]
Colour = Annotated[str, Field(pattern=r"^#[0-9a-f]{6}$")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FrameMeta(Contract):
    index: Annotated[int, Field(ge=0, le=31)]
    t_ms: Annotated[float, Field(ge=0.0)]
    phase: Phase = "baseline"


class Challenge(Contract):
    """What the server asked for: head poses in order, and screen colours shown step_ms apart."""

    poses: Annotated[list[Pose], Field(min_length=1, max_length=4)]
    colours: Annotated[list[Colour], Field(min_length=2, max_length=8)]
    step_ms: Annotated[int, Field(ge=400, le=2000)]


class ClientSignals(Contract):
    """What the browser reports about itself. Never trusted on its own: one input among many."""

    automation: bool = False
    virtual_camera: bool = False
    hidden_ms: Annotated[float, Field(ge=0.0)] = 0.0
    light_shown: bool = True


class FaceRequestMeta(Contract):
    frames: Annotated[list[FrameMeta], Field(min_length=1, max_length=MAX_FRAMES)]
    light_started_ms: Annotated[float, Field(ge=0.0)] | None = None
    signals: ClientSignals = ClientSignals()
    challenge: Challenge | None = None


class FrameReport(Contract):
    index: int
    faces: int
    detector_score: Probability
    brightness: Probability
    sharpness: Annotated[float, Field(ge=0.0)]
    eye_distance_px: Annotated[float, Field(ge=0.0)]
    yaw_ratio: float
    pitch_ratio: float = 0.0
    # The same two angles from the 478-point face mesh, which measures looking up far better; None when not measured.
    mesh_yaw: float | None = None
    mesh_pitch: float | None = None
    # Hands found next to the face: someone may be holding a phone or a photo up to the camera.
    hands_near_face: Annotated[int, Field(ge=0)] = 0
    # Presentation-attack evidence: how likely a real face rather than a photo or a screen (MiniFASNet), and how strong
    # a screen's regular pixel pattern is in the face. None when not measured.
    real_score: Probability | None = None
    screen_pattern: float | None = None
    # How likely the face was rendered by a computer (liveness level 6, ADR-0021); None without a trained model.
    rendered_score: Probability | None = None
    flags: list[str]

    @property
    def usable(self) -> bool:
        return not self.flags


class AgeEstimate(Contract):
    mean: Annotated[float, Field(ge=0.0, le=100.0)]
    std: Annotated[float, Field(ge=0.0)]
    p_over: dict[int, Probability]
    frame_means: list[float]


class PoseCheck(Contract):
    passed: bool
    problems: list[str]
    # Measurements for setting the limits from genuine attempts: the person's own frontal angles, and for each pose
    # asked for, the furthest any of its frames moved from them in that direction (None: no face to measure).
    baseline_yaw: float | None = None
    baseline_pitch: float | None = None
    reached: list[tuple[Pose, float | None]] = []
    measured_by: Literal["mesh", "five_points"] = "five_points"
    # For each pose, whether a photo caught the head on its way there: a real head passes through the angles between.
    gradual: list[tuple[Pose, bool]] = []


class LightCheck(Contract):
    usable: bool
    # False when the page showed no colours (the person's device asks for reduced motion): nothing could be measured.
    shown: bool = True
    r_skin: Annotated[float, Field(ge=-1.0, le=1.0)] | None = None
    r_background: Annotated[float, Field(ge=-1.0, le=1.0)] | None = None


class Liveness(Contract):
    pose: PoseCheck | None
    light: LightCheck | None
    injection: list[str]
    # Medians over the photos of one person: the anti-spoofing networks' "real face" chance, and the screen pattern.
    presentation: Probability | None = None
    screen_pattern: float | None = None
    # The render detector's median "rendered" chance: recorded only, deciding nothing until it is measured.
    rendered: Probability | None = None
    # "images": measured from the frames. "labels": the frames' phase labels were trusted instead — a test mode,
    # possible only with the stand-in age model, and never accepted for a live session.
    evidence: Literal["images", "labels"] = "images"


class FaceAnalysis(Contract):
    model_version: str
    frames: list[FrameReport]
    usable_frames: Annotated[int, Field(ge=0)]
    age: AgeEstimate | None
    duration_ms: Annotated[float, Field(ge=0.0)]
    liveness: Liveness | None = None
