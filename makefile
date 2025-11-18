.PHONY: tests makemigrations migrate

tests:
	uv run pytest

makemigrations:
	uv run alembic revision --autogenerate -m "$(comment)"

migrate:
	uv run alembic upgrade head
