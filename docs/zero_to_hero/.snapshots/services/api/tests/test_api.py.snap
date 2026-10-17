"""The API end to end, against real PostgreSQL and Valkey containers and the real inference service in memory."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
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
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.community.postgres import PostgresContainer
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy

from dwarpal_api.adapters.tables import METADATA
from dwarpal_api.cli import migrate, seed_dev
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
) -> AsyncIterator[Harness]:
    database_url, valkey_url = databases
    inference = create_inference(InferenceSettings(stub_age=stub_age, liveness=liveness))
    inference_transport = httpx.ASGITransport(app=inference)
    async with (
        inference.router.lifespan_context(inference),
        httpx.AsyncClient(transport=inference_transport, base_url="http://inference") as inference_http,
    ):
        settings = Settings(environment="test", database_url=database_url, valkey_url=valkey_url)
        api = create_api(settings, inference_http=inference_http)
        async with api.router.lifespan_context(api):
            project, key = await seed_dev(settings, livemode=livemode)
            transport = httpx.ASGITransport(app=api)
            async with httpx.AsyncClient(transport=transport, base_url="http://api") as client:
                yield Harness(client, key, project)


async def create(h: Harness, **body: Any) -> httpx.Response:
    payload = {"policy": "uk_osa_18", "return_url": RETURN_URL, **body}
    return await h.client.post("/v1/verification-sessions", json=payload, headers={"Authorization": f"Bearer {h.key}"})


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
