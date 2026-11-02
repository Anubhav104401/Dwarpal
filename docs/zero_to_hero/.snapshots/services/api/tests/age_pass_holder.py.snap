"""A software Age Pass holder for tests: what the verify page does in a browser — make key pairs, keep the passes it
is given, and present one with a key-binding JWT — so the server's checks run as they would against a real browser."""

from __future__ import annotations

import hashlib
import json
import time

from joserfc import jwt
from joserfc.jwk import ECKey

from dwarpal_api.domain.agepass import BATCH, b64url_decode, b64url_encode


def disclosures_of(kept: str) -> dict[str, str]:
    """A kept pass's disclosures, by the claim each discloses."""
    _, *disclosures, _ = kept.split("~")
    return {json.loads(b64url_decode(item))[1]: item for item in disclosures}


def present(
    kept: str,
    key: ECKey,
    names: list[str],
    nonce: str,
    audience: str,
    iat: int | None = None,
    typ: str = "kb+jwt",
) -> str:
    """A presentation of a kept pass: the signed JWT, the chosen disclosures, and a key-binding JWT over them."""
    signed = kept.split("~")[0]
    chosen = [disclosures_of(kept)[name] for name in names]
    signed_part = signed + "~" + "".join(item + "~" for item in chosen)
    claims = {
        "iat": int(time.time()) if iat is None else iat,
        "aud": audience,
        "nonce": nonce,
        "sd_hash": b64url_encode(hashlib.sha256(signed_part.encode("ascii")).digest()),
    }
    return signed_part + jwt.encode({"alg": "ES256", "typ": typ}, claims, key, algorithms=["ES256"])


class Holder:
    """A browser holding Age Passes: one P-256 key per pass, the private halves never leaving this object."""

    def __init__(self, count: int = BATCH) -> None:
        self.keys = [ECKey.generate_key("P-256") for _ in range(count)]
        self.passes: list[str] = []

    def public_keys(self) -> list[dict[str, str]]:
        return [{name: str(key.as_dict(private=False)[name]) for name in ("kty", "crv", "x", "y")} for key in self.keys]

    def keep(self, passes: list[str]) -> None:
        self.passes = passes

    def present(self, index: int, names: list[str], nonce: str, audience: str, **options: int | str) -> str:
        return present(self.passes[index], self.keys[index], names, nonce, audience, **options)  # type: ignore[arg-type]
