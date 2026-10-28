"""One-time codes from an authenticator app (TOTP, RFC 6238): the six digits that change every 30 seconds."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from urllib.parse import quote

STEP_S = 30
DIGITS = 6
WINDOW = 1  # also accept the code just before and just after, for clocks that disagree a little


def new_secret() -> str:
    """20 random bytes (160 bits, RFC 4226's recommendation) as Base32, the form authenticator apps expect."""
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def code_at(secret: str, step: int) -> str:
    """The code for one 30-second step: an HMAC-SHA1 of the step number, cut down to six digits (RFC 4226)."""
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    digest = hmac.new(key, step.to_bytes(8, "big"), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = int.from_bytes(digest[offset : offset + 4], "big") & 0x7FFF_FFFF
    return str(number % 10**DIGITS).zfill(DIGITS)


def accepted_step(secret: str, code: str, unix_s: float, last_step: int | None) -> int | None:
    """The step a code belongs to, if it is right for now (give or take one step) and newer than the last code
    used; otherwise None. Remembering the step makes every code single-use, even within its 30 seconds."""
    if len(code) != DIGITS or not code.isdigit():
        return None
    now = int(unix_s // STEP_S)
    for step in range(now - WINDOW, now + WINDOW + 1):
        if (last_step is None or step > last_step) and hmac.compare_digest(code_at(secret, step), code):
            return step
    return None


def provisioning_uri(secret: str, account: str, issuer: str = "Dwarpal") -> str:
    """The otpauth:// address an authenticator app reads, usually from a QR code."""
    label = quote(f"{issuer}:{account}")
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits={DIGITS}&period={STEP_S}"
    )


RECOVERY_CODES = 10
# Base32's alphabet in lower case: no 0, 1, 8 or 9, which are easy to mistake for letters when copied by hand.
RECOVERY_ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"


def new_recovery_codes(count: int = RECOVERY_CODES) -> list[str]:
    """Single-use codes for when the phone is lost: 10 random letters each (50 bits), shown as abcde-fghij."""
    codes = []
    for _ in range(count):
        letters = "".join(secrets.choice(RECOVERY_ALPHABET) for _ in range(10))
        codes.append(f"{letters[:5]}-{letters[5:]}")
    return codes


def recovery_digest(key: bytes, user_id: bytes, code: str) -> str:
    """What is stored instead of a recovery code: an HMAC of it, keyed by a server secret and bound to its user.
    Spaces, dashes and capitals don't matter, so a code typed as ABCDE FGHIJ still counts."""
    letters = "".join(code.split()).replace("-", "").lower()
    return hmac.new(key, user_id + letters.encode(), hashlib.sha256).hexdigest()
