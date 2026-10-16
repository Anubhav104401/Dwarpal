"""Health endpoints: "am I alive?" and "can I do real work right now?", for whatever runs and routes the service."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text

from dwarpal_api.app.verification import Services
from dwarpal_api.http.deps import services

router = APIRouter(tags=["health"])


@router.get("/livez")
async def livez() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/readyz")
async def readyz(response: Response, svc: Annotated[Services, Depends(services)]) -> dict[str, str]:
    checks: dict[str, str] = {}
    try:
        async with svc.sessions() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    try:
        await svc.store.ping()
        checks["valkey"] = "ok"
    except Exception:
        checks["valkey"] = "unavailable"
    if any(value != "ok" for value in checks.values()):
        response.status_code = 503
    return checks
