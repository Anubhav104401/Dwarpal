"""Tests for the Python SDK, with the API faked by httpx's own mock transport: no network, no server."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from dwarpal import (
    AgeTokenError,
    AsyncClient,
    Client,
    DwarpalApiError,
    Keys,
    WebhookSignatureError,
    verify_age_token,
    verify_webhook,
)
from joserfc import jwt
from joserfc.jwk import KeySet, OKPKey

API = "https://api.dwarpal.example"
KEY = "dk_test_" + "a" * 32
SESSION = "vs_" + "0" * 26
PROJECT = "prj_" + "1" * 26
CREATED = {
    "id": SESSION,
    "object": "verification_session",
    "status": "created",
    "livemode": False,
    "policy": "uk_osa_18",
    "client_secret": "secret",
    "url": f"https://dwarpal.example/v/{SESSION}#cs=secret",
    "expires_at": "2026-11-02T10:00:00+00:00",
}


def api(handler: Any) -> httpx.Client:
    return httpx.Client(base_url=API, transport=httpx.MockTransport(handler))


def test_a_session_is_created_with_the_key_and_only_the_fields_given() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json=CREATED)

    session = Client(KEY, API, http=api(handler)).create_session(policy="uk_osa_18", return_url="https://shop/x")
    assert seen[0].headers["authorization"] == f"Bearer {KEY}"
    assert json.loads(seen[0].content) == {"policy": "uk_osa_18", "return_url": "https://shop/x"}
    assert (session.id, session.status, session.url) == (SESSION, "created", CREATED["url"])
    assert session.expires_at == datetime(2026, 11, 2, 10, tzinfo=UTC)


def test_an_idempotency_key_is_sent_only_when_given_and_checked_first() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json=CREATED)

    client = Client(KEY, API, http=api(handler))
    client.create_session(idempotency_key="Zr3uQ0d9Hq1sV6tY")
    client.create_session()
    assert [request.headers.get("idempotency-key") for request in seen] == ["Zr3uQ0d9Hq1sV6tY", None]
    assert json.loads(seen[0].content) == {}  # a header, never part of the body
    for bad in ("short", "has a space in it", "x" * 256, "abcdefgh\n"):
        with pytest.raises(ValueError, match="idempotency_key"):
            client.create_session(idempotency_key=bad)
    assert len(seen) == 2  # nothing was sent for the malformed keys


def test_a_refusal_carries_the_api_s_stable_code_and_request_id() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        body = {"code": "policy_not_supported", "detail": "no such policy"}
        return httpx.Response(422, json=body, headers={"x-request-id": "req_1"})

    with pytest.raises(DwarpalApiError) as caught:
        Client(KEY, API, http=api(handler)).create_session(policy="nope")
    assert (caught.value.status, caught.value.code, caught.value.request_id) == (422, "policy_not_supported", "req_1")


def test_bad_keys_and_session_ids_are_refused_before_anything_is_sent() -> None:
    with pytest.raises(ValueError, match="secret key"):
        Client("pk_live_nothing", API)
    with pytest.raises(ValueError, match="session ID"):
        Client(KEY, API, http=api(lambda _: httpx.Response(500))).retrieve_session("../admin")


def test_a_malformed_answer_is_reported_not_trusted() -> None:
    answer = {**CREATED, "status": "approved"}  # no such status
    with pytest.raises(TypeError, match="status"):
        Client(KEY, API, http=api(lambda _: httpx.Response(201, json=answer))).create_session()


@pytest.mark.anyio
async def test_the_async_client_reads_a_completed_session() -> None:
    result = {
        "id": SESSION, "object": "verification_session", "status": "completed", "outcome": "pass",
        "livemode": False, "policy": "uk_osa_18", "min_age": 18, "attempts": 1, "external_ref": None,
        "created_at": "2026-11-02T09:00:00+00:00", "expires_at": "2026-11-02T10:00:00+00:00",
        "completed_at": "2026-11-02T09:01:00+00:00", "age_token": "a.b.c",
    }  # fmt: skip
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=result))
    async with AsyncClient(KEY, API, http=httpx.AsyncClient(base_url=API, transport=transport)) as dwarpal:
        session = await dwarpal.retrieve_session(SESSION)
    assert (session.outcome, session.min_age, session.age_token) == ("pass", 18, "a.b.c")


# --- Age tokens ---

SIGNER = OKPKey.generate_key("Ed25519", parameters={"kid": "k1"})


def token(key: OKPKey = SIGNER, typ: str = "dwarpal-age+jwt", **overrides: Any) -> str:
    now = int(time.time())
    claims = {
        "iss": API, "aud": PROJECT, "iat": now, "nbf": now, "exp": now + 600, "jti": "j", "sid": SESSION,
        "outcome": "pass", "age_over_18": True, "policy": "uk_osa_18", "livemode": False,
    }  # fmt: skip
    claims.update(overrides)
    return jwt.encode({"alg": "Ed25519", "typ": typ, "kid": key.kid}, claims, key, algorithms=["Ed25519"])


def keys(*published: OKPKey) -> Keys:
    """An issuer's keys, served by a fake JWKS address that counts how often it is asked."""
    calls = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json=KeySet(list(published)).as_dict(private=False))

    found = Keys(API, http=httpx.Client(transport=httpx.MockTransport(handler)), min_refresh_s=0)
    found.calls = calls  # type: ignore[attr-defined]
    return found


def check(value: str, found: Keys, **options: Any) -> Any:
    return verify_age_token(value, issuer=API, audience=PROJECT, min_age=18, keys=found, **options)


def test_a_genuine_pass_allows_entry_at_its_age_only() -> None:
    found = keys(SIGNER)
    assert check(token(), found, session_id=SESSION).allowed is True
    assert verify_age_token(token(), issuer=API, audience=PROJECT, min_age=21, keys=found).allowed is False


@pytest.mark.parametrize(
    ("value", "why"),
    [
        (token(iss="https://evil.example"), "not valid"),
        (token(aud="prj_someone_else"), "not valid"),
        (token(exp=int(time.time()) - 1), "not valid"),
        (token(typ="JWT"), "not a Dwarpal age token"),
        (token(outcome="maybe"), "unknown outcome"),
        (token(key=OKPKey.generate_key("Ed25519", parameters={"kid": "k1"})), "not valid"),  # forged, same key ID
    ],
)
def test_forged_foreign_expired_or_odd_tokens_are_refused(value: str, why: str) -> None:
    with pytest.raises(AgeTokenError, match=why):
        check(value, keys(SIGNER))


def test_a_token_for_another_session_is_refused() -> None:
    with pytest.raises(AgeTokenError, match="different session"):
        check(token(), keys(SIGNER), session_id="vs_" + "9" * 26)


def test_a_new_signing_key_is_fetched_once_when_a_token_needs_it() -> None:
    rotated = OKPKey.generate_key("Ed25519", parameters={"kid": "k2"})
    found = keys(SIGNER, rotated)
    found._keys = KeySet([SIGNER])  # what was fetched before the rotation
    assert check(token(key=rotated), found).allowed is True
    assert found.calls["n"] == 1  # type: ignore[attr-defined]


# --- Webhooks ---

SECRET = "whsec_test_only"  # noqa: S105 - a throwaway secret for tests
BODY = b'{"id":"evt_1","object":"event","type":"verification_session.completed","data":{}}'


def signed(body: bytes = BODY, at: int | None = None, secret: str = SECRET) -> str:
    stamp = int(time.time()) if at is None else at
    digest = hmac.new(secret.encode(), f"{stamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={stamp},v1={digest}"


def test_a_genuine_webhook_gives_its_event() -> None:
    assert verify_webhook(BODY, signed(), SECRET)["type"] == "verification_session.completed"


@pytest.mark.parametrize(
    "header",
    [
        None,
        "garbage",
        signed(secret="wrong"),  # noqa: S106 - a wrong secret, on purpose
        signed(at=int(time.time()) - 3600),
        signed(body=b"{}"),
    ],
)
def test_missing_forged_stale_or_mismatched_webhooks_are_refused(header: str | None) -> None:
    with pytest.raises(WebhookSignatureError):
        verify_webhook(BODY, header, SECRET)
