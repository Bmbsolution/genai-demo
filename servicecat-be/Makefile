.PHONY: install migrate downgrade revision seed dev lint fmt test test-cov

install:
	python -m pip install -e ".[dev]"

migrate:
	alembic upgrade head

downgrade:
	alembic downgrade -1

revision:
	alembic revision -m "$(m)"

seed:
	@echo "No seed script yet — added in a later backlog issue."

dev:
	uvicorn servicecat.main:app --reload --port 8000

lint:
	ruff check src tests
	ruff format --check src tests
	mypy src

fmt:
	ruff format src tests
	ruff check --fix src tests

test:
	pytest

test-cov:
	pytest --cov --cov-report=term-missing --cov-fail-under=80
