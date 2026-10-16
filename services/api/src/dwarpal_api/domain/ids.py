"""Identifiers: time-ordered UUIDv7 values, shown to the outside world with a type prefix such as vs_ or prj_."""

from __future__ import annotations

import os
import uuid

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
ENCODED_LENGTH = 26


class InvalidIdError(ValueError):
    """The text is not a well-formed identifier of the expected kind."""


def uuid7(unix_ms: int) -> uuid.UUID:
    random_bits = int.from_bytes(os.urandom(10))
    rand_a = (random_bits >> 62) & 0xFFF
    rand_b = random_bits & ((1 << 62) - 1)
    value = ((unix_ms & ((1 << 48) - 1)) << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    return uuid.UUID(int=value)


def encode(prefix: str, value: uuid.UUID) -> str:
    number = value.int
    chars = []
    for _ in range(ENCODED_LENGTH):
        chars.append(CROCKFORD[number & 31])
        number >>= 5
    return f"{prefix}_{''.join(reversed(chars))}"


def decode(prefix: str, text: str) -> uuid.UUID:
    head, separator, body = text.partition("_")
    if separator != "_" or head != prefix or len(body) != ENCODED_LENGTH:
        raise InvalidIdError(f"expected an identifier like {prefix}_…")
    number = 0
    for char in body.upper():
        digit = CROCKFORD.find(char)
        if digit < 0:
            raise InvalidIdError(f"invalid character {char!r} in identifier")
        number = number * 32 + digit
    if number >> 128:
        raise InvalidIdError("identifier is out of range")
    return uuid.UUID(int=number)
