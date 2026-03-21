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

FROM base AS deps

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project

FROM base

ARG VERSION=0.0.1a
ENV VERSION=${VERSION}

COPY --from=deps /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY src/ ./

RUN adduser --disabled-password --no-create-home --uid 1000 app
USER app

EXPOSE 8000

CMD ["uvicorn", "core.fastapi:app", "--host", "0.0.0.0", "--port", "8000"]
