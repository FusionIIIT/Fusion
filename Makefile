.DEFAULT_GOAL := help
PY := .venv/bin/python
export DJANGO_SETTINGS_MODULE ?= config.settings.dev

help:  ## show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install:  ## create the venv and install everything
	uv venv --python 3.12 .venv
	uv pip install --python $(PY) -e ".[dev]"

up:  ## start postgres + redis
	docker compose up -d

migrate:  ## apply migrations
	$(PY) manage.py migrate

seed:  ## register modules and load sample data
	$(PY) manage.py seed_modules
	$(PY) manage.py seed_demo

dev:  ## run the server
	$(PY) manage.py runserver 0.0.0.0:8002

test:  ## run the test suite
	$(PY) -m pytest

check: ## everything CI runs
	$(PY) manage.py check
	$(PY) manage.py makemigrations --check --dry-run
	.venv/bin/ruff check .
	.venv/bin/lint-imports
	$(PY) ops/checks/no_cross_module_fk.py
	$(PY) ops/checks/contracts_are_plural.py
	$(PY) ops/checks/nav_matches_routes.py
	$(PY) manage.py permission_manifest --check
	$(MAKE) schema-check
	$(PY) -m pytest -q

check-client: ## the client half of CI
	cd client && npm run typecheck && npm test && npm run build

SCHEMA := openapi/fusion-integrated.v1.yaml

schema:  ## regenerate the committed OpenAPI schema
	$(PY) manage.py spectacular --fail-on-warn --file $(SCHEMA)

permissions:  ## regenerate the permission manifest the IAM seeds from
	$(PY) manage.py permission_manifest

module-structure:  ## regenerate the module-structure reference PDF
	$(PY) ops/docs/module_structure.py

schema-check:  ## the committed schema must match the code
	@$(PY) manage.py spectacular --fail-on-warn --file /tmp/openapi.check.yaml
	@diff -u $(SCHEMA) /tmp/openapi.check.yaml > /dev/null \
		|| { echo "$(SCHEMA) is stale — run 'make schema'"; exit 1; }
	@echo "openapi schema matches the code"

.PHONY: help install up migrate seed dev test check check-client schema \
	schema-check permissions module-structure
