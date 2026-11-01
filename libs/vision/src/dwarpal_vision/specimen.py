"""Specimen document pages for tests and demonstrations: an invented passport of ICAO's fictional state "Utopia", with a
valid machine-readable zone, photographed as a phone would — at an angle, a little blurred, with noise.

No real person's document is ever used to test Dwarpal. The face on the specimen is whatever picture is given (the
tests use a NASA portrait in the public domain).

    python -m dwarpal_vision.specimen PORTRAIT OUT.jpg [BIRTH_YYMMDD] [EXPIRY_YYMMDD]
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

from dwarpal_vision.decode import Image

WEIGHTS = (7, 3, 1)


def check_digit(text: str) -> str:
    """ICAO 9303's check digit (the API has its own copy, in the parser that checks it)."""

    def value(char: str) -> int:
        return int(char) if char.isdigit() else 0 if char == "<" else ord(char) - ord("A") + 10

    return str(sum(value(char) * WEIGHTS[i % 3] for i, char in enumerate(text)) % 10)


def passport_zone(birth: str, expiry: str, number: str = "L898902C3", sex: str = "F") -> str:
    """A passport's two MRZ lines (TD3), for ICAO's specimen holder with the given dates (YYMMDD)."""
    personal = "ZE184226B".ljust(14, "<")
    middle = (
        f"{number}{check_digit(number)}UTO{birth}{check_digit(birth)}{sex}{expiry}{check_digit(expiry)}"
        f"{personal}{check_digit(personal)}"
    )
    composite = middle[0:10] + middle[13:20] + middle[21:43]
    return "P<UTOERIKSSON<<ANNA<MARIA".ljust(44, "<") + "\n" + middle + check_digit(composite)


def page(zone: str, portrait: Image) -> Image:
    """The data page, flat: a photo, a few printed fields, and the MRZ at the bottom in even, fixed-width characters."""
    font, ink = cv2.FONT_HERSHEY_SIMPLEX, (60, 60, 60)
    lines = zone.split("\n")
    pitch = {44: 22, 36: 28, 30: 32}[len(lines[0])]
    sheet = np.full((900, 1250, 3), (225, 232, 238), np.uint8)
    tall, wide = portrait.shape[:2]
    keep = min(wide, tall * 4 // 5)  # a passport photo is 4 wide by 5 tall: cut the picture's sides to that shape
    left = (wide - keep) // 2
    photo = portrait[: keep * 5 // 4, left : left + keep]
    sheet[120:420, 60:300] = cv2.resize(photo, (240, 300), interpolation=cv2.INTER_AREA)
    cv2.putText(sheet, "PASSPORT  UTOPIA  SPECIMEN", (360, 150), font, 1.2, ink, 2)
    for i, text in enumerate(("Surname ERIKSSON", "Given names ANNA MARIA", "Not a real document")):
        cv2.putText(sheet, text, (360, 230 + 60 * i), font, 0.8, ink, 2)
    for row, line in enumerate(lines):
        for column, char in enumerate(line):
            (width, _), _ = cv2.getTextSize(char, font, 0.9, 2)
            x = 140 + column * pitch + (pitch - width) // 2
            cv2.putText(sheet, char, (x, 760 + row * 55), font, 0.9, (20, 20, 20), 2, cv2.LINE_AA)
    return sheet


def photographed(sheet: Image, seed: int = 0) -> Image:
    """The page as a phone might take it: tilted in perspective on a dark table, slightly blurred, with sensor noise."""
    rng = np.random.default_rng(seed)
    height, width = sheet.shape[:2]
    corners = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype=np.float32)
    wobble = rng.uniform(-40, 40, (4, 2))
    placed = np.array([[150, 120], [1450, 90], [1500, 1080], [110, 1050]], dtype=np.float32) + wobble
    turn = cv2.getPerspectiveTransform(corners, placed.astype(np.float32))
    photo = cv2.warpPerspective(sheet, turn, (1600, 1200), borderValue=(90, 80, 70))
    photo = cv2.GaussianBlur(photo, (5, 5), 1.2)
    noise = np.asarray(rng.normal(0, 6, photo.shape), dtype=np.int16)
    noisy = np.asarray(photo, dtype=np.int16) + noise
    return np.asarray(np.clip(noisy, 0, 255), dtype=np.uint8)


def specimen_jpeg(portrait: Image, birth: str, expiry: str, seed: int = 0) -> bytes:
    photo = photographed(page(passport_zone(birth, expiry), portrait), seed)
    ok, encoded = cv2.imencode(".jpg", photo, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ok:
        raise ValueError("the specimen couldn't be encoded")
    return encoded.tobytes()


if __name__ == "__main__":
    portrait_path, out = Path(sys.argv[1]), Path(sys.argv[2])
    birth, expiry = (sys.argv[3:5] + ["900101", "360101"][len(sys.argv[3:5]) :])[:2]
    picture = cv2.imread(str(portrait_path))
    if picture is None:
        raise SystemExit(f"can't read {portrait_path}")
    out.write_bytes(specimen_jpeg(np.asarray(picture, dtype=np.uint8), birth, expiry))
