"""Tests for the inference pipeline and its HTTP interface, the stand-in age model, and ONNX age models."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
import cv2
import httpx
import numpy as np
import onnx
import pytest
from fastapi import FastAPI
from onnx import TensorProto, helper, numpy_helper

from dwarpal_contracts import DocumentAnalysis, FaceAnalysis, FaceRequestMeta, FrameMeta
from dwarpal_inference.backends import AGES, ModelFileError, OnnxAgeBackend, StubAgeBackend
from dwarpal_inference.main import build_age_backend, build_pipeline, create_app
from dwarpal_inference.pipeline import FacePipeline, sharpest
from dwarpal_inference.settings import Settings
from dwarpal_vision import Face, FaceDetector, Image, RenderDetector
from dwarpal_vision.document import Tesseract
from dwarpal_vision.specimen import specimen_jpeg

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


def test_the_age_model_sees_only_the_sharpest_few_flawless_frames(pipeline: FacePipeline) -> None:
    result = pipeline.analyze(burst(6), [PORTRAIT] * 6)
    assert result.usable_frames == 6  # every flawless frame still counts
    assert result.age is not None and len(result.age.frame_means) == 3  # but only 3 were estimated
    assert sharpest([0.2, 0.9, 0.5, 0.9, 0.1], 3) == [1, 3, 2]  # best first; a tie keeps its order


def test_a_bad_frame_is_reported_without_spoiling_the_others(pipeline: FacePipeline) -> None:
    result = pipeline.analyze(burst(2), [b"definitely not an image", PORTRAIT])
    assert result.frames[0].flags == ["undecodable"]
    assert result.usable_frames == 1


class FixedRender(RenderDetector):
    """Stands in for a trained render detector: the same answer for every face."""

    def __init__(self, chance: float) -> None:
        self.chance = chance

    def rendered(self, image: Image, face: Face) -> float:
        return self.chance


def test_the_render_detector_is_recorded_for_every_face_and_off_without_a_model() -> None:
    result = FacePipeline(FaceDetector(MODEL), StubAgeBackend(30.0, 2.5), render=FixedRender(0.25)).analyze(
        burst(2), [PORTRAIT] * 2
    )
    assert [frame.rendered_score for frame in result.frames] == [0.25, 0.25]
    assert result.liveness is not None and result.liveness.rendered == 0.25
    assert build_pipeline(Settings()).render is None
    with pytest.raises(FileNotFoundError, match="render detector not found"):
        build_pipeline(Settings(render_model="registry/render/none/render.onnx"))


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
async def test_readiness_says_when_the_anti_spoofing_networks_are_missing() -> None:
    settings = Settings(antispoof_files=("third_party/absent_a.onnx", "third_party/absent_b.onnx"))
    async with client_for(create_app(settings)) as client:
        ready = await client.get("/readyz")
    assert ready.json()["antispoof"] == "missing"


@pytest.mark.anyio
async def test_http_endpoint_rejects_a_missing_frame() -> None:
    files = {"frame_0": ("frame_0.jpg", PORTRAIT, "image/jpeg")}
    async with client_for(create_app()) as client:
        response = await client.post(
            "/internal/v1/analyze/face", data={"meta": burst(2).model_dump_json()}, files=files
        )
    assert response.status_code == 422
    assert response.json()["detail"] == "frame_1 is missing"


def tiny_model(folder: Path) -> Path:
    """A stand-in ONNX age model with the real one's interface: pixels in, 101 probabilities out."""
    weights = np.linspace(-1.0, 1.0, 3 * len(AGES), dtype=np.float32).reshape(3, len(AGES))
    graph = helper.make_graph(
        [
            helper.make_node("GlobalAveragePool", ["pixels"], ["pooled"]),
            helper.make_node("Flatten", ["pooled"], ["flat"]),
            helper.make_node("MatMul", ["flat", "weights"], ["logits"]),
            helper.make_node("Softmax", ["logits"], ["probabilities"], axis=1),
        ],
        "tiny",
        [helper.make_tensor_value_info("pixels", TensorProto.FLOAT, ["faces", 3, 224, 224])],
        [helper.make_tensor_value_info("probabilities", TensorProto.FLOAT, ["faces", len(AGES)])],
        [numpy_helper.from_array(weights / 255.0, "weights")],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 18)], ir_version=10)
    folder.mkdir(parents=True, exist_ok=True)
    onnx.save(model, folder / "model.onnx")
    digest = hashlib.sha256((folder / "model.onnx").read_bytes()).hexdigest()
    manifest = {"version": "tiny-1", "model": {"file": "model.onnx", "sha256": digest}}
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return folder


def test_an_onnx_model_gives_one_distribution_per_face(tmp_path: Path) -> None:
    backend = OnnxAgeBackend(tiny_model(tmp_path / "tiny"))
    faces = [np.zeros((224, 224, 3), dtype=np.uint8), np.full((224, 224, 3), 255, dtype=np.uint8)]
    rows = backend.predict(faces)
    assert backend.version == "tiny-1"
    assert rows.shape == (2, len(AGES))
    assert rows.sum(axis=1) == pytest.approx([1.0, 1.0], abs=1e-5)
    assert not np.allclose(rows[0], rows[1])


def test_a_model_file_that_is_not_the_pinned_one_is_refused(tmp_path: Path) -> None:
    folder = tiny_model(tmp_path / "tiny")
    (folder / "model.onnx").write_bytes((folder / "model.onnx").read_bytes() + b"tampered")
    with pytest.raises(ModelFileError, match="fingerprint"):
        OnnxAgeBackend(folder)
    (folder / "model.onnx").unlink()
    with pytest.raises(ModelFileError, match="missing"):
        OnnxAgeBackend(folder)


def test_settings_choose_the_age_backend(tmp_path: Path) -> None:
    tiny_model(tmp_path / "registry" / "tiny")
    chosen = build_age_backend(Settings(age_backend="onnx", models_dir=tmp_path, age_model="registry/tiny"))
    assert chosen.version == "tiny-1"
    assert isinstance(build_age_backend(Settings()), StubAgeBackend)


class Slow:
    """A stand-in pipeline that takes a quarter of a second, to fill the workers."""

    def analyze(self, meta: FaceRequestMeta, images: list[bytes]) -> FaceAnalysis:
        time.sleep(0.25)
        return FaceAnalysis(model_version="slow", frames=[], usable_frames=0, age=None, duration_ms=250.0)


@pytest.mark.anyio
@pytest.mark.parametrize(("queue_s", "statuses"), [(0.05, [200, 503]), (1.0, [200, 200])])
async def test_a_request_waits_briefly_for_a_free_worker_then_is_told_busy(queue_s: float, statuses: list[int]) -> None:
    files = {"frame_0": ("frame_0.jpg", PORTRAIT, "image/jpeg")}
    data = {"meta": burst(1).model_dump_json()}
    app = create_app(Settings(workers=1, queue_s=queue_s))
    async with client_for(app) as client:
        app.state.pipeline = Slow()
        answers: list[int] = []

        async def send() -> None:
            answers.append((await client.post("/internal/v1/analyze/face", data=data, files=files)).status_code)

        async with anyio.create_task_group() as group:
            group.start_soon(send)
            group.start_soon(send)
    assert sorted(answers) == statuses  # with one worker: a short wait gives up, a longer one is served


# Tesseract where it is installed, else in the project's OCR container (Phase 6); None if neither answers.
TESSERACT = next(
    (
        command
        for command in (["tesseract"], ["docker", "exec", "-i", "dwarpal-ocr-1", "tesseract"])
        if Tesseract(command).available()
    ),
    None,
)


@pytest.mark.anyio
async def test_a_document_check_reads_the_zone_and_matches_the_selfie_to_the_printed_face() -> None:
    if TESSERACT is None:
        pytest.skip("Tesseract isn't installed, and the OCR container isn't running")
    portrait = np.asarray(cv2.imdecode(np.frombuffer(PORTRAIT, np.uint8), cv2.IMREAD_COLOR), dtype=np.uint8)
    files = {f"frame_{i}": (f"frame_{i}.jpg", PORTRAIT, "image/jpeg") for i in range(3)}
    files["document"] = ("document.jpg", specimen_jpeg(portrait, "900101", "360101"), "image/jpeg")
    async with client_for(create_app(Settings(tesseract_command=TESSERACT))) as client:
        response = await client.post(
            "/internal/v1/analyze/document", data={"meta": burst(3).model_dump_json()}, files=files
        )
        ready = await client.get("/readyz")
    assert response.status_code == 200
    analysis = DocumentAnalysis.model_validate(response.json())
    assert len(analysis.zone) == 2 and analysis.zone[0].startswith("P<UTO")
    assert "ERIKSSON" not in analysis.zone[0]  # the names never leave the service
    assert analysis.document_faces == 1
    assert analysis.similarity is not None and analysis.similarity > 0.5
    assert analysis.face.usable_frames == 3
    assert ready.json()["ocr"] == "ready"


@pytest.mark.anyio
async def test_without_tesseract_a_document_check_says_so_and_reads_nothing() -> None:
    files = {"frame_0": ("frame_0.jpg", PORTRAIT, "image/jpeg"), "document": ("d.jpg", PORTRAIT, "image/jpeg")}
    async with client_for(create_app(Settings(tesseract_command=["no-such-program-dwarpal"]))) as client:
        response = await client.post(
            "/internal/v1/analyze/document", data={"meta": burst(1).model_dump_json()}, files=files
        )
        ready = await client.get("/readyz")
    analysis = DocumentAnalysis.model_validate(response.json())
    # The portrait has no MRZ, so the band isn't found before Tesseract is even needed; readiness says it's missing.
    assert (analysis.zone, analysis.zone_problem) == ([], "mrz_not_found")
    assert ready.json()["ocr"] == "missing"
