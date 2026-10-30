"""The API end to end, against real PostgreSQL and Valkey containers and the real inference service in memory."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import hashlib
import hmac
import json
import logging
import re
import threading
import time
import uuid
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

import cv2
import docker
import httpx
import numpy as np
import pytest
import schemathesis
import uvicorn
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from hypothesis import HealthCheck, settings
from joserfc import jwt
from joserfc.jwk import KeySet
from pydantic import SecretStr
from redis.asyncio import Redis
from schemathesis import Case
from schemathesis.specs.openapi.checks import positive_data_acceptance
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.community.postgres import PostgresContainer
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from dwarpal_api.adapters.db import make_engine, make_sessions, tenant
from dwarpal_api.adapters.signing import MasterKey
from dwarpal_api.adapters.tables import (
    METADATA,
    ApiKey,
    AuditEntry,
    AuditHead,
    Event,
    IssuedToken,
    Membership,
    Organization,
    PolicyVersion,
    Project,
    SessionStat,
    User,
    VerificationAttempt,
    VerificationSession,
    WebhookDelivery,
    WebhookEndpoint,
)
from dwarpal_api.app import audit, maintenance
from dwarpal_api.app.delivery import Deliverer
from dwarpal_api.cli import API_DOCUMENT, api_document, maintain, migrate, revoke_key, rotate_key, seed_dev
from dwarpal_api.domain import ids, totp
from dwarpal_api.main import create_app as create_api
from dwarpal_api.settings import Settings
from dwarpal_contracts import Challenge, ClientSignals, FaceRequestMeta, FrameMeta
from dwarpal_inference.main import create_app as create_inference
from dwarpal_inference.settings import Settings as InferenceSettings

REPO = Path(__file__).resolve().parents[3]
PORTRAIT = (REPO / "libs" / "vision" / "tests" / "fixtures" / "astronaut.jpg").read_bytes()
RETURN_URL = "http://localhost:3100/age-check/complete"


def blank_frame() -> bytes:
    ok, encoded = cv2.imencode(".jpg", np.full((240, 320, 3), 128, dtype=np.uint8))
    assert ok
    return encoded.tobytes()


@pytest.fixture(scope="session")
def databases() -> Iterator[tuple[str, str]]:
    try:
        docker.from_env(timeout=5).ping()
    except Exception as error:
        pytest.skip(f"these tests need a running Docker engine: {error}")
    postgres = PostgresContainer(
        "postgres:18.6-alpine3.24",
        username="dwarpal",
        password="test-only",  # noqa: S106 - a throwaway password for a throwaway test container
        dbname="dwarpal",
    )
    valkey = (
        DockerContainer("valkey/valkey:9.1.2-alpine3.24")
        .with_exposed_ports(6379)
        .waiting_for(LogMessageWaitStrategy("Ready to accept connections"))
    )
    postgres.start()
    valkey.start()
    host, port = postgres.get_container_host_ip(), postgres.get_exposed_port(5432)
    database_url = f"postgresql+asyncpg://dwarpal:test-only@{host}:{port}/dwarpal"
    valkey_url = f"redis://{valkey.get_container_host_ip()}:{valkey.get_exposed_port(6379)}/0"
    migrate(database_url)
    yield database_url, valkey_url
    valkey.stop()
    postgres.stop()


@dataclass
class Harness:
    client: httpx.AsyncClient
    key: str
    project: str
    transport: httpx.ASGITransport


@asynccontextmanager
async def harness(
    databases: tuple[str, str],
    stub_age: float = 30.0,
    livemode: bool = False,
    liveness: Literal["images", "labels"] = "labels",
    scopes: list[str] | None = None,
    inference_via: Callable[[httpx.AsyncBaseTransport], httpx.AsyncBaseTransport] | None = None,
    **overrides: Any,
) -> AsyncIterator[Harness]:
    database_url, valkey_url = databases
    inference = create_inference(InferenceSettings(stub_age=stub_age, liveness=liveness))
    inference_transport: httpx.AsyncBaseTransport = httpx.ASGITransport(app=inference)
    if inference_via is not None:
        inference_transport = inference_via(inference_transport)
    async with (
        inference.router.lifespan_context(inference),
        httpx.AsyncClient(transport=inference_transport, base_url="http://inference") as inference_http,
    ):
        settings = Settings(environment="test", database_url=database_url, valkey_url=valkey_url, **overrides)
        api = create_api(settings, inference_http=inference_http)
        async with api.router.lifespan_context(api):
            project, key = await seed_dev(settings, livemode=livemode, scopes=scopes)
            transport = httpx.ASGITransport(app=api)
            async with httpx.AsyncClient(transport=transport, base_url="http://api") as client:
                yield Harness(client, key, project, transport)


async def create(h: Harness, headers_extra: dict[str, str] | None = None, **body: Any) -> httpx.Response:
    payload = {"policy": "uk_osa_18", "return_url": RETURN_URL, **body}
    headers = {"Authorization": f"Bearer {h.key}", **(headers_extra or {})}
    return await h.client.post("/v1/verification-sessions", json=payload, headers=headers)


def secret(created: dict[str, Any]) -> dict[str, str]:
    return {"client_secret": created["client_secret"]}


async def start(h: Harness, created: dict[str, Any]) -> dict[str, str]:
    response = await h.client.post(f"/v1/flow/sessions/{created['id']}/start", json=secret(created))
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['flow_token']}"}


def following(poses: list[str], count: int) -> list[FrameMeta]:
    """Frame labels that follow some poses: a frontal baseline, then one frame per pose, in the order given."""
    phases = ["baseline"] * (count - len(poses)) + poses
    return [FrameMeta(index=i, t_ms=i * 120.0, phase=phase) for i, phase in enumerate(phases)]  # type: ignore[arg-type]


async def attempt(
    h: Harness,
    session: str,
    flow: dict[str, str],
    frames: list[bytes],
    poses: list[str] | None = None,
    signals: ClientSignals | None = None,
    claimed: Challenge | None = None,
    challenge: dict[str, Any] | None = None,
) -> httpx.Response:
    """One face attempt. By default the frames' labels follow the challenge the server issued; an attack may label
    them in another order (`poses`), report other browser signals, or claim a challenge of its own. A challenge
    fetched earlier can be given (`challenge`); otherwise one is fetched now."""
    if challenge is None:
        challenge = (await h.client.post(f"/v1/flow/sessions/{session}/challenge", headers=flow)).json()
    shown = poses if poses is not None else challenge["poses"]
    frames = frames + frames[-1:] * max(0, 3 + len(shown) - len(frames))  # at least 3 frontal frames, then the poses
    labels = following(shown, len(frames))
    meta = FaceRequestMeta(frames=labels, signals=signals or ClientSignals(), challenge=claimed)
    files = {f"frame_{i}": (f"frame_{i}.jpg", data, "image/jpeg") for i, data in enumerate(frames)}
    data = {"meta": meta.model_dump_json(), "challenge_id": challenge["challenge_id"]}
    return await h.client.post(f"/v1/flow/sessions/{session}/face-attempts", data=data, files=files, headers=flow)


@pytest.mark.anyio
async def test_an_adult_passes_and_the_website_can_verify_the_signed_token(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        result = (await attempt(h, created["id"], flow, [PORTRAIT] * 6)).json()
        assert result["outcome"] == "pass"
        finished = (await h.client.post(f"/v1/flow/sessions/{created['id']}/finish", headers=flow)).json()
        assert finished["redirect_url"] == f"{RETURN_URL}?session_id={created['id']}"
        reloaded = (await h.client.post(f"/v1/flow/sessions/{created['id']}/start", json=secret(created))).json()
        auth = {"Authorization": f"Bearer {h.key}"}
        session = (await h.client.get(f"/v1/verification-sessions/{created['id']}", headers=auth)).json()
        jwks = (await h.client.get("/.well-known/jwks.json")).json()
    assert reloaded["session"]["status"] == "completed"
    assert reloaded["session"]["outcome"] == "pass"
    assert session["status"] == "completed"
    assert session["outcome"] == "pass"
    token = jwt.decode(session["age_token"], KeySet.import_key_set(jwks), algorithms=["Ed25519"])
    assert token.header["typ"] == "dwarpal-age+jwt"
    assert token.claims["outcome"] == "pass"
    assert token.claims["age_over_18"] is True
    assert token.claims["aud"] == h.project
    assert token.claims["sid"] == created["id"]
    assert token.claims["livemode"] is False
    assert not {"age", "mean", "estimated_age"} & set(token.claims)


@pytest.mark.anyio
async def test_a_clear_child_is_refused_and_the_token_says_so_unmistakably(databases: tuple[str, str]) -> None:
    async with harness(databases, stub_age=12.0) as h:
        created = (await create(h)).json()
        result = (await attempt(h, created["id"], await start(h, created), [PORTRAIT] * 6)).json()
        auth = {"Authorization": f"Bearer {h.key}"}
        session = (await h.client.get(f"/v1/verification-sessions/{created['id']}", headers=auth)).json()
        jwks = (await h.client.get("/.well-known/jwks.json")).json()
    token = jwt.decode(session["age_token"], KeySet.import_key_set(jwks), algorithms=["Ed25519"])
    assert result["outcome"] == "fail"
    assert session["outcome"] == "fail"
    assert token.claims["outcome"] == "fail"
    assert token.claims["age_over_18"] is False


@pytest.mark.anyio
async def test_a_teenager_near_the_limit_must_use_a_stronger_check(databases: tuple[str, str]) -> None:
    async with harness(databases, stub_age=16.0) as h:
        created = (await create(h)).json()
        result = (await attempt(h, created["id"], await start(h, created), [PORTRAIT] * 6)).json()
    assert result["outcome"] == "step_up"
    assert result["reasons"] == ["age_uncertain"]


@pytest.mark.anyio
async def test_poor_frames_get_a_retry_and_then_a_step_up(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        outcomes = [(await attempt(h, created["id"], flow, [blank_frame()] * 6)).json() for _ in range(3)]
        auth = {"Authorization": f"Bearer {h.key}"}
        session = (await h.client.get(f"/v1/verification-sessions/{created['id']}", headers=auth)).json()
        counts = (await h.client.get("/v1/analytics/sessions", headers=auth)).json()
    assert [o["outcome"] for o in outcomes] == ["retry", "retry", "step_up"]
    assert outcomes[0]["reasons"] == ["no_face"]
    assert outcomes[0]["attempts_remaining"] == 2
    assert session["status"] == "awaiting_step_up"
    assert session["age_token"] is None
    # Not finished, so not in the totals; but its face check has decided, once, after its retries.
    assert (counts["totals"], counts["face_stage"]["outcomes"]) == ({}, {"step_up": 1})


@pytest.mark.anyio
async def test_credentials_are_checked_and_errors_are_problem_details(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        no_key = await h.client.post("/v1/verification-sessions", json={})
        created = (await create(h)).json()
        wrong_secret = await h.client.post(
            f"/v1/flow/sessions/{created['id']}/start", json={"client_secret": "vs_wrong_secret_0123456789"}
        )
        no_flow = await h.client.post(f"/v1/flow/sessions/{created['id']}/challenge")
    assert no_key.status_code == 401
    assert no_key.headers["content-type"] == "application/problem+json"
    assert no_key.json()["code"] == "invalid_api_key"
    assert no_key.json()["type"] == "/errors/invalid_api_key"
    assert no_key.json()["request_id"] == no_key.headers["x-request-id"]
    assert wrong_secret.json()["code"] == "invalid_client_secret"
    assert no_flow.json()["code"] == "invalid_flow_token"


@pytest.mark.anyio
async def test_each_request_is_logged_once_with_its_id_and_never_with_secrets(
    databases: tuple[str, str], caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="dwarpal.api")
    async with harness(databases) as h:
        created = await create(h)
    lines = [vars(record) for record in caplog.records if record.getMessage() == "request"]
    assert len(lines) == 1
    assert (lines[0]["method"], lines[0]["path"], lines[0]["status"]) == ("POST", "/v1/verification-sessions", 201)
    assert lines[0]["request_id"] == created.headers["x-request-id"]
    assert h.key not in caplog.text
    assert created.json()["client_secret"] not in caplog.text


@pytest.mark.anyio
async def test_a_challenge_can_be_used_only_once(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        challenge = (await h.client.post(f"/v1/flow/sessions/{created['id']}/challenge", headers=flow)).json()
        meta = FaceRequestMeta(frames=[FrameMeta(index=0, t_ms=0.0)]).model_dump_json()
        data = {"meta": meta, "challenge_id": challenge["challenge_id"]}
        files = {"frame_0": ("frame_0.jpg", blank_frame(), "image/jpeg")}
        path = f"/v1/flow/sessions/{created['id']}/face-attempts"
        first = await h.client.post(path, data=data, files=files, headers=flow)
        second = await h.client.post(path, data=data, files=files, headers=flow)
    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["code"] == "challenge_invalid"


@pytest.mark.anyio
async def test_a_session_gets_a_limited_number_of_challenges(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        path = f"/v1/flow/sessions/{created['id']}/challenge"
        responses = [await h.client.post(path, headers=flow) for _ in range(7)]
    assert [r.status_code for r in responses] == [200] * 6 + [429]
    assert responses[-1].json()["code"] == "too_many_challenges"


@pytest.mark.anyio
async def test_oversized_and_unmeasured_bodies_are_refused_before_they_are_read(databases: tuple[str, str]) -> None:
    async def stream() -> AsyncIterator[bytes]:
        yield b"{}"

    async with harness(databases) as h:
        auth = {"Authorization": f"Bearer {h.key}"}
        huge = await h.client.post("/v1/verification-sessions", json={"external_ref": "x" * 100_000}, headers=auth)
        unmeasured = await h.client.post("/v1/verification-sessions", content=stream(), headers=auth)
    assert huge.status_code == 413
    assert huge.json()["code"] == "request_too_large"
    assert huge.json()["request_id"] == huge.headers["x-request-id"]
    assert unmeasured.status_code == 411
    assert unmeasured.json()["code"] == "length_required"


@pytest.mark.anyio
async def test_sessions_refuse_foreign_return_urls_unknown_policies_and_live_mode_with_a_stub(
    databases: tuple[str, str],
) -> None:
    async with harness(databases) as h:
        foreign = await create(h, return_url="https://evil.example/collect")
        unknown = await create(h, policy="anything_goes")
    async with harness(databases, livemode=True) as live:
        live_attempt = await create(live)
    assert foreign.json()["code"] == "return_url_not_allowed"
    assert unknown.json()["code"] == "unknown_policy"
    assert live_attempt.status_code == 409
    assert live_attempt.json()["code"] == "model_not_calibrated"


@pytest.mark.anyio
async def test_discovery_endpoints_and_readiness(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        configuration = (await h.client.get("/.well-known/dwarpal-configuration")).json()
        jwks = await h.client.get("/.well-known/jwks.json")
        ready = await h.client.get("/readyz")
    assert configuration["token_signing_algorithms"] == ["Ed25519"]
    assert configuration["age_model_calibrated"] is False
    assert jwks.headers["cache-control"] == "public, max-age=300"
    assert all(key["kty"] == "OKP" and key["crv"] == "Ed25519" for key in jwks.json()["keys"])
    assert ready.json() == {"database": "ok", "valkey": "ok"}


def test_the_migrations_build_exactly_the_tables_the_code_describes(databases: tuple[str, str]) -> None:
    def differences(connection: Connection) -> list[Any]:
        return list(compare_metadata(MigrationContext.configure(connection), METADATA))

    async def check() -> list[Any]:
        engine = create_async_engine(databases[0])
        async with engine.connect() as connection:
            found = await connection.run_sync(differences)
        await engine.dispose()
        return found

    assert asyncio.run(check()) == []


@pytest.mark.anyio
async def test_red_team_a_printed_photo_is_retried_then_rejected(databases: tuple[str, str]) -> None:
    async with harness(databases, liveness="images") as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        first = (await attempt(h, created["id"], flow, [PORTRAIT] * 6)).json()
        second = (await attempt(h, created["id"], flow, [PORTRAIT] * 6)).json()
    assert (first["outcome"], first["reasons"]) == ("retry", ["liveness_check_failed"])
    assert (second["outcome"], second["reasons"]) == ("reject", ["verification_failed"])


@pytest.mark.anyio
async def test_red_team_poses_in_the_wrong_order_fail(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        result = (await attempt(h, created["id"], flow, [PORTRAIT] * 6, poses=["turn_right"] * 3)).json()
    assert (result["outcome"], result["reasons"]) == ("retry", ["liveness_check_failed"])


@pytest.mark.anyio
async def test_red_team_a_challenge_claimed_by_the_browser_is_ignored(databases: tuple[str, str]) -> None:
    claimed = Challenge(poses=["turn_left"], colours=["#000000", "#ffffff"], step_ms=400)
    async with harness(databases) as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        result = (await attempt(h, created["id"], flow, [PORTRAIT] * 4, poses=["turn_left"], claimed=claimed)).json()
    assert (result["outcome"], result["reasons"]) == ("retry", ["liveness_check_failed"])


@pytest.mark.anyio
async def test_red_team_automation_and_virtual_cameras_go_to_step_up(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        outcomes = []
        for signals in (ClientSignals(automation=True), ClientSignals(virtual_camera=True)):
            created = (await create(h)).json()
            flow = await start(h, created)
            outcomes.append((await attempt(h, created["id"], flow, [PORTRAIT] * 6, signals=signals)).json())
    assert [(o["outcome"], o["reasons"]) for o in outcomes] == [("step_up", ["liveness_uncertain"])] * 2


@pytest.mark.anyio
async def test_one_device_gets_only_so_many_challenges_however_many_sessions_it_starts(
    databases: tuple[str, str],
) -> None:
    async def challenge(h: Harness, device: str) -> httpx.Response:
        created = (await create(h)).json()
        flow = await start(h, created) | {"X-Dwarpal-Device": device}
        return await h.client.post(f"/v1/flow/sessions/{created['id']}/challenge", headers=flow)

    async with harness(databases, device_challenges_per_hour=2) as h:
        same = [await challenge(h, "device-0123456789abcdef") for _ in range(3)]
        other = await challenge(h, "device-fedcba9876543210")
    assert [r.status_code for r in same] == [200, 200, 429]
    assert same[2].json()["code"] == "too_many_attempts"
    assert other.status_code == 200


TENANT_TABLES = (
    Organization,
    Project,
    ApiKey,
    PolicyVersion,
    VerificationSession,
    VerificationAttempt,
    IssuedToken,
    WebhookEndpoint,
    Event,
    WebhookDelivery,
    AuditHead,
    AuditEntry,
    SessionStat,
    User,
    Membership,
)
NOT_TENANT_DATA = {"alembic_version", "signing_keys"}


def a_session(project_id: uuid.UUID, now: datetime) -> VerificationSession:
    return VerificationSession(
        id=uuid.uuid4(),
        project_id=project_id,
        livemode=False,
        policy_id="uk_osa_18",
        policy_version=0,
        status="created",
        outcome=None,
        client_secret_digest=bytes(32),
        return_url=None,
        external_ref=None,
        attempts_count=0,
        model_version=None,
        created_at=now,
        expires_at=now,
        completed_at=None,
    )


async def two_organisations(database_url: str) -> dict[str, uuid.UUID]:
    """Made as the tables' owner: organisation A with projects a1 and a2, organisation B with project b1, and one
    verification session in each project."""
    now = datetime.now(UTC)
    made = {name: uuid.uuid4() for name in ("org_a", "org_b", "a1", "a2", "b1")}
    engine = make_engine(database_url)
    async with make_sessions(engine)() as session:
        for org in ("org_a", "org_b"):
            session.add(Organization(id=made[org], name=org, slug=f"{org}-{made[org].hex}", created_at=now))
        await session.flush()
        for project, org in (("a1", "org_a"), ("a2", "org_a"), ("b1", "org_b")):
            session.add(Project(id=made[project], org_id=made[org], name=project, allowed_origins=[], created_at=now))
        await session.flush()
        session.add_all([a_session(made[project], now) for project in ("a1", "a2", "b1")])
        await session.commit()
    await engine.dispose()
    return made


@pytest.mark.anyio
async def test_each_tenant_sees_only_its_own_rows_and_no_tenant_sees_nothing(databases: tuple[str, str]) -> None:
    made = await two_organisations(databases[0])
    engine = make_engine(databases[0], role="dwarpal_app")
    sessions = make_sessions(engine)
    try:
        async with sessions() as session:
            unnamed = [await session.scalar(select(func.count()).select_from(table)) for table in TENANT_TABLES]
            await session.rollback()
            role = await session.scalar(text("SELECT current_user"))
        async with tenant(sessions, project_id=made["a1"]) as session:
            project_sees = set(await session.scalars(select(VerificationSession.project_id)))
            project_org = set(await session.scalars(select(Organization.id)))
        async with tenant(sessions, org_id=made["org_a"]) as session:
            org_sees = set(await session.scalars(select(Project.id)))
    finally:
        await engine.dispose()
    assert role == "dwarpal_app"  # still the restricted role after a rollback
    assert unnamed == [0] * len(TENANT_TABLES)
    assert project_sees == {made["a1"]}
    assert project_org == {made["org_a"]}
    assert org_sees == {made["a1"], made["a2"]}


@pytest.mark.anyio
async def test_a_tenant_cannot_write_another_tenants_rows_or_switch_the_policies_off(
    databases: tuple[str, str],
) -> None:
    made = await two_organisations(databases[0])
    engine = make_engine(databases[0], role="dwarpal_app")
    sessions = make_sessions(engine)
    try:
        with pytest.raises(DBAPIError, match="row-level security"):
            async with tenant(sessions, project_id=made["a1"]) as session:
                session.add(a_session(made["b1"], datetime.now(UTC)))
                await session.commit()
        async with tenant(sessions, project_id=made["a1"]) as session:
            expire_b1 = update(VerificationSession).where(VerificationSession.project_id == made["b1"])
            changed = (
                await session.execute(expire_b1.values(status="expired").returning(VerificationSession.id))
            ).all()
            await session.commit()
            # The tenant was named for one transaction only: the next one, in the same unit of work, sees nothing.
            after_commit = await session.scalar(select(func.count()).select_from(VerificationSession))
        with pytest.raises(DBAPIError, match="must be owner"):
            async with sessions() as session:
                await session.execute(text("ALTER TABLE projects DISABLE ROW LEVEL SECURITY"))
    finally:
        await engine.dispose()
    assert changed == []
    assert after_commit == 0


@pytest.mark.anyio
async def test_one_websites_key_cannot_read_another_websites_session(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        created = (await create(h)).json()
        settings = Settings(environment="test", database_url=databases[0], valkey_url=databases[1])
        _, other_key = await seed_dev(settings)
        foreign = await h.client.get(
            f"/v1/verification-sessions/{created['id']}", headers={"Authorization": f"Bearer {other_key}"}
        )
        own = await h.client.get(
            f"/v1/verification-sessions/{created['id']}", headers={"Authorization": f"Bearer {h.key}"}
        )
    assert foreign.status_code == 404
    assert foreign.json()["code"] == "session_not_found"
    assert own.status_code == 200


def test_every_table_but_dwarpals_own_has_row_level_security(databases: tuple[str, str]) -> None:
    async def unprotected() -> set[str]:
        engine = create_async_engine(databases[0])
        async with engine.connect() as connection:
            query = "SELECT relname FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relkind = 'r'"
            found = set(await connection.scalars(text(f"{query} AND NOT relrowsecurity")))
        await engine.dispose()
        return found

    assert asyncio.run(unprotected()) == NOT_TENANT_DATA


def bearer_of(key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {key}"}


@pytest.mark.anyio
async def test_a_repeated_request_with_the_same_idempotency_key_gets_the_first_answer(
    databases: tuple[str, str],
) -> None:
    async with harness(databases) as h:
        first = await create(h, external_ref="order-1", headers_extra={"Idempotency-Key": "order-1-attempt"})
        again = await create(h, external_ref="order-1", headers_extra={"Idempotency-Key": "order-1-attempt"})
        changed = await create(h, external_ref="order-2", headers_extra={"Idempotency-Key": "order-1-attempt"})
        too_short = await create(h, headers_extra={"Idempotency-Key": "short"})
        plain = [(await create(h)).json()["id"] for _ in range(2)]
    valkey = Redis.from_url(databases[1])
    stored = [await valkey.get(slot) or b"" async for slot in valkey.scan_iter("idem:*")]
    await valkey.aclose()
    assert stored and not any(first.json()["client_secret"].encode() in value for value in stored)  # sealed
    assert (first.status_code, again.status_code) == (201, 201)
    assert again.json() == first.json()  # the same session, and the same client secret
    assert again.headers["idempotent-replayed"] == "true"
    assert "idempotent-replayed" not in first.headers
    assert (changed.status_code, changed.json()["code"]) == (422, "idempotency_key_reused")
    # The documented pattern refuses it before the API's own check: a general 422 naming the header.
    assert (too_short.status_code, too_short.json()["code"]) == (422, "invalid_request")
    assert "idempotency-key" in too_short.json()["detail"]
    assert plain[0] != plain[1]  # without a key, every request makes a new session


@pytest.mark.anyio
async def test_each_api_key_may_make_only_so_many_requests_at_once(databases: tuple[str, str]) -> None:
    async with harness(databases, api_requests_per_second=0.01, api_burst=2) as h:
        answers = [await h.client.get("/v1/verification-sessions", headers=bearer_of(h.key)) for _ in range(3)]
    assert [a.status_code for a in answers] == [200, 200, 429]
    assert answers[2].json()["code"] == "rate_limited"
    assert int(answers[2].headers["retry-after"]) >= 1


@pytest.mark.anyio
async def test_sessions_are_listed_newest_first_a_page_at_a_time_without_tokens(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        made = [(await create(h, external_ref=f"order-{i}")).json()["id"] for i in range(5)]
        pages, cursor = [], None
        while True:
            query = {"limit": 2} | ({"starting_after": cursor} if cursor else {})
            page = (await h.client.get("/v1/verification-sessions", params=query, headers=bearer_of(h.key))).json()
            pages.append(page)
            cursor = page["next_cursor"]
            if not page["has_more"]:
                break
        too_big = await h.client.get("/v1/verification-sessions?limit=101", headers=bearer_of(h.key))
    listed = [item["id"] for page in pages for item in page["data"]]
    assert [len(page["data"]) for page in pages] == [2, 2, 1]
    assert listed == list(reversed(made))  # newest first, nothing repeated, nothing missed
    assert all("age_token" not in item for page in pages for item in page["data"])
    assert too_big.status_code == 422


@pytest.mark.anyio
async def test_a_key_can_do_only_what_its_scopes_allow(databases: tuple[str, str]) -> None:
    async with harness(databases, scopes=["sessions:read"]) as h:
        refused = await create(h)
        listed = await h.client.get("/v1/verification-sessions", headers=bearer_of(h.key))
    assert (refused.status_code, refused.json()["code"]) == (403, "insufficient_scope")
    assert listed.status_code == 200


@pytest.mark.anyio
async def test_a_rotated_key_works_until_its_grace_ends_and_a_revoked_key_stops_at_once(
    databases: tuple[str, str],
) -> None:
    async with harness(databases) as h:
        settings = Settings(environment="test", database_url=databases[0], valkey_url=databases[1])
        lookup = h.key[8:20]
        during = await rotate_key(settings, lookup, timedelta(hours=1))
        both = [await h.client.get("/v1/verification-sessions", headers=bearer_of(k)) for k in (h.key, during)]
        after = await rotate_key(settings, during[8:20], timedelta(0))
        old = await h.client.get("/v1/verification-sessions", headers=bearer_of(during))
        new = await h.client.get("/v1/verification-sessions", headers=bearer_of(after))
        assert await revoke_key(settings, after[8:20])
        revoked = await h.client.get("/v1/verification-sessions", headers=bearer_of(after))
    assert [r.status_code for r in both] == [200, 200]
    assert (old.status_code, old.json()["code"]) == (401, "api_key_expired")
    assert new.status_code == 200
    assert (revoked.status_code, revoked.json()["code"]) == (401, "invalid_api_key")


@pytest.mark.anyio
async def test_a_policy_is_versioned_and_a_session_keeps_the_version_it_started_with(
    databases: tuple[str, str],
) -> None:
    async with harness(databases) as h:
        auth = bearer_of(h.key)
        v1 = await h.client.post("/v1/policies", json={"name": "shop_18", "min_age": 18}, headers=auth)
        before = (await create(h, policy="shop_18")).json()
        v2 = await h.client.post(
            "/v1/policies", json={"name": "shop_18", "min_age": 18, "max_face_attempts": 1}, headers=auth
        )
        after = (await create(h, policy="shop_18")).json()
        started = await h.client.post(f"/v1/flow/sessions/{before['id']}/start", json=secret(before))
        listed = (await h.client.get("/v1/policies", headers=auth)).json()
        preset_name = await h.client.post("/v1/policies", json={"name": "uk_osa_18", "min_age": 18}, headers=auth)
        uncalibrated = await h.client.post("/v1/policies", json={"name": "odd_19", "min_age": 19}, headers=auth)
        unknown = await create(h, policy="nobody_has_this")
    assert (v1.status_code, v1.json()["id"], v2.json()["id"]) == (201, "shop_18@1", "shop_18@2")
    assert (before["policy"], after["policy"]) == ("shop_18@1", "shop_18@2")
    assert started.json()["session"]["attempts_remaining"] == 3  # still version 1's rules, though version 2 exists
    assert [p["id"] for p in listed["data"] if not p["preset"]] == ["shop_18@1", "shop_18@2"]
    assert (preset_name.status_code, preset_name.json()["code"]) == (422, "invalid_policy_name")
    assert (uncalibrated.status_code, uncalibrated.json()["code"]) == (422, "policy_not_supported")
    assert (unknown.status_code, unknown.json()["code"]) == (422, "unknown_policy")


@pytest.mark.anyio
async def test_policy_versions_can_be_added_but_never_changed_or_deleted(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        await h.client.post("/v1/policies", json={"name": "fixed_18", "min_age": 18}, headers=bearer_of(h.key))
    engine = make_engine(databases[0], role="dwarpal_app")
    try:
        for statement in ("UPDATE policies SET min_age = 13", "DELETE FROM policies"):
            with pytest.raises(DBAPIError, match="permission denied"):
                async with make_sessions(engine)() as session:
                    await session.execute(text(statement))
    finally:
        await engine.dispose()


@dataclass
class Receiver:
    """A website's webhook receiver, in memory: it records each request and answers with the next status in line."""

    statuses: list[int]
    received: list[httpx.Request]

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.received.append(request)
        return httpx.Response(self.statuses.pop(0) if self.statuses else 200)


def deliverer(databases: tuple[str, str], receiver: Receiver, clock: list[datetime]) -> tuple[Deliverer, Any]:
    """The delivery worker as it runs in production — the tables' owner — sending to the in-memory receiver."""
    engine = make_engine(databases[0])
    http = httpx.AsyncClient(transport=httpx.MockTransport(receiver.handle))
    master = MasterKey(Settings().master_key.get_secret_value())
    return Deliverer(make_sessions(engine), master, http, lambda: clock[0], allow_private=True), engine


async def pass_one_session(h: Harness) -> dict[str, Any]:
    created = (await create(h)).json()
    flow = await start(h, created)
    assert (await attempt(h, created["id"], flow, [PORTRAIT] * 6)).json()["outcome"] == "pass"
    return dict(created)


@pytest.mark.anyio
async def test_a_completed_session_is_announced_to_the_website_with_a_signature_it_can_check(
    databases: tuple[str, str],
) -> None:
    receiver, clock = Receiver([], []), [datetime.now(UTC)]
    async with harness(databases, webhook_allow_private=True) as h:
        auth = bearer_of(h.key)
        hook = {"url": "https://shop.example/hooks", "events": ["verification_session.completed"]}
        endpoint = (await h.client.post("/v1/webhook-endpoints", json=hook, headers=auth)).json()
        created = await pass_one_session(h)
        clock[0] = datetime.now(UTC) + timedelta(seconds=1)  # the event is due by now
        worker, engine = deliverer(databases, receiver, clock)
        sent = await worker.deliver_due()
        await engine.dispose()
        deliveries = (await h.client.get(f"/v1/webhook-endpoints/{endpoint['id']}/deliveries", headers=auth)).json()
        listed = (await h.client.get("/v1/webhook-endpoints", headers=auth)).json()
    assert endpoint["secret"].startswith("whsec_")
    assert "secret" not in listed["data"][0]  # shown once, at creation
    assert sent == 1 and len(receiver.received) == 1
    request = receiver.received[0]
    body = json.loads(request.content)
    assert body["type"] == "verification_session.completed"
    assert body["data"]["id"] == created["id"] and body["data"]["outcome"] == "pass"
    assert "age_token" not in body["data"]
    assert request.headers["dwarpal-event-id"] == body["id"]
    # What a receiver does: recompute the HMAC of "<t>.<body>" with its secret, and compare.
    fields = dict(part.split("=", 1) for part in request.headers["dwarpal-signature"].split(","))
    expected = hmac.new(endpoint["secret"].encode(), f"{fields['t']}.".encode() + request.content, hashlib.sha256)
    assert hmac.compare_digest(fields["v1"], expected.hexdigest())
    assert [(d["status"], d["attempt"], d["last_status"]) for d in deliveries["data"]] == [("delivered", 1, 200)]


@pytest.mark.anyio
async def test_a_failing_receiver_is_retried_on_schedule_until_dead_and_can_be_replayed(
    databases: tuple[str, str],
) -> None:
    receiver, clock = Receiver([500] * 8, []), [datetime.now(UTC)]
    async with harness(databases, webhook_allow_private=True) as h:
        auth = bearer_of(h.key)
        hook = {"url": "https://shop.example/hooks", "events": ["verification_session.completed"]}
        endpoint = (await h.client.post("/v1/webhook-endpoints", json=hook, headers=auth)).json()
        test_event = await h.client.post(f"/v1/webhook-endpoints/{endpoint['id']}/test", headers=auth)
        clock[0] = datetime.now(UTC) + timedelta(seconds=1)
        worker, engine = deliverer(databases, receiver, clock)
        waits = []
        for _ in range(8):
            assert await worker.deliver_due() == 1
            assert await worker.deliver_due() == 0  # nothing more is due until the wait is over
            page = (await h.client.get(f"/v1/webhook-endpoints/{endpoint['id']}/deliveries", headers=auth)).json()
            delivery = page["data"][0]
            if delivery["next_attempt_at"]:
                due = datetime.fromisoformat(delivery["next_attempt_at"])
                waits.append(round((due - clock[0]).total_seconds()))
                clock[0] = due
        replayed = (await h.client.post(f"/v1/webhook-deliveries/{delivery['id']}/replay", headers=auth)).json()
        clock[0] = datetime.now(UTC) + timedelta(seconds=1)
        assert await worker.deliver_due() == 1  # the receiver answers 200 now
        await engine.dispose()
        final = (await h.client.get(f"/v1/webhook-endpoints/{endpoint['id']}/deliveries", headers=auth)).json()
    assert test_event.status_code == 202 and test_event.json()["type"] == "webhook_endpoint.test"
    assert waits == [60, 300, 1800, 7200, 21_600, 43_200, 86_400]
    assert (delivery["status"], delivery["attempt"], delivery["last_status"]) == ("dead", 8, 500)
    assert (replayed["status"], replayed["attempt"]) == ("pending", 0)
    assert final["data"][0]["status"] == "delivered"


@pytest.mark.anyio
async def test_webhook_endpoints_must_be_public_addresses_and_known_events(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        auth = bearer_of(h.key)
        inside = {"url": "http://127.0.0.1:8000/v1/flow", "events": ["verification_session.completed"]}
        refused = await h.client.post("/v1/webhook-endpoints", json=inside, headers=auth)
        unknown = await h.client.post(
            "/v1/webhook-endpoints", json={"url": "https://93.184.215.14/x", "events": ["everything"]}, headers=auth
        )
    assert (refused.status_code, refused.json()["code"]) == (422, "unsafe_webhook_url")
    assert (unknown.status_code, unknown.json()["code"]) == (422, "unknown_event_type")


@pytest.mark.anyio
async def test_a_token_can_be_introspected_once_and_only_by_its_own_website(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        created = await pass_one_session(h)
        result = await h.client.get(f"/v1/verification-sessions/{created['id']}", headers=bearer_of(h.key))
        token = result.json()["age_token"]
        settings = Settings(environment="test", database_url=databases[0], valkey_url=databases[1])
        _, other_key = await seed_dev(settings)

        async def ask(key: str, value: str) -> dict[str, Any]:
            response = await h.client.post("/v1/tokens/introspect", json={"token": value}, headers=bearer_of(key))
            return dict(response.json())

        foreign = await ask(other_key, token)
        forged = await ask(h.key, token[:-4] + ("BBBB" if token.endswith("AAAA") else "AAAA"))
        first = await ask(h.key, token)
        second = await ask(h.key, token)
    assert foreign == {"active": False}  # another website's token: not even a hint
    assert forged == {"active": False}
    assert first["active"] is True and first["sid"] == created["id"] and first["age_over_18"] is True
    assert second == {"active": False}  # one use only: a replayed token is caught


@pytest.mark.anyio
async def test_an_expired_session_is_announced_once(databases: tuple[str, str]) -> None:
    async with harness(databases, webhook_allow_private=True, session_ttl_s=0) as h:
        auth = bearer_of(h.key)
        hook = {"url": "https://shop.example/hooks", "events": ["verification_session.expired"]}
        endpoint = (await h.client.post("/v1/webhook-endpoints", json=hook, headers=auth)).json()
        created = (await create(h)).json()
        reads = [await h.client.get(f"/v1/verification-sessions/{created['id']}", headers=auth) for _ in range(2)]
        deliveries = (await h.client.get(f"/v1/webhook-endpoints/{endpoint['id']}/deliveries", headers=auth)).json()
    assert [r.json()["status"] for r in reads] == ["expired", "expired"]
    assert len(deliveries["data"]) == 1  # the first read saved the expiry and its event; the second changed nothing


async def org_of(databases: tuple[str, str], project_text: str) -> uuid.UUID:
    """The organisation that owns a seeded project, read as the tables' owner."""
    engine = make_engine(databases[0])
    async with make_sessions(engine)() as session:
        project = await session.get(Project, ids.decode("prj", project_text))
    await engine.dispose()
    assert project is not None
    return project.org_id


@pytest.mark.anyio
async def test_changes_are_chained_in_the_audit_log_and_any_tampering_is_found(databases: tuple[str, str]) -> None:
    async with harness(databases, webhook_allow_private=True) as h:
        auth = bearer_of(h.key)
        await h.client.post("/v1/policies", json={"name": "audited_18", "min_age": 18}, headers=auth)
        hook = {"url": "https://shop.example/hooks", "events": ["verification_session.completed"]}
        endpoint = (await h.client.post("/v1/webhook-endpoints", json=hook, headers=auth)).json()
        await h.client.delete(f"/v1/webhook-endpoints/{endpoint['id']}", headers=auth)
    org_id = await org_of(databases, h.project)
    engine = make_engine(databases[0])
    sessions = make_sessions(engine)
    app_engine = make_engine(databases[0], role="dwarpal_app")
    try:
        async with sessions() as session:
            entries = list(await session.scalars(select(AuditEntry).where(AuditEntry.org_id == org_id)))
            before = await audit.verify(session, org_id)
        with pytest.raises(DBAPIError, match="permission denied"):  # the API itself can't rewrite history
            async with make_sessions(app_engine)() as session:
                await session.execute(text("UPDATE audit_log SET action = 'nothing.happened'"))
        async with sessions() as session:  # someone with the owner's rights edits entry 2...
            entry_2 = AuditEntry.org_id == org_id, AuditEntry.seq == 2
            await session.execute(update(AuditEntry).where(*entry_2).values(data={"min_age": 13}))
            await session.commit()
            edited = await audit.verify(session, org_id)
            await session.execute(update(AuditEntry).where(*entry_2).values(data=entries[1].data))
            last = AuditEntry.org_id == org_id, AuditEntry.seq == len(entries)
            await session.execute(delete(AuditEntry).where(*last))  # ...or quietly removes the last one
            await session.commit()
            shortened = await audit.verify(session, org_id)
    finally:
        await engine.dispose()
        await app_engine.dispose()
    assert [e.action for e in sorted(entries, key=lambda e: e.seq)] == [
        "api_key.created",
        "policy.version_added",
        "webhook_endpoint.created",
        "webhook_endpoint.deleted",
    ]
    assert {e.actor_id for e in entries if e.actor_type == "api_key"} == {h.key[8:20]}  # the key's id, not the key
    assert not any(h.key in json.dumps(e.data) for e in entries)
    assert (before.entries, before.intact) == (4, True)
    assert (edited.intact, edited.first_broken) == (False, 2)
    assert (shortened.intact, shortened.first_broken) == (False, 4)


@pytest.mark.anyio
async def test_finished_sessions_are_counted_by_day_and_outcome(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        for _ in range(2):
            await pass_one_session(h)
        counts = (await h.client.get("/v1/analytics/sessions?days=7", headers=bearer_of(h.key))).json()
        too_long = await h.client.get("/v1/analytics/sessions?days=366", headers=bearer_of(h.key))
    assert counts["totals"] == {"pass": 2}
    assert [(d["policy"], d["outcome"], d["sessions"]) for d in counts["data"]] == [("uk_osa_18", "pass", 2)]
    assert counts["face_stage"] == {"decided": 2, "outcomes": {"pass": 2}, "median_seconds": {"from": 0, "to": 5}}
    assert too_long.status_code == 422


@pytest.mark.anyio
async def test_abandoned_sessions_are_announced_and_old_metadata_is_purged_but_counts_stay(
    databases: tuple[str, str],
) -> None:
    settings = Settings(environment="test", database_url=databases[0], valkey_url=databases[1])
    async with harness(databases, webhook_allow_private=True, session_ttl_s=0) as h:
        auth = bearer_of(h.key)
        hook = {"url": "https://shop.example/hooks", "events": ["verification_session.expired"]}
        endpoint = (await h.client.post("/v1/webhook-endpoints", json=hook, headers=auth)).json()
        created = (await create(h)).json()  # abandoned: nobody ever reads it
        swept = await maintain(settings)
        deliveries = (await h.client.get(f"/v1/webhook-endpoints/{endpoint['id']}/deliveries", headers=auth)).json()
        engine = make_engine(databases[0])
        async with make_sessions(engine)() as session:
            project_id = ids.decode("prj", h.project)
            await session.execute(update(Project).where(Project.id == project_id).values(retention_days=1))
            await session.commit()
        await engine.dispose()
        kept = await maintain(settings, now=datetime.now(UTC) + timedelta(hours=23))
        still_there = await h.client.get(f"/v1/verification-sessions/{created['id']}", headers=auth)
        purged = await maintain(settings, now=datetime.now(UTC) + timedelta(days=2))
        gone = await h.client.get(f"/v1/verification-sessions/{created['id']}", headers=auth)
        counts = (await h.client.get("/v1/analytics/sessions", headers=auth)).json()
        owner = make_engine(databases[0])
        reports = await maintenance.verify_all_chains(make_sessions(owner))
        await owner.dispose()
    assert swept.startswith("expired ") and not swept.startswith("expired 0 ")
    assert len(deliveries["data"]) == 1  # the website heard about it without anyone reading the session
    assert "purged 0 sessions" in kept and still_there.status_code == 200
    assert "purged 0 sessions" not in purged
    assert gone.status_code == 404
    assert counts["totals"] == {"expired": 1}  # the count outlives the session
    assert reports[await org_of(databases, h.project)].intact


CONSOLE = "/console/v1"
CONSOLE_SETTINGS: dict[str, Any] = {"console_cookie_secure": False, "login_burst": 100}
PASSWORD = "a long and unguessable test passphrase"  # noqa: S105 - a throwaway password for a throwaway account


def person(h: Harness) -> httpx.AsyncClient:
    """A separate browser for one person: its own cookie jar, talking to the same API."""
    return httpx.AsyncClient(transport=h.transport, base_url="http://api")


async def sign_up(browser: httpx.AsyncClient, email: str, organisation: str = "Shop Ltd") -> dict[str, Any]:
    body = {"email": email, "password": PASSWORD, "organisation": organisation}
    response = await browser.post(f"{CONSOLE}/signup", json=body)
    assert response.status_code == 201, response.text
    return dict(response.json())


def unique(name: str) -> str:
    return f"{name}-{uuid.uuid4().hex[:8]}@shop.example"


@pytest.mark.anyio
async def test_a_person_signs_up_signs_in_and_out_and_wrong_details_all_look_the_same(
    databases: tuple[str, str],
) -> None:
    email = unique("ana")
    async with harness(databases, **CONSOLE_SETTINGS) as h, person(h) as browser:
        created = await sign_up(browser, email)
        cookie = browser.cookies.get("dwarpal_session")
        again = await browser.post(
            f"{CONSOLE}/signup", json={"email": email, "password": PASSWORD, "organisation": "X"}
        )
        weak = await browser.post(
            f"{CONSOLE}/signup", json={"email": unique("b"), "password": "short", "organisation": "X"}
        )
        wrong = await browser.post(f"{CONSOLE}/login", json={"email": email, "password": PASSWORD + "!"})
        nobody = await browser.post(f"{CONSOLE}/login", json={"email": unique("nobody"), "password": PASSWORD})
        signed_in = await browser.post(f"{CONSOLE}/login", json={"email": email.upper(), "password": PASSWORD})
        csrf = {"X-CSRF-Token": signed_in.json()["csrf_token"]}
        no_token = await browser.post(f"{CONSOLE}/logout")
        out = await browser.post(f"{CONSOLE}/logout", headers=csrf)
        after = await browser.get(f"{CONSOLE}/me")
    assert created["email"] == email and created["organisations"][0]["role"] == "owner"
    assert cookie and len(cookie) >= 40  # an opaque, unguessable token
    assert (again.status_code, again.json()["code"]) == (409, "email_taken")
    assert (weak.status_code, weak.json()["code"]) == (422, "weak_password")
    assert wrong.status_code == nobody.status_code == 401  # an unknown account and a wrong password...
    assert wrong.json()["detail"] == nobody.json()["detail"]  # ...can't be told apart
    assert signed_in.status_code == 200  # the address is matched whatever its capitals
    assert (no_token.status_code, no_token.json()["code"]) == (403, "csrf_failed")
    assert out.status_code == 204
    assert (after.status_code, after.json()["code"]) == (401, "not_signed_in")


@pytest.mark.anyio
async def test_changes_need_the_csrf_token_and_the_consoles_own_origin(databases: tuple[str, str]) -> None:
    async with harness(databases, **CONSOLE_SETTINGS) as h, person(h) as browser:
        me = await sign_up(browser, unique("csrf"))
        token = {"X-CSRF-Token": me["csrf_token"]}
        forged = await browser.post(f"{CONSOLE}/totp", headers={"X-CSRF-Token": "guessed"})
        elsewhere = await browser.post(f"{CONSOLE}/totp", headers=token | {"Origin": "https://evil.example"})
        genuine = await browser.post(f"{CONSOLE}/totp", headers=token | {"Origin": "http://localhost:3000"})
    assert (forged.status_code, forged.json()["code"]) == (403, "csrf_failed")
    assert (elsewhere.status_code, elsewhere.json()["code"]) == (403, "bad_origin")
    assert genuine.status_code == 200


@pytest.mark.anyio
async def test_one_time_codes_once_switched_on_are_required_and_single_use(databases: tuple[str, str]) -> None:
    email = unique("totp")
    async with harness(databases, **CONSOLE_SETTINGS) as h, person(h) as browser:
        token = {"X-CSRF-Token": (await sign_up(browser, email))["csrf_token"]}
        offer = (await browser.post(f"{CONSOLE}/totp", headers=token)).json()
        now_step = int(datetime.now(UTC).timestamp() // totp.STEP_S)
        wrong = await browser.post(f"{CONSOLE}/totp/confirm", json={"code": "000000"}, headers=token)
        confirmed = await browser.post(
            f"{CONSOLE}/totp/confirm", json={"code": totp.code_at(offer["secret"], now_step)}, headers=token
        )
        login = {"email": email, "password": PASSWORD}
        without = await browser.post(f"{CONSOLE}/login", json=login)
        code = totp.code_at(offer["secret"], now_step + 1)  # the next code, as a phone a moment ahead shows it
        first = await browser.post(f"{CONSOLE}/login", json=login | {"code": code})
        replayed = await browser.post(f"{CONSOLE}/login", json=login | {"code": code})
    assert offer["uri"].startswith("otpauth://totp/")
    assert wrong.status_code == 422 and confirmed.status_code == 200
    assert len(confirmed.json()["recovery_codes"]) == totp.RECOVERY_CODES  # shown once, now
    assert (without.status_code, without.json()["code"]) == (401, "totp_required")
    assert first.status_code == 200 and first.json()["totp_enabled"] is True
    assert (replayed.status_code, replayed.json()["code"]) == (401, "invalid_totp")


@pytest.mark.anyio
async def test_roles_decide_what_each_member_may_do_and_outsiders_see_nothing(databases: tuple[str, str]) -> None:
    owner_email, analyst_email, developer_email = unique("owner"), unique("analyst"), unique("dev")
    async with (
        harness(databases, **CONSOLE_SETTINGS) as h,
        person(h) as owner,
        person(h) as analyst,
        person(h) as developer,
        person(h) as outsider,
    ):
        me = await sign_up(owner, owner_email)
        org = me["organisations"][0]["id"]
        token = {"X-CSRF-Token": me["csrf_token"]}
        tokens = {}
        for browser, email in ((analyst, analyst_email), (developer, developer_email)):
            tokens[email] = {"X-CSRF-Token": (await sign_up(browser, email, "Their own Ltd"))["csrf_token"]}
        await sign_up(outsider, unique("outsider"), "Elsewhere Ltd")
        for email, role in ((analyst_email, "analyst"), (developer_email, "developer")):
            added = await owner.post(
                f"{CONSOLE}/orgs/{org}/members", json={"email": email, "role": role}, headers=token
            )
            assert added.status_code == 201, added.text
        projects = (await analyst.get(f"{CONSOLE}/orgs/{org}/projects")).json()["data"]
        assert [p["name"] for p in projects] == ["Default project"]  # any member may list them
        keys = f"{CONSOLE}/orgs/{org}/projects/{projects[0]['id']}/keys"
        wanted = {"scopes": ["sessions:read"]}
        by_analyst = await analyst.post(keys, json=wanted, headers=tokens[analyst_email])
        by_developer = await developer.post(keys, json=wanted, headers=tokens[developer_email])
        promoted = await developer.post(
            f"{CONSOLE}/orgs/{org}/members",
            json={"email": analyst_email, "role": "owner"},
            headers=tokens[developer_email],
        )
        members = await analyst.get(f"{CONSOLE}/orgs/{org}/members")
        outside = await outsider.get(f"{CONSOLE}/orgs/{org}/members")
        works = await h.client.get("/v1/verification-sessions", headers=bearer_of(by_developer.json()["key"]))
        log = await owner.get(f"{CONSOLE}/orgs/{org}/audit")
        log_for_analyst = await analyst.get(f"{CONSOLE}/orgs/{org}/audit")
    assert (by_analyst.status_code, by_analyst.json()["code"]) == (403, "forbidden_for_role")
    assert by_developer.status_code == 201 and by_developer.json()["key"].startswith("dk_test_")
    assert promoted.status_code == 403  # a developer can't manage members, let alone make owners
    assert sorted(m["role"] for m in members.json()["data"]) == ["analyst", "developer", "owner"]
    assert (outside.status_code, outside.json()["code"]) == (404, "organisation_not_found")
    assert works.status_code == 200  # the key made in the console works on the API
    actions = [entry["action"] for entry in reversed(log.json()["data"])]
    assert actions == ["organisation.created", "member.added", "member.added", "api_key.created"]
    assert log.json()["chain"]["intact"] is True
    assert by_developer.json()["key"] not in log.text  # the audit log names keys by id, never the key itself
    assert log_for_analyst.status_code == 403


@pytest.mark.anyio
async def test_sign_in_attempts_are_limited(databases: tuple[str, str]) -> None:
    async with harness(databases, console_cookie_secure=False, login_burst=2, login_per_minute=0.5) as h:
        # A browser at an address of its own, so that no other test's sign-ins count against it.
        transport = httpx.ASGITransport(app=h.transport.app, client=(f"192.0.2.{uuid.uuid4().int % 250}", 4000))
        async with httpx.AsyncClient(transport=transport, base_url="http://api") as browser:
            email = unique("limited")
            await sign_up(browser, email)
            tries = [
                await browser.post(f"{CONSOLE}/login", json={"email": email, "password": "wrong password!"})
                for _ in range(3)
            ]
    assert [t.status_code for t in tries] == [401, 401, 429]
    assert tries[2].json()["code"] == "too_many_sign_ins" and int(tries[2].headers["retry-after"]) >= 1


@pytest.fixture(scope="module")
def live_api(databases: tuple[str, str]) -> Iterator[tuple[str, str]]:
    """The API as a real server on a free local port, in a thread, with a website's key: Schemathesis speaks HTTP."""
    config = Settings(
        environment="test",
        database_url=databases[0],
        valkey_url=databases[1],
        webhook_allow_private=True,  # fuzzed webhook addresses are never looked up on the internet
        console_cookie_secure=False,
        api_burst=1_000_000,  # the fuzzer's thousands of requests shouldn't all end in 429
        login_burst=1_000_000,
    )
    _, key = asyncio.run(seed_dev(config))
    server = uvicorn.Server(uvicorn.Config(create_api(config), host="127.0.0.1", port=0, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)
    port = server.servers[0].sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}", key
    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="module")
def live_document(live_api: tuple[str, str]) -> schemathesis.schemas.BaseSchema:
    return schemathesis.openapi.from_url(f"{live_api[0]}/openapi.json")


contract = schemathesis.pytest.from_fixture("live_document")


@contract.parametrize()
@settings(max_examples=25, deadline=None, suppress_health_check=list(HealthCheck))
def test_every_operation_keeps_the_published_contract(case: Case[Any], live_api: tuple[str, str]) -> None:
    base_url, key = live_api
    # Every check but one: a request the document allows may still break a rule that depends on data (an age the
    # model isn't calibrated for, an address outside the project's origins), and refusing it with 422 is correct.
    excluded = [positive_data_acceptance]
    case.call_and_validate(base_url=base_url, headers={"Authorization": f"Bearer {key}"}, excluded_checks=excluded)


def test_the_published_api_document_matches_the_code() -> None:
    """docs/api/openapi.json is what websites read; it must never drift from the API. To refresh it, run
    `uv run --package dwarpal-api python -m dwarpal_api.cli openapi`."""
    assert API_DOCUMENT.read_text(encoding="utf-8") == api_document()


@pytest.mark.anyio
async def test_when_valkey_is_unreachable_the_api_says_try_again_and_nothing_passes(databases: tuple[str, str]) -> None:
    """Fail closed: with Valkey gone (here, an address where nothing listens), requests get 503 and Retry-After."""
    settings = Settings(environment="test", database_url=databases[0], valkey_url="redis://127.0.0.1:1/0")
    _, key = await seed_dev(settings)
    api = create_api(settings, inference_http=httpx.AsyncClient(base_url="http://inference"))
    async with api.router.lifespan_context(api):
        transport = httpx.ASGITransport(app=api)
        async with httpx.AsyncClient(transport=transport, base_url="http://api") as client:
            created = await client.post("/v1/verification-sessions", json={}, headers=bearer_of(key))
            ready = await client.get("/readyz")
    assert (created.status_code, created.json()["code"]) == (503, "service_unavailable")
    assert created.headers["retry-after"] == "5"
    assert (ready.status_code, ready.json()) == (503, {"database": "ok", "valkey": "unavailable"})


def unreachable(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("the inference service is down", request=request)


def broken(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content=b'{"not": "an analysis"}')


@pytest.mark.anyio
@pytest.mark.parametrize("inference", [unreachable, broken])
async def test_when_inference_fails_an_attempt_is_retried_never_passed(
    databases: tuple[str, str], inference: Any
) -> None:
    """Fail closed: an inference service that is down, or answers nonsense, can never let anyone through."""
    settings = Settings(environment="test", database_url=databases[0], valkey_url=databases[1])
    _, key = await seed_dev(settings)
    http = httpx.AsyncClient(transport=httpx.MockTransport(inference), base_url="http://inference")
    api = create_api(settings, inference_http=http)
    async with api.router.lifespan_context(api):
        transport = httpx.ASGITransport(app=api)
        h = Harness(httpx.AsyncClient(transport=transport, base_url="http://api"), key, "", transport)
        async with h.client:
            created = (await create(h)).json()
            flow = await start(h, created)
            results = [(await attempt(h, created["id"], flow, [PORTRAIT] * 6)).json() for _ in range(2)]
    assert all(result["outcome"] != "pass" for result in results)
    assert results[0]["outcome"] == "retry"


# --- Chaos: services that die in the middle of a check (Phase 7, "kill inference/Valkey mid-flow") ---


class Cutter:
    """A TCP passage in front of a real service (PostgreSQL, Valkey) that a test can cut, as if the service had died:
    every open connection is dropped at once, and new ones are hung up on. Restoring it lets connections through
    again — the service is back, with its data, as after a restart."""

    def __init__(self, host: str, port: int) -> None:
        self.target = (host, port)
        self.down = False
        self.open: set[asyncio.StreamWriter] = set()
        self.server: asyncio.Server | None = None

    async def __aenter__(self) -> Cutter:
        self.server = await asyncio.start_server(self.relay, "127.0.0.1", 0)
        return self

    async def __aexit__(self, *_: object) -> None:
        self.cut()
        if self.server is not None:
            self.server.close()

    @property
    def port(self) -> int:
        assert self.server is not None
        return int(self.server.sockets[0].getsockname()[1])

    async def relay(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        if self.down:
            writer.transport.abort()
            return
        upstream_reader, upstream_writer = await asyncio.open_connection(*self.target)
        pair = {writer, upstream_writer}
        self.open |= pair
        await asyncio.gather(pipe(reader, upstream_writer), pipe(upstream_reader, writer))
        self.open -= pair

    def cut(self) -> None:
        self.down = True
        for writer in list(self.open):
            writer.transport.abort()

    def restore(self) -> None:
        self.down = False


async def pipe(source: asyncio.StreamReader, sink: asyncio.StreamWriter) -> None:
    """Copy one direction of a connection until it ends; then drop the other side too, so neither is left hanging."""
    with contextlib.suppress(ConnectionError, OSError):
        while data := await source.read(65536):
            sink.write(data)
            await sink.drain()
    sink.transport.abort()


@asynccontextmanager
async def chaos(databases: tuple[str, str]) -> AsyncIterator[tuple[tuple[str, str], Cutter, Cutter]]:
    """The test databases reached through cutters: their new addresses, and the cutters for PostgreSQL and Valkey."""
    postgres_url, valkey_url = make_url(databases[0]), urlsplit(databases[1])
    assert postgres_url.host is not None and postgres_url.port is not None
    assert valkey_url.hostname is not None and valkey_url.port is not None
    async with (
        Cutter(postgres_url.host, postgres_url.port) as postgres,
        Cutter(valkey_url.hostname, valkey_url.port) as valkey,
    ):
        routed = postgres_url.set(host="127.0.0.1", port=postgres.port).render_as_string(hide_password=False)
        yield (routed, f"redis://127.0.0.1:{valkey.port}/0"), postgres, valkey


class Switch(httpx.AsyncBaseTransport):
    """In front of the inference service: while `down`, every call fails as if it had died; `on_call` runs first."""

    def __init__(self) -> None:
        self.inner: httpx.AsyncBaseTransport | None = None
        self.down = False
        self.on_call: Callable[[], None] = lambda: None

    def around(self, inner: httpx.AsyncBaseTransport) -> httpx.AsyncBaseTransport:
        self.inner = inner
        return self

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.on_call()
        if self.down or self.inner is None:
            raise httpx.ConnectError("the inference service is down", request=request)
        return await self.inner.handle_async_request(request)


def unavailable(response: httpx.Response) -> tuple[int, str, str]:
    return response.status_code, response.json()["code"], response.headers.get("retry-after", "")


async def outcome_of(h: Harness, session: str) -> tuple[str, str | None]:
    found = (await h.client.get(f"/v1/verification-sessions/{session}", headers=bearer_of(h.key))).json()
    return found["status"], found["outcome"]


@pytest.mark.anyio
async def test_chaos_valkey_dies_mid_check_nothing_passes_and_the_check_recovers(databases: tuple[str, str]) -> None:
    async with chaos(databases) as (routed, _, valkey), harness(routed) as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        challenge = (await h.client.post(f"/v1/flow/sessions/{created['id']}/challenge", headers=flow)).json()
        valkey.cut()
        down = await attempt(h, created["id"], flow, [PORTRAIT] * 6, challenge=challenge)
        ready = await h.client.get("/readyz")
        valkey.restore()
        result = (await attempt(h, created["id"], flow, [PORTRAIT] * 6)).json()
        final = await outcome_of(h, created["id"])
    assert unavailable(down) == (503, "service_unavailable", "5")
    assert ready.json() == {"database": "ok", "valkey": "unavailable"}
    assert (result["outcome"], final) == ("pass", ("completed", "pass"))


@pytest.mark.anyio
async def test_chaos_the_database_dies_between_steps_nothing_passes_and_the_check_recovers(
    databases: tuple[str, str],
) -> None:
    async with chaos(databases) as (routed, postgres, _), harness(routed) as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        challenge = (await h.client.post(f"/v1/flow/sessions/{created['id']}/challenge", headers=flow)).json()
        postgres.cut()
        down = await attempt(h, created["id"], flow, [PORTRAIT] * 6, challenge=challenge)
        ready = await h.client.get("/readyz")
        postgres.restore()
        result = (await attempt(h, created["id"], flow, [PORTRAIT] * 6)).json()
        final = await outcome_of(h, created["id"])
    assert unavailable(down) == (503, "service_unavailable", "5")
    assert ready.json() == {"database": "unavailable", "valkey": "ok"}
    assert (result["outcome"], final) == ("pass", ("completed", "pass"))


@pytest.mark.anyio
async def test_chaos_the_database_dies_while_a_face_is_analysed_nothing_is_recorded_or_passed(
    databases: tuple[str, str],
) -> None:
    switch = Switch()
    async with chaos(databases) as (routed, postgres, _), harness(routed, inference_via=switch.around) as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        switch.on_call = postgres.cut  # the database dies after the attempt is accepted, before it is decided
        down = await attempt(h, created["id"], flow, [PORTRAIT] * 6)
        switch.on_call = lambda: None
        postgres.restore()
        between = await outcome_of(h, created["id"])
        result = (await attempt(h, created["id"], flow, [PORTRAIT] * 6)).json()
        final = await outcome_of(h, created["id"])
    assert unavailable(down) == (503, "service_unavailable", "5")
    assert between == ("in_progress", None)
    assert (result["outcome"], final) == ("pass", ("completed", "pass"))


@pytest.mark.anyio
async def test_chaos_inference_dies_and_comes_back_a_retry_then_a_pass(databases: tuple[str, str]) -> None:
    switch = Switch()
    async with harness(databases, inference_via=switch.around) as h:
        created = (await create(h)).json()
        flow = await start(h, created)
        switch.down = True
        during = (await attempt(h, created["id"], flow, [PORTRAIT] * 6)).json()
        switch.down = False
        after = (await attempt(h, created["id"], flow, [PORTRAIT] * 6)).json()
        final = await outcome_of(h, created["id"])
    assert (during["outcome"], during["attempts_remaining"]) == ("retry", 2)
    assert (after["outcome"], final) == ("pass", ("completed", "pass"))


@pytest.mark.anyio
async def test_every_answer_carries_the_security_headers(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        refused = await h.client.get("/v1/verification-sessions")  # no key: a refusal gets them too
        jwks = await h.client.get("/.well-known/jwks.json")
        docs = await h.client.get("/docs")
    for response in (refused, jwks):
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["cross-origin-resource-policy"] == "same-origin"
        assert "strict-transport-security" not in response.headers  # only in production, behind HTTPS
    assert refused.headers["cache-control"] == "no-store"
    assert jwks.headers["cache-control"] == "public, max-age=300"  # a route that may be cached keeps its own rule
    assert docs.status_code == 200 and "content-security-policy" not in docs.headers


@pytest.mark.anyio
async def test_production_has_hsts_and_no_interactive_documentation() -> None:
    settings = Settings(
        environment="production",
        master_key=SecretStr(base64.b64encode(bytes(range(32))).decode()),
        issuer="https://api.dwarpal.example",
        verify_url="https://verify.dwarpal.example",
    )
    api = create_api(settings)  # not started: /livez needs no database, which is all this test asks
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api), base_url="https://api") as client:
        alive = await client.get("/livez")
        docs = await client.get("/docs")
        document = await client.get("/openapi.json")
    assert alive.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"
    assert docs.status_code == 404 and document.status_code == 200


@pytest.mark.anyio
async def test_the_console_shows_a_projects_sessions_with_their_decision_trace(databases: tuple[str, str]) -> None:
    async with (
        harness(databases, **CONSOLE_SETTINGS) as h,
        person(h) as owner,
        person(h) as analyst,
    ):
        me = await sign_up(owner, unique("trace-owner"))
        org, token = me["organisations"][0]["id"], {"X-CSRF-Token": me["csrf_token"]}
        analyst_email = unique("trace-analyst")
        analyst_token = {"X-CSRF-Token": (await sign_up(analyst, analyst_email, "Theirs"))["csrf_token"]}
        added = {"email": analyst_email, "role": "analyst"}
        await owner.post(f"{CONSOLE}/orgs/{org}/members", json=added, headers=token)
        project = (await owner.get(f"{CONSOLE}/orgs/{org}/projects")).json()["data"][0]["id"]
        base = f"{CONSOLE}/orgs/{org}/projects/{project}"
        wanted = {"scopes": ["sessions:read", "sessions:write"]}
        key = (await owner.post(f"{base}/keys", json=wanted, headers=token)).json()["key"]
        website = replace(h, key=key)  # a website using the key made in the console
        passed = (await create(website, return_url=None)).json()  # this project allows no return address yet
        flow = await start(website, passed)
        assert (await attempt(website, passed["id"], flow, [PORTRAIT] * 6)).json()["outcome"] == "pass"

        sessions = (await analyst.get(f"{base}/sessions")).json()
        trace = (await analyst.get(f"{base}/sessions/{passed['id']}")).json()
        counts = (await analyst.get(f"{base}/analytics?days=7")).json()
        policy = {"name": "console_18", "min_age": 18}
        by_analyst = await analyst.post(f"{base}/policies", json=policy, headers=analyst_token)
        by_owner = await owner.post(f"{base}/policies", json=policy, headers=token)
        listed = (await analyst.get(f"{base}/policies")).json()
        elsewhere = await analyst.get(f"{CONSOLE}/orgs/{org}/projects/{h.project}/sessions")
    assert [s["id"] for s in sessions["data"]] == [passed["id"]]
    assert trace["outcome"] == "pass" and len(trace["attempts"]) == 1
    traced = trace["attempts"][0]
    assert traced["outcome"] == "pass" and {"p_over", "tau", "liveness"} <= set(traced["scores"])
    assert "age_token" not in trace  # reading a trace never mints a token
    assert counts["totals"] == {"pass": 1}
    assert (by_analyst.status_code, by_analyst.json()["code"]) == (403, "forbidden_for_role")
    assert by_owner.status_code == 201 and by_owner.json()["id"] == "console_18@1"
    assert [p["id"] for p in listed["data"] if not p["preset"]] == ["console_18@1"]
    assert (elsewhere.status_code, elsewhere.json()["code"]) == (404, "project_not_found")  # another org's project


@pytest.mark.anyio
async def test_the_console_manages_a_projects_webhooks(databases: tuple[str, str]) -> None:
    settings = {**CONSOLE_SETTINGS, "webhook_allow_private": True}
    async with harness(databases, **settings) as h, person(h) as owner, person(h) as analyst:
        me = await sign_up(owner, unique("hooks-owner"))
        org, token = me["organisations"][0]["id"], {"X-CSRF-Token": me["csrf_token"]}
        analyst_email = unique("hooks-analyst")
        analyst_token = {"X-CSRF-Token": (await sign_up(analyst, analyst_email, "Theirs"))["csrf_token"]}
        added = {"email": analyst_email, "role": "analyst"}
        await owner.post(f"{CONSOLE}/orgs/{org}/members", json=added, headers=token)
        project = (await owner.get(f"{CONSOLE}/orgs/{org}/projects")).json()["data"][0]["id"]
        hooks = f"{CONSOLE}/orgs/{org}/projects/{project}/webhooks"
        hook = {"url": "http://localhost:9/hooks", "events": ["verification_session.completed"]}

        by_analyst = await analyst.post(hooks, json=hook, headers=analyst_token)
        created = (await owner.post(hooks, json=hook, headers=token)).json()
        seen_by_analyst = await analyst.get(hooks)
        live = (await owner.get(f"{hooks}?livemode=true")).json()
        sent = await owner.post(f"{hooks}/{created['id']}/test", headers=token)
        deliveries = (await owner.get(f"{hooks}/{created['id']}/deliveries")).json()["data"]
        delivery = deliveries[0]["id"]
        replay = f"{CONSOLE}/orgs/{org}/projects/{project}/webhook-deliveries/{delivery}/replay"
        replayed = await owner.post(replay, headers=token)
        wrong_mode = await owner.delete(f"{hooks}/{created['id']}?livemode=true", headers=token)
        removed = await owner.delete(f"{hooks}/{created['id']}", headers=token)
        after = (await owner.get(hooks)).json()
        audit = (await owner.get(f"{CONSOLE}/orgs/{org}/audit")).json()["data"]
    assert (by_analyst.status_code, by_analyst.json()["code"]) == (403, "forbidden_for_role")
    assert created["secret"].startswith("whsec_") and created["livemode"] is False  # the secret, shown once
    assert (seen_by_analyst.status_code, live["data"]) == (403, [])  # analysts can't see where events go
    assert sent.status_code == 202 and [d["status"] for d in deliveries] == ["pending"]
    assert replayed.status_code == 202
    assert (wrong_mode.status_code, removed.status_code, after["data"]) == (404, 204, [])
    actions = {(e["action"], e["actor"].partition(":")[0]) for e in audit}
    assert {("webhook_endpoint.created", "user"), ("webhook_endpoint.deleted", "user")} <= actions


@pytest.mark.anyio
async def test_members_roles_change_under_the_owner_rules(databases: tuple[str, str]) -> None:
    async with (
        harness(databases, **CONSOLE_SETTINGS) as h,
        person(h) as owner,
        person(h) as admin,
        person(h) as other,
    ):
        me = await sign_up(owner, unique("roles-owner"))
        org, token = me["organisations"][0]["id"], {"X-CSRF-Token": me["csrf_token"]}
        admin_email, other_email = unique("roles-admin"), unique("roles-other")
        admin_token = {"X-CSRF-Token": (await sign_up(admin, admin_email, "A"))["csrf_token"]}
        other_token = {"X-CSRF-Token": (await sign_up(other, other_email, "B"))["csrf_token"]}
        members = f"{CONSOLE}/orgs/{org}/members"
        await owner.post(members, json={"email": admin_email, "role": "admin"}, headers=token)
        other_id = (await owner.post(members, json={"email": other_email, "role": "analyst"}, headers=token)).json()
        other_id, owner_id = other_id["user"], (await owner.get(f"{CONSOLE}/me")).json()["id"]
        admin_id = next(m["user"] for m in (await owner.get(members)).json()["data"] if m["email"] == admin_email)

        promoted = await admin.patch(f"{members}/{other_id}", json={"role": "developer"}, headers=admin_token)
        crowned_by_admin = await admin.patch(f"{members}/{other_id}", json={"role": "owner"}, headers=admin_token)
        last_owner = await owner.patch(f"{members}/{owner_id}", json={"role": "admin"}, headers=token)
        crowned = await owner.patch(f"{members}/{other_id}", json={"role": "owner"}, headers=token)
        stepped_down = await owner.patch(f"{members}/{owner_id}", json={"role": "admin"}, headers=token)
        admin_removes_owner = await admin.delete(f"{members}/{other_id}", headers=admin_token)
        removed = await other.delete(f"{members}/{admin_id}", headers=other_token)
        unknown = await other.delete(f"{members}/usr_nobody", headers=other_token)
        left = {m["email"]: m["role"] for m in (await other.get(members)).json()["data"]}
        audit = (await other.get(f"{CONSOLE}/orgs/{org}/audit")).json()["data"]
    assert promoted.json() == {"user": other_id, "role": "developer"}  # an admin may change a non-owner
    assert (crowned_by_admin.status_code, crowned_by_admin.json()["code"]) == (403, "forbidden_for_role")
    assert (last_owner.status_code, last_owner.json()["code"]) == (409, "last_owner")
    assert crowned.status_code == 200 and stepped_down.status_code == 200  # two owners, then one steps down
    assert (admin_removes_owner.status_code, removed.status_code, unknown.status_code) == (403, 204, 404)
    assert sorted(left.values()) == ["admin", "owner"]  # the first owner (now admin) and the new owner
    changes = [e for e in audit if e["action"] in ("member.role_changed", "member.removed")]
    assert len(changes) == 4  # three role changes and one removal; refusals leave no trace


@pytest.mark.anyio
async def test_text_the_database_cant_store_is_refused_not_a_server_error(databases: tuple[str, str]) -> None:
    async with harness(databases, **CONSOLE_SETTINGS) as h, person(h) as browser:
        body = {"email": "nul\u0000@shop.example", "password": PASSWORD}  # found by the contract tests
        response = await browser.post(f"{CONSOLE}/login", json=body)
    assert (response.status_code, response.json()["code"]) == (422, "invalid_text")


@pytest.mark.anyio
async def test_the_console_describes_the_age_model_to_anyone_signed_in_and_nothing_of_its_build(
    databases: tuple[str, str],
) -> None:
    trained = "registry/age/age-convnext-tiny-2026.10.17/manifest.json"
    async with harness(databases, age_manifest=trained, **CONSOLE_SETTINGS) as h, person(h) as browser:
        signed_out = await browser.get(f"{CONSOLE}/model")
        await sign_up(browser, unique("model"))
        model = (await browser.get(f"{CONSOLE}/model")).json()
    assert (signed_out.status_code, signed_out.json()["code"]) == (401, "not_signed_in")
    assert (model["version"], model["calibrated"]) == ("age-convnext-tiny-2026.10.17", False)
    assert model["permitted_use"] == "non-commercial research only"
    assert model["training"]["dataset"]["name"] == "fairface" and model["calibration"]["faces"] == 11301
    eighteen = next(row for row in model["thresholds"] if row["min_age"] == 18)
    assert eighteen["risk_budget"] == 0.075 and eighteen["minor_bound"] < eighteen["risk_budget"]
    for internal in ("sha256", "git", "model.onnx", "uncommitted"):
        assert internal not in json.dumps(model)


@pytest.mark.anyio
async def test_the_console_session_cookie_is_host_only_secure_and_hidden_from_scripts(
    databases: tuple[str, str],
) -> None:
    async with harness(databases, login_burst=100) as h:  # the production setting: a Secure cookie
        body = {"email": unique("cookie"), "password": PASSWORD, "organisation": "Shop Ltd"}
        response = await h.client.post(f"{CONSOLE}/signup", json=body)
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("__Host-dwarpal_session=")  # browsers insist on Secure, Path=/ and no Domain
    attributes = {part.strip().lower() for part in cookie.split(";")[1:]}
    assert {"httponly", "secure", "path=/", "samesite=lax"} <= attributes
    assert not any(a.startswith("domain=") for a in attributes)


@pytest.mark.anyio
async def test_a_switched_off_endpoint_gets_nothing_until_switched_back_on(databases: tuple[str, str]) -> None:
    async with harness(databases, webhook_allow_private=True) as h:
        auth = {"Authorization": f"Bearer {h.key}"}
        hook = {"url": "http://localhost:9/hooks", "events": ["verification_session.completed"]}
        endpoint = (await h.client.post("/v1/webhook-endpoints", json=hook, headers=auth)).json()
        address = f"/v1/webhook-endpoints/{endpoint['id']}"
        off = await h.client.patch(address, json={"enabled": False}, headers=auth)
        await h.client.post(f"{address}/test", headers=auth)
        while_off = (await h.client.get(f"{address}/deliveries", headers=auth)).json()["data"]
        on = await h.client.patch(address, json={"enabled": True}, headers=auth)
        await h.client.post(f"{address}/test", headers=auth)
        while_on = (await h.client.get(f"{address}/deliveries", headers=auth)).json()["data"]
        unknown = await h.client.patch("/v1/webhook-endpoints/whe_nobody", json={"enabled": False}, headers=auth)
    assert (off.json()["enabled"], on.json()["enabled"]) == (False, True)
    assert while_off == []  # switched off: the test event was recorded, but nothing was queued for it
    assert [d["status"] for d in while_on] == ["pending"]
    assert unknown.status_code == 404


@pytest.mark.anyio
async def test_sessions_can_be_listed_by_outcome_and_by_the_websites_reference(databases: tuple[str, str]) -> None:
    async with harness(databases) as h:
        passed = (await create(h, external_ref="order-1")).json()
        flow = await start(h, passed)
        await attempt(h, passed["id"], flow, [PORTRAIT] * 6)
        waiting = (await create(h, external_ref="order-2")).json()
        auth = {"Authorization": f"Bearer {h.key}"}
        by_outcome = (await h.client.get("/v1/verification-sessions?outcome=pass", headers=auth)).json()["data"]
        by_ref = (await h.client.get("/v1/verification-sessions?external_ref=order-2", headers=auth)).json()["data"]
        nothing = (await h.client.get("/v1/verification-sessions?external_ref=order-9", headers=auth)).json()["data"]
        wrong = await h.client.get("/v1/verification-sessions?outcome=maybe", headers=auth)
    assert [s["id"] for s in by_outcome] == [passed["id"]]
    assert [s["id"] for s in by_ref] == [waiting["id"]]
    assert nothing == []
    assert wrong.status_code == 422  # only the outcomes that exist


@pytest.mark.anyio
async def test_a_recovery_code_signs_in_once_and_codes_go_off_only_with_password_and_code(
    databases: tuple[str, str],
) -> None:
    email = unique("recovery")
    async with harness(databases, **CONSOLE_SETTINGS) as h, person(h) as browser:
        token = {"X-CSRF-Token": (await sign_up(browser, email))["csrf_token"]}
        secret = (await browser.post(f"{CONSOLE}/totp", headers=token)).json()["secret"]
        step = int(datetime.now(UTC).timestamp() // totp.STEP_S)
        confirm = {"code": totp.code_at(secret, step)}
        codes = (await browser.post(f"{CONSOLE}/totp/confirm", json=confirm, headers=token)).json()["recovery_codes"]
        login = {"email": email, "password": PASSWORD}
        typed = codes[0].upper().replace("-", " ")  # as someone might type it from paper
        with_recovery = await browser.post(f"{CONSOLE}/login", json=login | {"code": typed})
        token = {"X-CSRF-Token": with_recovery.json()["csrf_token"]}
        reused = await browser.post(f"{CONSOLE}/login", json=login | {"code": codes[0]})
        replaced = (await browser.post(f"{CONSOLE}/totp/recovery-codes", headers=token)).json()["recovery_codes"]
        old_after_replacing = await browser.post(f"{CONSOLE}/login", json=login | {"code": codes[1]})
        now_code = totp.code_at(secret, step + 1)
        bad_password = await browser.post(
            f"{CONSOLE}/totp/disable", json={"password": "not it, at all", "code": now_code}, headers=token
        )
        disabled = await browser.post(
            f"{CONSOLE}/totp/disable", json={"password": PASSWORD, "code": now_code}, headers=token
        )
        plain = await browser.post(f"{CONSOLE}/login", json=login)
    assert len(set(codes)) == totp.RECOVERY_CODES and all(re.fullmatch(r"[a-z2-7]{5}-[a-z2-7]{5}", c) for c in codes)
    assert with_recovery.status_code == 200 and with_recovery.json()["recovery_codes_left"] == 9
    assert (reused.status_code, reused.json()["code"]) == (401, "invalid_totp")  # each code works once
    assert set(replaced).isdisjoint(codes) and old_after_replacing.status_code == 401  # the old set is gone
    assert (bad_password.status_code, bad_password.json()["code"]) == (403, "reauthentication_failed")
    assert disabled.status_code == 204
    assert plain.status_code == 200 and plain.json()["totp_enabled"] is False  # no code needed any more
