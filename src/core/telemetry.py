import typing as t

from opentelemetry import trace
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

if t.TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy.engine import Engine

    from core.config import OtelSettings


def setup_telemetry(settings: "OtelSettings") -> TracerProvider:
    resource = Resource.create({"service.name": settings.service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    return provider


def instrument_app(app: "FastAPI", settings: "OtelSettings") -> None:
    if not settings.enabled:
        return

    setup_telemetry(settings)
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health")
    HTTPXClientInstrumentor().instrument()
    CeleryInstrumentor().instrument()


def instrument_sqlalchemy(engine: "Engine", settings: "OtelSettings") -> None:
    if not settings.enabled:
        return
    SQLAlchemyInstrumentor().instrument(engine=engine)


def instrument_celery(settings: "OtelSettings") -> None:
    if not settings.enabled:
        return
    CeleryInstrumentor().instrument()
