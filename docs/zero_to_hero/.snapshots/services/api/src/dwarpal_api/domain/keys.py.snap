"""Secrets given to relying parties: API keys (dk_test_… / dk_live_…) and one-time client secrets for sessions."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

LOOKUP_LENGTH = 12
# What a key may do: create sessions, read their results, add policy versions, and manage webhooks. A website's server
# that only reads results can be given a key that can't create sessions, and the other way round.
SCOPES = frozenset({"sessions:read", "sessions:write", "policies:write", "webhooks:write"})


@dataclass(frozen=True)
class NewSecret:
    plaintext: str
    lookup: str
    digest: bytes


def digest(secret: str) -> bytes:
    return hashlib.sha256(secret.encode("utf-8")).digest()


def matches(secret: str, stored_digest: bytes) -> bool:
    return hmac.compare_digest(digest(secret), stored_digest)


def generate_api_key(livemode: bool) -> NewSecret:
    body = secrets.token_urlsafe(32)
    plaintext = f"dk_{'live' if livemode else 'test'}_{body}"
    return NewSecret(plaintext=plaintext, lookup=body[:LOOKUP_LENGTH], digest=digest(plaintext))


def parse_api_key(text: str) -> tuple[bool, str] | None:
    for livemode, prefix in ((False, "dk_test_"), (True, "dk_live_")):
        if text.startswith(prefix) and len(text) > len(prefix) + LOOKUP_LENGTH:
            return livemode, text[len(prefix) : len(prefix) + LOOKUP_LENGTH]
    return None


def generate_client_secret(public_session_id: str) -> NewSecret:
    plaintext = f"{public_session_id}_secret_{secrets.token_urlsafe(24)}"
    return NewSecret(plaintext=plaintext, lookup=public_session_id, digest=digest(plaintext))
