"""The document check's analysis (Phase 6): read the MRZ from a photo of a document page, find the face printed on it,
and compare that face with the selfie's. The selfie itself goes through the face pipeline, liveness included.

A picture of an Aadhaar Secure QR code is read too (Part 7): then the date of birth and the photo come out of the
code, and UIDAI's signature on it is checked."""

from __future__ import annotations

import statistics
import time

import cv2
import numpy as np

from dwarpal_contracts import MAX_DOCUMENT_BYTES, MAX_FRAME_BYTES, AadhaarReading, DocumentAnalysis, FaceRequestMeta
from dwarpal_inference.aadhaar import KeyRing
from dwarpal_inference.pipeline import FacePipeline
from dwarpal_vision import DecodeError, FaceDetector, Image, decode_image
from dwarpal_vision.aadhaar import SecureQrError, decode_photo, parse, read_qr, unpack
from dwarpal_vision.document import Tesseract, TesseractError, find_mrz, zone_lines
from dwarpal_vision.match import FaceMatcher

DOCUMENT_SIDE = 2400  # a document photo may be larger than a face frame (1920), for the MRZ's small print
QR_PHOTO_SIDE = 320  # the photo inside a Secure QR is tiny: it is enlarged to this before a face is looked for


class DocumentReader:
    def __init__(
        self,
        pipeline: FacePipeline,
        detector: FaceDetector,
        matcher: FaceMatcher,
        ocr: Tesseract,
        keys: KeyRing | None = None,
    ) -> None:
        self.pipeline = pipeline
        self.detector = detector
        self.matcher = matcher
        self.ocr = ocr
        self.keys = keys  # UIDAI's public keys; None: Aadhaar Secure QR codes aren't read

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
        # A Secure QR is looked for first: its dense pattern can look like lines of print to the MRZ finder.
        aadhaar, portrait = self.read_aadhaar(page)
        if aadhaar is None:
            zone, problem = self.read_zone(page)
            portrait = page
        else:
            zone, problem = [], None
        printed = [] if portrait is None else self.detector.detect(portrait)
        similarity = None
        if portrait is not None and len(printed) == 1:
            reference = self.matcher.embed(portrait, printed[0])
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
            aadhaar=aadhaar,
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

    def read_aadhaar(self, page: Image) -> tuple[AadhaarReading | None, Image | None]:
        """What an Aadhaar Secure QR in the picture says, and the photo inside it; (None, None) if the picture shows
        no such code. The code's bytes are dropped as this returns: of all it holds, only the date of birth leaves."""
        if self.keys is None:
            return None, None
        text = read_qr(page)
        if text is None:
            return None, None
        try:
            code = parse(unpack(text))
        except SecureQrError as error:
            return AadhaarReading(signed_by=None, born=None, problem=error.code), None
        reading = AadhaarReading(signed_by=self.keys.signer(code.signed, code.signature), born=code.born)
        photo = decode_photo(code.photo)
        if photo is None:
            return reading, None
        factor = QR_PHOTO_SIDE / min(photo.shape[:2])
        if factor > 1:
            photo = np.asarray(cv2.resize(photo, None, fx=factor, fy=factor, interpolation=cv2.INTER_CUBIC), np.uint8)
        return reading, photo
