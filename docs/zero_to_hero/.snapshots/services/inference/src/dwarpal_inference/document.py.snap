"""The document check's analysis (Phase 6): read the MRZ from a photo of a document page, find the face printed on it,
and compare that face with the selfie's. The selfie itself goes through the face pipeline, liveness included."""

from __future__ import annotations

import statistics
import time

from dwarpal_contracts import MAX_DOCUMENT_BYTES, MAX_FRAME_BYTES, DocumentAnalysis, FaceRequestMeta
from dwarpal_inference.pipeline import FacePipeline
from dwarpal_vision import DecodeError, FaceDetector, Image, decode_image
from dwarpal_vision.document import Tesseract, TesseractError, find_mrz, zone_lines
from dwarpal_vision.match import FaceMatcher

DOCUMENT_SIDE = 2400  # a document photo may be larger than a face frame (1920), for the MRZ's small print


class DocumentReader:
    def __init__(self, pipeline: FacePipeline, detector: FaceDetector, matcher: FaceMatcher, ocr: Tesseract) -> None:
        self.pipeline = pipeline
        self.detector = detector
        self.matcher = matcher
        self.ocr = ocr

    def analyze(self, document: bytes, meta: FaceRequestMeta, selfies: list[bytes]) -> DocumentAnalysis:
        started = time.perf_counter()
        face = self.pipeline.analyze(meta, selfies)
        try:
            page = decode_image(document, max_bytes=MAX_DOCUMENT_BYTES, max_side=DOCUMENT_SIDE)
        except DecodeError:
            return DocumentAnalysis(
                zone=[],
                zone_problem="undecodable",
                document_faces=0,
                similarity=None,
                face=face,
                duration_ms=(time.perf_counter() - started) * 1000,
            )
        zone, problem = self.read_zone(page)
        printed = self.detector.detect(page)
        similarity = None
        if len(printed) == 1:
            reference = self.matcher.embed(page, printed[0])
            scores = []
            for data in selfies:
                try:
                    image = decode_image(data, max_bytes=MAX_FRAME_BYTES)
                except DecodeError:
                    continue
                found = self.detector.detect(image)
                if len(found) == 1:
                    scores.append(self.matcher.similarity(reference, self.matcher.embed(image, found[0])))
            similarity = max(-1.0, min(1.0, statistics.median(scores))) if scores else None
        return DocumentAnalysis(
            zone=zone,
            zone_problem=problem,
            document_faces=len(printed),
            similarity=similarity,
            face=face,
            duration_ms=(time.perf_counter() - started) * 1000,
        )

    def read_zone(self, page: Image) -> tuple[list[str], str | None]:
        band = find_mrz(page)
        if band is None:
            return [], "mrz_not_found"
        try:
            lines = zone_lines(self.ocr.read(band))
        except TesseractError:
            return [], "ocr_unavailable"
        return (lines, None) if lines else ([], "mrz_not_found")
