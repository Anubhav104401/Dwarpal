"""Compare two faces with SFace, OpenCV Zoo's face recogniser (Apache-2.0): is the person in the selfie the person in
the document's photo? Each face becomes 128 numbers (an *embedding*) in memory; the two are compared and then dropped.
Nothing is stored, and the numbers can't be turned back into a face."""

from __future__ import annotations

import threading
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from dwarpal_vision.decode import Image
from dwarpal_vision.detect import Face

# OpenCV's published threshold for SFace's cosine similarity: at or above it, the same person (its accuracy on LFW is
# 99.4 %). Our own use — a printed, often older, photo against a webcam — is harder, and isn't measured yet.
SAME_PERSON = 0.363


class FaceMatcher:
    def __init__(self, model_path: Path) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(
                f"face recogniser model not found: {model_path} (run infra/scripts/fetch_models.py)"
            )
        self._model = cv2.FaceRecognizerSF.create(str(model_path), "")
        self._lock = threading.Lock()

    def embed(self, image: Image, face: Face) -> NDArray[np.float32]:
        """Line the face up as SFace expects (eyes level, 112 by 112 pixels), using YuNet's five landmarks, and turn it
        into its embedding."""
        row = np.array([*face.box, *face.landmarks.reshape(-1), face.score], dtype=np.float32)
        with self._lock:
            aligned = self._model.alignCrop(image, row)
            return np.asarray(self._model.feature(aligned), dtype=np.float32).reshape(-1)

    def similarity(self, one: NDArray[np.float32], other: NDArray[np.float32]) -> float:
        """Cosine similarity: 1 for the same direction, about 0 for unrelated faces."""
        return float(np.dot(one, other) / (np.linalg.norm(one) * np.linalg.norm(other) + 1e-12))
