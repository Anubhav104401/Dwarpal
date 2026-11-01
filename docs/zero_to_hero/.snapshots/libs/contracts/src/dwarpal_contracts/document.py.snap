"""Messages exchanged between the API and the inference service about a document check (the step-up, Phase 6).

As with faces, nothing here can hold an image. The MRZ lines are the one text read from a document, and the names line
in them is blanked by the inference service before they leave it.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from dwarpal_contracts.face import Contract, FaceAnalysis

MAX_DOCUMENT_BYTES = 1024 * 1024  # a photo of a document page needs more detail than a face frame


class DocumentAnalysis(Contract):
    zone: list[str]  # the MRZ lines as read, names blanked; empty when no MRZ was found or Tesseract failed
    zone_problem: str | None = None  # why there are no lines: "undecodable", "mrz_not_found" or "ocr_unavailable"
    document_faces: Annotated[int, Field(ge=0)]  # faces found on the document's photo (1 is right)
    # How alike the document's face and the selfie's are (cosine similarity, -1 to 1): the median over the selfie frames
    # that show one face. None when either face is missing.
    similarity: Annotated[float, Field(ge=-1.0, le=1.0)] | None
    face: FaceAnalysis  # the selfie, analysed exactly as a face attempt is: liveness included
    duration_ms: Annotated[float, Field(ge=0.0)]
