"""The MRZ reader against ICAO Doc 9303's own specimen documents, and against thousands of generated ones."""

from __future__ import annotations

from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from dwarpal_api.domain.mrz import MrzError, age_on, age_outcome, check_digit, parse, read_ocr

TODAY = date(2026, 10, 26)

# The specimens printed in ICAO Doc 9303 (parts 4, 5 and 6) for the fictional state of Utopia: Anna Maria Eriksson,
# born 12 August 1974, documents expiring 15 April 2012.
TD3 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10"
TD2 = "I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<\nD231458907UTO7408122F1204159<<<<<<<6"
TD1 = "I<UTOD231458907<<<<<<<<<<<<<<<\n7408122F1204159UTO<<<<<<<<<<<6\nERIKSSON<<ANNA<MARIA<<<<<<<<<<"


def test_check_digits_follow_the_731_weights() -> None:
    # Doc 9303 part 3's worked example: the date 520727 has the check digit 3.
    assert check_digit("520727") == "3"
    assert check_digit("L898902C3") == "6"
    assert check_digit("<<<<<") == "0"


@pytest.mark.parametrize(("zone", "kind", "kind_letter"), [(TD3, "TD3", "P"), (TD2, "TD2", "I"), (TD1, "TD1", "I")])
def test_the_icao_specimens_are_read_in_every_format(zone: str, kind: str, kind_letter: str) -> None:
    document = parse(zone, TODAY)
    assert (document.format, document.document_type, document.issuer) == (kind, kind_letter, "UTO")
    assert (document.birth, document.expiry) == (date(1974, 8, 12), date(2012, 4, 15))
    assert document.birth_year_month == (1974, 8)
    assert document.repaired == ()


def test_nothing_identifying_leaves_the_reader() -> None:
    fields = set(vars(parse(TD3, TODAY)))
    assert fields == {"format", "document_type", "issuer", "birth", "expiry", "repaired"}


def test_a_wrong_character_anywhere_checked_is_caught() -> None:
    tampered = TD3.replace("7408122", "7508122")  # a year changed, its check digit not
    with pytest.raises(MrzError) as caught:
        parse(tampered, TODAY)
    assert caught.value.code == "mrz_check_failed"


def test_an_ocr_confusion_is_repaired_only_where_it_makes_a_check_pass() -> None:
    misread = TD3.replace("7408122F", "74O8122F")  # the OCR read a zero in the birth date as the letter O
    document = parse(misread, TODAY)
    assert document.birth == date(1974, 8, 12)
    assert document.repaired == ("birth_date",)


def test_an_expired_document_fails_and_age_is_counted_from_the_birthday() -> None:
    expired = parse(TD3, TODAY)
    assert age_outcome(expired, 18, TODAY) == ("fail", ["document_expired"])
    assert age_outcome(expired, 18, date(2011, 1, 1)) == ("pass", [])
    assert age_on(date(2008, 10, 27), TODAY) == 17  # turns 18 tomorrow
    assert age_on(date(2008, 10, 26), TODAY) == 18
    assert age_on(date(2008, 2, 29), date(2026, 2, 28)) == 17  # a leap-day birthday comes on 1 March


@pytest.mark.parametrize(
    ("zone", "code"),
    [
        ("P<UTO\nL898902C36UTO", "mrz_unreadable"),
        (TD3.replace("7408122", "7413322"), "mrz_check_failed"),  # 33rd day: caught by the check digit first
        (TD3.replace("740812", "7408<<"), "mrz_check_failed"),
    ],
)
def test_broken_zones_are_refused_with_a_reason(zone: str, code: str) -> None:
    with pytest.raises(MrzError) as caught:
        parse(zone, TODAY)
    assert caught.value.code == code


def compose_td3(number: str, birth: str, expiry: str, personal: str) -> str:
    """A valid TD3 zone, built the way an issuing state would: every check digit computed."""
    number, personal = number.ljust(9, "<"), personal.ljust(14, "<")
    middle = f"{number}{check_digit(number)}UTO{birth}{check_digit(birth)}F{expiry}{check_digit(expiry)}"
    middle += f"{personal}{check_digit(personal)}"
    composite = middle[0:10] + middle[13:20] + middle[21:43]
    return "P<UTOSPECIMEN<<TEST".ljust(44, "<") + "\n" + middle + check_digit(composite)


dates = st.dates(min_value=date(1930, 1, 1), max_value=date(2025, 12, 31))
expiries = st.dates(min_value=date(2027, 1, 1), max_value=date(2070, 12, 31))
document_numbers = st.text(alphabet="ABCDEFGHJKLMNPRTUVWXY0123456789", min_size=6, max_size=9)
personal_numbers = st.text(alphabet="0123456789", max_size=14)


@given(document_numbers, dates, expiries, personal_numbers)
def test_any_valid_zone_reads_back_exactly(number: str, birth: date, expiry: date, personal: str) -> None:
    zone = compose_td3(number, f"{birth:%y%m%d}", f"{expiry:%y%m%d}", personal)
    document = parse(zone, TODAY)
    assert (document.birth, document.expiry, document.repaired) == (birth, expiry, ())


@given(dates, st.integers(min_value=0, max_value=5), st.integers(min_value=0, max_value=9))
def test_any_single_digit_change_in_the_birth_date_is_caught(birth: date, position: int, digit: int) -> None:
    good = f"{birth:%y%m%d}"
    if good[position] == str(digit):
        return  # not a change
    bad = good[:position] + str(digit) + good[position + 1 :]
    zone = compose_td3("L898902C3", good, "300101", "")
    with pytest.raises(MrzError):
        parse(zone.replace(f"UTO{good}", f"UTO{bad}"), TODAY)


# --- Reading what OCR read from a photo (Phase 6) ---

FUTURE = compose_td3("L898902C3", "900101", "360101", "ZE184226B").split("\n")


def test_ocr_lines_that_are_right_read_exactly_as_the_zone_does() -> None:
    document = read_ocr(FUTURE, TODAY)
    assert document == parse("\n".join(FUTURE), TODAY)
    assert document.repaired == ()


def test_the_names_line_is_ignored_whatever_ocr_made_of_it() -> None:
    """Only its document type and issuer are read: an age check needs no name, and no check digit covers it."""
    garbled = ["P<UTO" + "6K<<E4" * 6 + "<<<<<<<<", FUTURE[1]]
    document = read_ocr(garbled, TODAY)
    assert (document.document_type, document.issuer, document.birth) == ("P", "UTO", date(1990, 1, 1))


@pytest.mark.parametrize(
    "line",
    [
        FUTURE[1][:20] + "0" + FUTURE[1][20:],  # a character too many
        FUTURE[1][:38] + "<<" + FUTURE[1][38:],  # two too many, in a run of fillers
        FUTURE[1][:40] + FUTURE[1][41:],  # one missing
    ],
)
def test_a_line_one_or_two_characters_off_is_repaired_when_only_one_reading_passes(line: str) -> None:
    document = read_ocr([FUTURE[0], line], TODAY)
    assert (document.birth, document.expiry) == (date(1990, 1, 1), date(2036, 1, 1))
    assert "line_length" in document.repaired


def test_an_empty_optional_field_is_tried_when_ocr_misread_its_fillers() -> None:
    """A TD2 card's optional field is usually empty: long runs of fillers, which OCR misreads most. Its check digits
    decide whether "empty" is right; the dates keep their own check digits either way."""
    zone = parse(TD2, TODAY)
    misread = TD2.split("\n")[1][:28] + "<6<K<<4" + TD2.split("\n")[1][35:]
    document = read_ocr([TD2.split("\n")[0], misread], TODAY)
    assert (document.birth, document.expiry) == (zone.birth, zone.expiry)
    assert "optional_fields_read_as_empty" in document.repaired


@pytest.mark.parametrize(
    ("lines", "code"),
    [
        (["P<UTO"], "mrz_unreadable"),  # one line is no zone
        ([FUTURE[0], FUTURE[1][:30]], "mrz_check_failed"),  # far too short to repair
        ([FUTURE[0], FUTURE[1].replace("900101", "900102")], "mrz_check_failed"),  # a date its check digit refutes
    ],
)
def test_a_zone_too_damaged_to_trust_is_refused(lines: list[str], code: str) -> None:
    with pytest.raises(MrzError) as caught:
        read_ocr(lines, TODAY)
    assert caught.value.code == code


@given(birth=dates, expiry=expiries, cut=st.integers(min_value=0, max_value=43))
def test_a_dropped_character_never_yields_a_different_date(birth: date, expiry: date, cut: int) -> None:
    """Whatever character OCR drops, the repaired reading has the true dates, or there is no reading at all."""
    zone = compose_td3("X1234567", birth.strftime("%y%m%d"), expiry.strftime("%y%m%d"), "").split("\n")
    true = parse("\n".join(zone), TODAY)
    try:
        document = read_ocr([zone[0], zone[1][:cut] + zone[1][cut + 1 :]], TODAY)
    except MrzError:
        return
    assert (document.birth, document.expiry) == (true.birth, true.expiry)
