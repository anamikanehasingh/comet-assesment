PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: setup run test lint lint-fix docker-up migrate docker-migrate seed checks

setup:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	pre-commit install || true

run:
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

lint-fix:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

docker-up:
	docker compose up --build

migrate:
	$(PYTHON) -m alembic upgrade head

docker-migrate:
	docker compose run --rm api alembic upgrade head

seed:
	$(PYTHON) scripts/seed.py

checks:
	docker compose --profile checks run --rm checks
