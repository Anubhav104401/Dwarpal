"""Read the Secure QR code printed on an Aadhaar letter, card or e-Aadhaar: find the code in a picture, unpack what it
holds, and split that into its parts. UIDAI signs the code; the signature is checked elsewhere (the inference service's
key ring) — this module only reads.

What a Secure QR holds, as UIDAI's specification lays it out: a very long decimal number. Written as bytes, it is a
gzip file. Unpacked, it is a run of text fields, each ended by the byte 255; then the holder's photo (JPEG 2000);
then, if the holder registered them, hashes of their email and mobile (32 bytes each); and last, 256 bytes: UIDAI's
RSA signature over every byte before it.

An age check needs the date of birth, the photo and the signature. Nothing else is taken out of the code here: no
name, no address, no reference number.
"""

from __future__ import annotations

import re
import zlib
from collections.abc import Callable, Iterator
from dataclasses import dataclass

import cv2
import numpy as np

from dwarpal_vision.decode import Image

SIGNATURE_BYTES = 256  # an RSA-2048 signature
END_OF_FIELD = 255
MAX_DIGITS = 8000  # the largest QR code holds 7,089 digits
# Python refuses to turn text of more than 4,300 digits into a number in one step (a guard against a slow
# conversion being used to stall a server), so the number is built, and written out, this many digits at a time.
CHUNK = 4000
MAX_UNPACKED = 64 * 1024  # a real code unpacks to a few thousand bytes: a "zip bomb" is refused well before this
MAX_PHOTO_SIDE = 1024
# Field numbers, counted from the first field. The first code (2018) starts with the email/mobile marker; every later
# one starts with its version ("V2", "V3", …), which moves each field one place on.
BIRTH_FIELD_V1 = 3
JP2_FILE = b"\x00\x00\x00\x0cjP  \r\n\x87\n"  # a JPEG 2000 picture kept as a file …
JP2_STREAM = b"\xff\x4f\xff\x51"  # … or as a bare code stream
VERSION = re.compile(rb"V[2-9]")
DAY_FIRST = re.compile(r"(\d{2})[-/](\d{2})[-/](\d{4})")
YEAR_FIRST = re.compile(r"(\d{4})[-/](\d{2})[-/](\d{2})")
YEAR_ONLY = re.compile(r"\d{4}")
# How big the picture is made before each try: a dense code that isn't read at one size is often read at another.
SCALES = (1.0, 1.5, 2.0, 0.75)


class SecureQrError(ValueError):
    """The code isn't a Secure QR, or can't be trusted. `code` is stable, for programs."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SecureQr:
    version: int  # 1 for the first layout, else the number after "V"
    born: str  # the date of birth as "YYYY-MM-DD", or "YYYY" when the code gives only the year
    photo: bytes  # the holder's photo, JPEG 2000, as it is in the code
    signed: bytes  # every byte the signature covers
    signature: bytes  # UIDAI's signature over `signed`


def _views(image: Image) -> Iterator[Image]:
    """The picture in grey, at several sizes, then in pure black and white: the same code, easier or harder to read."""
    gray: Image = np.asarray(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), np.uint8) if image.ndim == 3 else image
    for scale in SCALES:
        if scale == 1.0:
            yield gray
        else:
            method = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
            yield np.asarray(cv2.resize(gray, None, fx=scale, fy=scale, interpolation=method), dtype=np.uint8)
    yield np.asarray(cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1], dtype=np.uint8)


def read_qr(image: Image) -> str | None:
    """The text of a QR code in the picture that could be a Secure QR (digits only, and many of them); None if there
    is none. A Secure QR is among the densest codes there are — up to 177 little squares a side — so it must fill
    most of the picture to be read."""
    detector = cv2.QRCodeDetectorAruco()
    for view in _views(image):
        try:
            text, _, _ = detector.detectAndDecode(view)
        except cv2.error:
            continue
        if text.isascii() and text.isdigit() and len(text) > SIGNATURE_BYTES:
            return str(text)
    return None


def unpack(text: str) -> bytes:
    """The code's text (one long decimal number) as the bytes it stands for, unzipped."""
    if not (text.isascii() and text.isdigit()) or len(text) > MAX_DIGITS:
        raise SecureQrError("aadhaar_qr_unreadable", "a Secure QR is one decimal number of at most 7,089 digits")
    number = 0
    for at in range(0, len(text), CHUNK):  # a few thousand digits at a time: see CHUNK
        piece = text[at : at + CHUNK]
        number = number * 10 ** len(piece) + int(piece)
    packed = number.to_bytes((number.bit_length() + 7) // 8, "big")
    unzip = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)  # 16 +: the data is in gzip's wrapping
    try:
        data = unzip.decompress(packed, MAX_UNPACKED)
    except zlib.error:
        raise SecureQrError("aadhaar_qr_unreadable", "the code's number isn't gzip data") from None
    if unzip.unconsumed_tail or not unzip.eof:
        raise SecureQrError("aadhaar_qr_unreadable", "the code unpacks to more than a Secure QR holds")
    return data


def _born(text: str) -> str:
    text = text.strip()
    if found := DAY_FIRST.fullmatch(text):
        day, month, year = found.groups()
        return f"{year}-{month}-{day}"
    if found := YEAR_FIRST.fullmatch(text):
        return "-".join(found.groups())
    if YEAR_ONLY.fullmatch(text):
        return text
    raise SecureQrError("aadhaar_qr_unreadable", "the date of birth isn't in a form this reader knows")


def parse(data: bytes) -> SecureQr:
    """Split the unpacked bytes into the parts an age check needs. Only the date-of-birth field is ever turned into
    text; the fields around it are counted past, not read."""
    if len(data) <= SIGNATURE_BYTES:
        raise SecureQrError("aadhaar_qr_unreadable", "too short to hold a signature")
    signed, signature = data[:-SIGNATURE_BYTES], data[-SIGNATURE_BYTES:]
    versioned = VERSION.match(signed)
    version = int(signed[1:2]) if versioned else 1
    birth_field = BIRTH_FIELD_V1 + (1 if versioned else 0)
    start = 0
    for _ in range(birth_field):
        start = signed.find(END_OF_FIELD, start) + 1
        if start == 0:
            raise SecureQrError("aadhaar_qr_unreadable", "fewer fields than a Secure QR has")
    end = signed.find(END_OF_FIELD, start)
    if end == -1:
        raise SecureQrError("aadhaar_qr_unreadable", "fewer fields than a Secure QR has")
    born = _born(signed[start:end].decode("iso-8859-1"))
    photo_at = min((at for at in (signed.find(JP2_FILE, end), signed.find(JP2_STREAM, end)) if at != -1), default=-1)
    # The hashes that may follow the photo are left on its end: a JPEG 2000 reader stops at the picture's own end mark.
    photo = signed[photo_at:] if photo_at != -1 else b""
    return SecureQr(version, born, photo, signed, signature)


def decode_photo(photo: bytes) -> Image | None:
    """The holder's photo as a picture; None if the code has none, or it can't be decoded."""
    if not photo:
        return None
    try:
        image = cv2.imdecode(np.frombuffer(photo, dtype=np.uint8), cv2.IMREAD_COLOR)
    except cv2.error:
        return None
    if image is None or max(image.shape[:2]) > MAX_PHOTO_SIDE:
        return None
    return np.asarray(image, dtype=np.uint8)


def specimen_photo(portrait: Image) -> bytes:
    """A portrait as a Secure QR holds one: small (160 by 200 pixels) and squeezed hard, as JPEG 2000, to about
    2 kB. The portrait should already be cut close round the face, upright, 4 wide to 5 tall."""
    small = cv2.resize(portrait, (160, 200), interpolation=cv2.INTER_AREA)
    ok, data = cv2.imencode(".jp2", small, [cv2.IMWRITE_JPEG2000_COMPRESSION_X1000, 20])
    if not ok:
        raise ValueError("the portrait couldn't be encoded")
    return bytes(data.tobytes())


def specimen_data(born: str, photo: bytes, sign: Callable[[bytes], bytes], version: int = 2) -> bytes:
    """A made-up Secure QR's bytes, for tests and demonstrations: fictional fields in the real layout, signed by
    whoever `sign` is — never by UIDAI, so no real reader takes it for a real Aadhaar."""
    fields = [
        "0",  # no email, no mobile: no hashes after the photo
        "000020260101120000000",  # a reference number that no Aadhaar has
        "Specimen Person",
        born,
        "F",
        *("C/O Specimen", "Utopia", "", "1", "", "000000", "Utopia", "Utopia", "Specimen Street", "Utopia", "Utopia"),
    ]
    if version >= 2:
        fields = [f"V{version}", *fields, "0000"]  # the version first; the mobile's last four digits last
    signed = b"".join(field.encode("iso-8859-1") + bytes([END_OF_FIELD]) for field in fields) + photo
    return signed + sign(signed)


def pack(data: bytes) -> str:
    """Unpacked bytes as a Secure QR's text: zipped, then written as one decimal number."""
    zipper = zlib.compressobj(9, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
    number = int.from_bytes(zipper.compress(data) + zipper.flush(), "big")
    pieces = []
    while number:
        number, piece = divmod(number, 10**CHUNK)
        pieces.append(str(piece).zfill(CHUNK))
    return "".join(reversed(pieces)).lstrip("0") or "0"


def specimen_png(text: str, module: int = 8) -> bytes:
    """A QR code holding `text`, as a PNG: each of the code's little squares `module` pixels wide, on a white
    margin."""
    # OpenCV's type hints leave its QR writer out, hence the "ignore" notes; the writer itself is there.
    settings = cv2.QRCodeEncoder_Params()  # type: ignore[attr-defined]
    settings.mode = cv2.QRCodeEncoder_MODE_NUMERIC
    settings.correction_level = cv2.QRCodeEncoder_CORRECT_LEVEL_L
    code = cv2.QRCodeEncoder_create(settings).encode(text)  # type: ignore[attr-defined]
    code = cv2.resize(code, None, fx=module, fy=module, interpolation=cv2.INTER_NEAREST)
    code = cv2.copyMakeBorder(code, *(8 * module,) * 4, cv2.BORDER_CONSTANT, value=255)
    ok, png = cv2.imencode(".png", code)
    if not ok:
        raise ValueError("the code couldn't be encoded")
    return bytes(png.tobytes())
