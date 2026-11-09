"""The webhook delivery worker: it empties the outbox, sending each due delivery and scheduling retries.

It is an operator process, like the command-line tools: it works across every project, so it connects as the tables'
owner, whom row-level security doesn't bind. It reads only the outbox and what a delivery needs.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dwarpal_api.adapters.signing import MasterKey
from dwarpal_api.adapters.tables import Event, WebhookDelivery, WebhookEndpoint
from dwarpal_api.adapters.webhooks import UnsafeUrlError, check_url, retry_delay, send
from dwarpal_api.app.webhooks import event_view
from dwarpal_api.domain import ids

# While a worker sends a delivery, the row is leased to it: due again only if the worker dies mid-send.
LEASE = timedelta(seconds=60)


class Deliverer:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        master: MasterKey,
        http: httpx.AsyncClient,
        now: Callable[[], datetime],
        allow_private: bool = False,
    ) -> None:
        self._sessions, self._master, self._http, self._now = sessions, master, http, now
        self._allow_private = allow_private

    async def deliver_due(self, limit: int = 20) -> int:
        """Send up to `limit` deliveries that are due; return how many were tried."""
        now = self._now()
        async with self._sessions() as session:
            # SKIP LOCKED: rows another worker is claiming right now are passed over, never sent twice.
            query = (
                select(WebhookDelivery)
                .where(WebhookDelivery.status == "pending", WebhookDelivery.next_attempt_at <= now)
                .order_by(WebhookDelivery.next_attempt_at)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            due = list(await session.scalars(query))
            for row in due:
                row.next_attempt_at = now + LEASE
            await session.commit()
        for row in due:
            await self.deliver(row.id)
        return len(due)

    async def deliver(self, delivery_id: uuid.UUID) -> None:
        async with self._sessions() as session:
            delivery = await session.get(WebhookDelivery, delivery_id)
            endpoint = await session.get(WebhookEndpoint, delivery.endpoint_id) if delivery else None
            event = await session.get(Event, delivery.event_id) if delivery else None
        if delivery is None or endpoint is None or event is None:
            return  # deleted meanwhile, with its endpoint
        status: int | None = None
        error: str | None = "endpoint disabled"
        if endpoint.enabled:
            status, error = await self._send(endpoint, event)
        await self._record(delivery_id, status, error, final=not endpoint.enabled)

    async def _send(self, endpoint: WebhookEndpoint, event: Event) -> tuple[int | None, str | None]:
        try:
            # Checked again now, not only when the endpoint was saved: the name may point somewhere else today.
            addresses = await check_url(endpoint.url, livemode=endpoint.livemode, allow_private=self._allow_private)
        except UnsafeUrlError as unsafe:
            return None, str(unsafe)[:200]
        secret = self._master.open(endpoint.secret_sealed, endpoint.id.bytes).decode()
        body = json.dumps(event_view(event), separators=(",", ":")).encode()
        timestamp = int(self._now().timestamp())
        # Sent to the addresses just checked, never to the name again: asked twice, it could answer differently.
        return await send(self._http, endpoint.url, secret, ids.encode("evt", event.id), body, timestamp, addresses)

    async def _record(self, delivery_id: uuid.UUID, status: int | None, error: str | None, final: bool) -> None:
        now = self._now()
        async with self._sessions() as session:
            row = await session.get(WebhookDelivery, delivery_id, with_for_update=True)
            if row is None:
                return
            row.attempt += 1
            row.last_status, row.last_error = status, error
            wait = None if final else retry_delay(row.attempt)
            if error is None:
                row.status, row.delivered_at = "delivered", now
            elif wait is None:
                row.status = "dead"
            else:
                row.next_attempt_at = now + timedelta(seconds=wait)
            await session.commit()

    async def run(self, poll_s: float, once: bool = False) -> None:
        """Keep the outbox empty: send what is due, and wait a moment whenever nothing is."""
        while True:
            tried = await self.deliver_due()
            if once:
                return
            if not tried:
                await asyncio.sleep(poll_s)
