"""Find hands with MediaPipe's palm detector (Apache-2.0), run by OpenCV from the pinned hand landmarker bundle.

Liveness uses it to notice a hand next to the face: someone holding a phone or a photo up to the camera.
"""

from __future__ import annotations

import tempfile
import threading
import zipfile
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from dwarpal_vision.decode import Image

MODEL_IN_BUNDLE = "hand_detector.tflite"
SIZE = 192
# The detector's fixed grid of candidate boxes: 2 per cell of a 24 x 24 grid, then 6 per cell of a 12 x 12 grid.
GRIDS = ((24, 2), (12, 6))
MIN_SCORE = 0.5

type Box = tuple[float, float, float, float]


def anchors() -> NDArray[np.float32]:
    centres = [
        ((x + 0.5) / cells, (y + 0.5) / cells)
        for cells, per_cell in GRIDS
        for y in range(cells)
        for x in range(cells)
        for _ in range(per_cell)
    ]
    return np.asarray(centres, dtype=np.float32)


ANCHORS = anchors()


class HandDetector:
    def __init__(self, bundle_path: Path) -> None:
        if not bundle_path.is_file():
            raise FileNotFoundError(f"hand landmarker not found: {bundle_path} (run infra/scripts/fetch_models.py)")
        # As for the face mesh: OpenCV honours the classic engine, which returns every output, only from a file.
        with tempfile.TemporaryDirectory() as folder, zipfile.ZipFile(bundle_path) as bundle:
            model = Path(folder) / MODEL_IN_BUNDLE
            model.write_bytes(bundle.read(MODEL_IN_BUNDLE))
            self._net = cv2.dnn.readNetFromTFLite(str(model), cv2.dnn.ENGINE_CLASSIC)
        self._outputs = list(self._net.getUnconnectedOutLayersNames())
        self._lock = threading.Lock()

    def detect(self, image: Image) -> list[Box]:
        """Hands in the picture, as boxes (left, top, width, height) in pixels, most confident first."""
        height, width = image.shape[:2]
        side = max(height, width)
        # Letterbox: pad the picture to a square, so hands keep their shape when it is shrunk to 192 x 192.
        square = cv2.copyMakeBorder(image, 0, side - height, 0, side - width, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        rgb = cv2.cvtColor(cv2.resize(square, (SIZE, SIZE), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
        blob = np.ascontiguousarray(rgb.astype(np.float32).transpose(2, 0, 1)[None] / 255.0)
        with self._lock:
            self._net.setInput(blob)
            raw = dict(zip(self._outputs, self._net.forward(self._outputs), strict=True))
        scores = next(v for v in raw.values() if v.shape[-1] == 1).reshape(-1)
        boxes = next(v for v in raw.values() if v.shape[-1] == 18).reshape(-1, 18)
        chances = 1.0 / (1.0 + np.exp(-np.clip(scores, -80.0, 80.0)))
        found: list[Box] = []
        for i in np.argsort(-chances):
            if chances[i] < MIN_SCORE:
                break
            cx = (boxes[i, 0] / SIZE + ANCHORS[i, 0]) * side
            cy = (boxes[i, 1] / SIZE + ANCHORS[i, 1]) * side
            w, h = boxes[i, 2] / SIZE * side, boxes[i, 3] / SIZE * side
            box = (float(cx - w / 2), float(cy - h / 2), float(w), float(h))
            if all(overlap(box, kept) < 0.3 for kept in found):
                found.append(box)
        return found


def near_face(face: Box, hands: list[Box]) -> int:
    """How many hands are next to the face: centred within one face-size of it, on any side."""
    x, y, w, h = face
    return sum(
        1
        for hx, hy, hw, hh in hands
        if abs(hx + hw / 2 - (x + w / 2)) <= 1.5 * w and abs(hy + hh / 2 - (y + h / 2)) <= 1.5 * h
    )


def overlap(a: Box, b: Box) -> float:
    """How much two boxes overlap: the shared area over the combined area (0 = apart, 1 = the same box)."""
    left, top = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[0] + a[2], b[0] + b[2]), min(a[1] + a[3], b[1] + b[3])
    shared = max(0.0, right - left) * max(0.0, bottom - top)
    return shared / max(a[2] * a[3] + b[2] * b[3] - shared, 1e-6)
