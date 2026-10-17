"""Aligned faces in, an age model's input out: the one conversion that training's checks and serving share."""

from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np
from numpy.typing import NDArray

from dwarpal_vision.decode import Image


def to_model_input(faces: Sequence[Image]) -> NDArray[np.float32]:
    """OpenCV's blue-green-red faces, each height x width x 3, become one red-green-blue batch shaped
    (faces, 3, height, width), with pixel values still 0-255: the model scales them itself."""
    rgb = np.stack([cv2.cvtColor(face, cv2.COLOR_BGR2RGB) for face in faces]).astype(np.float32)
    return np.ascontiguousarray(rgb.transpose(0, 3, 1, 2))
