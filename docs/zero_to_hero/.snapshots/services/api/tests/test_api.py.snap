"""The API end to end, against real PostgreSQL and Valkey containers and the real inference service in memory."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

import cv2
import docker
import httpx
import numpy as np
import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from joserfc import jwt
from joserfc.jwk import KeySet
from redis.asyncio import Redis
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.engine import Connection
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
    Organization,
    PolicyVersion,
    Project,
    SessionStat,
    VerificationAttempt,
    VerificationSession,
    WebhookDelivery,
    WebhookEndpoint,
)
from dwarpal_api.app import audit, maintenance
from dwarpal_api.app.delivery import Deliverer
from dwarpal_api.cli import maintain, migrate, revoke_key, rotate_key, seed_dev
from dwarpal_api.domain import ids
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


@asynccontextmanager
async def harness(
    databases: tuple[str, str],
    stub_age: float = 30.0,
    livemode: bool = False,
    liveness: Literal["images", "labels"] = "labels",
    scopes: list[str] | None = None,
    **overrides: Any,
) -> AsyncIterator[Harness]:
    database_url, valkey_url = databases
    inference = create_inference(InferenceSettings(stub_age=stub_age, liveness=liveness))
    inference_transport = httpx.ASGITransport(app=inference)
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
                yield Harness(client, key, project)


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
) -> httpx.Response:
    """One face attempt. By default the frames' labels follow the challenge the server issued; an attack may label
    them in another order (`poses`), report other browser signals, or claim a challenge of its own."""
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
    assert [o["outcome"] for o in outcomes] == ["retry", "retry", "step_up"]
    assert outcomes[0]["reasons"] == ["no_face"]
    assert outcomes[0]["attempts_remaining"] == 2
    assert session["status"] == "awaiting_step_up"
    assert session["age_token"] is None


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
    assert (too_short.status_code, too_short.json()["code"]) == (422, "invalid_idempotency_key")
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
