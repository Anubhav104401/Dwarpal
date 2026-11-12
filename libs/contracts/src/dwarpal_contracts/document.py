"""Messages exchanged between the API and the inference service about a document check (the step-up, Phase 6).

As with faces, nothing here can hold an image. The MRZ lines are the one text read from a passport or ID card, and the
names line in them is blanked by the inference service before they leave it. From an Aadhaar Secure QR code, only the
date of birth and the name of the key that signed it are passed on.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from dwarpal_contracts.face import Contract, FaceAnalysis

MAX_DOCUMENT_BYTES = 1024 * 1024  # a photo of a document page needs more detail than a face frame


class AadhaarReading(Contract):
    """What is taken from an Aadhaar Secure QR code: whether UIDAI signed it, and the date of birth. The name, the
    address and the reference number in the code never leave the inference service."""

    signed_by: str | None  # the UIDAI certificate whose key made the signature; None when no known key did
    born: str | None  # "YYYY-MM-DD", or "YYYY" when the code gives only the year; None when the code can't be read
    problem: str | None = None  # why there is no date: "aadhaar_qr_unreadable"


class DocumentAnalysis(Contract):
    zone: list[str]  # the MRZ lines as read, names blanked; empty when no MRZ was found or Tesseract failed
    zone_problem: str | None = None  # why there are no lines: "undecodable", "mrz_not_found" or "ocr_unavailable"
    # Set when the picture showed an Aadhaar Secure QR code and no MRZ: then the "document's photo" below is the one
    # inside the code.
    aadhaar: AadhaarReading | None = None
    document_faces: Annotated[int, Field(ge=0)]  # faces found on the document's photo (1 is right)
    # How alike the document's face and the selfie's are (cosine similarity, -1 to 1): the median over the selfie frames
    # that show one face. None when either face is missing.
    similarity: Annotated[float, Field(ge=-1.0, le=1.0)] | None
    face: FaceAnalysis  # the selfie, analysed exactly as a face attempt is: liveness included
    duration_ms: Annotated[float, Field(ge=0.0)]
