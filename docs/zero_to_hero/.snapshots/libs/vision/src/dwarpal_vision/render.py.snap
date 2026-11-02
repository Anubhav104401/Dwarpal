"""Tell a real face from a computer-rendered one (liveness level 6, ADR-0021): our own network, trained and exported by
`dwarpal_ml.render_detector`, run by OpenCV. It sees the same crop as MiniFASNet V2, which it was retaught from.
"""

from __future__ import annotations

import threading
from pathlib import Path

import cv2
import numpy as np

from dwarpal_vision.antispoof import crop
from dwarpal_vision.decode import Image
from dwarpal_vision.detect import Face

SCALE = 2.7
# The network answers two chances: [real, rendered].
RENDERED = 1


class RenderDetector:
    def __init__(self, path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(f"render detector not found: {path} (made by python -m dwarpal_ml.render_detector)")
        self._net = cv2.dnn.readNetFromONNX(str(path))
        self._lock = threading.Lock()

    def rendered(self, image: Image, face: Face) -> float:
        """How likely the face was rendered by a computer, from 0 to 1."""
        patch = crop(image, face.box, SCALE)
        # Pixels as the network was trained: blue-green-red, 0-255, channels first.
        pixels = np.ascontiguousarray(patch.astype(np.float32).transpose(2, 0, 1)[None])
        with self._lock:
            self._net.setInput(pixels)
            return float(self._net.forward().reshape(-1)[RENDERED])
