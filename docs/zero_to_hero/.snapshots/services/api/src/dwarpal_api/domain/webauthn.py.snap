"""Passkeys (WebAuthn, W3C Level 3) for console sign-in (Phase 9): pure rules, no I/O.

A passkey is a key pair made by the person's device. The device keeps the private key and signs a fresh challenge
from the server; the server keeps only the public key and checks the signature. Nothing to guess, nothing to phish:
the device signs only for the site (the *relying party*) that registered it.

Only what the console needs is supported: "none" attestation (the console doesn't need to know the device's make),
user verification required (a PIN, fingerprint or face on the device, so a passkey counts as two factors), and the
two signature algorithms passkeys use in practice: Ed25519 (EdDSA, COSE -8) and ECDSA P-256 (ES256, COSE -7).
"""

from __future__ import annotations

import base64
import hashlib
import json
import struct
from dataclasses import dataclass
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519

# Flags in the authenticator data's fifth byte.
USER_PRESENT = 0x01
USER_VERIFIED = 0x04
ATTESTED_CREDENTIAL = 0x40
MAX_DEPTH = 8  # nesting deeper than this is no WebAuthn structure: refuse rather than recurse
EDDSA, ES256 = -8, -7


class WebAuthnError(ValueError):
    """The device's answer can't be trusted. `code` is stable, for programs; the message says which check failed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def b64url_decode(text: str) -> bytes:
    """Base64url without padding, as WebAuthn and the browser send binary values."""
    try:
        return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    except (ValueError, TypeError):
        raise WebAuthnError("malformed", "a value isn't valid base64url") from None


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


# --- CBOR (RFC 8949): the compact binary format of WebAuthn's structures. Only what WebAuthn uses is read. ---


def _length(data: bytes, at: int, info: int) -> tuple[int, int]:
    """A CBOR item's argument: in the first byte's low bits (< 24), or in the next 1, 2, 4 or 8 bytes."""
    if info < 24:
        return info, at
    sizes = {24: 1, 25: 2, 26: 4, 27: 8}
    if info not in sizes or at + sizes[info] > len(data):
        raise WebAuthnError("malformed", "a CBOR item has a length this reader doesn't accept")
    size = sizes[info]
    return int.from_bytes(data[at : at + size], "big"), at + size


def cbor_decode(data: bytes, at: int = 0, depth: int = 0) -> tuple[Any, int]:
    """One CBOR item starting at `at`: its value, and where the next item starts."""
    if depth > MAX_DEPTH or at >= len(data):
        raise WebAuthnError("malformed", "the CBOR data is cut short or nested too deeply")
    major, info = data[at] >> 5, data[at] & 0x1F
    value, at = _length(data, at + 1, info) if major != 7 else (info, at + 1)
    if major == 0:  # unsigned integer
        return value, at
    if major == 1:  # negative integer: -1 - value
        return -1 - value, at
    if major in (2, 3):  # byte string, text string
        if at + value > len(data):
            raise WebAuthnError("malformed", "a CBOR string runs past the end")
        raw = data[at : at + value]
        if major == 2:
            return raw, at + value
        try:
            return raw.decode("utf-8"), at + value
        except UnicodeDecodeError:
            raise WebAuthnError("malformed", "a CBOR text string isn't valid UTF-8") from None
    if major == 4:  # array
        items = []
        for _ in range(value):
            item, at = cbor_decode(data, at, depth + 1)
            items.append(item)
        return items, at
    if major == 5:  # map
        entries: dict[Any, Any] = {}
        for _ in range(value):
            key, at = cbor_decode(data, at, depth + 1)
            if isinstance(key, bool) or not isinstance(key, int | str) or key in entries:
                raise WebAuthnError("malformed", "a CBOR map has a key that isn't a number or text, or has it twice")
            entries[key], at = cbor_decode(data, at, depth + 1)
        return entries, at
    simple = {20: False, 21: True, 22: None}
    if major == 7 and info in simple:
        return simple[info], at
    raise WebAuthnError("malformed", "the CBOR data holds a kind of item WebAuthn doesn't use")


# --- The authenticator's data, and the public key in it. ---


@dataclass(frozen=True)
class AuthenticatorData:
    rp_id_hash: bytes
    flags: int
    sign_count: int
    credential_id: bytes | None = None
    public_key: bytes | None = None  # the COSE key, as its CBOR bytes: what is stored


def parse_authenticator_data(data: bytes) -> AuthenticatorData:
    """32 bytes of the relying party's hash, 1 byte of flags, a 4-byte signature counter, then — when the flags say
    a credential is attested — its 16-byte device model ID, a 2-byte length, the credential's ID and its COSE key."""
    if len(data) < 37:
        raise WebAuthnError("malformed", "the authenticator data is too short")
    flags = data[32]
    (sign_count,) = struct.unpack(">I", data[33:37])
    if not flags & ATTESTED_CREDENTIAL:
        return AuthenticatorData(data[:32], flags, sign_count)
    if len(data) < 55:
        raise WebAuthnError("malformed", "the attested credential data is too short")
    (id_length,) = struct.unpack(">H", data[53:55])
    credential_id = data[55 : 55 + id_length]
    _, end = cbor_decode(data, 55 + id_length)
    return AuthenticatorData(data[:32], flags, sign_count, credential_id, data[55 + id_length : end])


def public_key_of(cose: bytes) -> tuple[int, ed25519.Ed25519PublicKey | ec.EllipticCurvePublicKey]:
    """A COSE key (RFC 9053) as the algorithm and a key `cryptography` can check signatures with."""
    key, _ = cbor_decode(cose)
    if not isinstance(key, dict):
        raise WebAuthnError("unsupported_key", "the public key isn't a COSE key")
    kty, alg, crv = key.get(1), key.get(3), key.get(-1)
    try:
        if kty == 1 and alg == EDDSA and crv == 6 and isinstance(key.get(-2), bytes):  # OKP, Ed25519
            return EDDSA, ed25519.Ed25519PublicKey.from_public_bytes(key[-2])
        if kty == 2 and alg == ES256 and crv == 1 and isinstance(key.get(-2), bytes) and isinstance(key.get(-3), bytes):
            point = b"\x04" + key[-2] + key[-3]  # EC2 on P-256: the uncompressed point x, y
            return ES256, ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), point)
    except ValueError:  # the right kind of key, but not a valid one: a wrong length, or a point off the curve
        raise WebAuthnError("unsupported_key", "the public key isn't a valid key") from None
    raise WebAuthnError("unsupported_key", "only Ed25519 and P-256 passkeys are accepted")


# --- The two ceremonies. ---


def _client_data(raw: bytes, kind: str, challenge: bytes, origins: list[str]) -> None:
    """The browser's own record of what it was asked to sign: the right kind of request, our challenge, our site."""
    try:
        client = json.loads(raw)
    except ValueError:
        raise WebAuthnError("malformed", "the client data isn't JSON") from None
    if not isinstance(client, dict) or client.get("type") != kind:
        raise WebAuthnError("wrong_type", f"expected a {kind} request")
    if not isinstance(client.get("challenge"), str) or b64url_decode(client["challenge"]) != challenge:
        raise WebAuthnError("wrong_challenge", "the answer is for a different challenge")
    if client.get("origin") not in origins:
        raise WebAuthnError("wrong_origin", "the answer comes from another site")


def _checked(data: AuthenticatorData, rp_id: str) -> None:
    if data.rp_id_hash != hashlib.sha256(rp_id.encode()).digest():
        raise WebAuthnError("wrong_rp", "the passkey belongs to another site")
    if not data.flags & USER_PRESENT or not data.flags & USER_VERIFIED:
        raise WebAuthnError("not_verified", "the device didn't verify the person (PIN, fingerprint or face)")


@dataclass(frozen=True)
class NewPasskey:
    credential_id: bytes
    public_key: bytes  # the COSE key, as stored
    sign_count: int


def verify_registration(
    client_data_json: bytes, attestation_object: bytes, challenge: bytes, origins: list[str], rp_id: str
) -> NewPasskey:
    """Check a new passkey's registration (`navigator.credentials.create`) and return what to store."""
    _client_data(client_data_json, "webauthn.create", challenge, origins)
    attestation, _ = cbor_decode(attestation_object)
    if not isinstance(attestation, dict) or not isinstance(attestation.get("authData"), bytes):
        raise WebAuthnError("malformed", "the attestation object has no authenticator data")
    data = parse_authenticator_data(attestation["authData"])
    _checked(data, rp_id)
    if data.credential_id is None or data.public_key is None:
        raise WebAuthnError("malformed", "the registration carries no credential")
    public_key_of(data.public_key)  # refuse an algorithm we couldn't check later
    return NewPasskey(data.credential_id, data.public_key, data.sign_count)


def verify_assertion(
    public_key: bytes,
    stored_count: int,
    client_data_json: bytes,
    authenticator_data: bytes,
    signature: bytes,
    challenge: bytes,
    origins: list[str],
    rp_id: str,
) -> int:
    """Check a sign-in with a passkey (`navigator.credentials.get`); return the signature counter to store next."""
    _client_data(client_data_json, "webauthn.get", challenge, origins)
    data = parse_authenticator_data(authenticator_data)
    _checked(data, rp_id)
    signed = authenticator_data + hashlib.sha256(client_data_json).digest()
    algorithm, key = public_key_of(public_key)
    try:
        if algorithm == EDDSA and isinstance(key, ed25519.Ed25519PublicKey):
            key.verify(signature, signed)
        elif isinstance(key, ec.EllipticCurvePublicKey):
            key.verify(signature, signed, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        raise WebAuthnError("bad_signature", "the passkey's signature doesn't match") from None
    # A counter that doesn't go up means two devices answer for one passkey: a cloned key. (Many passkeys that sync
    # between devices always send 0, which says nothing either way.)
    if data.sign_count and data.sign_count <= stored_count:
        raise WebAuthnError("cloned", "the passkey's counter went backwards: it may have been copied")
    return data.sign_count
