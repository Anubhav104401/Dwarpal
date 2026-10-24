"""Who is calling? FastAPI "dependencies" that check credentials before an endpoint's own code runs."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated, cast

from fastapi import Depends, Header, Request

from dwarpal_api.adapters.db import FIND_API_KEY, name_tenant
from dwarpal_api.adapters.tables import Project
from dwarpal_api.app.verification import Services, parse_session_id
from dwarpal_api.domain.keys import matches, parse_api_key
from dwarpal_api.errors import ApiError


@dataclass(frozen=True)
class Caller:
    project: Project
    livemode: bool


def services(request: Request) -> Services:
    return cast(Services, request.app.state.services)


def bearer(authorization: str | None) -> str:
    scheme, _, credential = (authorization or "").partition(" ")
    return credential.strip() if scheme.lower() == "bearer" else ""


async def rp_caller(
    svc: Annotated[Services, Depends(services)], authorization: Annotated[str | None, Header()] = None
) -> Caller:
    credential = bearer(authorization)
    parsed = parse_api_key(credential)
    if parsed is None:
        raise ApiError(401, "invalid_api_key", "send your secret key as: Authorization: Bearer dk_test_…")
    livemode, lookup = parsed
    async with svc.sessions() as session:
        key = (await session.execute(FIND_API_KEY, {"lookup": lookup})).one_or_none()
        if key is None or key.revoked_at is not None or key.livemode != livemode:
            raise ApiError(401, "invalid_api_key", "this API key is unknown or revoked")
        if not matches(credential, key.secret_digest):
            raise ApiError(401, "invalid_api_key", "this API key is unknown or revoked")
        # From here on, this unit of work sees only the key's own project.
        await name_tenant(session, project_id=key.project_id)
        project = await session.get(Project, key.project_id)
    if project is None:
        raise ApiError(401, "invalid_api_key", "this API key belongs to no project")
    return Caller(project=project, livemode=livemode)


async def flow_session(
    session_text: str,
    svc: Annotated[Services, Depends(services)],
    authorization: Annotated[str | None, Header()] = None,
) -> uuid.UUID:
    session_id = await svc.store.session_for(bearer(authorization)) if bearer(authorization) else None
    if session_id is None or session_id != parse_session_id(session_text):
        raise ApiError(401, "invalid_flow_token", "start the flow again to get a fresh flow token")
    return session_id
