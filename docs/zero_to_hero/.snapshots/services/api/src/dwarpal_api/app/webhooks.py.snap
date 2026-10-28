"""Events and webhooks: what happened to a project's sessions, and the endpoints that are told about it."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dwarpal_api.adapters.db import tenant
from dwarpal_api.adapters.tables import Event, WebhookDelivery, WebhookEndpoint
from dwarpal_api.adapters.webhooks import UnsafeUrlError, check_url, new_secret
from dwarpal_api.app import audit
from dwarpal_api.domain import ids
from dwarpal_api.errors import ApiError

if TYPE_CHECKING:  # only for type hints: verification.py imports this module
    from dwarpal_api.app.verification import Services

EVENT_TYPES = ("verification_session.completed", "verification_session.expired")
TEST_EVENT = "webhook_endpoint.test"
MAX_ENDPOINTS = 16
RECENT_DELIVERIES = 100


def event_view(event: Event) -> dict[str, Any]:
    """An event as receivers see it: the body of every webhook, and what signatures are computed over."""
    return {
        "id": ids.encode("evt", event.id),
        "object": "event",
        "type": event.type,
        "livemode": event.livemode,
        "created_at": event.created_at.isoformat(),
        "data": event.data,
    }


def endpoint_view(row: WebhookEndpoint) -> dict[str, Any]:
    return {
        "id": ids.encode("whe", row.id),
        "object": "webhook_endpoint",
        "url": row.url,
        "events": row.events,
        "enabled": row.enabled,
        "livemode": row.livemode,
        "created_at": row.created_at.isoformat(),
    }


def delivery_view(row: WebhookDelivery) -> dict[str, Any]:
    return {
        "id": ids.encode("whd", row.id),
        "object": "webhook_delivery",
        "event": ids.encode("evt", row.event_id),
        "status": row.status,
        "attempt": row.attempt,
        "next_attempt_at": row.next_attempt_at.isoformat() if row.status == "pending" else None,
        "last_status": row.last_status,
        "last_error": row.last_error,
        "created_at": row.created_at.isoformat(),
        "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None,
    }


async def emit(
    session: AsyncSession,
    new_id: Callable[[], uuid.UUID],
    now: datetime,
    project_id: uuid.UUID,
    livemode: bool,
    event_type: str,
    data: dict[str, Any],
    only: uuid.UUID | None = None,
) -> Event:
    """Write an event, and one pending delivery for each enabled endpoint that wants it (or only for `only`), inside
    the caller's transaction: the change and its notification are saved together or not at all."""
    event = Event(id=new_id(), project_id=project_id, livemode=livemode, type=event_type, data=data, created_at=now)
    session.add(event)
    query = select(WebhookEndpoint.id).where(
        WebhookEndpoint.project_id == project_id,
        WebhookEndpoint.livemode == livemode,
        WebhookEndpoint.enabled.is_(True),
    )
    query = (
        query.where(WebhookEndpoint.id == only) if only else query.where(WebhookEndpoint.events.contains([event_type]))
    )
    for endpoint_id in await session.scalars(query):
        session.add(
            WebhookDelivery(
                id=new_id(),
                endpoint_id=endpoint_id,
                event_id=event.id,
                status="pending",
                attempt=0,
                next_attempt_at=now,
                last_status=None,
                last_error=None,
                created_at=now,
                delivered_at=None,
            )
        )
    return event


async def create_endpoint(
    svc: Services,
    project_id: uuid.UUID,
    org_id: uuid.UUID,
    livemode: bool,
    actor: tuple[str, str],
    url: str,
    events: list[str],
) -> dict[str, Any]:
    """A new endpoint, by a website's key or a person in the console (`actor`, for the audit log)."""
    unknown = sorted(set(events) - set(EVENT_TYPES))
    if unknown or not events:
        raise ApiError(422, "unknown_event_type", f"choose events from {', '.join(EVENT_TYPES)}")
    try:
        await check_url(url, livemode=livemode, allow_private=svc.settings.webhook_allow_private)
    except UnsafeUrlError as error:
        raise ApiError(422, "unsafe_webhook_url", str(error)) from None
    if svc.master is None:
        raise RuntimeError("the toolbox has no master key")
    endpoint_id, secret, now = svc.new_id(), new_secret(), svc.now()
    row = WebhookEndpoint(
        id=endpoint_id,
        project_id=project_id,
        livemode=livemode,
        url=url,
        # Bound to this endpoint (its ID is the associated data): a sealed secret can't be moved to another one.
        secret_sealed=svc.master.seal(secret.encode(), endpoint_id.bytes),
        events=sorted(set(events)),
        enabled=True,
        created_at=now,
    )
    async with tenant(svc.sessions, project_id) as session:
        count = select(func.count()).select_from(WebhookEndpoint).where(WebhookEndpoint.project_id == project_id)
        if (await session.scalar(count) or 0) >= MAX_ENDPOINTS:
            raise ApiError(409, "too_many_webhook_endpoints", f"a project may have at most {MAX_ENDPOINTS} endpoints")
        session.add(row)
        target, facts = ids.encode("whe", endpoint_id), {"url": url, "events": row.events, "livemode": livemode}
        await audit.record(session, org_id, actor, "webhook_endpoint.created", target, facts, now)
        await session.commit()
    # The secret is shown once, now; afterwards only its sealed form exists.
    return {**endpoint_view(row), "secret": secret}


async def load_endpoint(session: AsyncSession, livemode: bool, endpoint_text: str) -> WebhookEndpoint:
    try:
        endpoint_id = ids.decode("whe", endpoint_text)
    except ids.InvalidIdError:
        endpoint_id = None
    row = await session.get(WebhookEndpoint, endpoint_id) if endpoint_id else None
    if row is None or row.livemode != livemode:
        raise ApiError(404, "webhook_endpoint_not_found", "no such webhook endpoint")
    return row


async def list_endpoints(svc: Services, project_id: uuid.UUID, livemode: bool) -> dict[str, Any]:
    query = select(WebhookEndpoint).where(
        WebhookEndpoint.project_id == project_id, WebhookEndpoint.livemode == livemode
    )
    async with tenant(svc.sessions, project_id) as session:
        rows = list(await session.scalars(query.order_by(WebhookEndpoint.id)))
    return {"object": "list", "data": [endpoint_view(row) for row in rows]}


async def delete_endpoint(
    svc: Services, project_id: uuid.UUID, org_id: uuid.UUID, livemode: bool, actor: tuple[str, str], endpoint_text: str
) -> None:
    async with tenant(svc.sessions, project_id) as session:
        endpoint = await load_endpoint(session, livemode, endpoint_text)
        facts = {"url": endpoint.url}
        await audit.record(session, org_id, actor, "webhook_endpoint.deleted", endpoint_text, facts, svc.now())
        await session.delete(endpoint)
        await session.commit()


async def set_enabled(
    svc: Services,
    project_id: uuid.UUID,
    org_id: uuid.UUID,
    livemode: bool,
    actor: tuple[str, str],
    endpoint_text: str,
    enabled: bool,
) -> dict[str, Any]:
    """Switch an endpoint off (no new deliveries; any still pending are closed unsent) or back on, keeping its address,
    events and secret — for a receiver that is down for maintenance, say."""
    async with tenant(svc.sessions, project_id) as session:
        endpoint = await load_endpoint(session, livemode, endpoint_text)
        if endpoint.enabled != enabled:
            endpoint.enabled = enabled
            action = "webhook_endpoint.enabled" if enabled else "webhook_endpoint.disabled"
            await audit.record(session, org_id, actor, action, endpoint_text, {"url": endpoint.url}, svc.now())
        await session.commit()
    return endpoint_view(endpoint)


async def send_test(svc: Services, project_id: uuid.UUID, livemode: bool, endpoint_text: str) -> dict[str, Any]:
    """Queue a test event for one endpoint, whatever it subscribes to, so a website can check its receiver."""
    async with tenant(svc.sessions, project_id) as session:
        endpoint = await load_endpoint(session, livemode, endpoint_text)
        data = {"message": "a test event from Dwarpal", "endpoint": ids.encode("whe", endpoint.id)}
        event = await emit(session, svc.new_id, svc.now(), project_id, livemode, TEST_EVENT, data, only=endpoint.id)
        await session.commit()
    return event_view(event)


async def list_deliveries(svc: Services, project_id: uuid.UUID, livemode: bool, endpoint_text: str) -> dict[str, Any]:
    async with tenant(svc.sessions, project_id) as session:
        endpoint = await load_endpoint(session, livemode, endpoint_text)
        query = (
            select(WebhookDelivery)
            .where(WebhookDelivery.endpoint_id == endpoint.id)
            .order_by(WebhookDelivery.id.desc())
            .limit(RECENT_DELIVERIES)
        )
        rows = list(await session.scalars(query))
    return {"object": "list", "data": [delivery_view(row) for row in rows]}


async def replay(svc: Services, project_id: uuid.UUID, livemode: bool, delivery_text: str) -> dict[str, Any]:
    """Send a delivery again from the start of the retry schedule: after a receiver was fixed, or for a dead one."""
    try:
        delivery_id = ids.decode("whd", delivery_text)
    except ids.InvalidIdError:
        raise ApiError(404, "webhook_delivery_not_found", "no such webhook delivery") from None
    async with tenant(svc.sessions, project_id) as session:
        row = await session.get(WebhookDelivery, delivery_id, with_for_update=True)
        endpoint = await session.get(WebhookEndpoint, row.endpoint_id) if row else None
        if row is None or endpoint is None or endpoint.livemode != livemode:
            raise ApiError(404, "webhook_delivery_not_found", "no such webhook delivery")
        row.status, row.attempt, row.next_attempt_at = "pending", 0, svc.now()
        row.last_status = row.last_error = row.delivered_at = None
        await session.commit()
    return delivery_view(row)
