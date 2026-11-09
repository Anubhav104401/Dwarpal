"""Analytics: how a project's checks have been ending, day by day, from counts that outlive the sessions themselves."""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from dwarpal_api.adapters.db import tenant
from dwarpal_api.adapters.tables import DocumentStageStat, FaceStageStat, SessionStat
from dwarpal_api.domain.timing import median_band

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
    face_query = select(FaceStageStat).where(
        FaceStageStat.project_id == project_id, FaceStageStat.livemode == livemode, FaceStageStat.day >= since
    )
    document_query = select(DocumentStageStat).where(
        DocumentStageStat.project_id == project_id,
        DocumentStageStat.livemode == livemode,
        DocumentStageStat.day >= since,
    )
    async with tenant(svc.sessions, project_id) as session:
        rows = list(await session.scalars(query))
        face_rows = list(await session.scalars(face_query))
        document_rows = list(await session.scalars(document_query))
    totals: Counter[str] = Counter()
    for row in rows:
        totals[row.outcome] += row.sessions
    data = [
        {"day": row.day.isoformat(), "policy": row.policy, "outcome": row.outcome, "sessions": row.sessions}
        for row in rows
    ]
    return {
        "object": "list",
        "since": since.isoformat(),
        "data": data,
        "totals": dict(sorted(totals.items())),
        "face_stage": face_stage(face_rows),
        "document_stage": document_stage(document_rows),
    }


def face_stage(rows: list[FaceStageStat]) -> dict[str, Any]:
    """How the face checks that reached a decision ended, and the band of time holding the median, from opening the
    verify page to the decision. A session sent to a stronger check is counted here as `step_up` even though its final
    outcome, in `totals`, comes later."""
    outcomes: Counter[str] = Counter()
    bands: Counter[int] = Counter()
    for row in rows:
        outcomes[row.outcome] += row.sessions
        bands[row.from_s] += row.sessions
    median = median_band(bands)
    return {
        "decided": sum(outcomes.values()),
        "outcomes": dict(sorted(outcomes.items())),
        "median_seconds": None if median is None else {"from": median[0], "to": median[1]},
    }


def document_stage(rows: list[DocumentStageStat]) -> dict[str, Any]:
    """How many sessions reached the ID-document check (sent there by a face check that couldn't decide, or starting
    there, D24), and how many of those checks ended each way. The ones that reached it but have no ending left — or
    are still on it: the design's step-up conversion is the share that ended."""
    steps: Counter[str] = Counter()
    for row in rows:
        steps[row.step] += row.sessions
    opened = steps.pop("opened", 0)
    return {"opened": opened, "outcomes": dict(sorted(steps.items()))}
