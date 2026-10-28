"""Traces and metrics (Phase 7, decision D11): for each request, which route it took, how it ended and how long it
took — one trace each, and running totals for dashboards and alerts — sent to an OpenTelemetry collector when
`DWARPAL_OTEL_ENDPOINT` is set, and off otherwise.

A trace must carry nothing about the person: no body, header or query string (so no image, token, key or secret), and
not the visitor's network address or browser, which the instrumentation records by default and this module blanks.
Metrics are labelled with the route's pattern (`/v1/flow/sessions/{session_text}/start`), never a real address."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span

SERVICE = "dwarpal-api"
# Health checks arrive every few seconds from the load balancer; traced, they would drown everything else.
UNTRACED = "livez,readyz"
# What the instrumentation records about the caller, and what it becomes: the full address (with its query string)
# becomes the path alone; the caller's network address, port and browser become nothing.
BLANKED: dict[str, str | int] = {
    "net.peer.ip": "",
    "net.peer.port": 0,
    "http.user_agent": "",
    "client.address": "",
    "client.port": 0,
}


def provider_for(endpoint: str) -> TracerProvider:
    """Send finished traces in batches, over HTTP, to the collector at `endpoint`."""
    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE}))
    exporter = OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    return provider


def meters_for(endpoint: str) -> MeterProvider:
    """Send the running totals to the collector at `endpoint` every 15 seconds."""
    exporter = OTLPMetricExporter(endpoint=f"{endpoint.rstrip('/')}/v1/metrics")
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=15_000)
    return MeterProvider(resource=Resource.create({"service.name": SERVICE}), metric_readers=[reader])


def _blank_the_caller(span: Span, scope: dict[str, Any]) -> None:
    if span.is_recording():
        span.set_attribute("http.url", scope["path"])
        span.set_attributes(BLANKED)


def install(app: FastAPI, provider: TracerProvider, meters: MeterProvider | None = None) -> None:
    """Trace (and count) every request to `app`, except health checks; only the request as a whole, not each read and
    write."""
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        meter_provider=meters,
        excluded_urls=UNTRACED,
        exclude_spans=["receive", "send"],
        server_request_hook=_blank_the_caller,
    )
