import typing as t

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

if t.TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy.engine import Engine

    from core.config import OtelSettings


def setup_telemetry(settings: "OtelSettings") -> TracerProvider:
    resource = Resource.create({"service.name": settings.service_name})

    provider = TracerProvider(resource=resource)
    if settings.endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=f"{settings.endpoint}/v1/traces",
                    headers=settings.headers,
                )
            )
        )

        metrics.set_meter_provider(
            MeterProvider(
                resource=resource,
                metric_readers=[
                    PeriodicExportingMetricReader(
                        OTLPMetricExporter(
                            endpoint=f"{settings.endpoint}/v1/metrics",
                            headers=settings.headers,
                        )
                    )
                ],
            )
        )

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
    setup_telemetry(settings)
    CeleryInstrumentor().instrument()
