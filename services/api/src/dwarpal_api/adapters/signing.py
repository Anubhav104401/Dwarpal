"""Signing keys and age tokens. A private key exists in plain form only in memory; the database keeps it sealed."""

from __future__ import annotations

import base64
import os
import secrets
from datetime import datetime
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet, OKPKey
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from dwarpal_api.adapters.tables import SigningKey

ALG = "Ed25519"
JWT_TYPE = "dwarpal-age+jwt"
KEY_CREATION_LOCK = 7_316_001


class MasterKey:
    def __init__(self, encoded: str) -> None:
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) != 32:
            raise ValueError("the master key must be exactly 32 bytes, base64-encoded")
        self._aead = AESGCM(raw)

    def seal(self, plaintext: bytes, context: bytes) -> bytes:
        nonce = os.urandom(12)
        return nonce + self._aead.encrypt(nonce, plaintext, context)

    def open(self, sealed: bytes, context: bytes) -> bytes:
        return self._aead.decrypt(sealed[:12], sealed[12:], context)


class KeyRing:
    def __init__(self, master: MasterKey) -> None:
        self._master = master
        self._signing: OKPKey | None = None
        self._public: list[dict[str, Any]] = []

    async def load(self, session: AsyncSession, now: datetime) -> None:
        await session.execute(text("SELECT pg_advisory_xact_lock(:lock)"), {"lock": KEY_CREATION_LOCK})
        query = select(SigningKey).where(SigningKey.status.in_(("active", "retiring")))
        rows = list((await session.scalars(query)).all())
        active = next((row for row in rows if row.status == "active"), None)
        if active is None:
            active = self._create(now)
            session.add(active)
            rows.append(active)
        await session.commit()
        pem = self._master.open(active.private_key_sealed, active.kid.encode())
        self._signing = OKPKey.import_key(pem, parameters={"kid": active.kid})
        self._public = [row.public_jwk for row in rows]

    def _create(self, now: datetime) -> SigningKey:
        kid = f"sig_{now:%Y%m%d}_{secrets.token_hex(4)}"
        key = OKPKey.generate_key("Ed25519", parameters={"kid": kid, "use": "sig", "alg": ALG})
        sealed = self._master.seal(key.as_pem(private=True), kid.encode())
        return SigningKey(
            kid=kid, public_jwk=key.as_dict(private=False), private_key_sealed=sealed, status="active", created_at=now
        )

    def jwks(self) -> dict[str, Any]:
        return {"keys": self._public}

    def sign(self, claims: dict[str, Any]) -> str:
        if self._signing is None:
            raise RuntimeError("the key ring has not been loaded")
        header = {"alg": ALG, "typ": JWT_TYPE, "kid": self._signing.kid}
        return jwt.encode(header, claims, self._signing, algorithms=[ALG])

    def verify(self, token: str) -> dict[str, Any] | None:
        """The claims of an age token signed by one of our current keys, or None for anything else: a bad signature,
        an unknown or retired key, another algorithm or another type of token. Times are the caller's to check."""
        try:
            keys = KeySet([OKPKey.import_key(jwk) for jwk in self._public])
            decoded = jwt.decode(token, keys, algorithms=[ALG])
        except (JoseError, ValueError):
            return None
        if decoded.header.get("typ") != JWT_TYPE:
            return None
        return dict(decoded.claims)
