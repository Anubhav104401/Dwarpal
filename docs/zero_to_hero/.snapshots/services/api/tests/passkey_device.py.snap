"""A software passkey device for tests: it makes real WebAuthn answers, signed with a real key made here, so the
server's checks run exactly as they would against a phone or a security key."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import struct
from dataclasses import dataclass, field
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


def cbor(value: Any) -> bytes:
    """The few CBOR kinds WebAuthn uses, written as a device writes them."""

    def head(major: int, n: int) -> bytes:
        if n < 24:
            return bytes([major << 5 | n])
        for info, size in ((24, 1), (25, 2), (26, 4), (27, 8)):
            if n < 1 << (8 * size):
                return bytes([major << 5 | info]) + n.to_bytes(size, "big")
        raise ValueError(n)

    if value is None:
        return bytes([0xF6])
    if isinstance(value, bool):
        return bytes([0xF5 if value else 0xF4])
    if isinstance(value, int):
        return head(0, value) if value >= 0 else head(1, -1 - value)
    if isinstance(value, bytes):
        return head(2, len(value)) + value
    if isinstance(value, str):
        return head(3, len(value.encode())) + value.encode()
    if isinstance(value, list):
        return head(4, len(value)) + b"".join(cbor(item) for item in value)
    if isinstance(value, dict):
        return head(5, len(value)) + b"".join(cbor(k) + cbor(v) for k, v in value.items())
    raise TypeError(type(value))


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


@dataclass
class Device:
    """One passkey on one device, for one site. `algorithm` is -8 (Ed25519) or -7 (P-256)."""

    rp_id: str = "localhost"
    origin: str = "http://localhost:3000"
    algorithm: int = -8
    flags: int = 0x01 | 0x04  # the person was present and verified
    counter: int = 0
    credential_id: bytes = field(default_factory=lambda: os.urandom(16))

    def __post_init__(self) -> None:
        self._ed = ed25519.Ed25519PrivateKey.generate()
        self._ec = ec.generate_private_key(ec.SECP256R1())

    def cose_key(self) -> bytes:
        if self.algorithm == -8:
            raw = self._ed.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            return cbor({1: 1, 3: -8, -1: 6, -2: raw})
        point = self._ec.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        return cbor({1: 2, 3: -7, -1: 1, -2: point[1:33], -3: point[33:]})

    def _auth_data(self, extra_flags: int = 0, attested: bytes = b"") -> bytes:
        rp_hash = hashlib.sha256(self.rp_id.encode()).digest()
        return rp_hash + bytes([self.flags | extra_flags]) + struct.pack(">I", self.counter) + attested

    def _client(self, kind: str, challenge: str, origin: str | None) -> bytes:
        return json.dumps({"type": kind, "challenge": challenge, "origin": origin or self.origin}).encode()

    def create(self, challenge: str, origin: str | None = None) -> dict[str, str]:
        """`navigator.credentials.create`'s answer, as the browser hands it over (base64url fields)."""
        attested = bytes(16) + struct.pack(">H", len(self.credential_id)) + self.credential_id + self.cose_key()
        auth_data = self._auth_data(0x40, attested)
        attestation = cbor({"fmt": "none", "attStmt": {}, "authData": auth_data})
        return {
            "id": b64url(self.credential_id),
            "client_data_json": b64url(self._client("webauthn.create", challenge, origin)),
            "attestation_object": b64url(attestation),
        }

    def get(self, challenge: str, origin: str | None = None, step: int = 1) -> dict[str, str]:
        """`navigator.credentials.get`'s answer: the counter goes up by `step` (0 for a passkey that syncs)."""
        self.counter += step
        client = self._client("webauthn.get", challenge, origin)
        auth_data = self._auth_data()
        signed = auth_data + hashlib.sha256(client).digest()
        signature = self._ed.sign(signed) if self.algorithm == -8 else self._ec.sign(signed, ec.ECDSA(hashes.SHA256()))
        return {
            "id": b64url(self.credential_id),
            "client_data_json": b64url(client),
            "authenticator_data": b64url(auth_data),
            "signature": b64url(signature),
        }
