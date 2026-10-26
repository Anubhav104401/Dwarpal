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
