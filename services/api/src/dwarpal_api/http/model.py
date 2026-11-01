"""The age model's published performance: what anyone may know of the model now deciding, without signing in. A
provider should publish how well its system works (ISO/IEC 27566-1); the website's home page shows it."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response

from dwarpal_api.app import console
from dwarpal_api.app.verification import Services
from dwarpal_api.http.deps import services

router = APIRouter(prefix="/v1", tags=["model"])


@router.get("/model")
async def model(response: Response, svc: Annotated[Services, Depends(services)]) -> dict[str, Any]:
    response.headers["Cache-Control"] = "public, max-age=300"
    return console.published_model(svc)
