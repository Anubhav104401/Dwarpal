"""Short-lived state in Valkey: flow tokens, one-time challenges, budgets, rate limits and idempotent replies.
Everything stored here expires on its own."""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from typing import Any

from redis.asyncio import Redis

from dwarpal_contracts import Challenge

# A token bucket (ADR-0011): it holds up to `burst` tokens and refills at `rate` per second; each request takes one.
# Run inside Valkey as one script, so two API servers can't both take the last token, and timed by Valkey's own
# clock, so their clocks needn't agree. Returns {1, 0} when allowed, or {0, milliseconds until a token is back}.
RATE_LIMIT_SCRIPT = """
local rate, burst = tonumber(ARGV[1]), tonumber(ARGV[2])
local clock = redis.call('TIME')
local now = clock[1] * 1000 + math.floor(clock[2] / 1000)
local state = redis.call('HMGET', KEYS[1], 'tokens', 'at')
local tokens = math.min(burst, (tonumber(state[1]) or burst) + (now - (tonumber(state[2]) or now)) * rate / 1000)
local allowed, wait = 0, math.ceil((1 - tokens) * 1000 / rate)
if tokens >= 1 then
    tokens, allowed, wait = tokens - 1, 1, 0
end
redis.call('HSET', KEYS[1], 'tokens', tostring(tokens), 'at', now)
redis.call('PEXPIRE', KEYS[1], math.ceil(burst * 1000 / rate) + 1000)
return {allowed, wait}
"""


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

    async def take_token(self, key: str, rate: float, burst: int) -> int:
        """Take one token from the bucket called `key`: 0 if it was there, else how many milliseconds until one is."""
        allowed, wait = await self._client.eval(RATE_LIMIT_SCRIPT, 1, f"bucket:{_hashed(key)}", rate, burst)
        return 0 if int(allowed) else max(int(wait), 1)

    async def claim(self, key: str, value: bytes, ttl_s: int) -> bytes | None:
        """Store `value` under `key` unless something is already there; return what was there (None if we claimed)."""
        existing = await self._client.set(key, value, ex=ttl_s, nx=True, get=True)
        return existing if isinstance(existing, bytes) else None

    async def put(self, key: str, value: bytes, ttl_s: int) -> None:
        await self._client.set(key, value, ex=ttl_s)

    async def drop(self, key: str) -> None:
        await self._client.delete(key)

    async def take(self, key: str) -> bytes | None:
        """Read a value and delete it in one step: whoever takes it first has it, and nobody can take it twice."""
        value = await self._client.getdel(key)
        return value if isinstance(value, bytes) else None

    async def fetch(self, key: str, ttl_s: int) -> bytes | None:
        """Read a value and restart its time to live: a sliding expiry, for sessions that last while they are used."""
        value = await self._client.getex(key, ex=ttl_s)
        return value if isinstance(value, bytes) else None

    async def take_challenge(self, challenge_id: str, session_id: uuid.UUID) -> Challenge | None:
        stored = await self._client.getdel(f"challenge:{challenge_id}")
        if stored is None:
            return None
        issued = json.loads(stored)
        if issued["session_id"] != str(session_id):
            return None
        return Challenge(poses=issued["poses"], colours=issued["colours"], step_ms=issued["step_ms"])
