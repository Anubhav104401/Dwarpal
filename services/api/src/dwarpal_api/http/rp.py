"""The relying-party API: websites create verification sessions and read their results, using their secret key."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from dwarpal_api.app import verification
from dwarpal_api.app.verification import Services
from dwarpal_api.http.deps import Caller, rp_caller, services

router = APIRouter(prefix="/v1/verification-sessions", tags=["verification sessions"])


class CreateSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy: Annotated[str, Field(max_length=40)] = "uk_osa_18"
    return_url: AnyHttpUrl | None = None
    external_ref: Annotated[str | None, Field(max_length=200)] = None


@router.post("", status_code=201)
async def create_session(
    body: CreateSession,
    caller: Annotated[Caller, Depends(rp_caller)],
    svc: Annotated[Services, Depends(services)],
) -> dict[str, Any]:
    return_url = str(body.return_url) if body.return_url else None
    row, secret = await verification.create_session(
        svc, caller.project, caller.livemode, body.policy, return_url, body.external_ref
    )
    return verification.created_view(svc, row, secret)


@router.get("/{session_text}")
async def retrieve_session(
    session_text: str,
    caller: Annotated[Caller, Depends(rp_caller)],
    svc: Annotated[Services, Depends(services)],
) -> dict[str, Any]:
    return await verification.result_view(svc, session_text, caller.project.id, caller.livemode)
