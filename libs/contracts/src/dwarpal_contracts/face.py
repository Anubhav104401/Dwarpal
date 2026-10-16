"""Messages exchanged between the API and the inference service about a face attempt.

Nothing in these models can hold an image: only numbers, flags and short texts.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Probability = Annotated[float, Field(ge=0.0, le=1.0)]
POLICY_AGES = (13, 16, 18, 21, 25)
MAX_FRAMES = 16
MAX_FRAME_BYTES = 512 * 1024


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FrameMeta(Contract):
    index: Annotated[int, Field(ge=0, le=31)]
    t_ms: Annotated[float, Field(ge=0.0)]
    phase: Annotated[str, Field(max_length=32)] = "baseline"


class FaceRequestMeta(Contract):
    frames: Annotated[list[FrameMeta], Field(min_length=1, max_length=MAX_FRAMES)]


class FrameReport(Contract):
    index: int
    faces: int
    detector_score: Probability
    brightness: Probability
    sharpness: Annotated[float, Field(ge=0.0)]
    eye_distance_px: Annotated[float, Field(ge=0.0)]
    yaw_ratio: float
    flags: list[str]

    @property
    def usable(self) -> bool:
        return not self.flags


class AgeEstimate(Contract):
    mean: Annotated[float, Field(ge=0.0, le=100.0)]
    std: Annotated[float, Field(ge=0.0)]
    p_over: dict[int, Probability]
    frame_means: list[float]


class FaceAnalysis(Contract):
    model_version: str
    frames: list[FrameReport]
    usable_frames: Annotated[int, Field(ge=0)]
    age: AgeEstimate | None
    duration_ms: Annotated[float, Field(ge=0.0)]
