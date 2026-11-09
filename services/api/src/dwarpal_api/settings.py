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
    # The role the API works as: it owns no tables, so row-level security confines it to one tenant at a time.
    database_role: str | None = "dwarpal_app"
    valkey_url: str = "redis://127.0.0.1:6379/0"
    inference_url: str = "http://127.0.0.1:8001"
    inference_timeout_s: float = 5.0
    # The step-up's document check does more (the face checks, then OCR and a second face comparison), so it waits
    # longer before giving up.
    document_timeout_s: float = 20.0
    master_key: SecretStr = SecretStr(DEV_MASTER_KEY)
    issuer: str = "http://localhost:8000"
    verify_url: str = "http://localhost:3000"
    cors_origins: list[str] = ["http://localhost:3000"]
    models_dir: Path = REPO_ROOT / "models"
    age_manifest: str = "registry/age/stub/manifest.json"
    session_ttl_s: int = 1800
    flow_ttl_s: int = 900
    challenge_ttl_s: int = 120
    # Liveness challenges one device, and one network address, may take per project in an hour. A device is the random
    # ID the verify page keeps; the address budget is larger, because many people can share one network.
    device_challenges_per_hour: int = 30
    address_challenges_per_hour: int = 120
    # Requests one API key may make: a steady rate per second, with bursts of up to `api_burst` at once.
    api_requests_per_second: float = 100.0
    api_burst: int = 200
    # Calls of the verify page's API from one network address: a steady rate per second, with bursts of up to
    # `flow_burst`. Plenty for many people sharing a network; a flood from one address stops before the database.
    flow_requests_per_second: float = 10.0
    flow_burst: int = 300
    # Webhooks: never to private or local addresses, except for local development and tests (refused in production).
    webhook_allow_private: bool = False
    webhook_timeout_s: float = 10.0
    webhook_poll_s: float = 2.0
    # The console: the sites its pages are served from (checked against Origin), how long a signed-in session lasts
    # without use, and whether its cookie needs HTTPS (only tests over plain http turn this off; never production).
    console_origins: list[str] = ["http://localhost:3000"]
    console_session_ttl_s: int = 43_200  # 12 hours
    console_cookie_secure: bool = True
    # Passkeys belong to a site's name (WebAuthn's relying party ID): the console's host name, such as dwarpal.in.
    # Left empty, it is the host of the first console origin.
    passkey_rp_id: str = ""
    # Sign-in attempts: per account and per network address, a few at once, then one every so often.
    login_burst: int = 5
    login_per_minute: float = 1.0
    # The lock-out back-off: after this many wrong passwords or codes in a row for one account from one network address,
    # that address must wait before trying the account again — a minute at first, twice as long after each further
    # wrong one, at most an hour. Other addresses aren't locked, so a stranger's guessing can't lock the owner out.
    login_free_failures: int = 5
    login_first_lock_s: int = 60
    login_longest_lock_s: int = 3600
    # Where to send traces (an OpenTelemetry collector's address, such as http://127.0.0.1:4318); none means no traces.
    otel_endpoint: str | None = None

    @model_validator(mode="after")
    def refuse_development_values_in_production(self) -> Settings:
        if self.environment != "production":
            return self
        if self.master_key.get_secret_value() == DEV_MASTER_KEY:
            raise ValueError("DWARPAL_MASTER_KEY must be set to a real secret in production")
        if self.webhook_allow_private:
            raise ValueError("DWARPAL_WEBHOOK_ALLOW_PRIVATE must not be set in production")
        if not self.console_cookie_secure:
            raise ValueError("DWARPAL_CONSOLE_COOKIE_SECURE must not be turned off in production")
        for name in ("issuer", "verify_url"):
            if not getattr(self, name).startswith("https://"):
                raise ValueError(f"DWARPAL_{name.upper()} must be an https:// address in production")
        return self
