"""Short-lived state in Valkey: flow tokens and one-time challenges. Everything stored here expires on its own."""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from typing import Any

from redis.asyncio import Redis

from dwarpal_contracts import Challenge


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
        self, session_id: uuid.UUID, challenge: Challenge, ttl_s: int, budget: int, budget_ttl_s: int
    ) -> dict[str, Any] | None:
        counter = f"challenges:{session_id}"
        await self._client.set(counter, 0, ex=budget_ttl_s, nx=True)
        if await self._client.incr(counter) > budget:
            return None
        issued = {
            "challenge_id": secrets.token_urlsafe(16),
            "nonce": secrets.token_urlsafe(16),
            **challenge.model_dump(),
            "expires_in": ttl_s,
        }
        stored = json.dumps({"session_id": str(session_id), **issued})
        await self._client.set(f"challenge:{issued['challenge_id']}", stored, ex=ttl_s)
        return issued

    async def spend_budget(self, key: str, limit: int, window_s: int) -> bool:
        """Count one use against a budget that starts afresh every window; False once the budget is spent."""
        counter = f"budget:{_hashed(key)}"
        await self._client.set(counter, 0, ex=window_s, nx=True)
        return await self._client.incr(counter) <= limit

    async def take_challenge(self, challenge_id: str, session_id: uuid.UUID) -> Challenge | None:
        stored = await self._client.getdel(f"challenge:{challenge_id}")
        if stored is None:
            return None
        issued = json.loads(stored)
        if issued["session_id"] != str(session_id):
            return None
        return Challenge(poses=issued["poses"], colours=issued["colours"], step_ms=issued["step_ms"])
