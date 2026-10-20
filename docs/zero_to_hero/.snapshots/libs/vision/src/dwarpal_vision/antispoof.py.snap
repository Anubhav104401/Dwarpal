"""Tell a real face from a photo or a screen held up to the camera: MiniFASNet (Apache-2.0), two small networks trained
to spot presentation attacks, each looking at a differently sized crop around the face. Run by OpenCV from ONNX files
made by `dwarpal_ml.antispoof`.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from dwarpal_vision.decode import Image
from dwarpal_vision.detect import Face

SIZE = 80
# The networks answer three probabilities; the second is "a real face" (the repository's label 1).
REAL = 1


@dataclass(frozen=True)
class SpoofModel:
    """One network's file and how large a crop around the face it was trained on (2.7 or 4 face-sizes)."""

    path: Path
    scale: float


def crop(image: Image, box: tuple[float, float, float, float], scale: float) -> Image:
    """The crop the networks were trained on: a box `scale` times the face, centred on it, slid back inside the picture
    where it would cross an edge (never stretched), resized to 80 x 80."""
    height, width = image.shape[:2]
    x, y, w, h = box
    scale = min((height - 1) / max(h, 1.0), (width - 1) / max(w, 1.0), scale)
    new_w, new_h = w * scale, h * scale
    left, top = x + w / 2 - new_w / 2, y + h / 2 - new_h / 2
    left = min(max(left, 0.0), width - 1 - new_w)
    top = min(max(top, 0.0), height - 1 - new_h)
    patch = image[int(top) : int(top + new_h) + 1, int(left) : int(left + new_w) + 1]
    return np.asarray(cv2.resize(patch, (SIZE, SIZE)), dtype=np.uint8)


def screen_pattern(image: Image, face: Face) -> float:
    """How strongly a regular fine pattern stands out in the middle of the face: the brightest spot of its fine-detail
    spectrum against the typical one. Re-filming a screen leaves a grid of pixels and moiré stripes there; skin doesn't.
    Measured on the picture as it came, never resized, which would smooth the pattern away."""
    x, y, w, h = face.box
    height, width = image.shape[:2]
    left, top = max(0, int(x + 0.2 * w)), max(0, int(y + 0.2 * h))
    right, bottom = min(width, int(x + 0.8 * w)), min(height, int(y + 0.8 * h))
    grey = cv2.cvtColor(image[top:bottom, left:right], cv2.COLOR_BGR2GRAY).astype(np.float64)
    if min(grey.shape) < 32:
        return 0.0
    grey -= grey.mean()
    window = np.outer(np.hanning(grey.shape[0]), np.hanning(grey.shape[1]))
    spectrum = np.abs(np.fft.fftshift(np.fft.fft2(grey * window)))
    rows, cols = np.indices(spectrum.shape)
    radius = np.hypot(
        (rows - spectrum.shape[0] / 2) / spectrum.shape[0], (cols - spectrum.shape[1] / 2) / spectrum.shape[1]
    )
    fine = spectrum[(radius > 0.15) & (radius < 0.5)]
    return float(np.log10(np.percentile(fine, 99.9) / max(float(np.median(fine)), 1e-9)))


class SpoofDetector:
    def __init__(self, models: list[SpoofModel]) -> None:
        missing = [str(model.path) for model in models if not model.path.is_file()]
        if missing:
            raise FileNotFoundError(
                f"anti-spoofing model not found: {', '.join(missing)} (run python -m dwarpal_ml.antispoof)"
            )
        self._nets = [(cv2.dnn.readNetFromONNX(str(model.path)), model.scale) for model in models]
        self._lock = threading.Lock()

    def real(self, image: Image, face: Face) -> float:
        """How likely the face is a real one in front of the camera, from 0 to 1: the networks' average."""
        chances = []
        with self._lock:
            for net, scale in self._nets:
                patch = crop(image, face.box, scale)
                # Pixels as the networks were trained: blue-green-red, 0-255, channels first.
                net.setInput(np.ascontiguousarray(patch.astype(np.float32).transpose(2, 0, 1)[None]))
                chances.append(float(net.forward().reshape(-1)[REAL]))
        return float(np.mean(chances))
