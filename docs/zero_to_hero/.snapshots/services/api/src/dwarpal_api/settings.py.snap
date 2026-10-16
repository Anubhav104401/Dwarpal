"""Settings for the API service, read from environment variables that start with DWARPAL_."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]
DEV_MASTER_KEY = base64.b64encode(b"dev-only-master-key-for-dwarpal!").decode()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DWARPAL_", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://dwarpal:dwarpal-local-only@127.0.0.1:5432/dwarpal"
    valkey_url: str = "redis://127.0.0.1:6379/0"
    inference_url: str = "http://127.0.0.1:8001"
    inference_timeout_s: float = 5.0
    master_key: SecretStr = SecretStr(DEV_MASTER_KEY)
    issuer: str = "http://localhost:8000"
    verify_url: str = "http://localhost:3000"
    cors_origins: list[str] = ["http://localhost:3000"]
    models_dir: Path = REPO_ROOT / "models"
    age_manifest: str = "registry/age/stub/manifest.json"
    session_ttl_s: int = 1800
    flow_ttl_s: int = 900
    challenge_ttl_s: int = 120

    @model_validator(mode="after")
    def refuse_development_values_in_production(self) -> Settings:
        if self.environment != "production":
            return self
        if self.master_key.get_secret_value() == DEV_MASTER_KEY:
            raise ValueError("DWARPAL_MASTER_KEY must be set to a real secret in production")
        for name in ("issuer", "verify_url"):
            if not getattr(self, name).startswith("https://"):
                raise ValueError(f"DWARPAL_{name.upper()} must be an https:// address in production")
        return self
