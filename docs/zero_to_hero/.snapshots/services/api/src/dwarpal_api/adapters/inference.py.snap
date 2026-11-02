"""The API's client for the inference service. Any failure becomes "no analysis", which can never become a pass."""

from __future__ import annotations

import httpx
from pydantic import ValidationError

from dwarpal_contracts import DocumentAnalysis, FaceAnalysis, FaceRequestMeta


class InferenceClient:
    def __init__(self, client: httpx.AsyncClient, document_timeout_s: float = 20.0) -> None:
        self._client = client
        self._document_timeout_s = document_timeout_s

    async def analyze_face(self, meta: FaceRequestMeta, frames: list[bytes]) -> FaceAnalysis | None:
        files = {
            f"frame_{frame.index}": (f"frame_{frame.index}.jpg", data, "image/jpeg")
            for frame, data in zip(meta.frames, frames, strict=True)
        }
        try:
            response = await self._client.post(
                "/internal/v1/analyze/face", data={"meta": meta.model_dump_json()}, files=files
            )
        except httpx.HTTPError:
            return None
        if response.status_code != 200:
            return None
        try:
            return FaceAnalysis.model_validate_json(response.content)
        except ValidationError:
            return None

    async def analyze_document(
        self, meta: FaceRequestMeta, frames: list[bytes], document: bytes
    ) -> DocumentAnalysis | None:
        """The step-up's document check: the document's photo with the selfie frames (Phase 6)."""
        files = {
            f"frame_{frame.index}": (f"frame_{frame.index}.jpg", data, "image/jpeg")
            for frame, data in zip(meta.frames, frames, strict=True)
        }
        files["document"] = ("document.jpg", document, "image/jpeg")
        try:
            response = await self._client.post(
                "/internal/v1/analyze/document",
                data={"meta": meta.model_dump_json()},
                files=files,
                timeout=self._document_timeout_s,
            )
        except httpx.HTTPError:
            return None
        if response.status_code != 200:
            return None
        try:
            return DocumentAnalysis.model_validate_json(response.content)
        except ValidationError:
            return None
