import logging

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from starlette import status
from starlette.responses import Response

from core.database import get_async_session_factory
from core.lifespan import lifespan
from core.telemetry import instrument_app
from libs.app import AppRegistry
from services.ratelimit import limiter
from utils.fastapi import register_exception_handlers

from .config import settings


async def healthcheck() -> Response:
    try:
        async with get_async_session_factory()() as session:
            await session.execute(text("SELECT 1"))
        return Response(status_code=status.HTTP_200_OK)
    except Exception:
        logging.exception("Health check failed")
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


def create_app() -> FastAPI:
    registry = AppRegistry()
    registry.register_modules(settings)

    app = FastAPI(
        title="OpenMeals API",
        summary="Nutrition tracking with AI-powered analysis",
        version=settings.version,
        license_info={"name": "Apache-2.0"},
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    instrument_app(app, settings.otel)

    app.add_api_route("/health", healthcheck, methods=["GET"], include_in_schema=False)

    v1 = APIRouter(prefix="/api/v1")
    for router in registry.get_all_routers():
        v1.include_router(router)
    app.include_router(v1)

    return app


app = create_app()
