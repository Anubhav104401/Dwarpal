"""Head angles from MediaPipe's 478-point face mesh (Apache-2.0), run by OpenCV from the pinned face landmarker bundle.

The five points YuNet finds measure a turn well but looking up poorly; the mesh places the eye corners, nose tip and
mouth corners far more precisely. The angles use the verify page's formulas (`apps/web/lib/challenge.ts`), so the page's
meter and the server measure the same thing.
"""

from __future__ import annotations

import tempfile
import threading
import zipfile
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from dwarpal_vision.decode import Image
from dwarpal_vision.detect import Face

MODEL_IN_BUNDLE = "face_landmarks_detector.tflite"
SIZE = 256
# The mesh model expects the face in the middle of a square a little larger than the face itself.
MARGIN = 1.5
RIGHT_EYE, LEFT_EYE, NOSE, MOUTH = (33, 133), (362, 263), (1,), (61, 291)


@dataclass(frozen=True)
class HeadAngles:
    yaw: float
    pitch: float


def centre(points: NDArray[np.float32], indices: tuple[int, ...]) -> NDArray[np.float32]:
    return np.asarray(points[list(indices), :2].mean(axis=0), dtype=np.float32)


def angles_from(points: NDArray[np.float32]) -> HeadAngles:
    right, left = centre(points, RIGHT_EYE), centre(points, LEFT_EYE)
    nose, mouth = centre(points, NOSE), centre(points, MOUTH)
    eyes = (right + left) / 2
    eye_distance = max(float(np.linalg.norm(left - right)), 1e-6)
    drop = max(float(mouth[1] - eyes[1]), 1e-6)
    return HeadAngles(float((nose[0] - eyes[0]) / eye_distance), float((nose[1] - eyes[1]) / drop))


class FaceMesh:
    def __init__(self, bundle_path: Path) -> None:
        if not bundle_path.is_file():
            raise FileNotFoundError(f"face landmarker not found: {bundle_path} (run infra/scripts/fetch_models.py)")
        # Unpacked to a temporary folder because OpenCV honours the engine choice only when loading from a file. The
        # classic engine is needed: OpenCV 5's new engine returns only the model's last output, not the 478 points.
        with tempfile.TemporaryDirectory() as folder, zipfile.ZipFile(bundle_path) as bundle:
            model = Path(folder) / MODEL_IN_BUNDLE
            model.write_bytes(bundle.read(MODEL_IN_BUNDLE))
            self._net = cv2.dnn.readNetFromTFLite(str(model), cv2.dnn.ENGINE_CLASSIC)
        self._outputs = list(self._net.getUnconnectedOutLayersNames())
        self._lock = threading.Lock()

    def angles(self, image: Image, face: Face) -> HeadAngles | None:
        """The head's angles for a detected face, or None when the mesh model doesn't see a face in the crop."""
        x, y, w, h = face.box
        side = max(w, h) * MARGIN
        left, top = round(x + w / 2 - side / 2), round(y + h / 2 - side / 2)
        size = max(round(side), 1)
        # Pad with black where the square reaches past the picture's edge, so the face stays centred and unstretched.
        height, width = image.shape[:2]
        pad = max(0, -left, -top, left + size - width, top + size - height)
        padded = cv2.copyMakeBorder(image, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        crop = padded[top + pad : top + pad + size, left + pad : left + pad + size]
        rgb = cv2.cvtColor(cv2.resize(crop, (SIZE, SIZE), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        blob = np.ascontiguousarray(rgb.astype(np.float32).transpose(2, 0, 1)[None] / 255.0)
        with self._lock:
            self._net.setInput(blob)
            presence, points, _ = self._net.forward(self._outputs)
        if float(presence.reshape(-1)[0]) <= 0.0:
            return None
        return angles_from(np.asarray(points, dtype=np.float32).reshape(478, 3))
