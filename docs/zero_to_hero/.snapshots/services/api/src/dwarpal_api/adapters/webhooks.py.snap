"""Sending webhooks safely: only to public addresses, signed so that receivers can trust them, retried on a schedule."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import ipaddress
import secrets
import socket
from collections.abc import Sequence
from urllib.parse import urlsplit

import httpx

# Seconds to wait after each failed attempt: 1 min, 5 min, 30 min, 2 h, 6 h, 12 h, 24 h. Then the delivery is dead.
RETRY_AFTER_S = (60, 300, 1800, 7200, 21_600, 43_200, 86_400)
SECRET_PREFIX = "whsec_"  # noqa: S105 - the public prefix of every webhook secret, not a secret itself
# A name may point to several addresses: up to this many are tried in turn, while none of them can be reached.
MAX_ADDRESSES = 3
# Failures before anything was sent: the next address may answer. Any other failure may come after the event arrived.
UNREACHED = (httpx.ConnectError, httpx.ConnectTimeout)


class UnsafeUrlError(ValueError):
    """The address is not one Dwarpal will send to."""


def is_public(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True only for addresses on the public internet: not private, loopback, link-local, multicast or reserved."""
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped is not None:
        address = address.ipv4_mapped  # ::ffff:10.0.0.1 is 10.0.0.1 in disguise
    return address.is_global and not address.is_multicast


async def check_url(url: str, *, livemode: bool, allow_private: bool) -> list[str]:
    """Refuse an address an attacker could use to make Dwarpal call inside its own network (SSRF).

    Returns the addresses the name points to, every one checked, for `send` to connect to: asked again, the name's
    owner could answer with another address (DNS rebinding). When private addresses are allowed (in development),
    nothing is looked up and none are returned."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise UnsafeUrlError("the webhook URL must be an http:// or https:// address")
    if livemode and parts.scheme != "https":
        raise UnsafeUrlError("live webhooks must use https://")
    if parts.username or parts.password:
        raise UnsafeUrlError("the webhook URL must not contain a user name or password")
    if allow_private:
        return []
    port = parts.port or (443 if parts.scheme == "https" else 80)
    try:
        found = await asyncio.get_running_loop().getaddrinfo(parts.hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise UnsafeUrlError(f"the host {parts.hostname} can't be found") from None
    addresses = list(dict.fromkeys(str(address[0]) for *_, address in found))  # in the order given, each once
    # Every address the name points to must be public: an attacker's name may hold a public and a private one.
    for address in addresses:
        if not is_public(ipaddress.ip_address(address)):
            raise UnsafeUrlError(f"the host {parts.hostname} points to a non-public address")
    return addresses


def new_secret() -> str:
    return SECRET_PREFIX + secrets.token_urlsafe(32)


def signature(secret: str, timestamp: int, body: bytes) -> str:
    """The Dwarpal-Signature header: when it was signed, and an HMAC-SHA256 of that time and the exact body."""
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


async def send(
    http: httpx.AsyncClient,
    url: str,
    secret: str,
    event_id: str,
    body: bytes,
    timestamp: int,
    addresses: Sequence[str] = (),
) -> tuple[int | None, str | None]:
    """POST one event — to one of `addresses`, the ones `check_url` checked, when it gave any. Returns the receiver's
    status (None if it never answered) and, unless it accepted the event with a 2xx status, a short reason why not."""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Dwarpal-Webhooks/1",
        "Dwarpal-Event-Id": event_id,
        "Dwarpal-Signature": signature(secret, timestamp, body),
    }
    target = httpx.URL(url)
    tries: list[tuple[httpx.URL, dict[str, str], dict[str, str]]] = [(target, headers, {})]  # the name, looked up
    if addresses:
        # To a checked address, still naming the website: in the Host header, and to TLS, which then insists on a
        # certificate for that name. Connection: close — a connection made for one name never carries another's event.
        named = {**headers, "Host": target.netloc.decode("ascii"), "Connection": "close"}
        sni = {"sni_hostname": target.raw_host.decode("ascii")}
        tries = [(target.copy_with(host=address), named, sni) for address in addresses[:MAX_ADDRESSES]]
    reason = None
    for to, with_headers, extensions in tries:
        try:
            # No redirects: a public address must not be able to bounce the request into a private one.
            response = await http.post(
                to, content=body, headers=with_headers, extensions=extensions, follow_redirects=False
            )
        except UNREACHED as error:
            reason = type(error).__name__
            continue
        except httpx.HTTPError as error:
            return None, type(error).__name__
        return response.status_code, None if response.is_success else f"HTTP {response.status_code}"
    return None, reason


def retry_delay(attempts_made: int) -> int | None:
    """Seconds until the next try after `attempts_made` failures, or None when it's time to give up."""
    return RETRY_AFTER_S[attempts_made - 1] if attempts_made <= len(RETRY_AFTER_S) else None
