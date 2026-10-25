"""The analytics API: a website reads how its age checks have been ending."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from dwarpal_api.app import analytics
from dwarpal_api.app.verification import Services
from dwarpal_api.http.deps import Caller, needs, services

router = APIRouter(prefix="/v1/analytics", tags=["analytics"])


@router.get("/sessions")
async def session_counts(
    caller: Annotated[Caller, Depends(needs("sessions:read"))],
    svc: Annotated[Services, Depends(services)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> dict[str, Any]:
    return await analytics.session_counts(svc, caller.project.id, caller.livemode, days)
