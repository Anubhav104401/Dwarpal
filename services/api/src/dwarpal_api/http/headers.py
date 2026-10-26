"""Security headers on every answer the API sends. The API serves only JSON, so browsers are told to treat it as
nothing else: never run it, never frame it, never cache it, and never tell anyone where a request came from."""

from __future__ import annotations

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

HEADERS = {
    "X-Content-Type-Options": "nosniff",  # a JSON answer is JSON, never guessed to be a script or a page
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",  # for browsers too old for frame-ancestors
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cache-Control": "no-store",  # answers carry secrets and tokens; a route that may be cached says so itself
}
# The interactive documentation is a real page with scripts and styles, so it is left without the strict policy.
DOCUMENTATION = ("/docs", "/redoc")
HSTS = "max-age=63072000; includeSubDomains"  # two years of HTTPS only


class SecurityHeaders:
    def __init__(self, app: ASGIApp, production: bool = False) -> None:
        self.app = app
        self.production = production

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        documentation = scope["path"].startswith(DOCUMENTATION)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in HEADERS.items():
                    if name not in headers and not (documentation and name == "Content-Security-Policy"):
                        headers[name] = value
                if self.production:
                    headers["Strict-Transport-Security"] = HSTS
            await send(message)

        await self.app(scope, receive, send_with_headers)
