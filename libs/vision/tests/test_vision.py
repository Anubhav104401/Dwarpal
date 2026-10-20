"""Tests for decoding, detection, alignment and quality, using a public-domain portrait (fixtures/README.md)."""

from __future__ import annotations

import dataclasses
import struct
from pathlib import Path

import cv2
import numpy as np
import pytest

from dwarpal_vision import (
    DecodeError,
    FaceDetector,
    FaceMesh,
    HandDetector,
    SpoofDetector,
    SpoofModel,
    align_face,
    assess,
    decode_image,
    image_size,
    screen_pattern,
    to_model_input,
)
from dwarpal_vision.align import template
from dwarpal_vision.hands import near_face
from dwarpal_vision.quality import people

FIXTURE = Path(__file__).parent / "fixtures" / "astronaut.jpg"
MODEL = Path(__file__).resolve().parents[3] / "models" / "third_party" / "face_detection_yunet_2023mar.onnx"
MESH = MODEL.with_name("face_landmarker.task")
HANDS = MODEL.with_name("hand_landmarker.task")
SPOOF = [
    SpoofModel(MODEL.with_name("minifasnet_v2_2.7.onnx"), 2.7),
    SpoofModel(MODEL.with_name("minifasnet_v1se_4.0.onnx"), 4.0),
]


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


def test_only_a_separate_similar_sized_face_counts_as_a_second_person(detector: FaceDetector, portrait: bytes) -> None:
    main = detector.detect(decode_image(portrait))[0]
    x, y, w, h = main.box
    shifted = dataclasses.replace(main, box=(x + 2 * w, y, w, h), score=0.9)
    inside = dataclasses.replace(main, box=(x + w / 4, y + h / 2, w / 2, h / 2), score=0.9)
    faint = dataclasses.replace(shifted, score=0.7, landmarks=main.landmarks * 0.7)
    small = dataclasses.replace(shifted, landmarks=main.landmarks * 0.3)
    assert people([main, shifted]) == 2
    assert people([main, inside]) == 1
    assert people([main, faint]) == 1
    assert people([main, small]) == 1
    assert people([]) == 0


def test_faces_become_one_rgb_batch_with_pixels_unchanged(detector: FaceDetector, portrait: bytes) -> None:
    image = decode_image(portrait)
    face = align_face(image, detector.detect(image)[0])
    batch = to_model_input([face, face[:, ::-1]])
    assert batch.shape == (2, 3, 224, 224)
    assert batch.dtype == np.float32
    assert batch.flags["C_CONTIGUOUS"]
    assert np.array_equal(batch[0, 0], face[:, :, 2].astype(np.float32))
    assert np.array_equal(batch[0, 2], face[:, :, 0].astype(np.float32))


def test_the_face_mesh_measures_a_frontal_face_and_mirrors(detector: FaceDetector, portrait: bytes) -> None:
    mesh = FaceMesh(MESH)
    image = decode_image(portrait)
    frontal = mesh.angles(image, detector.detect(image)[0])
    mirrored_image = np.ascontiguousarray(image[:, ::-1])
    mirrored = mesh.angles(mirrored_image, detector.detect(mirrored_image)[0])
    assert frontal is not None
    assert mirrored is not None
    assert abs(frontal.yaw) < 0.1
    assert 0.6 < frontal.pitch < 0.9
    assert frontal.yaw * mirrored.yaw < 0
    assert mesh.angles(np.full_like(image, 128), detector.detect(image)[0]) is None


def test_a_smaller_second_face_counts_in_the_middle_of_the_picture_but_not_at_the_side(
    detector: FaceDetector, portrait: bytes
) -> None:
    main = detector.detect(decode_image(portrait))[0]
    x, y, w, h = main.box
    beside = dataclasses.replace(
        main, box=(x + 1.5 * w, y, w * 0.4, h * 0.4), landmarks=main.landmarks * 0.4, score=0.9
    )
    assert people([main, beside], size=(600, 600)) == 2
    assert people([main, beside], size=(600, 4000)) == 1
    unsure = dataclasses.replace(main, box=(x + 2 * w, y, w * 1.2, h * 1.2), landmarks=main.landmarks * 1.2, score=0.65)
    assert people([main, unsure], size=(600, 4000)) == 2


def test_hands_count_only_beside_the_face_and_none_are_found_in_the_portrait(portrait: bytes) -> None:
    face = (100.0, 100.0, 100.0, 120.0)
    assert near_face(face, [(180.0, 260.0, 60.0, 60.0), (600.0, 100.0, 60.0, 60.0)]) == 1
    assert HandDetector(HANDS).detect(decode_image(portrait)) == []


@pytest.mark.skipif(
    not all(model.path.is_file() for model in SPOOF),
    reason="made by: uv run --package dwarpal-ml python -m dwarpal_ml.antispoof",
)
def test_the_anti_spoofing_networks_take_a_real_photograph_for_a_real_face(
    detector: FaceDetector, portrait: bytes
) -> None:
    image = decode_image(portrait)
    assert SpoofDetector(SPOOF).real(image, detector.detect(image)[0]) > 0.8


def test_a_fine_regular_grid_stands_out_in_the_screen_pattern(detector: FaceDetector, portrait: bytes) -> None:
    image = decode_image(portrait)
    face = detector.detect(image)[0]
    grid = image.copy()
    grid[::3, :] = (grid[::3, :] * 0.6).astype(np.uint8)
    grid[:, ::3] = (grid[:, ::3] * 0.6).astype(np.uint8)
    assert screen_pattern(grid, face) > screen_pattern(image, face) + 0.5
