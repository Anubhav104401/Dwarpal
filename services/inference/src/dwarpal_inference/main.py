"""The inference service's HTTP interface. Internal only: the public internet can never reach it."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from dwarpal_contracts import MAX_FRAME_BYTES, MAX_FRAMES, FaceAnalysis, FaceRequestMeta
from dwarpal_inference.backends import AgeBackend, OnnxAgeBackend, StubAgeBackend
from dwarpal_inference.pipeline import FacePipeline
from dwarpal_inference.settings import Settings
from dwarpal_vision import FaceDetector


def build_age_backend(settings: Settings) -> AgeBackend:
    if settings.age_backend == "onnx":
        return OnnxAgeBackend(settings.models_dir / settings.age_model, settings.age_threads)
    return StubAgeBackend(settings.stub_age, settings.stub_spread)


def build_pipeline(settings: Settings) -> FacePipeline:
    detector = FaceDetector(settings.models_dir / settings.detector_file)
    return FacePipeline(detector, build_age_backend(settings), trust_labels=settings.liveness == "labels")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    limiter = anyio.CapacityLimiter(settings.workers)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.pipeline = build_pipeline(settings)
        yield

    app = FastAPI(title="Dwarpal inference", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/livez")
    async def livez() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/readyz")
    async def readyz(request: Request) -> dict[str, str]:
        pipeline: FacePipeline = request.app.state.pipeline
        return {"status": "ready", "age_model": pipeline.age.version}

    @app.post("/internal/v1/analyze/face")
    async def analyze_face(request: Request) -> FaceAnalysis:
        if limiter.available_tokens == 0:
            raise HTTPException(503, "inference is busy; retry shortly", headers={"Retry-After": "1"})
        form = await request.form(max_files=MAX_FRAMES, max_fields=1)
        try:
            meta = FaceRequestMeta.model_validate_json(str(form.get("meta", "")))
        except ValidationError as error:
            raise HTTPException(422, "meta is missing or invalid") from error
        images: list[bytes] = []
        for frame in meta.frames:
            upload = form.get(f"frame_{frame.index}")
            if not isinstance(upload, UploadFile):
                raise HTTPException(422, f"frame_{frame.index} is missing")
            data = await upload.read(MAX_FRAME_BYTES + 1)
            if len(data) > MAX_FRAME_BYTES:
                raise HTTPException(413, f"frame_{frame.index} is larger than {MAX_FRAME_BYTES} bytes")
            images.append(data)
        pipeline: FacePipeline = request.app.state.pipeline
        return await anyio.to_thread.run_sync(pipeline.analyze, meta, images, limiter=limiter)

    return app
