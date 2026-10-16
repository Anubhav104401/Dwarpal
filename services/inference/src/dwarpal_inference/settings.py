"""Settings for the inference service, read from environment variables that start with DWARPAL_INFERENCE_."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DWARPAL_INFERENCE_", extra="ignore")

    models_dir: Path = REPO_ROOT / "models"
    detector_file: str = "third_party/face_detection_yunet_2023mar.onnx"
    age_backend: Literal["stub"] = "stub"
    stub_age: float = 30.0
    stub_spread: float = 2.5
    workers: int = 4
