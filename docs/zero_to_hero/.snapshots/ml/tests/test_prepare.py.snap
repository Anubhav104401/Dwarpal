"""Tests for face preparation and near-duplicate removal, using the vision library's public-domain test portrait."""

from __future__ import annotations

import zipfile
from pathlib import Path

import cv2
import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from dwarpal_ml import dedup
from dwarpal_ml.manifest import Row
from dwarpal_ml.prepare import DETECTOR, SIZE, central_face, perceptual_hash, prepare, prepare_one
from dwarpal_vision import FaceDetector, decode_image
from dwarpal_vision.detect import Face

PORTRAIT = Path(__file__).resolve().parents[2] / "libs" / "vision" / "tests" / "fixtures" / "astronaut.jpg"


@pytest.fixture(scope="module")
def detector() -> FaceDetector:
    return FaceDetector(DETECTOR)


def jpeg(image: np.ndarray, quality: int = 90) -> bytes:
    return bytes(cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])[1].tobytes())


def row(image_id: str, split: str, age_low: int = 20) -> Row:
    return Row(image_id, "d", "a.zip", image_id, age_low, age_low + 9, None, "female", "g", "CC0", split)


def test_a_face_is_aligned_to_the_serving_layout_and_fingerprinted(detector: FaceDetector) -> None:
    prepared, data = prepare_one(detector, PORTRAIT.read_bytes(), "x/1.jpg")
    assert prepared.status == "ok"
    assert prepared.faces == 1
    assert len(prepared.phash) == 16
    aligned = decode_image(data)
    assert aligned.shape == (SIZE, SIZE, 3)


def test_what_cannot_be_prepared_is_recorded_with_a_reason(detector: FaceDetector) -> None:
    assert prepare_one(detector, b"not an image", "x/1")[0].status == "undecodable"
    blank, data = prepare_one(detector, jpeg(np.full((224, 224, 3), 128, np.uint8)), "x/2")
    assert (blank.status, data) == ("no_face", b"")


def test_the_face_nearest_the_centre_is_chosen() -> None:
    image = np.zeros((200, 200, 3), np.uint8)
    corner = Face((0.0, 0.0, 40.0, 40.0), np.zeros((5, 2), np.float32), 0.99)
    centre = Face((80.0, 80.0, 40.0, 40.0), np.zeros((5, 2), np.float32), 0.7)
    assert central_face(image, [corner, centre]) is centre


def test_the_fingerprint_and_the_pixels_agree_on_a_resaved_copy_but_not_a_mirrored_one() -> None:
    portrait = decode_image(PORTRAIT.read_bytes())
    resaved = decode_image(jpeg(cv2.resize(portrait, (300, 300)), quality=60))
    mirrored = np.ascontiguousarray(portrait[:, ::-1])
    original = perceptual_hash(portrait)
    assert (original ^ perceptual_hash(resaved)).bit_count() <= dedup.SIEVE_DISTANCE
    assert (original ^ perceptual_hash(mirrored)).bit_count() > dedup.SIEVE_DISTANCE
    look = dedup.fine_detail(jpeg(portrait))
    assert dedup.similarity(look, dedup.fine_detail(jpeg(resaved))) >= dedup.MIN_SIMILARITY
    assert dedup.similarity(look, dedup.fine_detail(jpeg(mirrored))) < dedup.MIN_SIMILARITY


def test_preparing_a_dataset_writes_a_reproducible_archive(tmp_path: Path) -> None:
    with zipfile.ZipFile(tmp_path / "a.zip", "w") as source:
        source.writestr("one.jpg", PORTRAIT.read_bytes())
        source.writestr("two.jpg", b"broken")
    rows = [row("one.jpg", "train"), row("two.jpg", "test")]
    first = prepare(rows, tmp_path, tmp_path / "out" / "first.zip", workers=1)
    prepare(rows, tmp_path, tmp_path / "out" / "second.zip", workers=1)
    assert [p.status for p in first] == ["ok", "undecodable"]
    assert zipfile.ZipFile(tmp_path / "out" / "first.zip").namelist() == ["one.jpg"]
    assert (tmp_path / "out" / "first.zip").read_bytes() == (tmp_path / "out" / "second.zip").read_bytes()


@given(st.lists(st.integers(0, 2**64 - 1), min_size=2, max_size=40), st.integers(0, 12))
def test_close_pairs_finds_exactly_the_pairs_a_slow_search_finds(values: list[int], max_distance: int) -> None:
    hashes = np.array(values, dtype=np.uint64)
    slow = {
        (a, b)
        for a in range(len(values))
        for b in range(a + 1, len(values))
        if (values[a] ^ values[b]).bit_count() <= max_distance
    }
    assert set(dedup.close_pairs(hashes, max_distance)) == slow


def test_only_confirmed_copies_are_removed_and_the_most_protected_copy_is_kept(tmp_path: Path) -> None:
    portrait = decode_image(PORTRAIT.read_bytes())
    noise = np.random.default_rng(0).integers(0, 256, portrait.shape, dtype=np.uint8)
    pictures = {
        "a": portrait,
        "b": cv2.resize(cv2.resize(portrait, (300, 300)), (512, 512)),
        "c": cv2.cvtColor(cv2.cvtColor(portrait, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR),
        "d": noise,
    }
    with zipfile.ZipFile(tmp_path / "faces.zip", "w") as faces:
        for name, picture in pictures.items():
            faces.writestr(name, jpeg(picture))
    rows = [row("a", "train"), row("b", "test", age_low=30), row("c", "val"), row("d", "train")]
    everything_looks_alike = np.zeros(4, dtype=np.uint64)
    duplicates = dedup.find_duplicates(rows, everything_looks_alike, {"d": tmp_path / "faces.zip"})
    assert sorted((d.image_id, d.kept, d.kept_split, d.same_label) for d in duplicates) == [
        ("a", "b", "test", False),
        ("c", "b", "test", False),
    ]


def test_a_copy_of_a_photo_the_model_learned_from_is_removed_from_the_other_dataset(tmp_path: Path) -> None:
    portrait = decode_image(PORTRAIT.read_bytes())
    with zipfile.ZipFile(tmp_path / "seen.zip", "w") as seen, zipfile.ZipFile(tmp_path / "new.zip", "w") as new:
        seen.writestr("s", jpeg(portrait))
        new.writestr("n", jpeg(cv2.resize(cv2.resize(portrait, (300, 300)), (512, 512))))
    rows = [
        Row("n", "new", "a.zip", "n", 15, 15, 15, "female", "g", "CC0", "test"),
        Row("s", "seen", "a.zip", "s", 10, 19, None, "female", "g", "CC0", "train"),
    ]
    faces = {"new": tmp_path / "new.zip", "seen": tmp_path / "seen.zip"}
    duplicates = dedup.find_duplicates(rows, np.zeros(2, dtype=np.uint64), faces, seen="seen")
    assert [(d.image_id, d.kept, d.kept_split) for d in duplicates] == [("n", "s", "train")]
