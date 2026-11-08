"""Web origins — `scheme://host[:port]` — written one way, so a project's allowed origins and a session's return address
can be compared as plain text (decision D29). Pure rules, no I/O."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

MAX_ORIGINS = 10
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
DEFAULT_PORTS = {"https": 443, "http": 80}
# A host name: dot-separated labels of letters, digits and inner hyphens (international names in their xn-- form).
HOST_NAME = re.compile(r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*")


class InvalidOriginError(ValueError):
    """Not an origin this project may allow; the message says what is wrong, in words a person can act on."""


def _host(host: str) -> str:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        if not HOST_NAME.fullmatch(host) or len(host) > 253:
            raise InvalidOriginError(f"{host!r} isn't a host name") from None
        return host
    return f"[{address}]" if address.version == 6 else str(address)


def origin_of(url: str) -> str:
    """The origin of an address, written as browsers write it: lower-case, without a default port. Raises
    InvalidOriginError if the address has no http(s) origin at all."""
    parts = urlsplit(url.strip())
    scheme, host = parts.scheme.lower(), (parts.hostname or "").lower()
    if scheme not in DEFAULT_PORTS or not host:
        raise InvalidOriginError("an origin starts with https:// and a host name")
    try:
        port = parts.port
    except ValueError:
        port = 0
    if port == 0:  # out of range, or 0, which Python accepts but no website listens on
        raise InvalidOriginError("the port must be a number from 1 to 65535")
    netloc = _host(host)
    if port is not None and port != DEFAULT_PORTS[scheme]:
        netloc = f"{netloc}:{port}"
    return f"{scheme}://{netloc}"


def allowed_origin(text: str, production: bool) -> str:
    """One origin a project may allow, checked and written the standard way. Only an origin — no path, query, fragment
    or user name — and https, except http for this computer while developing."""
    parts = urlsplit(text.strip())
    if parts.username is not None or parts.password is not None:
        raise InvalidOriginError("an origin has no user name or password")
    if parts.path not in ("", "/") or parts.query or parts.fragment:
        raise InvalidOriginError("an origin is just https://host[:port], with no path, query or fragment")
    origin = origin_of(text)
    host = (parts.hostname or "").lower()
    if origin.startswith("http://") and (production or host not in LOCAL_HOSTS):
        raise InvalidOriginError("use https:// (http:// is allowed only for localhost while developing)")
    return origin


def allowed_origins(texts: list[str], production: bool) -> list[str]:
    """A project's whole list: each origin checked, duplicates dropped, in the order given, at most MAX_ORIGINS."""
    origins = list(dict.fromkeys(allowed_origin(text, production) for text in texts))
    if len(origins) > MAX_ORIGINS:
        raise InvalidOriginError(f"a project may allow at most {MAX_ORIGINS} origins")
    return origins
