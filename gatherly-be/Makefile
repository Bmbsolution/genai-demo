.PHONY: lint format test seed run

PY ?= .venv/Scripts/python.exe

lint:
	$(PY) -m ruff check src tests
	$(PY) -m ruff format --check src tests
	$(PY) -m mypy --strict src

format:
	$(PY) -m ruff format src tests
	$(PY) -m ruff check --fix src tests

test:
	$(PY) -m pytest

seed:
	$(PY) -m gatherly.scripts.seed

run:
	$(PY) -m uvicorn gatherly.main:app --port 8002
