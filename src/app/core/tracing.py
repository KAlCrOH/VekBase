from __future__ import annotations

import os

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
except Exception:  # optional dependency
    trace = None
    FastAPIInstrumentor = None
    HTTPXClientInstrumentor = None

from .config import settings


def setup_tracing() -> None:
    if not settings.otlp_endpoint or trace is None:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": "vekbase"}))
    exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def instrument_fastapi(app) -> None:
    if FastAPIInstrumentor:
        FastAPIInstrumentor.instrument_app(app)
    if HTTPXClientInstrumentor:
        HTTPXClientInstrumentor().instrument()
