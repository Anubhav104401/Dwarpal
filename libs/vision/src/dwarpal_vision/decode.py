"""Turn uploaded bytes into a picture, refusing anything unexpected before a single pixel is decoded."""

from __future__ import annotations

import struct

import cv2
import numpy as np
from numpy.typing import NDArray

MAX_BYTES = 512 * 1024
MAX_SIDE = 1920
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_FRAME_MARKERS = frozenset({0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF})

type Image = NDArray[np.uint8]


class DecodeError(ValueError):
    """The bytes are not an image we are willing to decode."""


def image_size(data: bytes) -> tuple[int, int]:
    if data.startswith(PNG_MAGIC) and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return int(width), int(height)
    if data.startswith(JPEG_MAGIC):
        pos = 2
        while pos + 9 <= len(data):
            if data[pos] != 0xFF:
                raise DecodeError("corrupt JPEG: expected a marker")
            marker = data[pos + 1]
            if marker == 0xFF:
                pos += 1
                continue
            if marker in JPEG_FRAME_MARKERS:
                height, width = struct.unpack(">HH", data[pos + 5 : pos + 9])
                return int(width), int(height)
            (length,) = struct.unpack(">H", data[pos + 2 : pos + 4])
            pos += 2 + length
        raise DecodeError("corrupt JPEG: no frame header")
    raise DecodeError("only JPEG and PNG images are accepted")


def decode_image(data: bytes, max_bytes: int = MAX_BYTES, max_side: int = MAX_SIDE) -> Image:
    if not data or len(data) > max_bytes:
        raise DecodeError(f"image must be between 1 byte and {max_bytes} bytes")
    width, height = image_size(data)
    if not (0 < width <= max_side and 0 < height <= max_side):
        raise DecodeError(f"image is {width}x{height}; at most {max_side} pixels per side are allowed")
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise DecodeError("image data could not be decoded")
    return np.asarray(image, dtype=np.uint8)
