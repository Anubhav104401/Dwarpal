"""The inference service's HTTP interface. Internal only: the public internet can never reach it."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from dwarpal_contracts import (
    MAX_DOCUMENT_BYTES,
    MAX_FRAME_BYTES,
    MAX_FRAMES,
    DocumentAnalysis,
    FaceAnalysis,
    FaceRequestMeta,
)
from dwarpal_inference.backends import AgeBackend, OnnxAgeBackend, StubAgeBackend
from dwarpal_inference.document import DocumentReader
from dwarpal_inference.pipeline import FacePipeline
from dwarpal_inference.settings import Settings
from dwarpal_vision import FaceDetector, FaceMesh, HandDetector, SpoofDetector, SpoofModel
from dwarpal_vision.document import Tesseract
from dwarpal_vision.match import FaceMatcher


def build_age_backend(settings: Settings) -> AgeBackend:
    if settings.age_backend == "onnx":
        return OnnxAgeBackend(settings.models_dir / settings.age_model, settings.age_threads)
    return StubAgeBackend(settings.stub_age, settings.stub_spread)


def build_pipeline(settings: Settings) -> FacePipeline:
    detector = FaceDetector(settings.models_dir / settings.detector_file)
    mesh = FaceMesh(settings.models_dir / settings.mesh_file)
    hands = HandDetector(settings.models_dir / settings.hands_file)
    models = [
        SpoofModel(settings.models_dir / file, scale)
        for file, scale in zip(settings.antispoof_files, (2.7, 4.0), strict=True)
    ]
    # Made from the pinned weights by `python -m dwarpal_ml.antispoof`; without them, liveness says so and decides less.
    spoof = SpoofDetector(models) if all(model.path.is_file() for model in models) else None
    return FacePipeline(
        detector,
        build_age_backend(settings),
        mesh=mesh,
        hands=hands,
        spoof=spoof,
        trust_labels=settings.liveness == "labels",
        age_frames=settings.age_frames,
    )


def build_reader(settings: Settings, pipeline: FacePipeline) -> DocumentReader:
    matcher = FaceMatcher(settings.models_dir / settings.matcher_file)
    ocr = Tesseract(settings.tesseract_command, settings.tesseract_timeout_s)
    return DocumentReader(pipeline, pipeline.detector, matcher, ocr)


async def read_frames(form: object, meta: FaceRequestMeta) -> list[bytes]:
    """The frames a request's meta lists, each read only up to its size limit."""
    images: list[bytes] = []
    for frame in meta.frames:
        upload = form.get(f"frame_{frame.index}")  # type: ignore[attr-defined]
        if not isinstance(upload, UploadFile):
            raise HTTPException(422, f"frame_{frame.index} is missing")
        data = await upload.read(MAX_FRAME_BYTES + 1)
        if len(data) > MAX_FRAME_BYTES:
            raise HTTPException(413, f"frame_{frame.index} is larger than {MAX_FRAME_BYTES} bytes")
        images.append(data)
    return images


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    limiter = anyio.CapacityLimiter(settings.workers)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.pipeline = build_pipeline(settings)
        app.state.reader = build_reader(settings, app.state.pipeline)
        # Checked once, at start-up: without Tesseract, every document check says "unavailable" and is retried.
        app.state.ocr = "ready" if app.state.reader.ocr.available() else "missing"
        yield

    app = FastAPI(title="Dwarpal inference", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/livez")
    async def livez() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/readyz")
    async def readyz(request: Request) -> dict[str, str]:
        pipeline: FacePipeline = request.app.state.pipeline
        # Whether the anti-spoofing networks are loaded: without them, live sessions can't be decided (the API refuses).
        antispoof = "loaded" if pipeline.spoof is not None else "missing"
        return {
            "status": "ready",
            "age_model": pipeline.age.version,
            "antispoof": antispoof,
            "ocr": request.app.state.ocr,
        }

    @app.post("/internal/v1/analyze/face")
    async def analyze_face(request: Request) -> FaceAnalysis:
        # The uploads are closed as the block ends, however it ends: the frames live on only as the bytes read here.
        async with request.form(max_files=MAX_FRAMES, max_fields=1) as form:
            try:
                meta = FaceRequestMeta.model_validate_json(str(form.get("meta", "")))
            except ValidationError as error:
                raise HTTPException(422, "meta is missing or invalid") from error
            images = await read_frames(form, meta)
        pipeline: FacePipeline = request.app.state.pipeline
        async with worker():
            return await anyio.to_thread.run_sync(pipeline.analyze, meta, images)

    @app.post("/internal/v1/analyze/document")
    async def analyze_document(request: Request) -> DocumentAnalysis:
        """The step-up's document check: a photo of the document's data page, and the selfie frames of a face
        challenge. As with faces, the uploads are closed as the block ends."""
        async with request.form(max_files=MAX_FRAMES + 1, max_fields=1) as form:
            try:
                meta = FaceRequestMeta.model_validate_json(str(form.get("meta", "")))
            except ValidationError as error:
                raise HTTPException(422, "meta is missing or invalid") from error
            upload = form.get("document")
            if not isinstance(upload, UploadFile):
                raise HTTPException(422, "document is missing")
            document = await upload.read(MAX_DOCUMENT_BYTES + 1)
            if len(document) > MAX_DOCUMENT_BYTES:
                raise HTTPException(413, f"document is larger than {MAX_DOCUMENT_BYTES} bytes")
            images = await read_frames(form, meta)
        reader: DocumentReader = request.app.state.reader
        async with worker():
            return await anyio.to_thread.run_sync(reader.analyze, document, meta, images)

    @asynccontextmanager
    async def worker() -> AsyncIterator[None]:
        # People arrive at random, so a short wait for a free worker absorbs a burst; if none frees up in time, say
        # "busy" rather than let work pile up (§5.7.4). The API turns "busy" into a safe "try again".
        try:
            with anyio.fail_after(settings.queue_s):
                await limiter.acquire()
        except TimeoutError:
            raise HTTPException(503, "inference is busy; retry shortly", headers={"Retry-After": "1"}) from None
        try:
            yield
        finally:
            limiter.release()

    return app
