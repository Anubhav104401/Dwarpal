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
    Image,
    QualityRules,
    align_face,
    assess,
    decode_image,
)


class FacePipeline:
    def __init__(
        self, detector: FaceDetector, age: AgeBackend, rules: QualityRules = DEFAULT_RULES, trust_labels: bool = False
    ) -> None:
        self.detector = detector
        self.age = age
        self.rules = rules
        self.trust_labels = trust_labels

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
                    flags=list(quality.flags),
                )
            )
            face = align_face(image, faces[0]) if not quality.flags else None
            seen.append(Seen(frame, reports[-1], face))
            if face is not None:
                aligned.append(face)
                weights.append(quality.detector_score * min(1.0, quality.sharpness / 200.0))
        age = self.estimate(aligned, weights) if aligned else None
        challenge = meta.challenge
        trusting = self.trust_labels
        liveness = Liveness(
            pose=pose_check(seen, challenge, trusting) if challenge else None,
            light=light_check(seen, challenge, meta.light_started_ms, meta.signals)
            if challenge and not trusting
            else None,
            injection=injection_signs(seen, meta.signals, trusting),
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
