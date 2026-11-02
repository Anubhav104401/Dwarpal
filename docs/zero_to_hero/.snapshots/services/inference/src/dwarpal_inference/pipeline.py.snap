"""From a burst of frames to one FaceAnalysis: decode, detect, check quality, align, estimate, combine,
and gather the liveness evidence."""

from __future__ import annotations

import time

import numpy as np

from dwarpal_contracts import (
    MAX_FRAME_BYTES,
    POLICY_AGES,
    AgeEstimate,
    FaceAnalysis,
    FaceRequestMeta,
    FrameReport,
    Liveness,
)
from dwarpal_inference.backends import AGES, AgeBackend
from dwarpal_inference.liveness import Seen, injection_signs, light_check, pose_check
from dwarpal_vision import (
    DEFAULT_RULES,
    DecodeError,
    FaceDetector,
    FaceMesh,
    HandDetector,
    Image,
    QualityRules,
    RenderDetector,
    SpoofDetector,
    align_face,
    assess,
    decode_image,
    screen_pattern,
)
from dwarpal_vision.hands import near_face


def sharpest(weights: list[float], count: int) -> list[int]:
    """The positions of the `count` best-weighted frames, best first; ties keep their order."""
    return sorted(range(len(weights)), key=lambda i: -weights[i])[:count]


def median_of(values: list[float | None]) -> float | None:
    measured = [value for value in values if value is not None]
    return float(np.median(measured)) if measured else None


class FacePipeline:
    def __init__(
        self,
        detector: FaceDetector,
        age: AgeBackend,
        rules: QualityRules = DEFAULT_RULES,
        mesh: FaceMesh | None = None,
        hands: HandDetector | None = None,
        spoof: SpoofDetector | None = None,
        render: RenderDetector | None = None,
        trust_labels: bool = False,
        age_frames: int = 3,
    ) -> None:
        self.detector = detector
        self.age = age
        self.rules = rules
        self.mesh = mesh
        self.hands = hands
        self.spoof = spoof
        self.render = render
        self.trust_labels = trust_labels
        self.age_frames = age_frames

    def analyze(self, meta: FaceRequestMeta, images: list[bytes]) -> FaceAnalysis:
        started = time.perf_counter()
        reports: list[FrameReport] = []
        aligned: list[Image] = []
        weights: list[float] = []
        seen: list[Seen] = []
        for frame, data in zip(meta.frames, images, strict=True):
            try:
                image = decode_image(data, max_bytes=MAX_FRAME_BYTES)
            except DecodeError:
                reports.append(
                    FrameReport(
                        index=frame.index,
                        faces=0,
                        detector_score=0.0,
                        brightness=0.0,
                        sharpness=0.0,
                        eye_distance_px=0.0,
                        yaw_ratio=0.0,
                        flags=["undecodable"],
                    )
                )
                seen.append(Seen(frame, reports[-1], None))
                continue
            faces = self.detector.detect(image)
            quality = assess(image, faces, self.rules)
            head = self.mesh.angles(image, faces[0]) if self.mesh is not None and faces else None
            nearby = near_face(faces[0].box, self.hands.detect(image)) if self.hands is not None and faces else 0
            one = quality.faces == 1
            real = self.spoof.real(image, faces[0]) if self.spoof is not None and one else None
            pattern = screen_pattern(image, faces[0]) if one else None
            rendered = self.render.rendered(image, faces[0]) if self.render is not None and one else None
            reports.append(
                FrameReport(
                    index=frame.index,
                    faces=quality.faces,
                    detector_score=quality.detector_score,
                    brightness=quality.brightness,
                    sharpness=quality.sharpness,
                    eye_distance_px=quality.eye_distance_px,
                    yaw_ratio=quality.yaw_ratio,
                    pitch_ratio=quality.pitch_ratio,
                    mesh_yaw=None if head is None else head.yaw,
                    mesh_pitch=None if head is None else head.pitch,
                    hands_near_face=nearby,
                    real_score=real,
                    screen_pattern=pattern,
                    rendered_score=rendered,
                    flags=list(quality.flags),
                )
            )
            # Liveness looks at every photo of exactly one person: a turned head, or a face darkened by the screen's
            # blue, is exactly what its checks expect. The age is estimated from flawless photos only.
            face = align_face(image, faces[0]) if quality.faces == 1 else None
            seen.append(Seen(frame, reports[-1], face))
            if face is not None and not quality.flags:
                aligned.append(face)
                weights.append(quality.detector_score * min(1.0, quality.sharpness / 200.0))
        # The age model is by far the costliest step (§5.7.4): it sees only the sharpest few flawless frames. Every
        # flawless frame still counts as usable, and liveness still sees them all.
        best = sharpest(weights, self.age_frames)
        age = self.estimate([aligned[i] for i in best], [weights[i] for i in best]) if aligned else None
        challenge = meta.challenge
        trusting = self.trust_labels
        liveness = Liveness(
            pose=pose_check(seen, challenge, trusting) if challenge else None,
            light=light_check(seen, challenge, meta.light_started_ms, meta.signals)
            if challenge and not trusting
            else None,
            injection=injection_signs(seen, meta.signals, trusting),
            presentation=median_of([r.real_score for r in reports]) if not trusting else None,
            screen_pattern=median_of([r.screen_pattern for r in reports]) if not trusting else None,
            rendered=median_of([r.rendered_score for r in reports]) if not trusting else None,
            evidence="labels" if trusting else "images",
        )
        elapsed = (time.perf_counter() - started) * 1000.0
        return FaceAnalysis(
            model_version=self.age.version,
            frames=reports,
            usable_frames=len(aligned),
            age=age,
            duration_ms=elapsed,
            liveness=liveness,
        )

    def estimate(self, aligned: list[Image], weights: list[float]) -> AgeEstimate:
        rows = self.age.predict(aligned)
        share = np.asarray(weights, dtype=np.float64)
        share = share / share.sum() if share.sum() > 0 else np.full(len(rows), 1.0 / len(rows))
        mixture = (rows * share[:, None]).sum(axis=0)
        mean = float((mixture * AGES).sum())
        std = float(np.sqrt((mixture * (AGES - mean) ** 2).sum()))
        p_over = {age: float(np.clip(mixture[age:].sum(), 0.0, 1.0)) for age in POLICY_AGES}
        frame_means = [float((row * AGES).sum()) for row in rows]
        return AgeEstimate(mean=mean, std=std, p_over=p_over, frame_means=frame_means)
