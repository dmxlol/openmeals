## Stack

- **Python 3.13** · **FastAPI** · **SQLAlchemy** · **SQLModel**
- **PostgreSQL** (Citus) · **pgvector** for vector similarity search
- **Celery** + **Redis** for async task processing
- **sentence-transformers** (`intfloat/multilingual-e5-base`) for multilingual embeddings
- **authlib** for JWT and OAuth

## Project structure

```
migrations/   # DB migrations
tests/        # unit and e2e tests
src/
    core/      # app config, framework entrypoints, shared DB/scheme primitives
    modules/   # subapplications (one per business domain)
    libs/      # shared low-level utilities (DB mixins, time helpers)
    services/  # business logic managers — sit between modules and external systems
    utils/     # generic helpers (FastAPI factory, S3 utils, etc.)
```

Each module under `src/modules/` follows this layout most of them are optional:
```
modulesX/
    dependencies.py  # FastAPI dependencies: request validation, DB retrieval
    dto.py           # dataclasses grouping resolved dependencies for handlers
    models.py        # ORM definitions
    handlers.py      # FastAPI route handlers
    schemes.py       # Pydantic request/response schemas
    exceptions.py    # package-specific exceptions
```

## Setup

```bash
# dependencies
uv sync

# infrastructure
docker compose up -d

# migrations
make migrate

# download embedding model
make download-model

# run api
make dev

# run celery worker
make worker
```

Copy `.env.example` to `.env` and fill in the values. Generate a secret key with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Auth

OAuth2 Authorization Code flow with pluggable providers. Currently supported: `local` (dev).

**Local provider flow:**
1. Generate a permanent ID token: `make script name=create_local_token`
2. Exchange it for a session: `GET /api/v1/auth/local/callback?code=<token>`
3. Use the returned `access_token` as `Authorization: Bearer <token>`
4. Refresh with `POST /api/v1/auth/refresh`

Access tokens expire in 30 min, refresh tokens in 30 days. Tokens include `iss`/`aud` claims for multi-service validation.
