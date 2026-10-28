"""Traces must say how a request went, and nothing about who sent it (Phase 7, decision D11)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from dwarpal_api.adapters import telemetry


def test_a_trace_keeps_the_route_and_timing_and_drops_the_query_string_address_and_browser() -> None:
    app = FastAPI()

    @app.post("/v1/flow/sessions/{session}/start")
    async def start(session: str) -> dict[str, str]:
        return {"session": session}

    @app.get("/livez")
    async def livez() -> dict[str, str]:
        return {"status": "ok"}

    kept = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(kept))
    telemetry.install(app, provider)
    client = TestClient(app)
    client.post(
        "/v1/flow/sessions/vs_1/start?client_secret=never-in-a-trace",
        json={"client_secret": "nor-this"},
        headers={"Authorization": "Bearer nor-this-either", "User-Agent": "Ann's phone"},
    )
    client.get("/livez")

    (span,) = kept.get_finished_spans()  # one request traced: health checks are not
    attributes = dict(span.attributes or {})
    assert span.name == "POST /v1/flow/sessions/{session}/start"
    assert attributes["http.route"] == "/v1/flow/sessions/{session}/start" and attributes["http.status_code"] == 200
    assert attributes["http.url"] == "/v1/flow/sessions/vs_1/start"
    assert attributes["net.peer.ip"] == "" and attributes["http.user_agent"] == ""
    recorded = repr(attributes)
    for secret in ("never-in-a-trace", "nor-this", "Bearer", "Ann's phone", "testclient"):
        assert secret not in recorded


def test_request_metrics_are_labelled_with_the_route_pattern_and_nothing_about_the_caller() -> None:
    app = FastAPI()

    @app.post("/v1/flow/sessions/{session}/start")
    async def start(session: str) -> dict[str, str]:
        return {"session": session}

    reader = InMemoryMetricReader()
    telemetry.install(app, TracerProvider(), MeterProvider(metric_readers=[reader]))
    TestClient(app).post("/v1/flow/sessions/vs_1/start?client_secret=never", headers={"User-Agent": "Ann's phone"})

    data = reader.get_metrics_data()
    assert data is not None
    points = {
        metric.name: dict(point.attributes or {})
        for resource in data.resource_metrics
        for scope in resource.scope_metrics
        for metric in scope.metrics
        for point in metric.data.data_points
    }
    duration = points["http.server.duration"]  # how long requests take, by route and status: for the dashboards
    assert duration["http.target"] == "/v1/flow/sessions/{session}/start" and duration["http.status_code"] == 200
    recorded = repr(points)
    for secret in ("vs_1", "never", "Ann's phone", "testclient"):
        assert secret not in recorded
