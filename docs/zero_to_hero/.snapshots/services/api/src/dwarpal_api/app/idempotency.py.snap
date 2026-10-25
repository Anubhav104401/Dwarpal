"""Idempotency: a website that sends the same request twice, because the first answer was lost on the way, gets the
first answer again instead of a second verification session."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
from collections.abc import Awaitable, Callable
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from dwarpal_api.adapters.store import FlowStore
from dwarpal_api.errors import ApiError

KEY_SHAPE = re.compile(r"^[\x21-\x7e]{8,255}$")  # 8 to 255 printable characters, no spaces
NONCE_BYTES = 12


def fingerprint(operation: str, body: dict[str, Any]) -> str:
    """What the request asked for, as a digest: the same key may only ever be used for the same request."""
    canonical = json.dumps({"operation": operation, "body": body}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def server_secret(master_key_b64: str) -> bytes:
    return hmac.new(base64.b64decode(master_key_b64), b"dwarpal idempotency", hashlib.sha256).digest()


def _derive(secret: bytes, key: str, purpose: str) -> bytes:
    return hmac.new(secret, f"{purpose}\x00{key}".encode(), hashlib.sha256).digest()


async def once(
    store: FlowStore,
    secret: bytes,
    scope: str,
    key: str,
    request_fingerprint: str,
    ttl_s: int,
    make: Callable[[], Awaitable[dict[str, Any]]],
) -> tuple[dict[str, Any], bool]:
    """Run `make` at most once per (scope, key) within `ttl_s`; return its reply, and whether it was replayed."""
    if not KEY_SHAPE.match(key):
        raise ApiError(422, "invalid_idempotency_key", "Idempotency-Key must be 8 to 255 printable characters")
    slot = f"idem:{scope}:{_derive(secret, key, 'slot').hex()}"
    pending = json.dumps({"state": "pending", "fingerprint": request_fingerprint}).encode()
    existing = await store.claim(slot, pending, ttl_s)
    if existing is not None:
        return _replay(secret, key, slot, request_fingerprint, json.loads(existing)), True
    try:
        reply = await make()
    except BaseException:
        await store.drop(slot)  # nothing was made: the same key may be tried again
        raise
    nonce = secrets.token_bytes(NONCE_BYTES)
    sealed = AESGCM(_derive(secret, key, "seal")).encrypt(nonce, json.dumps(reply).encode(), slot.encode())
    record = {"state": "done", "fingerprint": request_fingerprint, "reply": base64.b64encode(nonce + sealed).decode()}
    await store.put(slot, json.dumps(record).encode(), ttl_s)
    return reply, False


def _replay(secret: bytes, key: str, slot: str, request_fingerprint: str, record: dict[str, Any]) -> dict[str, Any]:
    if record["fingerprint"] != request_fingerprint:
        raise ApiError(422, "idempotency_key_reused", "this Idempotency-Key was already used for a different request")
    if record["state"] != "done":
        raise ApiError(409, "idempotency_in_progress", "a request with this Idempotency-Key is still running; retry")
    packed = base64.b64decode(record["reply"])
    opened = AESGCM(_derive(secret, key, "seal")).decrypt(packed[:NONCE_BYTES], packed[NONCE_BYTES:], slot.encode())
    reply: dict[str, Any] = json.loads(opened)
    return reply
