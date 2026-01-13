before-commit: lint pytest

create-db:
	uv run main.py db create

dev:
	uv run uvicorn main:app --loop uvloop --reload

drop-db:
	uv run main.py db drop

install:
	uv sync

init-db: drop-db create-db migrate

lint:
	uv run ruff format
	uv run ruff check --fix

makemigrations:
	uv run alembic revision --autogenerate

migrate:
	uv run alembic upgrade head

pytest:
	uv run pytest

update:
	uv lock --upgrade
	uv sync
