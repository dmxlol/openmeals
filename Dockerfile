FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local/ \
    UV_SYSTEM_PYTHON=1 \
    UV_NO_MANAGED_PYTHON=1 \
    UV_LOCKED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN adduser --disabled-password --no-create-home --uid 1000 app

# --- runtime base: shared source, no deps ---
# Inheriting from base keeps src/ changes out of the dep-install cache layers.
FROM base AS runtime

COPY src/ ./

# --- api deps (no ML) ---
FROM base AS deps-api

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project

# --- worker deps (api deps + ml group) ---
FROM deps-api AS deps-worker

RUN uv sync --no-dev --no-install-project --group ml

# --- api image ---
FROM runtime AS api

ARG VERSION=0.0.1a
ENV VERSION=${VERSION}

COPY --from=deps-api /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=deps-api /usr/local/bin /usr/local/bin

USER app

EXPOSE 8000

CMD ["uvicorn", "core.fastapi:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]

# --- worker image ---
FROM runtime AS worker

ARG VERSION=0.0.1a
ENV VERSION=${VERSION}

COPY --from=deps-worker /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=deps-worker /usr/local/bin /usr/local/bin

USER app

CMD ["celery", "-A", "core.celery:celery_app", "worker", "--loglevel=info"]