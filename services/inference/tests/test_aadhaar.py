"""Tests for the Aadhaar Secure QR check (Part 7): UIDAI's key ring, and the document check reading a code.

No real Aadhaar is used. The specimens are signed with a key made here and thrown away with the test, so UIDAI's own
keys must — and do — refuse them; a second ring that holds the throwaway key's certificate shows the accepting path.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

import cv2
import httpx
import numpy as np
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID
from fastapi import FastAPI

from dwarpal_contracts import DocumentAnalysis, FaceRequestMeta, FrameMeta
from dwarpal_inference.aadhaar import UIDAI_KEYS, KeyRing
from dwarpal_inference.main import create_app
from dwarpal_inference.settings import Settings
from dwarpal_vision.aadhaar import pack, specimen_data, specimen_photo, specimen_png

REPO = Path(__file__).resolve().parents[3]
PORTRAIT = (REPO / "libs" / "vision" / "tests" / "fixtures" / "astronaut.jpg").read_bytes()
NO_OCR = ["no-such-program-dwarpal"]  # these tests never need Tesseract


@pytest.fixture(scope="module")
def issuer() -> rsa.RSAPrivateKey:
    """A stand-in for UIDAI's signing key: the same kind (RSA, 2,048 bits), made for this test run only."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="module")
def keys_dir(issuer: rsa.RSAPrivateKey, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A folder holding the stand-in's certificate, as UIDAI's folder holds UIDAI's."""
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Dwarpal test issuer")])
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(issuer.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .sign(issuer, hashes.SHA256())
    )
    folder = tmp_path_factory.mktemp("keys")
    (folder / "test_issuer.cer").write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    (folder / "test_issuer_der.cer").write_bytes(certificate.public_bytes(serialization.Encoding.DER))
    return folder


def specimen(issuer: rsa.RSAPrivateKey, born: str = "01-01-1990") -> bytes:
    """A made-up Secure QR's bytes: the fixture's portrait inside, signed by the stand-in."""
    portrait = np.asarray(cv2.imdecode(np.frombuffer(PORTRAIT, np.uint8), cv2.IMREAD_COLOR), dtype=np.uint8)
    photo = specimen_photo(portrait[20:245, 133:313])  # cut close round the face, as an ID photo is
    return specimen_data(born, photo, lambda signed: issuer.sign(signed, padding.PKCS1v15(), hashes.SHA256()))


@asynccontextmanager
async def client_for(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://inference") as client:
            yield client


async def check(settings: Settings, document: bytes) -> tuple[DocumentAnalysis, dict[str, str]]:
    meta = FaceRequestMeta(frames=[FrameMeta(index=i, t_ms=i * 120.0) for i in range(3)])
    files = {f"frame_{i}": (f"frame_{i}.jpg", PORTRAIT, "image/jpeg") for i in range(3)}
    files["document"] = ("document.png", document, "image/png")
    async with client_for(create_app(settings)) as client:
        response = await client.post(
            "/internal/v1/analyze/document", data={"meta": meta.model_dump_json()}, files=files
        )
        ready = await client.get("/readyz")
    assert response.status_code == 200
    return DocumentAnalysis.model_validate(response.json()), ready.json()


def test_uidais_ring_holds_its_five_published_keys_and_refuses_a_stranger(issuer: rsa.RSAPrivateKey) -> None:
    ring = KeyRing(UIDAI_KEYS)
    assert len(ring.keys) == 5
    assert all(key.key_size == 2048 for key in ring.keys.values())
    data = specimen(issuer)
    assert ring.signer(data[:-256], data[-256:]) is None  # not signed by UIDAI: not accepted


def test_a_ring_names_the_key_that_signed_and_a_changed_byte_breaks_it(
    issuer: rsa.RSAPrivateKey, keys_dir: Path
) -> None:
    ring = KeyRing(keys_dir)
    assert set(ring.keys) == {"test_issuer", "test_issuer_der"}  # a certificate is read as text (PEM) or bytes (DER)
    data = specimen(issuer)
    signed, signature = data[:-256], data[-256:]
    assert ring.signer(signed, signature) == "test_issuer"
    older = signed.replace(b"01-01-1990", b"01-01-1980")  # the same code, claiming to be ten years older
    assert older != signed and ring.signer(older, signature) is None


def test_a_file_that_is_not_a_certificate_is_refused(tmp_path: Path) -> None:
    (tmp_path / "bad.cer").write_bytes(b"-----BEGIN CERTIFICATE-----\nnot one\n-----END CERTIFICATE-----\n")
    with pytest.raises(ValueError):
        KeyRing(tmp_path)


@pytest.mark.anyio
async def test_a_document_check_reads_a_secure_qr_and_matches_the_selfie_to_its_photo(
    issuer: rsa.RSAPrivateKey, keys_dir: Path
) -> None:
    code = specimen_png(pack(specimen(issuer, "15-08-2001")))
    analysis, ready = await check(Settings(tesseract_command=NO_OCR, aadhaar_keys_dir=str(keys_dir)), code)
    assert analysis.aadhaar is not None
    assert analysis.aadhaar.signed_by == "test_issuer" and analysis.aadhaar.born == "2001-08-15"
    assert analysis.zone == [] and analysis.zone_problem is None
    assert analysis.document_faces == 1  # the face in the code's own photo
    assert analysis.similarity is not None and analysis.similarity > 0.5
    assert analysis.face.usable_frames == 3
    assert "Specimen" not in analysis.model_dump_json()  # the name never leaves the service
    assert ready["aadhaar_keys"] == "2"


@pytest.mark.anyio
async def test_a_specimen_is_read_but_not_taken_for_uidais(issuer: rsa.RSAPrivateKey) -> None:
    code = specimen_png(pack(specimen(issuer)))
    analysis, ready = await check(Settings(tesseract_command=NO_OCR), code)  # the real ring: UIDAI's keys
    assert analysis.aadhaar is not None
    assert analysis.aadhaar.signed_by is None and analysis.aadhaar.born == "1990-01-01"
    assert ready["aadhaar_keys"] == "5"


@pytest.mark.anyio
async def test_a_qr_code_that_is_not_a_secure_qr_says_so() -> None:
    code = specimen_png("1234567890" * 40)  # digits, as a Secure QR is, but not one
    analysis, _ = await check(Settings(tesseract_command=NO_OCR), code)
    assert analysis.aadhaar is not None
    assert analysis.aadhaar.born is None and analysis.aadhaar.problem == "aadhaar_qr_unreadable"
    assert analysis.document_faces == 0 and analysis.similarity is None


@pytest.mark.anyio
async def test_switched_off_a_secure_qr_is_just_a_picture_without_an_mrz(issuer: rsa.RSAPrivateKey) -> None:
    code = specimen_png(pack(specimen(issuer)))
    analysis, ready = await check(Settings(tesseract_command=NO_OCR, aadhaar_qr=False), code)
    assert analysis.aadhaar is None
    assert ready["aadhaar_keys"] == "0"
