"""Decide whether a frame is good enough to judge: one clear face, enough light, sharp, large and frontal."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from dwarpal_vision.decode import Image
from dwarpal_vision.detect import Face


@dataclass(frozen=True)
class QualityRules:
    min_detector_score: float = 0.8
    min_brightness: float = 0.22
    max_brightness: float = 0.92
    min_sharpness: float = 30.0
    min_eye_distance: float = 40.0
    max_yaw_ratio: float = 0.25


DEFAULT_RULES = QualityRules()


@dataclass(frozen=True)
class Quality:
    faces: int
    detector_score: float
    brightness: float
    sharpness: float
    eye_distance_px: float
    yaw_ratio: float
    flags: tuple[str, ...]
    pitch_ratio: float = 0.0


def face_region(image: Image, face: Face) -> Image:
    x, y, w, h = face.box
    height, width = image.shape[:2]
    left, top = max(0, int(x)), max(0, int(y))
    right, bottom = min(width, int(x + w)), min(height, int(y + h))
    return image[top:bottom, left:right]


def yaw_ratio(face: Face) -> float:
    right_eye, left_eye, nose = face.landmarks[0], face.landmarks[1], face.landmarks[2]
    eyes_mid_x = (right_eye[0] + left_eye[0]) / 2.0
    return float((nose[0] - eyes_mid_x) / max(face.eye_distance, 1.0))


def pitch_ratio(face: Face) -> float:
    eyes_mid_y = (face.landmarks[0][1] + face.landmarks[1][1]) / 2.0
    mouth_mid_y = (face.landmarks[3][1] + face.landmarks[4][1]) / 2.0
    return float((face.landmarks[2][1] - eyes_mid_y) / max(mouth_mid_y - eyes_mid_y, 1.0))


def people(faces: list[Face], rules: QualityRules = DEFAULT_RULES) -> int:
    """How many different people the detections show. A detection counts beside the main face only if it is confident,
    lies outside the main face's box, and is at least half its size: the detector sometimes boxes part of the same
    face a second time (a beard, a lit cheek), or a faint shape far in the background."""
    if not faces:
        return 0
    main = faces[0]
    x, y, w, h = main.box
    others = [
        face
        for face in faces[1:]
        if face.score >= rules.min_detector_score
        and face.eye_distance >= 0.5 * main.eye_distance
        and not (x <= face.box[0] + face.box[2] / 2 <= x + w and y <= face.box[1] + face.box[3] / 2 <= y + h)
    ]
    return 1 + len(others)


def assess(image: Image, faces: list[Face], rules: QualityRules = DEFAULT_RULES) -> Quality:
    if not faces:
        return Quality(0, 0.0, 0.0, 0.0, 0.0, 0.0, ("no_face",))
    face = faces[0]
    count = people(faces, rules)
    region = face_region(image, face)
    if region.size == 0:
        return Quality(count, face.score, 0.0, 0.0, 0.0, 0.0, ("no_face",))
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean()) / 255.0
    small = cv2.resize(gray, (112, 112), interpolation=cv2.INTER_AREA)
    sharpness = float(cv2.Laplacian(small, cv2.CV_64F).var())
    yaw = yaw_ratio(face)
    checks = {
        "multiple_faces": count > 1,
        "low_confidence": face.score < rules.min_detector_score,
        "too_dark": brightness < rules.min_brightness,
        "too_bright": brightness > rules.max_brightness,
        "too_blurry": sharpness < rules.min_sharpness,
        "face_too_small": face.eye_distance < rules.min_eye_distance,
        "not_frontal": abs(yaw) > rules.max_yaw_ratio,
    }
    flags = tuple(name for name, failed in checks.items() if failed)
    return Quality(
        count,
        face.score,
        float(np.clip(brightness, 0.0, 1.0)),
        sharpness,
        face.eye_distance,
        yaw,
        flags,
        pitch_ratio(face),
    )
