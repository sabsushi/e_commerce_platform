.DEFAULT_GOAL := help
PYTHON := python3
UV     := $(shell command -v uv 2>/dev/null)

ifdef UV
  RUN := uv run
else
  RUN := $(PYTHON)
endif

.PHONY: help setup install migrate seed run test reset clean-venv

help:
	@echo "Usage:"
	@echo "  make setup     — (re)install, migrate, seed and start the app"
	@echo "  make run       — start the dev server (port 8000)"
	@echo "  make test      — run the test suite"
	@echo "  make reset     — wipe the DB, re-migrate and re-seed"
	@echo "  make clean-venv — delete and recreate the virtual environment"

## One-command bootstrap ────────────────────────────────────
setup: clean-venv install migrate seed run

clean-venv:
	rm -rf .venv
ifdef UV
	uv venv
else
	$(PYTHON) -m venv .venv
endif

install:
ifdef UV
	uv sync
else
	.venv/bin/pip install -q -r requirements.txt
endif

migrate:
	$(RUN) manage.py migrate

seed:
	$(RUN) manage.py seed

## Daily use ────────────────────────────────────────────────
run:
	$(RUN) manage.py runserver

test:
	$(RUN) manage.py test

reset:
	rm -f db.sqlite3
	$(MAKE) migrate seed
