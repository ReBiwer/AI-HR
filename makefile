.PHONY: tests makemigrations migrate run-bot run-web run-all run-linter

tests:
	uv run pytest

makemigrations:
	uv run alembic revision --autogenerate -m "$(comment)"

migrate:
	uv run alembic upgrade head

run-all:
	docker compose up -d

run-bot:
	docker compose up -d bot

run-web:
	docker compose up -d web

run-linter:
	uv run ruff check --fix && uv run ruff format
