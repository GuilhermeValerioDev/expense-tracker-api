.PHONY: dev migrate test lint check prod prod-down down seed backup

dev:
	docker compose up -d postgres
	uv run alembic upgrade head
	uv run uvicorn app.main:app --reload

migrate:
	uv run alembic upgrade head

test:
	uv run pytest --cov --cov-report=term-missing

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

check: lint test

prod:
	docker compose -f compose.yml -f compose.prod.yml up --build

prod-down:
	docker compose -f compose.yml -f compose.prod.yml down

down:
	docker compose down

seed:
	uv run python -m scripts.seed --reset

backup:
	./scripts/backup.sh
