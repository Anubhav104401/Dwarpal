"""The relying-party API: websites create verification sessions, list them and read their results, using their
secret key."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query, Response
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from dwarpal_api.app import idempotency, verification
from dwarpal_api.app.verification import Services
from dwarpal_api.domain.decision import Outcome
from dwarpal_api.http.deps import Caller, needs, services

router = APIRouter(prefix="/v1/verification-sessions", tags=["verification sessions"])


class CreateSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy: Annotated[str, Field(max_length=40)] = "uk_osa_18"
    return_url: AnyHttpUrl | None = None
    external_ref: Annotated[str | None, Field(max_length=200)] = None


@router.post("", status_code=201)
async def create_session(
    body: CreateSession,
    response: Response,
    caller: Annotated[Caller, Depends(needs("sessions:write"))],
    svc: Annotated[Services, Depends(services)],
    idempotency_key: Annotated[str | None, Header(pattern=r"^[\x21-\x7e]{8,255}$")] = None,
) -> dict[str, Any]:
    async def make() -> dict[str, Any]:
        return_url = str(body.return_url) if body.return_url else None
        row, secret = await verification.create_session(
            svc, caller.project, caller.livemode, body.policy, return_url, body.external_ref
        )
        return verification.created_view(svc, row, secret)

    if idempotency_key is None:
        return await make()
    # Replies are kept only as long as the session they describe: after that the client secret inside is useless.
    scope = f"{caller.project.id}:{'live' if caller.livemode else 'test'}"
    request = idempotency.fingerprint("create_session", body.model_dump(mode="json"))
    reply, replayed = await idempotency.once(
        svc.store, svc.idempotency_secret, scope, idempotency_key, request, svc.settings.session_ttl_s, make
    )
    if replayed:
        response.headers["Idempotent-Replayed"] = "true"
    return reply


@router.get("")
async def list_sessions(
    caller: Annotated[Caller, Depends(needs("sessions:read"))],
    svc: Annotated[Services, Depends(services)],
    limit: Annotated[int, Query(ge=1, le=verification.MAX_PAGE)] = 20,
    starting_after: Annotated[str | None, Query(max_length=64)] = None,
    outcome: Annotated[Outcome | None, Query()] = None,
    external_ref: Annotated[str | None, Query(max_length=200)] = None,
) -> dict[str, Any]:
    only = verification.SessionFilter(outcome, external_ref)
    return await verification.list_sessions(svc, caller.project.id, caller.livemode, limit, starting_after, only)


@router.get("/{session_text}")
async def retrieve_session(
    session_text: str,
    caller: Annotated[Caller, Depends(needs("sessions:read"))],
    svc: Annotated[Services, Depends(services)],
) -> dict[str, Any]:
    return await verification.result_view(svc, session_text, caller.project.id, caller.livemode)
