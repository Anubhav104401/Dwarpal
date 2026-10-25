"""Jobs the operator runs on a schedule, across every project: expiring abandoned sessions, purging old metadata, and
checking every organisation's audit chain. Like the other operator tools, they work as the tables' owner."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dwarpal_api.adapters.tables import Event, Organization, VerificationSession
from dwarpal_api.app import audit
from dwarpal_api.app.verification import record_final
from dwarpal_api.domain.sessions import Status, move

OPEN = (Status.CREATED, Status.IN_PROGRESS, Status.AWAITING_STEP_UP)
# Older than its project's retention period: each project keeps its rows for its own number of days.
TOO_OLD = text(
    "created_at < CAST(:now AS timestamptz)"
    " - make_interval(days => (SELECT retention_days FROM projects WHERE id = project_id))"
)


async def sweep_expired(
    sessions: async_sessionmaker[AsyncSession], new_id: Callable[[], uuid.UUID], now: datetime, limit: int = 500
) -> int:
    """Expire open sessions whose time is up, and announce each one. Sessions also expire when they are next read;
    this finds the ones nobody reads again, so that the website still hears about them."""
    async with sessions() as session:
        query = (
            select(VerificationSession)
            .where(VerificationSession.status.in_(OPEN), VerificationSession.expires_at <= now)
            .order_by(VerificationSession.expires_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        due = list(await session.scalars(query))
        for row in due:
            row.status = move(Status(row.status), Status.EXPIRED)
            await record_final(session, new_id, row, now)
        await session.commit()
    return len(due)


@dataclass(frozen=True)
class Purged:
    sessions: int
    events: int


async def purge(sessions: async_sessionmaker[AsyncSession], now: datetime) -> Purged:
    """Delete session metadata older than each project's retention period: the sessions (with their attempts and
    issued tokens) and the events (with their deliveries). The daily counts and the audit log stay."""
    async with sessions() as session:
        gone = await session.execute(delete(VerificationSession).where(TOO_OLD), {"now": now})
        told = await session.execute(delete(Event).where(TOO_OLD), {"now": now})
        await session.commit()
    return Purged(sessions=_count(gone), events=_count(told))


def _count(result: object) -> int:
    return int(getattr(result, "rowcount", 0) or 0)


async def verify_all_chains(sessions: async_sessionmaker[AsyncSession]) -> dict[uuid.UUID, audit.ChainReport]:
    """Recompute every organisation's audit chain; the operator is told of any that is broken."""
    async with sessions() as session:
        orgs = list(await session.scalars(select(Organization.id).order_by(Organization.id)))
        return {org_id: await audit.verify(session, org_id) for org_id in orgs}
