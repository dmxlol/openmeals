import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded
from starlette import status

from libs.exceptions import AppError
from libs.schemes import ErrorResponse

logger = logging.getLogger(__name__)

_E = ErrorResponse
RESPONSES_AUTH = {status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid bearer token", "model": _E}}
RESPONSES_NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"description": "Resource not found", "model": _E}}
RESPONSES_FORBIDDEN = {status.HTTP_403_FORBIDDEN: {"description": "Not authorized to modify resource", "model": _E}}
RESPONSES_CONFLICT = {status.HTTP_409_CONFLICT: {"description": "Resource conflict", "model": _E}}
RESPONSES_TIMEOUT = {status.HTTP_408_REQUEST_TIMEOUT: {"description": "Upstream processing timed out", "model": _E}}
RESPONSES_RATE_LIMIT = {status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Rate limit exceeded", "model": _E}}


def merge_responses(*dicts: dict) -> dict:
    merged: dict = {}
    for d in dicts:
        merged.update(d)
    return merged


def _error_response(status_code: int, detail: str, extra: list | dict | None = None) -> JSONResponse:
    content: dict = {"detail": detail}
    if extra is not None:
        content["extra"] = extra
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.detail, getattr(exc, "extra", None))

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        return _error_response(exc.status_code, exc.detail)

    @app.exception_handler(ValidationError)
    async def validation_error_handler(_request: Request, exc: ValidationError) -> JSONResponse:
        return _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "Validation failed", exc.errors())

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(_request: Request, _exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": "60"},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Something went wrong")
