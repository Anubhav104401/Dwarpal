"""Read the machine-readable zone (MRZ) from a photo of a passport or ID card: find the band, straighten it, and have
Tesseract read it. The text is checked elsewhere (the API's ICAO 9303 parser); this module only reads."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Sequence

import cv2
import numpy as np

from dwarpal_vision.decode import Image

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
WORK_WIDTH = 800  # the band is looked for in a copy this wide: the kernels' sizes below are for this scale
LINE_HEIGHT = 45  # each line's share of the band, in pixels: capital letters about 30 pixels tall read best
MIN_LINE = 20  # shorter lines are stray marks, not MRZ lines (the shortest MRZ line has 30 characters)
NOT_THE_ALPHABET = re.compile(f"[^{ALPHABET}]")


class TesseractError(RuntimeError):
    """Tesseract couldn't be run, or failed."""


def find_mrz(image: Image) -> Image | None:
    """The MRZ band, cut out, turned level and in grey; None if no band was found. The MRZ is a block of dark
    characters on a light ground, much wider than tall, with small even gaps: the steps below make such a block into
    one solid shape and pick the widest one that is shaped like an MRZ."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    scale = WORK_WIDTH / gray.shape[1]
    small = cv2.GaussianBlur(cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA), (3, 3), 0)
    # Black-hat: dark details smaller than the kernel (characters) stand out; large dark areas (photos) don't.
    dark = cv2.morphologyEx(small, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_RECT, (13, 5)))
    # Where brightness changes from left to right: the edges of characters, strongest in rows of text.
    edges = np.absolute(cv2.Sobel(dark, cv2.CV_32F, 1, 0, ksize=-1))
    edges = (255 * (edges - edges.min()) / (np.ptp(edges) + 1e-6)).astype(np.uint8)  # stretched to 0-255
    # Close the gaps between characters, then between lines, so the zone becomes one blob.
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (21, 5)))
    blobs = cv2.threshold(edges, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    blobs = cv2.morphologyEx(blobs, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25)))
    blobs = cv2.erode(blobs, np.ones((3, 3), np.uint8), iterations=3)
    contours, _ = cv2.findContours(blobs, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        (x, y), (width, height), angle = cv2.minAreaRect(contour)
        if width < height:  # minAreaRect may describe the same box standing up
            width, height, angle = height, width, angle + 90
        # At least 4 times as wide as tall, and across at least 40 % of the picture.
        if width > 4 * height and width > 0.4 * WORK_WIDTH:
            centre = (x / scale, y / scale)
            # A margin round the blob: erosion trimmed its edges, and Tesseract needs some clear space.
            size = (int(width / scale * 1.06), int(height / scale * 1.35))
            turn = cv2.getRotationMatrix2D(centre, angle, 1.0)
            level = cv2.warpAffine(gray, turn, gray.shape[::-1], flags=cv2.INTER_CUBIC, borderValue=255)
            return np.asarray(cv2.getRectSubPix(level, size, centre), dtype=np.uint8)
    return None


def zone_lines(text: str) -> list[str]:
    """Tesseract's text as MRZ lines: spaces dropped, anything outside the MRZ alphabet dropped, short lines dropped.
    The line that holds only names (the first of a passport's or a TD2 card's two, the third of a TD1 card's three) is
    blanked after its first five characters (document type and issuer): no check digit covers it, an age check needs
    none of it, and so no name ever leaves the service that read it."""
    lines = [NOT_THE_ALPHABET.sub("", line.upper().replace(" ", "")) for line in text.splitlines()]
    lines = [line for line in lines if len(line) >= MIN_LINE]
    if len(lines) == 2:
        lines[0] = lines[0][:5].ljust(len(lines[0]), "<")
    elif len(lines) == 3:
        lines[2] = "<" * len(lines[2])
    return lines


class Tesseract:
    """Runs Tesseract on one picture at a time, passing it in and reading the text back through pipes: nothing is
    written to disk. `command` starts Tesseract: `["tesseract"]` where it is installed, or
    `["docker", "exec", "-i", "dwarpal-ocr-1", "tesseract"]` to use the project's OCR container."""

    def __init__(self, command: Sequence[str], timeout_s: float = 10.0) -> None:
        self.command = list(command)
        self.timeout_s = timeout_s

    def available(self) -> bool:
        """Whether Tesseract answers at all: for the service's readiness check, and for tests."""
        try:
            subprocess.run(  # noqa: S603 - a fixed command from settings
                [*self.command, "--version"], capture_output=True, timeout=self.timeout_s, check=True
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return True

    def read(self, band: Image) -> str:
        height, width = band.shape[:2]
        # Two lines make a band over 5.5 times as wide as tall; three (an ID card's) a squarer one.
        lines = 2 if width > 5.5 * height else 3
        factor = LINE_HEIGHT * lines / height
        larger = cv2.resize(band, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC)
        larger = cv2.copyMakeBorder(larger, 20, 20, 20, 20, cv2.BORDER_REPLICATE)
        ok, png = cv2.imencode(".png", larger)
        if not ok:
            raise TesseractError("the band couldn't be encoded")
        arguments = [
            *("stdin", "stdout", "--psm", "6", "-l", "eng"),  # read from the pipe; one block of text
            *("-c", f"tessedit_char_whitelist={ALPHABET}"),  # only the MRZ's characters
            *("-c", "load_system_dawg=0", "-c", "load_freq_dawg=0"),  # no dictionary: MRZ lines aren't words
        ]
        try:
            done = subprocess.run(  # noqa: S603 - a fixed command from settings, never from a request
                [*self.command, *arguments], input=png.tobytes(), capture_output=True, timeout=self.timeout_s
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise TesseractError(f"Tesseract couldn't be run: {error}") from None
        if done.returncode != 0:
            raise TesseractError(f"Tesseract failed: {done.stderr.decode(errors='replace')[:200]}")
        return done.stdout.decode(errors="replace")
