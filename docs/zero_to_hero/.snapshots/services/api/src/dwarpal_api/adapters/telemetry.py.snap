"""Traces (Phase 7, decision D11): for each request, which route it took, how it ended and how long it took, sent to an
OpenTelemetry collector when `DWARPAL_OTEL_ENDPOINT` is set, and off otherwise.

A trace must carry nothing about the person: no body, header or query string (so no image, token, key or secret), and
not the visitor's network address or browser, which the instrumentation records by default and this module blanks."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
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


def _blank_the_caller(span: Span, scope: dict[str, Any]) -> None:
    if span.is_recording():
        span.set_attribute("http.url", scope["path"])
        span.set_attributes(BLANKED)


def install(app: FastAPI, provider: TracerProvider) -> None:
    """Trace every request to `app`, except health checks; only the request as a whole, not each read and write."""
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        excluded_urls=UNTRACED,
        exclude_spans=["receive", "send"],
        server_request_hook=_blank_the_caller,
    )
