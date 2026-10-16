"""Tests for the inference pipeline and its HTTP interface, using the stand-in age model."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import numpy as np
import pytest
from fastapi import FastAPI

from dwarpal_contracts import FaceAnalysis, FaceRequestMeta, FrameMeta
from dwarpal_inference.backends import AGES, StubAgeBackend
from dwarpal_inference.main import create_app
from dwarpal_inference.pipeline import FacePipeline
from dwarpal_inference.settings import Settings
from dwarpal_vision import FaceDetector

REPO = Path(__file__).resolve().parents[3]
PORTRAIT = (REPO / "libs" / "vision" / "tests" / "fixtures" / "astronaut.jpg").read_bytes()
MODEL = REPO / "models" / "third_party" / "face_detection_yunet_2023mar.onnx"


def burst(count: int) -> FaceRequestMeta:
    return FaceRequestMeta(frames=[FrameMeta(index=i, t_ms=i * 120.0) for i in range(count)])


@asynccontextmanager
async def client_for(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://inference") as client:
            yield client


@pytest.fixture(scope="module")
def pipeline() -> FacePipeline:
    return FacePipeline(FaceDetector(MODEL), StubAgeBackend(30.0, 2.5))


def test_stub_backend_is_a_distribution_centred_on_its_age() -> None:
    row = StubAgeBackend(30.0, 2.5).predict([np.zeros((224, 224, 3), dtype=np.uint8)])[0]
    assert row.shape == (101,)
    assert abs(row.sum() - 1.0) < 1e-9
    assert abs(float((row * AGES).sum()) - 30.0) < 0.01


def test_pipeline_turns_a_burst_of_frames_into_one_analysis(pipeline: FacePipeline) -> None:
    result = pipeline.analyze(burst(3), [PORTRAIT] * 3)
    assert result.usable_frames == 3
    assert result.age is not None
    assert abs(result.age.mean - 30.0) < 0.5
    assert result.age.p_over[18] > 0.999
    assert result.age.p_over[25] > 0.95
    assert len(result.age.frame_means) == 3


def test_a_bad_frame_is_reported_without_spoiling_the_others(pipeline: FacePipeline) -> None:
    result = pipeline.analyze(burst(2), [b"definitely not an image", PORTRAIT])
    assert result.frames[0].flags == ["undecodable"]
    assert result.usable_frames == 1


def test_no_usable_frames_means_no_age_estimate(pipeline: FacePipeline) -> None:
    result = pipeline.analyze(burst(1), [bytes(16)])
    assert result.usable_frames == 0
    assert result.age is None


@pytest.mark.anyio
async def test_http_endpoint_analyses_multipart_frames() -> None:
    files = {f"frame_{i}": (f"frame_{i}.jpg", PORTRAIT, "image/jpeg") for i in range(2)}
    async with client_for(create_app(Settings(stub_age=40.0))) as client:
        response = await client.post(
            "/internal/v1/analyze/face", data={"meta": burst(2).model_dump_json()}, files=files
        )
        ready = await client.get("/readyz")
    assert response.status_code == 200
    analysis = FaceAnalysis.model_validate(response.json())
    assert analysis.model_version == "stub-age-40"
    assert analysis.usable_frames == 2
    assert ready.json()["age_model"] == "stub-age-40"


@pytest.mark.anyio
async def test_http_endpoint_rejects_a_missing_frame() -> None:
    files = {"frame_0": ("frame_0.jpg", PORTRAIT, "image/jpeg")}
    async with client_for(create_app()) as client:
        response = await client.post(
            "/internal/v1/analyze/face", data={"meta": burst(2).model_dump_json()}, files=files
        )
    assert response.status_code == 422
    assert response.json()["detail"] == "frame_1 is missing"
