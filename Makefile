export PYTHONPATH := src

.PHONY: install install-dev run worker script download-model format lint test migrate migration db

install:
	uv sync

install-dev:
	uv sync --dev

run:
	uv run uvicorn core.app:create_app --factory --reload --host 0.0.0.0 --port 8000

script:
	uv run --env-file .env $(if $(env),--env-file .env.$(env)) python scripts/$(name).py

download-model:
	$(MAKE) script name=download_model $(if $(env),env=$(env))

worker:
	uv run celery -A core.celery:celery_app worker --loglevel=info

format:
	uv run ruff check --select I,F,UP,PERF,PLE,PLC,E --fix
	uv run ruff format .

lint:
	uv run ruff check .

test:
	uv run pytest tests/ -v

migrate:
	uv run alembic upgrade head

migration:
	uv run alembic revision --autogenerate -m "$(name)"

db:
	docker compose up -d db
