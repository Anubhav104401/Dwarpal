"""Check that a webhook really came from Dwarpal, and is recent, before acting on it."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from typing import Any

from dwarpal.errors import WebhookSignatureError

#: How old a signature may be, by default: five minutes. Older ones are refused as possible replays.
WEBHOOK_TOLERANCE_S = 300
DIGEST = re.compile(r"^[0-9a-f]{64}$")


def verify_webhook(
    raw_body: bytes | str,
    signature_header: str | None,
    secret: str,
    *,
    tolerance_s: int = WEBHOOK_TOLERANCE_S,
    now: float | None = None,
) -> dict[str, Any]:
    """The event in a webhook, once its `Dwarpal-Signature` header proves Dwarpal sent this very body, recently.

    Pass the body exactly as it arrived: parsing and re-serialising JSON changes the bytes, and the signature with them.
    """
    fields = dict(part.strip().split("=", 1) for part in (signature_header or "").split(",") if "=" in part)
    timestamp, given = fields.get("t", ""), fields.get("v1", "")
    if not timestamp.isdigit() or not DIGEST.match(given):
        raise WebhookSignatureError("the Dwarpal-Signature header is missing or malformed")
    if abs((time.time() if now is None else now) - int(timestamp)) > tolerance_s:
        raise WebhookSignatureError("the signature is too old, or from the future: this may be a replay")
    body = raw_body.encode("utf-8") if isinstance(raw_body, str) else raw_body
    expected = hmac.new(secret.encode("utf-8"), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    # Compared in constant time, so the time taken reveals nothing about how much of a forgery was right.
    if not hmac.compare_digest(expected, given):
        raise WebhookSignatureError("the signature does not match: the body or the secret is wrong")
    event: dict[str, Any] = json.loads(body)
    return event
