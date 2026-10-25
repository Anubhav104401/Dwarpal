"""Webhook safety without a database: which addresses are refused, how deliveries are signed, and when to retry."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress

import pytest

from dwarpal_api.adapters.webhooks import RETRY_AFTER_S, UnsafeUrlError, check_url, is_public, retry_delay, signature

INSIDE = [
    "http://127.0.0.1/hook",  # this computer
    "https://localhost/hook",  # a name for this computer
    "https://10.0.0.5/hook",  # a private network
    "https://192.168.1.20/hook",
    "https://169.254.169.254/latest/meta-data",  # the cloud's metadata service, the classic SSRF prize
    "https://[::1]/hook",
    "https://[::ffff:10.0.0.1]/hook",  # a private IPv4 address dressed as IPv6
    "https://[fc00::1]/hook",
    "https://0.0.0.0/hook",
]


@pytest.mark.anyio
@pytest.mark.parametrize("url", INSIDE)
async def test_addresses_inside_a_network_are_refused(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        await check_url(url, livemode=False, allow_private=False)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("url", "livemode"),
    [
        ("ftp://93.184.215.14/hook", False),  # not a web address
        ("http://93.184.215.14/hook", True),  # live webhooks need https
        ("https://user:pass@93.184.215.14/hook", False),  # no credentials in the address
    ],
)
async def test_badly_formed_addresses_are_refused(url: str, livemode: bool) -> None:
    with pytest.raises(UnsafeUrlError):
        await check_url(url, livemode=livemode, allow_private=True)


@pytest.mark.anyio
async def test_a_public_address_is_accepted() -> None:
    await check_url("https://93.184.215.14/hook", livemode=True, allow_private=False)


def test_public_means_global_and_not_multicast() -> None:
    assert is_public(ipaddress.ip_address("93.184.215.14"))
    assert not is_public(ipaddress.ip_address("224.0.0.1"))
    assert not is_public(ipaddress.ip_address("100.64.0.1"))  # carrier-grade NAT, shared space


def test_the_signature_is_an_hmac_of_the_time_and_the_exact_body() -> None:
    body = b'{"id":"evt_1"}'
    header = signature("whsec_test", 1_700_000_000, body)
    expected = hmac.new(b"whsec_test", b"1700000000." + body, hashlib.sha256).hexdigest()
    assert header == f"t=1700000000,v1={expected}"
    assert signature("whsec_test", 1_700_000_000, body + b" ") != header


def test_retries_follow_the_schedule_then_stop() -> None:
    assert [retry_delay(n) for n in range(1, len(RETRY_AFTER_S) + 2)] == [*RETRY_AFTER_S, None]
