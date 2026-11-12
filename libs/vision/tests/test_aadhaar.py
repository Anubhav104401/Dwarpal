"""Tests for reading Aadhaar Secure QR codes (Part 7): the code in a picture, its number as bytes, and its parts.

Every code here is a specimen made by `dwarpal_vision.aadhaar` itself: fictional fields, a public-domain portrait, and
a "signature" that is plain filler. No real Aadhaar is in this repository, and none is needed: the layout is UIDAI's
published one.
"""

from __future__ import annotations

import zlib
from pathlib import Path

import cv2
import numpy as np
import pytest

from dwarpal_vision import decode_image
from dwarpal_vision.aadhaar import (
    SIGNATURE_BYTES,
    SecureQrError,
    decode_photo,
    pack,
    parse,
    read_qr,
    specimen_data,
    specimen_photo,
    specimen_png,
    unpack,
)

FIXTURE = Path(__file__).parent / "fixtures" / "astronaut.jpg"
PORTRAIT = np.asarray(cv2.imread(str(FIXTURE)), dtype=np.uint8)
FILLER = bytes(range(256))  # stands where a signature would: 256 bytes that no key made


ID_PHOTO = PORTRAIT[20:245, 133:313]  # the fixture cut close round the face, as an ID photo is


def specimen(born: str = "01-01-1990", version: int = 2) -> bytes:
    return specimen_data(born, specimen_photo(ID_PHOTO), lambda signed: FILLER, version)


def test_a_code_number_longer_than_pythons_limit_goes_both_ways() -> None:
    data = specimen()
    text = pack(data)
    assert text.isdigit() and len(text) > 4300  # past the length Python converts in one step
    assert unpack(text) == data


@pytest.mark.parametrize(
    ("printed", "born"),
    [("01-01-1990", "1990-01-01"), ("31/12/2008", "2008-12-31"), ("2008-12-31", "2008-12-31"), ("1990", "1990")],
)
def test_the_date_of_birth_is_read_in_each_form_uidai_has_printed(printed: str, born: str) -> None:
    assert parse(specimen(printed)).born == born


def test_both_layouts_give_the_same_parts() -> None:
    old, new = parse(specimen(version=1)), parse(specimen(version=2))
    assert (old.version, new.version) == (1, 2)
    assert old.born == new.born == "1990-01-01"
    for code in (old, new):
        assert code.signature == FILLER and len(code.signature) == SIGNATURE_BYTES
        assert code.signed + code.signature == specimen(version=code.version)
        photo = decode_photo(code.photo)
        assert photo is not None and photo.shape == (200, 160, 3)


def test_a_code_without_a_photo_is_still_read() -> None:
    code = parse(specimen_data("01-01-1990", b"", lambda signed: FILLER))
    assert code.born == "1990-01-01" and code.photo == b""
    assert decode_photo(code.photo) is None
    assert decode_photo(b"\xff\x4f\xff\x51 not a picture") is None


@pytest.mark.parametrize(
    "data",
    [
        b"short",
        FILLER * 3,  # long enough, but no fields
        b"V2\xff0\xff1\xffname\xffnot a date\xffF\xff" + FILLER * 2,
        b"V2\xff0\xff1\xff" + FILLER,  # ends before the date of birth
    ],
)
def test_bytes_that_are_not_a_secure_qr_are_refused(data: bytes) -> None:
    with pytest.raises(SecureQrError) as caught:
        parse(data)
    assert caught.value.code == "aadhaar_qr_unreadable"


def test_text_that_is_not_a_secure_qr_number_is_refused() -> None:
    cut_short = pack(specimen())[:-40]  # a real code's number with its last digits missing
    for text in ("https://example.com", "12345", "9" * 9000, cut_short):
        with pytest.raises(SecureQrError):
            unpack(text)


def test_a_zip_bomb_is_stopped_at_the_size_limit() -> None:
    bomb = zlib.compressobj(9, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
    small = bomb.compress(bytes(200 * 1024)) + bomb.flush()  # 200 kB of zeros in a few hundred bytes
    with pytest.raises(SecureQrError, match="more than"):
        unpack(str(int.from_bytes(small, "big")))


def test_the_code_is_found_in_a_picture_and_a_portrait_has_none() -> None:
    text = pack(specimen())
    picture = decode_image(specimen_png(text), max_bytes=1 << 20, max_side=2400)
    assert read_qr(picture) == text
    assert read_qr(PORTRAIT) is None


def test_the_code_is_read_from_a_blurred_and_tilted_photo_of_it() -> None:
    text = pack(specimen())
    flat = decode_image(specimen_png(text), max_bytes=1 << 20, max_side=2400)
    height, width = flat.shape[:2]
    corners = np.array([[0, 0], [width, 0], [width, height], [0, height]], np.float32)
    leaning = np.array(
        [[width * 0.02, height * 0.02], [width * 0.97, 0], [width, height * 0.98], [0, height]], np.float32
    )
    turn = cv2.getPerspectiveTransform(corners, leaning)
    photo = cv2.warpPerspective(flat, turn, (width, height), borderValue=(200, 200, 200))
    photo = cv2.GaussianBlur(photo, (0, 0), 1.0)
    assert read_qr(np.asarray(photo, dtype=np.uint8)) == text
