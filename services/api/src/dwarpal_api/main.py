"""The API application: connect every part at start-up, close them at shutdown, and route requests.

Run it with:  uvicorn dwarpal_api.main:create_app --factory --port 8000 --log-config services/api/logging.json
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from dwarpal_api.adapters.db import make_engine, make_sessions
from dwarpal_api.adapters.inference import InferenceClient
from dwarpal_api.adapters.signing import KeyRing, MasterKey
from dwarpal_api.adapters.store import FlowStore
from dwarpal_api.app.verification import Services
from dwarpal_api.domain.policy import load_manifest
from dwarpal_api.http import flow, health, problems, rp, wellknown
from dwarpal_api.http.limits import BodyLimit
from dwarpal_api.settings import Settings


def create_app(settings: Settings | None = None, inference_http: httpx.AsyncClient | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(settings.database_url, role=settings.database_role)
        sessions = make_sessions(engine)
        valkey = Redis.from_url(settings.valkey_url)
        http = inference_http or httpx.AsyncClient(
            base_url=settings.inference_url, timeout=settings.inference_timeout_s
        )
        keyring = KeyRing(MasterKey(settings.master_key.get_secret_value()))
        async with sessions() as session:
            await keyring.load(session, datetime.now(UTC))
        app.state.services = Services(
            settings=settings,
            sessions=sessions,
            store=FlowStore(valkey),
            inference=InferenceClient(http),
            keyring=keyring,
            manifest=load_manifest(settings.models_dir / settings.age_manifest),
        )
        try:
            yield
        finally:
            if inference_http is None:
                await http.aclose()
            await valkey.aclose()
            await engine.dispose()

    app = FastAPI(title="Dwarpal API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(BodyLimit)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-Id", "X-Dwarpal-Device"],
        expose_headers=["X-Request-Id"],
    )
    problems.install(app)
    for module in (rp, flow, wellknown, health):
        app.include_router(module.router)
    return app
