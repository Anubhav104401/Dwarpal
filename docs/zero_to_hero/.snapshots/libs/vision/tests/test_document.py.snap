"""Tests for reading documents (Phase 6): finding the MRZ, reading it with Tesseract, and matching faces with SFace.

The documents are specimens drawn by `dwarpal_vision.specimen` (ICAO's fictional Utopia), never real ones. The tests
that need Tesseract use it where it is installed, or the project's OCR container, and are skipped if neither is there.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from dwarpal_vision import FaceDetector, decode_image
from dwarpal_vision.document import Tesseract, TesseractError, find_mrz, zone_lines
from dwarpal_vision.match import SAME_PERSON, FaceMatcher
from dwarpal_vision.specimen import check_digit, passport_zone, specimen_jpeg

FIXTURE = Path(__file__).parent / "fixtures" / "astronaut.jpg"
MODELS = Path(__file__).resolve().parents[3] / "models" / "third_party"
PORTRAIT = np.asarray(cv2.imread(str(FIXTURE)), dtype=np.uint8)


def tesseract_command() -> list[str] | None:
    """Tesseract as configured for the inference service, else installed, else in the OCR container; None if none
    of them answers."""
    configured = os.environ.get("DWARPAL_INFERENCE_TESSERACT_COMMAND")
    candidates = [json.loads(configured)] if configured else []
    candidates += [["tesseract"], ["docker", "exec", "-i", "dwarpal-ocr-1", "tesseract"]]
    return next((command for command in candidates if Tesseract(command).available()), None)


@pytest.fixture(scope="module")
def ocr() -> Tesseract:
    command = tesseract_command()
    if command is None:
        pytest.skip("Tesseract isn't installed, and the OCR container isn't running")
    return Tesseract(command)


def photo(birth: str = "900101", seed: int = 0) -> np.ndarray:
    return decode_image(specimen_jpeg(PORTRAIT, birth, "360101", seed), max_bytes=1 << 20, max_side=2400)


def test_specimen_zones_carry_icao_check_digits() -> None:
    """The specimen's zone is the one in ICAO Doc 9303 when given its dates: the drawing starts from a valid zone."""
    zone = passport_zone("740812", "120415")
    assert zone.split("\n")[1] == "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
    assert check_digit("L898902C3") == "6"


def test_ocr_text_becomes_mrz_lines_with_the_names_blanked() -> None:
    text = "P<UTO ERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nnoise\nL898902C36UTO7408122F1204159ZE184226B<<<<<10\n"
    lines = zone_lines(text)
    assert lines == ["P<UTO" + "<" * 39, "L898902C36UTO7408122F1204159ZE184226B<<<<<10"]
    card = zone_lines("I<UTOD231458907<<<<<<<<<<<<<<<\n7408122F1204159UTO<<<<<<<<<<<6\nERIKSSON<<ANNA<MARIA<<<<<<<<<<")
    assert card[2] == "<" * 30  # a TD1 card's names are its third line


def test_the_band_is_found_on_a_photographed_page_and_not_on_a_face() -> None:
    band = find_mrz(photo())
    assert band is not None
    height, width = band.shape[:2]
    assert width > 5 * height  # two long lines of characters
    assert find_mrz(PORTRAIT) is None


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_tesseract_reads_the_data_line_of_a_photographed_specimen(ocr: Tesseract, seed: int) -> None:
    """The data line holds the dates and every check digit. (The parser repairs a character more or less; here the
    tests only ask that the dates themselves were read.)"""
    band = find_mrz(photo(seed=seed))
    assert band is not None
    lines = zone_lines(ocr.read(band))
    assert len(lines) == 2
    assert "900101" in lines[1] and "360101" in lines[1]


def test_a_tesseract_that_cannot_run_is_reported_not_guessed_around() -> None:
    band = find_mrz(photo())
    assert band is not None
    with pytest.raises(TesseractError):
        Tesseract(["no-such-program-dwarpal"]).read(band)


def test_the_same_face_matches_itself_on_a_printed_page_and_a_scrambled_one_doesnt() -> None:
    detector = FaceDetector(MODELS / "face_detection_yunet_2023mar.onnx")
    matcher = FaceMatcher(MODELS / "face_recognition_sface_2021dec_int8.onnx")
    page = photo()
    printed, live = detector.detect(page), detector.detect(PORTRAIT)
    assert len(printed) == 1 and len(live) == 1
    reference = matcher.embed(page, printed[0])
    assert matcher.similarity(reference, matcher.embed(PORTRAIT, live[0])) >= SAME_PERSON
    # The same face with its features scrambled (cut into blocks and shuffled) is not the same person.
    blocks = [PORTRAIT[y : y + 64, x : x + 64] for y in range(0, 512, 64) for x in range(0, 512, 64)]
    order = np.random.default_rng(1).permutation(len(blocks))
    rows = [np.hstack([blocks[i] for i in order[r * 8 : r * 8 + 8]]) for r in range(8)]
    scrambled = np.ascontiguousarray(np.vstack(rows))
    assert matcher.similarity(reference, matcher.embed(scrambled, live[0])) < SAME_PERSON
