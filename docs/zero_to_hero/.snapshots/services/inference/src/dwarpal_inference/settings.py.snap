"""Settings for the inference service, read from environment variables that start with DWARPAL_INFERENCE_."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DWARPAL_INFERENCE_", extra="ignore")

    models_dir: Path = REPO_ROOT / "models"
    detector_file: str = "third_party/face_detection_yunet_2023mar.onnx"
    mesh_file: str = "third_party/face_landmarker.task"
    hands_file: str = "third_party/hand_landmarker.task"
    antispoof_files: tuple[str, str] = ("third_party/minifasnet_v2_2.7.onnx", "third_party/minifasnet_v1se_4.0.onnx")
    matcher_file: str = "third_party/face_recognition_sface_2021dec_int8.onnx"
    # The render detector, once one is trained and has passed its gates (e.g. "registry/render/0.1.0/render.onnx");
    # empty: none, and nothing is measured.
    render_model: str = ""
    # How to start Tesseract, as a JSON list: installed (the default, as in production), or in the project's OCR
    # container: DWARPAL_INFERENCE_TESSERACT_COMMAND='["docker", "exec", "-i", "dwarpal-ocr-1", "tesseract"]'.
    tesseract_command: list[str] = ["tesseract"]
    tesseract_timeout_s: float = 10.0
    # Read Aadhaar Secure QR codes in the document check (Part 7), trusting the certificates in this folder; empty: the
    # ones UIDAI publishes, which are part of this service.
    aadhaar_qr: bool = True
    aadhaar_keys_dir: str = ""
    age_backend: Literal["stub", "onnx"] = "stub"
    stub_age: float = 30.0
    stub_spread: float = 2.5
    age_model: str = "registry/age/age-convnext-tiny-2026.10.17"
    age_threads: int = 1
    # How many of an attempt's flawless frames the age model sees: the sharpest ones (decision P1, §5.7.4).
    age_frames: int = 3
    workers: int = 4
    # How long a request may wait for a free worker before the answer is "busy" (§5.7.4).
    queue_s: float = 1.0
    liveness: Literal["images", "labels"] = "images"

    @model_validator(mode="after")
    def labels_only_with_the_stand_in(self) -> Settings:
        if self.liveness == "labels" and self.age_backend != "stub":
            raise ValueError("liveness from labels is a test mode, allowed only with the stand-in age model")
        return self
