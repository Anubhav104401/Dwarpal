"""The Age Pass (Phase 9, decision D21): a reusable "over N" pass that a person keeps in their own browser, so the
next website needs no new face check. Pure rules, no I/O.

The format is the IETF's SD-JWT VC — a JSON Web Token signed by Dwarpal whose claims stay hidden until the holder
chooses to disclose them (*selective disclosure*, SD-JWT), and which is bound to a key made by the holder's browser
(*key binding*), so a copied pass is useless without that key. A presentation is

    <the pass's signed JWT>~<one disclosure>~<a key-binding JWT>

Passes are issued 20 at a time, each with its own salts, key and signature, and each is used once: two websites
see two passes that share nothing but Dwarpal's name, the issue day and the pass's type.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from cryptography.hazmat.primitives.asymmetric import ec
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import ECKey

TYP = "dc+sd-jwt"  # a pass's type, as SD-JWT VC names it
KB_TYP = "kb+jwt"  # the type of the holder's key-binding JWT
VCT = "urn:dwarpal:age-pass:1"  # what kind of credential this is: Dwarpal's Age Pass, first version
HOLDER_ALG = "ES256"  # the holder's key: ECDSA on P-256, which every browser's WebCrypto can make
LIFETIME = timedelta(days=90)
BATCH = 20  # passes issued at once, each used once
LINES = (13, 16, 18, 21)  # the age lines a pass can state, besides the policy's own
DIGESTS = 6  # every pass lists this many digests, real and decoy, so its size says nothing about its lines
SKEW_S = 300  # how far a key-binding JWT's time may differ from ours
MAX_LENGTH = 4096  # about three times a presentation with one disclosure: refuse anything longer unread
B64URL = re.compile(r"^[A-Za-z0-9_-]*$")


class AgePassError(ValueError):
    """A pass or a presentation that can't be trusted. `code` is stable, for programs; the message says why."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(text: str) -> bytes:
    """Strict base64url: only its own 64 characters (Python's decoder would quietly skip any others)."""
    if not B64URL.match(text) or len(text) % 4 == 1:
        raise AgePassError("malformed", "a value isn't valid base64url")
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def digest(disclosure: str) -> str:
    """A disclosure's digest, as the signed pass lists it: SHA-256 of its base64url text."""
    return b64url_encode(hashlib.sha256(disclosure.encode("ascii")).digest())


def lines_for(min_age: int) -> list[int]:
    """The age lines a pass from a check at `min_age` states: that age, and every standard line below it. Passing
    "over 18" proves "over 16" and "over 13" too; nothing is said about lines above."""
    return sorted({line for line in LINES if line < min_age} | {min_age})


def holder_key(jwk: object) -> dict[str, str]:
    """The holder's public key, as a JWK: an EC key on P-256 whose point is really on the curve, and no private part.
    Returned with only the fields that define it, so nothing else the browser sent ends up in a pass."""
    if not isinstance(jwk, dict) or jwk.get("kty") != "EC" or jwk.get("crv") != "P-256":
        raise AgePassError("invalid_holder_key", "the holder's key must be an EC key on P-256")
    if "d" in jwk:
        raise AgePassError("invalid_holder_key", "a private key was sent: only the public half may leave the browser")
    x, y = jwk.get("x"), jwk.get("y")
    if not isinstance(x, str) or not isinstance(y, str):
        raise AgePassError("invalid_holder_key", "the holder's key has no coordinates")
    raw_x, raw_y = b64url_decode(x), b64url_decode(y)
    if len(raw_x) != 32 or len(raw_y) != 32:
        raise AgePassError("invalid_holder_key", "the holder's key has coordinates of the wrong length")
    try:
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), b"\x04" + raw_x + raw_y)
    except ValueError:
        raise AgePassError("invalid_holder_key", "the holder's key isn't a point on P-256") from None
    return {"kty": "EC", "crv": "P-256", "x": x, "y": y}


@dataclass(frozen=True)
class NewPass:
    claims: dict[str, Any]  # for Dwarpal to sign
    disclosures: list[str]  # one per age line, kept by the holder beside the signed pass


def new_pass(
    issuer: str,
    min_age: int,
    livemode: bool,
    holder: dict[str, str],
    today: date,
    random: Callable[[int], bytes] = os.urandom,
) -> NewPass:
    """One pass: a disclosure for each age line, each with its own 128-bit salt; their digests, padded with decoys to
    a fixed count and sorted; and the pass's few plain claims. The issue time is the start of the day, so passes
    issued on one day can't be told apart by the second."""
    disclosures = [
        b64url_encode(json.dumps([b64url_encode(random(16)), f"age_over_{line}", True]).encode())
        for line in lines_for(min_age)
    ]
    digests = [digest(item) for item in disclosures]
    digests += [b64url_encode(hashlib.sha256(random(32)).digest()) for _ in range(DIGESTS - len(digests))]
    issued = datetime(today.year, today.month, today.day, tzinfo=UTC)
    claims = {
        "iss": issuer,
        "iat": int(issued.timestamp()),
        "exp": int((issued + LIFETIME).timestamp()),
        "vct": VCT,
        "livemode": livemode,
        "cnf": {"jwk": holder},
        "_sd": sorted(digests),
        "_sd_alg": "sha-256",
    }
    return NewPass(claims, disclosures)


def joined(signed: str, disclosures: list[str]) -> str:
    """A pass as the holder keeps it: the signed JWT, then each disclosure, each followed by `~`."""
    return signed + "~" + "".join(item + "~" for item in disclosures)


@dataclass(frozen=True)
class Presentation:
    signed: str  # the pass's JWT, signed by Dwarpal
    disclosures: list[str]  # what the holder chose to show
    key_binding: str  # the holder's JWT, signed with the key the pass is bound to
    signed_part: str  # everything before the key-binding JWT: what its `sd_hash` must cover


def split(text: str) -> Presentation:
    """Take a presentation apart at its `~` separators: the signed pass first, the key-binding JWT last."""
    if len(text) > MAX_LENGTH:
        raise AgePassError("malformed", "the presentation is too long")
    if not text.isascii():  # every part is base64url: anything else is refused here, before hashing needs ASCII
        raise AgePassError("malformed", "a presentation holds only base64url, dots and ~")
    parts = text.split("~")
    if len(parts) < 2 or not all(parts):
        raise AgePassError("malformed", "a presentation is a pass, its disclosures and a key-binding JWT, with ~")
    signed, *disclosures, key_binding = parts
    return Presentation(signed, disclosures, key_binding, text[: len(text) - len(key_binding)])


def check_pass(claims: dict[str, Any], *, issuer: str, livemode: bool, now: datetime) -> None:
    """The signed pass's own claims, once its signature has been checked: ours, an Age Pass, of the session's mode,
    not yet expired, and with the digest algorithm this module knows."""
    if claims.get("iss") != issuer or claims.get("vct") != VCT or claims.get("_sd_alg") != "sha-256":
        raise AgePassError("not_an_age_pass", "this isn't an Age Pass from this issuer")
    if claims.get("livemode") is not livemode:
        raise AgePassError("wrong_mode", "a test pass works only in test sessions, and a live one only in live ones")
    exp, iat = claims.get("exp"), claims.get("iat")
    if not isinstance(exp, int) or not isinstance(iat, int) or isinstance(exp, bool) or isinstance(iat, bool):
        raise AgePassError("malformed", "the pass has no valid times")
    if now.timestamp() >= exp:
        raise AgePassError("expired", "the pass has expired")
    if iat > now.timestamp() + SKEW_S:
        raise AgePassError("malformed", "the pass is dated in the future")


def disclosed(claims: dict[str, Any], disclosures: list[str]) -> dict[str, Any]:
    """The claims the holder disclosed. Each disclosure must be one the pass lists by its digest, only once, and of
    the shape [salt, name, value]; anything else means the presentation was tampered with."""
    listed = claims.get("_sd")
    if not isinstance(listed, list):
        raise AgePassError("malformed", "the pass lists no digests")
    values: dict[str, Any] = {}
    for item in disclosures:
        if digest(item) not in listed:
            raise AgePassError("tampered", "a disclosure doesn't belong to this pass")
        try:
            decoded = json.loads(b64url_decode(item))
        except ValueError:
            raise AgePassError("malformed", "a disclosure isn't JSON") from None
        if not isinstance(decoded, list) or len(decoded) != 3:
            raise AgePassError("malformed", "a disclosure isn't [salt, name, value]")
        salt, name, value = decoded
        if not isinstance(salt, str) or not isinstance(name, str) or name in values or name in claims:
            raise AgePassError("malformed", "a disclosure has no salt, or repeats a claim")
        values[name] = value
    return values


def check_key_binding(
    key_binding: str, holder: dict[str, str], *, nonce: str, audience: str, now: datetime, signed_part: str
) -> None:
    """The holder's proof: a JWT signed with the key the pass is bound to, for this audience and this one-time nonce,
    made just now, and covering exactly the pass and the disclosures it came with (`sd_hash`)."""
    key: dict[str, str | list[str]] = {**holder}
    try:
        token = jwt.decode(key_binding, ECKey.import_key(key), algorithms=[HOLDER_ALG])
    except (JoseError, ValueError):
        raise AgePassError("bad_key_binding", "the presentation wasn't signed with the pass's key") from None
    claims = token.claims
    if token.header.get("typ") != KB_TYP:
        raise AgePassError("bad_key_binding", "the key-binding JWT has the wrong type")
    if claims.get("nonce") != nonce or claims.get("aud") != audience:
        raise AgePassError("bad_key_binding", "the presentation was made for another request")
    iat = claims.get("iat")
    if not isinstance(iat, int) or isinstance(iat, bool) or abs(iat - now.timestamp()) > SKEW_S:
        raise AgePassError("bad_key_binding", "the presentation wasn't made just now")
    expected = b64url_encode(hashlib.sha256(signed_part.encode("ascii")).digest())
    if claims.get("sd_hash") != expected:
        raise AgePassError("tampered", "the presentation's disclosures aren't the ones the holder signed")


def line_proved(values: dict[str, Any], min_age: int) -> int | None:
    """The lowest age line at or above `min_age` that the disclosed claims state as true, or None."""
    lines = []
    for name, value in values.items():
        number = name.removeprefix("age_over_")
        if number != name and number.isdigit() and value is True and int(number) >= min_age:
            lines.append(int(number))
    return min(lines, default=None)
