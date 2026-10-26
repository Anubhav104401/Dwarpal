"""The webhooks API: websites register the addresses Dwarpal notifies, send test events, and look at deliveries."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field

from dwarpal_api.app import webhooks
from dwarpal_api.app.verification import Services
from dwarpal_api.http.deps import Caller, needs, services

router = APIRouter(prefix="/v1", tags=["webhooks"])
Manager = Annotated[Caller, Depends(needs("webhooks:write"))]
Toolbox = Annotated[Services, Depends(services)]


class NewEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: Annotated[str, Field(min_length=8, max_length=2000)]
    events: Annotated[list[str], Field(min_length=1, max_length=len(webhooks.EVENT_TYPES))]


@router.post("/webhook-endpoints", status_code=201)
async def create_endpoint(body: NewEndpoint, caller: Manager, svc: Toolbox) -> dict[str, Any]:
    project = caller.project
    return await webhooks.create_endpoint(
        svc, project.id, project.org_id, caller.livemode, caller.actor, body.url, body.events
    )


@router.get("/webhook-endpoints")
async def list_endpoints(caller: Manager, svc: Toolbox) -> dict[str, Any]:
    return await webhooks.list_endpoints(svc, caller.project.id, caller.livemode)


@router.delete("/webhook-endpoints/{endpoint_text}", status_code=204)
async def delete_endpoint(endpoint_text: str, caller: Manager, svc: Toolbox) -> Response:
    project = caller.project
    await webhooks.delete_endpoint(svc, project.id, project.org_id, caller.livemode, caller.actor, endpoint_text)
    return Response(status_code=204)


@router.post("/webhook-endpoints/{endpoint_text}/test", status_code=202)
async def send_test(endpoint_text: str, caller: Manager, svc: Toolbox) -> dict[str, Any]:
    return await webhooks.send_test(svc, caller.project.id, caller.livemode, endpoint_text)


@router.get("/webhook-endpoints/{endpoint_text}/deliveries")
async def list_deliveries(endpoint_text: str, caller: Manager, svc: Toolbox) -> dict[str, Any]:
    return await webhooks.list_deliveries(svc, caller.project.id, caller.livemode, endpoint_text)


@router.post("/webhook-deliveries/{delivery_text}/replay", status_code=202)
async def replay(delivery_text: str, caller: Manager, svc: Toolbox) -> dict[str, Any]:
    return await webhooks.replay(svc, caller.project.id, caller.livemode, delivery_text)
