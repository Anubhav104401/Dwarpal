"""Tests for the passkey checks (Phase 9), with a software device that makes real WebAuthn answers."""

from __future__ import annotations

import base64
import contextlib
import json
import os

import pytest
from hypothesis import given
from hypothesis import strategies as st
from passkey_device import Device, b64url, cbor

from dwarpal_api.domain.webauthn import (
    WebAuthnError,
    b64url_decode,
    cbor_decode,
    parse_authenticator_data,
    public_key_of,
    verify_assertion,
    verify_registration,
)

ORIGINS = ["http://localhost:3000"]
RP = "localhost"


def register(device: Device, challenge: bytes) -> tuple[bytes, bytes, int]:
    answer = device.create(b64url(challenge))
    made = verify_registration(
        b64url_decode(answer["client_data_json"]),
        b64url_decode(answer["attestation_object"]),
        challenge,
        ORIGINS,
        RP,
    )
    return made.credential_id, made.public_key, made.sign_count


def sign_in(device: Device, public_key: bytes, stored: int, challenge: bytes, **options: object) -> int:
    answer = device.get(b64url(challenge), **options)  # type: ignore[arg-type]
    return verify_assertion(
        public_key,
        stored,
        b64url_decode(answer["client_data_json"]),
        b64url_decode(answer["authenticator_data"]),
        b64url_decode(answer["signature"]),
        challenge,
        ORIGINS,
        RP,
    )


@given(st.recursive(
    st.none() | st.booleans() | st.integers(-(2**63), 2**64 - 1) | st.binary(max_size=40) | st.text(max_size=20),
    lambda inner: st.lists(inner, max_size=4) | st.dictionaries(st.integers(-50, 50), inner, max_size=4),
    max_leaves=12,
))  # fmt: skip
def test_cbor_reads_back_what_a_device_writes(value: object) -> None:
    encoded = cbor(value)
    assert cbor_decode(encoded) == (value, len(encoded))


@given(st.binary(max_size=64))
def test_cbor_refuses_garbage_with_its_own_error_and_nothing_else(data: bytes) -> None:
    with contextlib.suppress(WebAuthnError):
        cbor_decode(data)


def test_cbor_refuses_deep_nesting_cut_strings_odd_or_repeated_keys_and_bad_text() -> None:
    odd_key, repeated_key, bad_text = b"\xa1\x80\x00", b"\xa2\x01\x00\x01\x00", b"\x62\xff\xfe"
    for data in (b"\x81" * 20 + b"\x00", b"\x45ab", b"\x1c", b"", odd_key, repeated_key, bad_text):
        with pytest.raises(WebAuthnError):
            cbor_decode(data)


@pytest.mark.parametrize("algorithm", [-8, -7])
def test_a_passkey_registers_and_then_signs_in(algorithm: int) -> None:
    device = Device(algorithm=algorithm)
    credential_id, public_key, count = register(device, b"c" * 32)
    assert credential_id == device.credential_id
    assert public_key_of(public_key)[0] == algorithm
    assert sign_in(device, public_key, count, b"d" * 32) == 1
    assert sign_in(device, public_key, 1, b"e" * 32) == 2


def test_registration_refuses_the_wrong_challenge_site_or_kind_and_an_unverified_person() -> None:
    challenge = b"c" * 32
    cases = {
        "wrong_challenge": (Device(), {"challenge": b64url(b"x" * 32)}),
        "wrong_origin": (Device(), {"origin": "https://evil.example"}),
        "wrong_rp": (Device(rp_id="evil.example"), {}),
        "not_verified": (Device(flags=0x01), {}),
    }
    for code, (device, changes) in cases.items():
        answer = device.create(changes.get("challenge", b64url(challenge)), origin=changes.get("origin"))
        with pytest.raises(WebAuthnError) as caught:
            verify_registration(
                b64url_decode(answer["client_data_json"]),
                b64url_decode(answer["attestation_object"]),
                challenge,
                ORIGINS,
                RP,
            )
        assert caught.value.code == code, code
    sign_in_answer = Device().get(b64url(challenge))  # a sign-in's answer offered as a registration
    with pytest.raises(WebAuthnError) as caught:
        verify_registration(b64url_decode(sign_in_answer["client_data_json"]), cbor({}), challenge, ORIGINS, RP)
    assert caught.value.code == "wrong_type"


def test_registration_refuses_rsa_other_algorithms_and_broken_keys() -> None:
    rsa = cbor({1: 3, 3: -257, -1: b"n", -2: b"e"})
    short_ed25519 = cbor({1: 1, 3: -8, -1: 6, -2: b"short"})
    off_the_curve = cbor({1: 2, 3: -7, -1: 1, -2: bytes(32), -3: bytes(31) + bytes([1])})
    for key in (rsa, short_ed25519, off_the_curve, cbor([1, 2])):
        with pytest.raises(WebAuthnError) as caught:
            public_key_of(key)
        assert caught.value.code == "unsupported_key"


def test_a_sign_in_with_a_forged_signature_or_another_passkeys_key_is_refused() -> None:
    device, other = Device(), Device()
    _, public_key, _ = register(device, b"c" * 32)
    _, other_key, _ = register(other, b"c" * 32)
    with pytest.raises(WebAuthnError) as caught:
        sign_in(device, other_key, 0, b"d" * 32)
    assert caught.value.code == "bad_signature"
    answer = device.get(b64url(b"d" * 32))
    tampered = bytearray(b64url_decode(answer["signature"]))
    tampered[0] ^= 1
    with pytest.raises(WebAuthnError):
        verify_assertion(
            public_key,
            0,
            b64url_decode(answer["client_data_json"]),
            b64url_decode(answer["authenticator_data"]),
            bytes(tampered),
            b"d" * 32,
            ORIGINS,
            RP,
        )


def test_a_counter_that_goes_backwards_means_a_copied_passkey_but_zero_is_a_syncing_one() -> None:
    device = Device()
    _, public_key, _ = register(device, b"c" * 32)
    assert sign_in(device, public_key, 0, b"d" * 32, step=5) == 5
    with pytest.raises(WebAuthnError) as caught:
        sign_in(device, public_key, 9, b"e" * 32)  # the server has seen 9: a 6 came from another copy
    assert caught.value.code == "cloned"
    syncing = Device()
    _, synced_key, _ = register(syncing, b"c" * 32)
    assert sign_in(syncing, synced_key, 0, b"f" * 32, step=0) == 0
    assert sign_in(syncing, synced_key, 0, b"g" * 32, step=0) == 0


def test_a_sign_in_answer_cant_be_replayed_against_a_new_challenge() -> None:
    device = Device()
    _, public_key, _ = register(device, b"c" * 32)
    answer = device.get(b64url(b"d" * 32))
    with pytest.raises(WebAuthnError) as caught:
        verify_assertion(
            public_key,
            0,
            b64url_decode(answer["client_data_json"]),
            b64url_decode(answer["authenticator_data"]),
            b64url_decode(answer["signature"]),
            b"new" * 11,
            ORIGINS,
            RP,
        )
    assert caught.value.code == "wrong_challenge"


def test_malformed_answers_are_refused_with_the_passkey_error() -> None:
    for client, auth_data in ((b"not json", b"\x00" * 37), (json.dumps([1]).encode(), b"\x00" * 37)):
        with pytest.raises(WebAuthnError):
            verify_assertion(b"", 0, client, auth_data, b"", b"c", ORIGINS, RP)
    with pytest.raises(WebAuthnError):
        parse_authenticator_data(b"\x00" * 36)
    with pytest.raises(WebAuthnError):
        parse_authenticator_data(b"\x00" * 32 + b"\x40" + b"\x00" * 10)
    with pytest.raises(WebAuthnError):
        b64url_decode("a")
    assert b64url_decode(base64.urlsafe_b64encode(os.urandom(5)).decode().rstrip("=")) is not None
