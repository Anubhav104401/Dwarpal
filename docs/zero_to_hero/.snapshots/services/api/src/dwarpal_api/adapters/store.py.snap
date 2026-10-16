"""Short-lived state in Valkey: flow tokens and one-time challenges. Everything stored here expires on its own."""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from typing import Any

from redis.asyncio import Redis


def _hashed(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class FlowStore:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def ping(self) -> None:
        await self._client.ping()

    async def open_flow(self, session_id: uuid.UUID, ttl_s: int) -> str:
        token = secrets.token_urlsafe(32)
        await self._client.set(f"flow:{_hashed(token)}", str(session_id), ex=ttl_s)
        return token

    async def session_for(self, token: str) -> uuid.UUID | None:
        value = await self._client.get(f"flow:{_hashed(token)}")
        if value is None:
            return None
        return uuid.UUID(value.decode() if isinstance(value, bytes) else value)

    async def issue_challenge(
        self, session_id: uuid.UUID, ttl_s: int, budget: int, budget_ttl_s: int
    ) -> dict[str, Any] | None:
        counter = f"challenges:{session_id}"
        await self._client.set(counter, 0, ex=budget_ttl_s, nx=True)
        if await self._client.incr(counter) > budget:
            return None
        challenge = {
            "challenge_id": secrets.token_urlsafe(16),
            "nonce": secrets.token_urlsafe(16),
            "poses": [],
            "colours": [],
            "expires_in": ttl_s,
        }
        stored = json.dumps({"session_id": str(session_id), **challenge})
        await self._client.set(f"challenge:{challenge['challenge_id']}", stored, ex=ttl_s)
        return challenge

    async def take_challenge(self, challenge_id: str, session_id: uuid.UUID) -> bool:
        stored = await self._client.getdel(f"challenge:{challenge_id}")
        return stored is not None and json.loads(stored)["session_id"] == str(session_id)
