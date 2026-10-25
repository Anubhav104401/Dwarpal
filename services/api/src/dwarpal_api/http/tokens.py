"""Token introspection: a website's server asks Dwarpal whether an age token is genuine, instead of checking it."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from dwarpal_api.app import verification
from dwarpal_api.app.verification import Services
from dwarpal_api.http.deps import Caller, needs, services

router = APIRouter(prefix="/v1/tokens", tags=["tokens"])


class Introspection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: Annotated[str, Field(min_length=1, max_length=4000)]


@router.post("/introspect")
async def introspect(
    body: Introspection,
    caller: Annotated[Caller, Depends(needs("sessions:read"))],
    svc: Annotated[Services, Depends(services)],
) -> dict[str, Any]:
    return await verification.introspect(svc, caller.project.id, body.token)
