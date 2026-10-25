"""Analytics: how a project's checks have been ending, day by day, from counts that outlive the sessions themselves."""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from dwarpal_api.adapters.db import tenant
from dwarpal_api.adapters.tables import SessionStat

if TYPE_CHECKING:
    from dwarpal_api.app.verification import Services


async def session_counts(svc: Services, project_id: uuid.UUID, livemode: bool, days: int) -> dict[str, Any]:
    """The last `days` days of finished sessions, by day, policy and outcome, with totals by outcome. Test and live
    sessions are counted apart, so integration testing never blurs the real figures."""
    since = (svc.now() - timedelta(days=days - 1)).date()
    query = (
        select(SessionStat)
        .where(SessionStat.project_id == project_id, SessionStat.livemode == livemode, SessionStat.day >= since)
        .order_by(SessionStat.day, SessionStat.policy, SessionStat.outcome)
    )
    async with tenant(svc.sessions, project_id) as session:
        rows = list(await session.scalars(query))
    totals: Counter[str] = Counter()
    for row in rows:
        totals[row.outcome] += row.sessions
    data = [
        {"day": row.day.isoformat(), "policy": row.policy, "outcome": row.outcome, "sessions": row.sessions}
        for row in rows
    ]
    return {"object": "list", "since": since.isoformat(), "data": data, "totals": dict(sorted(totals.items()))}
