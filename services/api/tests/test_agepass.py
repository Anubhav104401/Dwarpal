"""Tests for the Age Pass's rules (Phase 9, D21): passes made, presented and checked, against a software holder."""

from __future__ import annotations

import contextlib
import json
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from age_pass_holder import Holder, disclosures_of
from hypothesis import given
from hypothesis import strategies as st
from joserfc import jwt
from joserfc.jwk import ECKey, OKPKey

from dwarpal_api.domain import agepass
from dwarpal_api.domain.agepass import AgePassError

ISSUER = "http://localhost:8000"
ISSUER_KEY = OKPKey.generate_key("Ed25519", parameters={"kid": "k1"})
NOW = datetime(2026, 11, 2, 12, tzinfo=UTC)
AUDIENCE = "vs_01ABCDEFGHJKMNPQRSTVWXYZ00"
TODAY = NOW.date()


def issue(holder: Holder, min_age: int = 18, livemode: bool = False, today: date = TODAY) -> list[str]:
    """Passes as the API issues them: one per holder key, each signed and joined to its disclosures."""
    passes = []
    for key in holder.public_keys():
        made = agepass.new_pass(ISSUER, min_age, livemode, agepass.holder_key(key), today)
        header = {"alg": "Ed25519", "typ": agepass.TYP, "kid": "k1"}
        passes.append(
            agepass.joined(jwt.encode(header, made.claims, ISSUER_KEY, algorithms=["Ed25519"]), made.disclosures)
        )
    holder.keep(passes)
    return passes


def verify(
    text: str, *, nonce: str = "n-1", min_age: int = 18, livemode: bool = False, now: datetime = NOW
) -> int | None:
    """What the API does with a presentation: every check, in order; the age line it proves."""
    shown = agepass.split(text)
    token = jwt.decode(shown.signed, ISSUER_KEY, algorithms=["Ed25519"])
    assert token.header["typ"] == agepass.TYP
    claims: dict[str, Any] = dict(token.claims)
    agepass.check_pass(claims, issuer=ISSUER, livemode=livemode, now=now)
    values = agepass.disclosed(claims, shown.disclosures)
    holder = agepass.holder_key(claims["cnf"]["jwk"])
    agepass.check_key_binding(
        shown.key_binding, holder, nonce=nonce, audience=AUDIENCE, now=now, signed_part=shown.signed_part
    )
    return agepass.line_proved(values, min_age)


def payload(kept: str) -> dict[str, Any]:
    return dict(jwt.decode(kept.split("~")[0], ISSUER_KEY, algorithms=["Ed25519"]).claims)


def now_s() -> int:
    return int(NOW.timestamp())


def test_a_pass_states_its_line_and_every_standard_line_below() -> None:
    assert agepass.lines_for(18) == [13, 16, 18]
    assert agepass.lines_for(13) == [13]
    assert agepass.lines_for(21) == [13, 16, 18, 21]
    assert agepass.lines_for(15) == [13, 15]
    assert agepass.lines_for(25) == [13, 16, 18, 21, 25]


def test_a_pass_presented_with_one_disclosure_proves_that_line_and_nothing_else() -> None:
    holder = Holder(2)
    issue(holder)
    shown = holder.present(0, ["age_over_18"], "n-1", AUDIENCE, iat=now_s())
    assert verify(shown) == 18
    assert verify(holder.present(1, ["age_over_16"], "n-1", AUDIENCE, iat=now_s()), min_age=16) == 16
    seen = agepass.disclosed(payload(holder.passes[0]), agepass.split(shown).disclosures)
    assert seen == {"age_over_18": True}  # the website learns one fact, not the pass's other lines


def test_a_pass_proves_no_more_than_it_states() -> None:
    holder = Holder(1)
    issue(holder, min_age=16)
    assert "age_over_18" not in disclosures_of(holder.passes[0])
    assert verify(holder.present(0, ["age_over_16"], "n-1", AUDIENCE, iat=now_s()), min_age=18) is None


def test_passes_from_one_check_share_nothing_that_could_link_them() -> None:
    count = 5
    holder = Holder(count)
    passes = issue(holder)
    claims = [payload(kept) for kept in passes]
    shared = {name for name in claims[0] if all(c[name] == claims[0][name] for c in claims)}
    assert shared == {"iss", "iat", "exp", "vct", "livemode", "_sd_alg"}  # the same for everyone issued that day
    digests = [digest for c in claims for digest in c["_sd"]]
    assert len(digests) == len(set(digests)) == count * agepass.DIGESTS
    salts = [json.loads(agepass.b64url_decode(d))[0] for kept in passes for d in disclosures_of(kept).values()]
    assert len(salts) == len(set(salts))
    assert claims[0]["iat"] == int(datetime(2026, 11, 2, tzinfo=UTC).timestamp())  # the day, not the second


def test_every_pass_lists_the_same_number_of_digests_whatever_its_lines() -> None:
    holder = Holder(1)
    sizes = {len(payload(issue(holder, min_age=age)[0])["_sd"]) for age in (13, 16, 18, 21, 25)}
    assert sizes == {agepass.DIGESTS}


def test_tampered_presentations_are_refused() -> None:
    holder, other = Holder(2), Holder(1)
    issue(holder)
    issue(other)
    good = holder.present(0, ["age_over_18"], "n-1", AUDIENCE, iat=now_s())
    signed, disclosure, key_binding = good.split("~")
    foreign = disclosures_of(other.passes[0])["age_over_18"]
    cases = {
        "tampered": [
            f"{signed}~{foreign}~{key_binding}",  # another pass's disclosure
            f"{signed}~{key_binding}",  # the disclosure dropped after signing
        ],
        "bad_key_binding": [
            agepass.joined(signed, [disclosure]) + other.present(0, ["age_over_18"], "n-1", AUDIENCE).split("~")[-1],
            holder.present(0, ["age_over_18"], "another nonce", AUDIENCE, iat=now_s()),
            holder.present(0, ["age_over_18"], "n-1", "vs_another", iat=now_s()),
            holder.present(0, ["age_over_18"], "n-1", AUDIENCE, iat=now_s() - 3600),
            holder.present(0, ["age_over_18"], "n-1", AUDIENCE, iat=now_s(), typ="JWT"),
        ],
    }
    for code, texts in cases.items():
        for text in texts:
            with pytest.raises(AgePassError) as caught:
                verify(text)
            assert caught.value.code == code


def test_a_pass_must_be_ours_unexpired_and_of_the_sessions_mode() -> None:
    holder = Holder(1)
    issue(holder)
    claims = payload(holder.passes[0])
    expired_at = datetime.fromtimestamp(claims["exp"], UTC)
    cases = {
        "not_an_age_pass": [{**claims, "iss": "https://elsewhere.example"}, {**claims, "vct": "urn:other"}],
        "wrong_mode": [{**claims, "livemode": True}],
        "expired": [claims],
        "malformed": [{**claims, "exp": "soon"}, {**claims, "iat": claims["iat"] + 86_400 * 200}],
    }
    for code, variants in cases.items():
        for variant in variants:
            when = expired_at if code == "expired" else NOW
            with pytest.raises(AgePassError) as caught:
                agepass.check_pass(variant, issuer=ISSUER, livemode=False, now=when)
            assert caught.value.code == code
    agepass.check_pass(claims, issuer=ISSUER, livemode=False, now=expired_at - timedelta(seconds=1))


def test_only_a_public_p256_key_on_the_curve_can_hold_a_pass() -> None:
    good = Holder(1).public_keys()[0]
    assert agepass.holder_key({**good, "kid": "extra", "use": "sig"}) == good  # extra fields are dropped
    private = ECKey.generate_key("P-256").as_dict(private=True)
    bad: list[object] = [
        {**good, "d": private["d"]},
        {**good, "crv": "P-384"},
        {**good, "kty": "OKP"},
        {**good, "x": good["y"]},  # (y, y) is not on the curve
        {**good, "x": good["x"][:-2]},
        {"kty": "EC", "crv": "P-256"},
        "not a key",
    ]
    for key in bad:
        with pytest.raises(AgePassError) as caught:
            agepass.holder_key(key)
        assert caught.value.code in ("invalid_holder_key", "malformed")


def test_malformed_presentations_and_disclosures_are_refused() -> None:
    for text in ("", "only-one-part", "a~~b", "a~b~", "x" * (agepass.MAX_LENGTH + 1), "jwt~dïsclosure~kb"):
        with pytest.raises(AgePassError):
            agepass.split(text)
    claims: dict[str, Any] = {"_sd": [], "iss": ISSUER}

    def listed(value: object) -> str:
        text = agepass.b64url_encode(json.dumps(value).encode())
        claims["_sd"].append(agepass.digest(text))
        return text

    for value in ({"a": 1, "b": 2, "c": 3}, ["salt", "iss", "evil"], ["salt", "x"], [1, "x", True]):
        with pytest.raises(AgePassError):
            agepass.disclosed(claims, [listed(value)])
    twice = listed(["salt", "age_over_18", True])
    with pytest.raises(AgePassError):
        agepass.disclosed(claims, [twice, twice])


def test_the_lowest_true_line_at_or_above_the_policys_is_the_one_proved() -> None:
    values = {"age_over_13": True, "age_over_16": True, "age_over_18": True, "age_over_21": False, "name": True}
    assert agepass.line_proved(values, 15) == 16
    assert agepass.line_proved(values, 18) == 18
    assert agepass.line_proved(values, 21) is None
    assert agepass.line_proved({"age_over_x": True, "age_over_18": "yes"}, 13) is None


@given(st.text(max_size=300))
def test_any_text_is_either_a_presentation_or_refused_with_our_error(text: str) -> None:
    with contextlib.suppress(AgePassError):
        shown = agepass.split(text)
        assert shown.signed_part + shown.key_binding == text


@given(st.text(max_size=60))
def test_base64url_is_read_strictly(text: str) -> None:
    with contextlib.suppress(AgePassError):
        assert agepass.b64url_encode(agepass.b64url_decode(text)) == text.rstrip("=") or len(text) % 4
