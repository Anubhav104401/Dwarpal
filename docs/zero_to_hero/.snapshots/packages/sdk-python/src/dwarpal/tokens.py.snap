"""Check a Dwarpal age token on the website's own server: its signature (Ed25519, with Dwarpal's published keys), who
issued it and for whom, that it hasn't expired, and what it says about the age the website requires."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

import httpx
from joserfc import errors, jwt
from joserfc.jwk import KeySet

from dwarpal.errors import AgeTokenError

#: The only signature algorithm Dwarpal uses, by its RFC 9864 name. Tokens claiming any other are refused.
ALGORITHM = "Ed25519"
#: The type every Dwarpal age token declares in its header.
TOKEN_TYPE = "dwarpal-age+jwt"  # noqa: S105 - a token type's name, not a password


@dataclass(frozen=True)
class AgeVerdict:
    allowed: bool  # true only if the check passed for exactly the age asked about
    outcome: Literal["pass", "fail", "reject"]
    session_id: str
    policy: str
    livemode: bool
    expires_at: datetime


class Keys:
    """An issuer's public keys, fetched from its `/.well-known/jwks.json` and kept. A token signed with a key not yet
    seen makes them be fetched once more — that is how a rotated key is picked up — but no more often than every
    `min_refresh_s` seconds, so forged tokens can't make the website hammer Dwarpal."""

    def __init__(self, issuer: str, http: httpx.Client | None = None, min_refresh_s: float = 60.0) -> None:
        self.url = f"{issuer.rstrip('/')}/.well-known/jwks.json"
        self._http = http or httpx.Client(timeout=10.0)
        self._min_refresh_s = min_refresh_s
        self._keys: KeySet | None = None
        self._fetched_at = 0.0
        self._lock = threading.Lock()

    def get(self, refresh: bool = False) -> KeySet:
        with self._lock:
            now = datetime.now(UTC).timestamp()
            stale = refresh and now - self._fetched_at >= self._min_refresh_s
            if self._keys is None or stale:
                response = self._http.get(self.url)
                response.raise_for_status()
                self._keys = KeySet.import_key_set(response.json())
                self._fetched_at = now
            return self._keys


_known: dict[str, Keys] = {}


def _keys_for(issuer: str) -> Keys:
    if issuer not in _known:
        _known[issuer] = Keys(issuer)
    return _known[issuer]


def _decode(token: str, keys: Keys) -> jwt.Token:
    try:
        return jwt.decode(token, keys.get(), algorithms=[ALGORITHM])
    except errors.InvalidKeyIdError:
        # A key not seen yet: perhaps just rotated. Fetch the keys again (rate-limited) and try once more.
        return jwt.decode(token, keys.get(refresh=True), algorithms=[ALGORITHM])


def verify_age_token(
    token: str,
    *,
    issuer: str,
    audience: str,
    min_age: int,
    session_id: str | None = None,
    keys: Keys | None = None,
) -> AgeVerdict:
    """Check an age token and say whether it allows entry at `min_age`. Raises `AgeTokenError` if it is invalid.

    `issuer` is the API's address exactly as its discovery document gives it; `audience` is your project's ID
    (`prj_…`); `session_id`, if given, is the session you expect, from the redirect back to your site.
    """
    if isinstance(min_age, bool) or not isinstance(min_age, int) or min_age < 1:
        raise ValueError("min_age must be a whole number of years, such as 18")
    try:
        decoded = _decode(token, keys or _keys_for(issuer))
        if decoded.header.get("typ") != TOKEN_TYPE:
            raise AgeTokenError("the token is not a Dwarpal age token")
        registry = jwt.JWTClaimsRegistry(
            iss={"essential": True, "value": issuer},
            aud={"essential": True, "value": audience},
            exp={"essential": True},
            iat={"essential": True},
            jti={"essential": True},
            sid={"essential": True},
            outcome={"essential": True},
        )
        registry.validate(decoded.claims)
    except errors.JoseError as error:
        raise AgeTokenError(f"the age token is not valid ({error.error})") from error
    claims: dict[str, Any] = decoded.claims
    outcome = claims["outcome"]
    if outcome not in ("pass", "fail", "reject"):
        raise AgeTokenError("the age token has an unknown outcome")
    sid = claims["sid"]
    if not isinstance(sid, str) or (session_id is not None and sid != session_id):
        raise AgeTokenError("the age token describes a different session")
    return AgeVerdict(
        allowed=outcome == "pass" and claims.get(f"age_over_{min_age}") is True,
        outcome=outcome,
        session_id=sid,
        policy=str(claims["policy"]) if isinstance(claims.get("policy"), str) else "",
        livemode=claims.get("livemode") is True,
        expires_at=datetime.fromtimestamp(int(claims["exp"]), UTC),
    )
