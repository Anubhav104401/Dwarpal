"""The API's client for the inference service: the document check has its own, longer time limit."""

from __future__ import annotations

import anyio
import httpx

from dwarpal_api.adapters.inference import InferenceClient
from dwarpal_contracts import FaceRequestMeta


def meta() -> FaceRequestMeta:
    return FaceRequestMeta.model_validate({"frames": [{"index": 0, "t_ms": 0.0}]})


def test_the_document_check_waits_longer_than_the_face_check() -> None:
    waited: dict[str, float] = {}

    def inference(request: httpx.Request) -> httpx.Response:
        waited[request.url.path] = request.extensions["timeout"]["read"]
        return httpx.Response(503)

    async def both() -> None:
        http = httpx.AsyncClient(transport=httpx.MockTransport(inference), base_url="http://inference", timeout=5.0)
        client = InferenceClient(http, document_timeout_s=20.0)
        assert await client.analyze_face(meta(), [b"frame"]) is None
        assert await client.analyze_document(meta(), [b"frame"], b"document") is None

    anyio.run(both)
    assert waited == {"/internal/v1/analyze/face": 5.0, "/internal/v1/analyze/document": 20.0}
