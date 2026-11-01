"""Reading the machine-readable zone (MRZ) of passports and ID cards (ICAO Doc 9303): pure rules, no I/O.

Only what an age check needs leaves this module: the document's type and issuer, the date of birth (from which only the
year and month are kept) and the expiry date. The name, the document number and the nationality are read only to
check the check digits, and are then dropped.
"""

from __future__ import annotations

import dataclasses
import itertools
import math
from dataclasses import dataclass
from datetime import date
from typing import Literal

FILLER = "<"
WEIGHTS = (7, 3, 1)
# Characters an OCR engine confuses with digits, and the digit each stands for.
LOOKS_LIKE_A_DIGIT = {
    "O": "0",
    "D": "0",
    "Q": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "S": "5",
    "G": "6",
    "T": "7",
    "B": "8",
}
LOOKS_LIKE_A_LETTER = {"0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "7": "T", "8": "B"}
MAX_REPAIRS = 4  # a field with more doubtful characters than this is too damaged to guess at
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
MAX_LENGTH_EDITS = 2  # characters OCR may have added to a line; at most one may be missing
MAX_READINGS = 5000  # repaired readings of a whole zone worth trying; more means the photo is too poor

Format = Literal["TD1", "TD2", "TD3"]
LAYOUTS: dict[Format, tuple[int, int]] = {"TD1": (3, 30), "TD2": (2, 36), "TD3": (2, 44)}


class MrzError(ValueError):
    """The zone can't be trusted. `code` is stable, for programs; the message says which part failed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class MrzDocument:
    format: Format
    document_type: str  # "P" for a passport, "I", "A" or "C" for ID cards, …
    issuer: str  # the issuing state or organisation, as a three-letter code
    birth: date
    expiry: date
    repaired: tuple[str, ...]  # fields whose OCR confusions were repaired to make their check digits pass

    @property
    def birth_year_month(self) -> tuple[int, int]:
        """All of the date of birth that Dwarpal keeps."""
        return self.birth.year, self.birth.month


def value(char: str) -> int:
    """A character's value for check digits: digits as themselves, A to Z as 10 to 35, the filler as 0."""
    if char.isdigit():
        return int(char)
    if "A" <= char <= "Z":
        return ord(char) - ord("A") + 10
    if char == FILLER:
        return 0
    raise MrzError("mrz_unreadable", f"{char!r} can't appear in an MRZ")


def check_digit(text: str) -> str:
    """ICAO 9303 part 3: weight the values 7, 3, 1, 7, 3, 1, …, add them up, and keep the last digit."""
    return str(sum(value(char) * WEIGHTS[i % 3] for i, char in enumerate(text)) % 10)


def _candidates(text: str, numeric: bool) -> list[str]:
    """The ways an OCR engine's reading could be repaired: a numeric field's look-alike letters become digits; in an
    alphanumeric field, each doubtful character may be either."""
    if numeric:
        return ["".join(LOOKS_LIKE_A_DIGIT.get(char, char) for char in text)]
    choices = [(char, LOOKS_LIKE_A_DIGIT.get(char) or LOOKS_LIKE_A_LETTER.get(char) or char) for char in text]
    doubtful = sum(1 for a, b in choices if a != b)
    if doubtful > MAX_REPAIRS:
        return []
    return ["".join(option) for option in itertools.product(*({a, b} for a, b in choices))]


def checked(name: str, text: str, digit: str, numeric: bool, repaired: list[str]) -> str:
    """The field, if its check digit agrees; otherwise its one repair that makes it agree; otherwise an error."""
    digit = LOOKS_LIKE_A_DIGIT.get(digit, digit)
    if digit == FILLER and set(text) == {FILLER}:
        return text  # an optional field left empty may leave its check digit empty too
    readable = all(char.isdigit() or "A" <= char <= "Z" or char == FILLER for char in text)
    if digit.isdigit() and readable and check_digit(text) == digit:
        return text
    passing = {option for option in _candidates(text, numeric) if option != text and check_digit(option) == digit}
    if len(passing) == 1:
        repaired.append(name)
        return passing.pop()
    raise MrzError("mrz_check_failed", f"the check digit of the {name.replace('_', ' ')} doesn't match")


def _date(text: str, name: str) -> tuple[int, int, int]:
    if not text.isdigit():
        raise MrzError("mrz_date_unknown", f"the {name.replace('_', ' ')} is incomplete")
    return int(text[:2]), int(text[2:4]), int(text[4:])


def _real_date(year: int, month: int, day: int, name: str) -> date:
    try:
        return date(year, month, day)
    except ValueError:
        raise MrzError("mrz_date_invalid", f"the {name.replace('_', ' ')} isn't a real date") from None


def birth_date(text: str, today: date) -> date:
    """Two-digit years: the most recent century that doesn't put the birth in the future."""
    yy, month, day = _date(text, "birth_date")
    year = 2000 + yy if 2000 + yy <= today.year else 1900 + yy
    born = _real_date(year, month, day, "birth_date")
    return born if born <= today else _real_date(year - 100, month, day, "birth_date")


def expiry_date(text: str, today: date) -> date:
    """Two-digit years: this century, unless that is more than 50 years ahead (no document lasts that long)."""
    yy, month, day = _date(text, "expiry_date")
    year = 2000 + yy if 2000 + yy <= today.year + 50 else 1900 + yy
    return _real_date(year, month, day, "expiry_date")


def layout(lines: list[str]) -> Format:
    for name, (count, width) in LAYOUTS.items():
        if len(lines) == count and all(len(line) == width for line in lines):
            return name
    raise MrzError("mrz_unreadable", "the zone isn't 3 lines of 30, or 2 lines of 36 or 44, characters")


def parse(text: str, today: date) -> MrzDocument:
    """Read an MRZ, check every check digit (repairing OCR confusions only where that makes a check pass), and
    return only what an age check needs."""
    lines = [line.strip().upper().replace(" ", "") for line in text.strip().splitlines() if line.strip()]
    kind = layout(lines)
    repaired: list[str] = []
    if kind == "TD1":
        top, middle = lines[0], lines[1]
        number, number_digit, optional_1 = top[5:14], top[14], top[15:30]
        if number_digit == FILLER and optional_1.strip(FILLER):  # a long number continues in the optional field
            rest = optional_1.rstrip(FILLER)
            number, number_digit = number + rest[:-1], rest[-1]
        number = checked("document_number", number, number_digit, False, repaired)
        birth = checked("birth_date", middle[0:6], middle[6], True, repaired)
        expiry = checked("expiry_date", middle[8:14], middle[14], True, repaired)
        composite = top[5:30] + birth + middle[6] + expiry + middle[14] + middle[18:29]
        checked("composite", composite, middle[29], False, repaired)
        document_type, issuer = top[0:2], top[2:5]
    else:
        top, bottom = lines
        end = 35 if kind == "TD2" else 42
        number = checked("document_number", bottom[0:9], bottom[9], False, repaired)
        birth = checked("birth_date", bottom[13:19], bottom[19], True, repaired)
        expiry = checked("expiry_date", bottom[21:27], bottom[27], True, repaired)
        optional = bottom[28:end]
        if kind == "TD3":
            optional = checked("personal_number", optional, bottom[42], False, repaired)
            optional += bottom[42]
        composite = number + bottom[9] + birth + bottom[19] + expiry + bottom[27] + optional
        checked("composite", composite, bottom[end if kind == "TD2" else 43], False, repaired)
        document_type, issuer = top[0:2], top[2:5]
    return MrzDocument(
        format=kind,
        document_type=document_type.rstrip(FILLER),
        issuer=issuer.rstrip(FILLER),
        birth=birth_date(birth, today),
        expiry=expiry_date(expiry, today),
        repaired=tuple(repaired),
    )


def _format_of(lines: list[str]) -> Format:
    """Which layout OCR'd lines are meant to be, though a character may be missing or extra: three lines are a TD1
    card; two are a passport (44) or a TD2 card (36), whichever the data line is closer to."""
    if len(lines) == 3:
        return "TD1"
    if len(lines) == 2:
        return "TD3" if abs(len(lines[1]) - 44) < abs(len(lines[1]) - 36) else "TD2"
    raise MrzError("mrz_unreadable", "the zone isn't 2 or 3 lines")


def _resized(text: str, width: int, edits: int) -> list[str]:
    """Every way of making `text` exactly `width` characters long with exactly `edits` drops or additions, the usual
    slips of OCR in long runs of the same character: none, if the lengths are further apart than that."""
    gap = len(text) - width
    if abs(gap) != edits:
        return []
    if gap >= 0:
        return [
            "".join(c for i, c in enumerate(text) if i not in drop)
            for drop in itertools.combinations(range(len(text)), gap)
        ]
    if gap == -1:
        return [text[:i] + char + text[i:] for i in range(len(text) + 1) for char in ALPHABET]
    return []  # adding two characters anywhere is too much guessing


def _line_readings(line: str, width: int, skeleton: tuple[int, int], edits: int) -> list[tuple[str, bool]]:
    """The ways a data line could have read, with exactly `edits` characters dropped or added: as a whole, or as its
    fixed fields (the first `skeleton[0]` characters) and its last `skeleton[1]` (check digits) around an empty optional
    field — what an optional field usually is, and what OCR misreads most. The flag says which."""
    fields, tail = skeleton
    found = [(text, False) for text in _resized(line, width, edits)]
    middle = width - fields - tail
    ending = line[len(line) - tail :] if tail else ""
    for size in range(fields - MAX_LENGTH_EDITS, fields + MAX_LENGTH_EDITS + 1):
        found += [(text + FILLER * middle + ending, True) for text in _resized(line[:size], fields, edits)]
    return found


# Per layout, for each data line: how many characters of fixed fields it starts with, and how many check digits it
# ends with; everything between is an optional field.
SKELETONS: dict[Format, dict[int, tuple[int, int]]] = {
    "TD1": {0: (15, 0), 1: (18, 1)},
    "TD2": {1: (28, 1)},
    "TD3": {1: (28, 2)},
}


def read_ocr(lines: list[str], today: date) -> MrzDocument:
    """Parse an MRZ as OCR read it from a photo. The names line is ignored (an age check needs no name, and no check
    digit covers it): only its document type and issuer are kept. The data lines are read the simplest way that passes
    every check digit — with the fewest characters dropped or added, trying an empty optional field too — and only if
    that way gives **exactly one** document. Each repair is reported, so a reviewer can see what a decision rested on.
    """
    kind = _format_of(lines)
    _, width = LAYOUTS[kind]
    names = 2 if kind == "TD1" else 0
    fixed = ("" if kind == "TD1" else lines[names][:5]).ljust(width, FILLER)[:width]
    data = sorted(SKELETONS[kind].items())
    for total in range(MAX_LENGTH_EDITS + 1):
        readings: dict[tuple[str, str, str, date, date], MrzDocument] = {}
        for split in itertools.product(range(total + 1), repeat=len(data)):
            if sum(split) != total:
                continue
            options = [
                _line_readings(lines[index], width, skeleton, edits)
                for (index, skeleton), edits in zip(data, split, strict=True)
            ]
            if math.prod(len(choice) for choice in options) > MAX_READINGS:
                continue
            for chosen in itertools.product(*options):
                zone = [fixed] * len(lines)
                for (index, _), (text, _) in zip(data, chosen, strict=True):
                    zone[index] = text
                try:
                    document = parse("\n".join(zone), today)
                except MrzError:
                    continue
                notes: tuple[str, ...] = ("line_length",) if total else ()
                notes += ("optional_fields_read_as_empty",) if any(empty for _, empty in chosen) else ()
                document = dataclasses.replace(document, repaired=(*document.repaired, *notes))
                key = (document.format, document.document_type, document.issuer, document.birth, document.expiry)
                # The plainest reading of a document is kept: a whole line read as is beats an assumed-empty field.
                if key not in readings or len(document.repaired) < len(readings[key].repaired):
                    readings[key] = document
        if len(readings) == 1:
            return next(iter(readings.values()))
        if readings:
            raise MrzError("mrz_check_failed", "more than one reading of the zone passes its check digits")
    raise MrzError("mrz_check_failed", "no reading of the zone passes its check digits")


def age_on(birth: date, today: date) -> int:
    """Whole years of age: a birthday counts from its day, and someone born on 29 February has it on 1 March."""
    had_birthday = (today.month, today.day) >= (birth.month, birth.day)
    return today.year - birth.year - (0 if had_birthday else 1)


def age_outcome(document: MrzDocument, min_age: int, today: date) -> tuple[str, list[str]]:
    """The age rule for an MRZ alone: an expired document fails; otherwise pass at `min_age` or more, else fail.
    The reasons say why, including any repairs, so a reviewer can see what the decision rested on."""
    reasons = [f"repaired_{field}" for field in document.repaired]
    if document.expiry < today:
        return "fail", ["document_expired", *reasons]
    if age_on(document.birth, today) >= min_age:
        return "pass", reasons
    return "fail", ["under_age", *reasons]
