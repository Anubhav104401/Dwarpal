"""Tests for decoding, detection, alignment and quality, using a public-domain portrait (fixtures/README.md)."""

from __future__ import annotations

import struct
from pathlib import Path

import cv2
import numpy as np
import pytest

from dwarpal_vision import DecodeError, FaceDetector, align_face, assess, decode_image, image_size, to_model_input
from dwarpal_vision.align import template

FIXTURE = Path(__file__).parent / "fixtures" / "astronaut.jpg"
MODEL = Path(__file__).resolve().parents[3] / "models" / "third_party" / "face_detection_yunet_2023mar.onnx"


def png_header(width: int, height: int) -> bytes:
    return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + struct.pack(">II", width, height) + b"\x08\x02\x00\x00\x00"


@pytest.fixture(scope="module")
def detector() -> FaceDetector:
    return FaceDetector(MODEL)


@pytest.fixture(scope="module")
def portrait() -> bytes:
    return FIXTURE.read_bytes()


def test_image_size_reads_headers_without_decoding(portrait: bytes) -> None:
    assert image_size(portrait) == (512, 512)
    assert image_size(png_header(640, 480)) == (640, 480)


def test_decode_refuses_other_formats_oversized_files_and_decompression_bombs() -> None:
    with pytest.raises(DecodeError, match="only JPEG and PNG"):
        decode_image(b"GIF89a-not-welcome")
    with pytest.raises(DecodeError, match="50000x50000"):
        decode_image(png_header(50_000, 50_000))
    with pytest.raises(DecodeError, match="between 1 byte and 100 bytes"):
        decode_image(bytes(101), max_bytes=100)


def test_detector_finds_exactly_one_clear_face(detector: FaceDetector, portrait: bytes) -> None:
    faces = detector.detect(decode_image(portrait))
    assert len(faces) == 1
    assert faces[0].score > 0.8
    assert faces[0].eye_distance > 40


def test_alignment_puts_the_eyes_where_the_template_says(detector: FaceDetector, portrait: bytes) -> None:
    image = decode_image(portrait)
    aligned = align_face(image, detector.detect(image)[0])
    assert aligned.shape == (224, 224, 3)
    again = detector.detect(aligned)
    assert again, "the aligned crop must still contain a detectable face"
    eye_error = np.abs(again[0].landmarks[:2] - template(224, 0.25)[:2]).max()
    assert eye_error < 8.0


def test_quality_accepts_a_good_frame_and_names_what_is_wrong_with_bad_ones(
    detector: FaceDetector, portrait: bytes
) -> None:
    image = decode_image(portrait)
    faces = detector.detect(image)
    assert assess(image, faces).flags == ()
    dark = (image * 0.12).astype(np.uint8)
    assert "too_dark" in assess(dark, faces).flags
    blurred = np.asarray(cv2.GaussianBlur(image, (0, 0), 6), dtype=np.uint8)
    assert "too_blurry" in assess(blurred, faces).flags
    assert assess(image, []).flags == ("no_face",)


def test_faces_become_one_rgb_batch_with_pixels_unchanged(detector: FaceDetector, portrait: bytes) -> None:
    image = decode_image(portrait)
    face = align_face(image, detector.detect(image)[0])
    batch = to_model_input([face, face[:, ::-1]])
    assert batch.shape == (2, 3, 224, 224)
    assert batch.dtype == np.float32
    assert batch.flags["C_CONTIGUOUS"]
    assert np.array_equal(batch[0, 0], face[:, :, 2].astype(np.float32))
    assert np.array_equal(batch[0, 2], face[:, :, 0].astype(np.float32))
