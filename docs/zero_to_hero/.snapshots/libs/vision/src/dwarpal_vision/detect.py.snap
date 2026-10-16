"""Find faces with YuNet, a small and fast face detector from the OpenCV model zoo (MIT licence)."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import cv2
import numpy as np
from numpy.typing import NDArray

from dwarpal_vision.decode import Image


@dataclass(frozen=True)
class Face:
    box: tuple[float, float, float, float]
    landmarks: NDArray[np.float32]
    score: float

    @property
    def eye_distance(self) -> float:
        return float(np.linalg.norm(self.landmarks[0] - self.landmarks[1]))


class FaceDetector:
    def __init__(self, model_path: Path, score_threshold: float = 0.6) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(f"face detector model not found: {model_path} (run infra/scripts/fetch_models.py)")
        self._detector = cv2.FaceDetectorYN.create(str(model_path), "", (320, 320), score_threshold)
        self._lock = threading.Lock()

    def detect(self, image: Image) -> list[Face]:
        height, width = image.shape[:2]
        with self._lock:
            self._detector.setInputSize((width, height))
            found = cast("NDArray[np.float32] | None", self._detector.detect(image)[1])
        if found is None:
            return []
        faces = []
        for row in found:
            x, y, w, h = (float(v) for v in row[:4])
            landmarks = np.asarray(row[4:14], dtype=np.float32).reshape(5, 2)
            faces.append(Face(box=(x, y, w, h), landmarks=landmarks, score=float(row[14])))
        return sorted(faces, key=lambda face: face.score, reverse=True)
