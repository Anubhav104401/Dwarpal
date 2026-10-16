"""Straighten and crop a face so that the eyes, nose and mouth always land in the same places."""

from __future__ import annotations

import cv2
import numpy as np

from dwarpal_vision.decode import Image
from dwarpal_vision.detect import Face

TEMPLATE_112 = np.array(
    [[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366], [41.5493, 92.3655], [70.7299, 92.2041]],
    dtype=np.float32,
)


def template(size: int, margin: float) -> np.ndarray:
    scale = size / 112.0 * (1.0 - margin)
    return (TEMPLATE_112 - 56.0) * scale + size / 2.0


def align_face(image: Image, face: Face, size: int = 224, margin: float = 0.25) -> Image:
    matrix, _ = cv2.estimateAffinePartial2D(face.landmarks, template(size, margin), method=cv2.LMEDS)
    if matrix is None:
        raise ValueError("face landmarks are degenerate; cannot align")
    aligned = cv2.warpAffine(image, matrix, (size, size), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return np.asarray(aligned, dtype=np.uint8)
