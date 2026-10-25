"""The policies API: websites list the presets and their own policies, and add new versions of their own."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from dwarpal_api.app import policies
from dwarpal_api.app.verification import Services
from dwarpal_api.domain.policy import Policy
from dwarpal_api.http.deps import Caller, needs, services

router = APIRouter(prefix="/v1/policies", tags=["policies"])


class NewVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Annotated[str, Field(min_length=3, max_length=40)]
    min_age: Annotated[int, Field(ge=13, le=25)]
    risk_budget: Annotated[float, Field(gt=0, le=0.1)] = 0.02
    max_face_attempts: Annotated[int, Field(ge=1, le=5)] = 3
    token_ttl_s: Annotated[int, Field(ge=60, le=3600)] = 600


@router.get("")
async def list_policies(
    caller: Annotated[Caller, Depends(needs("sessions:read"))], svc: Annotated[Services, Depends(services)]
) -> dict[str, Any]:
    return await policies.list_all(svc.sessions, caller.project.id)


@router.post("", status_code=201)
async def add_version(
    body: NewVersion,
    caller: Annotated[Caller, Depends(needs("policies:write"))],
    svc: Annotated[Services, Depends(services)],
) -> dict[str, Any]:
    draft = Policy(body.name, body.min_age, body.risk_budget, body.max_face_attempts, body.token_ttl_s)
    project = caller.project
    return await policies.add_version(
        svc.sessions, svc.manifest, project.id, draft, svc.now(), svc.new_id(), project.org_id, caller.actor
    )
