"""The capture-flow API, called by the hosted verify page in the user's browser."""

from __future__ import annotations

import re
import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.datastructures import FormData, UploadFile

from dwarpal_api.app import agepass, verification
from dwarpal_api.app.verification import Services
from dwarpal_api.domain.decision import Outcome
from dwarpal_api.errors import ApiError
from dwarpal_api.http.deps import flow_session, services
from dwarpal_contracts import MAX_DOCUMENT_BYTES, MAX_FRAME_BYTES, MAX_FRAMES, FaceRequestMeta

router = APIRouter(prefix="/v1/flow/sessions/{session_text}", tags=["capture flow"])
CHALLENGE_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
# The verify page's random device ID (a UUID). Anything else is ignored, as if no ID had been sent.
DEVICE_ID = re.compile(r"^[A-Za-z0-9-]{16,64}$")


class StartFlow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_secret: Annotated[str, Field(min_length=20, max_length=200)]


@router.post("/start")
async def start(session_text: str, body: StartFlow, svc: Annotated[Services, Depends(services)]) -> dict[str, Any]:
    return await verification.start_flow(svc, session_text, body.client_secret)


@router.get("/frame-ancestor")
async def frame_ancestor(session_text: str, svc: Annotated[Services, Depends(services)]) -> dict[str, str | None]:
    """Asked by the verify page's web server before it serves the page: which website may frame it. Needs no
    secret — it names only a website the session will send the person back to anyway."""
    return {"origin": await verification.frame_ancestor(svc, session_text)}


@router.post("/challenge")
async def challenge(
    request: Request,
    flow: Annotated[uuid.UUID, Depends(flow_session)],
    svc: Annotated[Services, Depends(services)],
    x_dwarpal_device: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    device = x_dwarpal_device if x_dwarpal_device and DEVICE_ID.match(x_dwarpal_device) else None
    address = request.client.host if request.client else None
    return await verification.issue_challenge(svc, flow, device, address)


@router.post("/face-attempts")
async def face_attempt(
    request: Request, flow: Annotated[uuid.UUID, Depends(flow_session)], svc: Annotated[Services, Depends(services)]
) -> dict[str, Any]:
    # The uploads are closed as the block ends, however it ends: the frames live on only as the bytes read here.
    async with request.form(max_files=MAX_FRAMES, max_fields=2) as form:
        challenge_id, meta, frames = await read_attempt(form)
    decision, remaining = await verification.submit_face_attempt(svc, flow, challenge_id, meta, frames)
    reasons = ["verification_failed"] if decision.outcome == Outcome.REJECT else list(decision.reasons)
    return {"outcome": decision.outcome, "reasons": reasons, "attempts_remaining": max(remaining, 0)}


@router.post("/stepup/mrz")
async def document_attempt(
    request: Request, flow: Annotated[uuid.UUID, Depends(flow_session)], svc: Annotated[Services, Depends(services)]
) -> dict[str, Any]:
    """The step-up with an ID document (Phase 6): a photo of the document's data page, with the selfie frames of a
    new face challenge. Nothing of the photo is kept; of the document, only what an age check needs (§9.1)."""
    async with request.form(max_files=MAX_FRAMES + 1, max_fields=2) as form:
        challenge_id, meta, frames = await read_attempt(form)
        upload = form.get("document")
        if not isinstance(upload, UploadFile):
            raise ApiError(422, "invalid_request", "document is missing")
        document = await upload.read(MAX_DOCUMENT_BYTES + 1)
        if len(document) > MAX_DOCUMENT_BYTES:
            raise ApiError(413, "frame_too_large", f"document is larger than {MAX_DOCUMENT_BYTES} bytes")
    decision, remaining = await verification.submit_document_attempt(svc, flow, challenge_id, meta, frames, document)
    reasons = ["verification_failed"] if decision.outcome == Outcome.REJECT else list(decision.reasons)
    return {"outcome": decision.outcome, "reasons": reasons, "attempts_remaining": max(remaining, 0)}


async def read_attempt(form: FormData) -> tuple[str, FaceRequestMeta, list[bytes]]:
    """An attempt's challenge, its meta and its frames, each frame read only up to its size limit."""
    challenge_id = str(form.get("challenge_id", ""))
    if not CHALLENGE_ID.match(challenge_id):
        raise ApiError(422, "invalid_request", "challenge_id is missing or malformed")
    try:
        meta = FaceRequestMeta.model_validate_json(str(form.get("meta", "")))
    except ValidationError:
        raise ApiError(422, "invalid_request", "meta is missing or invalid") from None
    frames: list[bytes] = []
    for frame in meta.frames:
        upload = form.get(f"frame_{frame.index}")
        if not isinstance(upload, UploadFile):
            raise ApiError(422, "invalid_request", f"frame_{frame.index} is missing")
        data = await upload.read(MAX_FRAME_BYTES + 1)
        if len(data) > MAX_FRAME_BYTES:
            raise ApiError(413, "frame_too_large", f"frame_{frame.index} is larger than {MAX_FRAME_BYTES} bytes")
        frames.append(data)
    return challenge_id, meta, frames


class HolderKey(BaseModel):
    """The public half of a key pair the browser made for one pass: an EC key on P-256, as a JWK, and nothing more —
    a private part (`d`) or anything else is refused."""

    model_config = ConfigDict(extra="forbid")

    kty: Literal["EC"]
    crv: Literal["P-256"]
    x: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{43}$")]
    y: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{43}$")]


class AgePassKeys(BaseModel):
    """One public key per pass (Phase 9, D21)."""

    model_config = ConfigDict(extra="forbid")

    keys: Annotated[list[HolderKey], Field(min_length=1, max_length=20)]


class AgePassPresentation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    presentation: Annotated[str, Field(min_length=20, max_length=4096)]


@router.post("/age-pass")
async def issue_age_passes(
    body: AgePassKeys, flow: Annotated[uuid.UUID, Depends(flow_session)], svc: Annotated[Services, Depends(services)]
) -> dict[str, Any]:
    """A batch of Age Passes for a person who has just passed, under a policy that accepts them."""
    return await agepass.issue(svc, flow, [key.model_dump() for key in body.keys])


@router.post("/age-pass/nonce")
async def age_pass_nonce(
    request: Request,
    flow: Annotated[uuid.UUID, Depends(flow_session)],
    svc: Annotated[Services, Depends(services)],
    x_dwarpal_device: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    device = x_dwarpal_device if x_dwarpal_device and DEVICE_ID.match(x_dwarpal_device) else None
    address = request.client.host if request.client else None
    return await agepass.nonce(svc, flow, device, address)


@router.post("/age-pass/present")
async def present_age_pass(
    body: AgePassPresentation,
    flow: Annotated[uuid.UUID, Depends(flow_session)],
    svc: Annotated[Services, Depends(services)],
) -> dict[str, Any]:
    """An Age Pass in place of a face check: the session completes, as after any pass."""
    return await agepass.present(svc, flow, body.presentation)


@router.post("/finish")
async def finish(
    flow: Annotated[uuid.UUID, Depends(flow_session)], svc: Annotated[Services, Depends(services)]
) -> dict[str, Any]:
    return {"redirect_url": await verification.finish(svc, flow)}
