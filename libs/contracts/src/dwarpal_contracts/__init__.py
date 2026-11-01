"""Data models shared across Dwarpal services, so their messages can never drift apart."""

from dwarpal_contracts.document import MAX_DOCUMENT_BYTES, DocumentAnalysis
from dwarpal_contracts.face import (
    MAX_FRAME_BYTES,
    MAX_FRAMES,
    POLICY_AGES,
    POSES,
    AgeEstimate,
    Challenge,
    ClientSignals,
    FaceAnalysis,
    FaceRequestMeta,
    FrameMeta,
    FrameReport,
    LightCheck,
    Liveness,
    Phase,
    Pose,
    PoseCheck,
)

__all__ = [
    "MAX_DOCUMENT_BYTES",
    "MAX_FRAMES",
    "MAX_FRAME_BYTES",
    "POLICY_AGES",
    "POSES",
    "AgeEstimate",
    "Challenge",
    "ClientSignals",
    "DocumentAnalysis",
    "FaceAnalysis",
    "FaceRequestMeta",
    "FrameMeta",
    "FrameReport",
    "LightCheck",
    "Liveness",
    "Phase",
    "Pose",
    "PoseCheck",
]
