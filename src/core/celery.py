from celery import Celery

from core.config import settings
from core.telemetry import instrument_celery

celery_app = Celery("openmeals")
celery_app.config_from_object(settings.celery, namespace="")
celery_app.autodiscover_tasks([*settings.modules, "services"])
instrument_celery(settings.otel)
