"""Webhook safety without a database: which addresses are refused, how deliveries are signed, and when to retry."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import ipaddress
import socket
from typing import Any

import httpx
import pytest

from dwarpal_api.adapters.webhooks import (
    MAX_ADDRESSES,
    RETRY_AFTER_S,
    UnsafeUrlError,
    check_url,
    is_public,
    retry_delay,
    send,
    signature,
)

V4, V6 = "93.184.215.14", "2606:2800:220:1:248:1893:25c8:1946"  # public addresses (example.com's)

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
async def test_a_public_address_is_accepted_and_given_back_to_connect_to() -> None:
    assert await check_url(f"https://{V4}/hook", livemode=True, allow_private=False) == [V4]
    assert await check_url("http://localhost:3001/hook", livemode=False, allow_private=True) == []  # nothing looked up


@pytest.mark.anyio
async def test_every_address_a_name_gives_is_checked_and_given_back_once_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def resolve(host: str, port: int, **_: Any) -> list[tuple[Any, ...]]:
        assert (host, port) == ("hooks.example.com", 443), (host, port)
        v6 = (socket.AF_INET6, socket.SOCK_STREAM, 6, "", (V6, 443, 0, 0))
        v4 = (socket.AF_INET, socket.SOCK_STREAM, 6, "", (V4, 443))
        return [v6, v4, v4]

    monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", resolve)
    addresses = await check_url("https://hooks.example.com/in", livemode=True, allow_private=False)
    assert addresses == [V6, V4], addresses


@pytest.mark.anyio
async def test_a_webhook_goes_to_the_address_that_was_checked_still_naming_the_website() -> None:
    """DNS rebinding: a name that gave a public address to the check could give a private one to a second lookup. So
    there is none: the request goes to the checked address, with the name in Host and in TLS (SNI, and the certificate
    must be for it), and its connection is closed after it."""
    seen: list[httpx.Request] = []

    def receiver(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(204)

    async with httpx.AsyncClient(transport=httpx.MockTransport(receiver)) as http:
        outcome = await send(http, "https://Hooks.Example.com:8443/in?x=1", "whsec_t", "evt_1", b"{}", 1, [V4])
    assert outcome == (204, None), outcome
    (request,) = seen
    assert str(request.url) == f"https://{V4}:8443/in?x=1", request.url
    assert request.headers["host"] == "hooks.example.com:8443", request.headers
    assert request.extensions["sni_hostname"] == "hooks.example.com", request.extensions
    assert request.headers["connection"] == "close", request.headers


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("failure", "expected", "tried"),
    [
        # Never connected, so nothing was sent: the next checked address is tried, up to MAX_ADDRESSES.
        (httpx.ConnectError, (None, "ConnectError"), MAX_ADDRESSES),
        (httpx.ConnectTimeout, (None, "ConnectTimeout"), MAX_ADDRESSES),
        # Connected, then no answer: the event may have arrived, so it waits for the retry schedule instead.
        (httpx.ReadTimeout, (None, "ReadTimeout"), 1),
    ],
)
async def test_only_an_address_that_cant_be_reached_is_passed_over_for_the_next(
    failure: type[httpx.TransportError], expected: tuple[None, str], tried: int
) -> None:
    hosts: list[str] = []

    def receiver(request: httpx.Request) -> httpx.Response:
        hosts.append(request.url.host)
        raise failure("no luck", request=request)

    addresses = [V6, V4, "93.184.215.15", "93.184.215.16"]
    async with httpx.AsyncClient(transport=httpx.MockTransport(receiver)) as http:
        outcome = await send(http, "https://hooks.example.com/in", "whsec_t", "evt_1", b"{}", 1, addresses)
    assert outcome == expected, outcome
    assert hosts == addresses[:tried], hosts


@pytest.mark.anyio
async def test_the_next_address_answers_when_the_first_cant_be_reached() -> None:
    def receiver(request: httpx.Request) -> httpx.Response:
        if request.url.host == V6:  # a server without IPv6, say
            raise httpx.ConnectError("no route to host", request=request)
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(receiver)) as http:
        outcome = await send(http, "https://hooks.example.com/in", "whsec_t", "evt_1", b"{}", 1, [V6, V4])
    assert outcome == (200, None), outcome


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
