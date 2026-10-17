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
    age_backend: Literal["stub", "onnx"] = "stub"
    stub_age: float = 30.0
    stub_spread: float = 2.5
    age_model: str = "registry/age/age-convnext-tiny-2026.10.17"
    age_threads: int = 1
    workers: int = 4
    liveness: Literal["images", "labels"] = "images"

    @model_validator(mode="after")
    def labels_only_with_the_stand_in(self) -> Settings:
        if self.liveness == "labels" and self.age_backend != "stub":
            raise ValueError("liveness from labels is a test mode, allowed only with the stand-in age model")
        return self
