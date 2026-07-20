"""
OpenTelemetry → Jaeger (OTLP).

ENV:
  CITYVIBE_TRACING_ENABLED=true
  CITYVIBE_OTEL_ENDPOINT=http://localhost:4317
  CITYVIBE_OTEL_SERVICE_NAME=<имя сервиса>  # обязательно разное на процесс
"""

from __future__ import annotations

import logging
from typing import Any

from python.libs.infra.flags import flags

logger = logging.getLogger(__name__)

_provider_ready = False
_requests_ready = False
_httpx_ready = False
_instrumented_engines: set[int] = set()


def setup_tracer_provider(service_name: str | None = None) -> bool:
    """Идемпотентно поднимает TracerProvider + OTLP exporter. False если tracing выключен."""
    global _provider_ready
    f = flags()
    if not f.tracing:
        return False
    if _provider_ready:
        return True

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    name = service_name or f.otel_service_name
    resource = Resource.create(
        {
            "service.name": name,
            "service.namespace": "city-vibe",
        },
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f.otel_endpoint, insecure=True)
    provider.add_span_processor(
        BatchSpanProcessor(exporter, schedule_delay_millis=1000),
    )
    trace.set_tracer_provider(provider)
    _provider_ready = True
    logger.info("Tracing ON → %s (service=%s)", f.otel_endpoint, name)
    return True


def instrument_fastapi(app: Any, service_name: str | None = None) -> None:
    """Входящие HTTP-запросы FastAPI/Starlette."""
    if not setup_tracer_provider(service_name):
        return

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    def _request_hook(span, scope):  # noqa: ANN001
        if span is None or not span.is_recording():
            return
        for key, value in scope.get("headers") or ():
            if key.lower() == b"x-request-id":
                span.set_attribute("http.request_id", value.decode("utf-8", errors="replace"))
                break

    FastAPIInstrumentor.instrument_app(
        app,
        server_request_hook=_request_hook,
        excluded_urls="/health,/docs,/redoc,/openapi.json",
    )
    logger.info("Tracing: FastAPI instrumented")


def instrument_requests() -> None:
    """Исходящие HTTP через requests (on_mbclient_api)."""
    global _requests_ready
    if not setup_tracer_provider():
        return
    if _requests_ready:
        return

    from opentelemetry.instrumentation.requests import RequestsInstrumentor

    RequestsInstrumentor().instrument()
    _requests_ready = True
    logger.info("Tracing: requests instrumented")


def instrument_httpx() -> None:
    """Исходящие HTTP через httpx (gateway, auth→user S2S)."""
    global _httpx_ready
    if not setup_tracer_provider():
        return
    if _httpx_ready:
        return

    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
        _httpx_ready = True
        logger.info("Tracing: httpx instrumented")
    except ImportError:
        logger.warning("opentelemetry-instrumentation-httpx не установлен — httpx без трейсов")


def instrument_sqlalchemy(engine: Any) -> None:
    """SQL-запросы. Для AsyncEngine берём sync_engine."""
    if not setup_tracer_provider():
        return
    if engine is None:
        return

    sync_engine = getattr(engine, "sync_engine", engine)
    eng_id = id(sync_engine)
    if eng_id in _instrumented_engines:
        return

    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(
        engine=sync_engine,
        enable_commenter=True,
        commenter_options={"db_driver": True, "db_framework": True},
    )
    _instrumented_engines.add(eng_id)
    logger.info("Tracing: SQLAlchemy instrumented")
