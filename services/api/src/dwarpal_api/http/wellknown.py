"""Public, well-known addresses: the keys anyone can use to check our signatures, and a description of the issuer."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response

from dwarpal_api.adapters.signing import ALG, JWT_TYPE
from dwarpal_api.app.verification import Services
from dwarpal_api.domain.policy import PRESETS
from dwarpal_api.http.deps import services

router = APIRouter(prefix="/.well-known", tags=["well-known"])


@router.get("/jwks.json")
async def jwks(response: Response, svc: Annotated[Services, Depends(services)]) -> dict[str, Any]:
    response.headers["Cache-Control"] = "public, max-age=300"
    return svc.keyring.jwks()


@router.get("/dwarpal-configuration")
async def configuration(svc: Annotated[Services, Depends(services)]) -> dict[str, Any]:
    issuer = svc.settings.issuer
    return {
        "issuer": issuer,
        "jwks_uri": f"{issuer}/.well-known/jwks.json",
        "token_type": JWT_TYPE,
        "token_signing_algorithms": [ALG],
        "policies": sorted(PRESETS),
        "age_model": svc.manifest.version,
        "age_model_calibrated": svc.manifest.calibrated,
    }
