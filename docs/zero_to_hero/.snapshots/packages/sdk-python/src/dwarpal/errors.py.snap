"""What can go wrong, as exceptions a website can catch one by one."""

from __future__ import annotations


class DwarpalApiError(Exception):
    """The API refused a request. `code` is stable and meant for programs; the message is meant for people."""

    def __init__(self, status: int, code: str, message: str, request_id: str | None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.request_id = request_id


class AgeTokenError(Exception):
    """An age token failed verification: its signature, issuer, audience, type, age or session didn't check out."""


class WebhookSignatureError(Exception):
    """A webhook failed verification: its signature header was missing, malformed, too old, or didn't match."""
