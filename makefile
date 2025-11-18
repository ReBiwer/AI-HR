.PHONY: tests makemigrations migrate start-containers

tests:
	uv run pytest

makemigrations:
	uv run alembic revision --autogenerate -m "$(comment)"

migrate:
	uv run alembic upgrade head

start-containers:
	docker compose up -d
