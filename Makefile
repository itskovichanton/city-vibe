# City Vibe — корневой Makefile
# Python: предпочтительно /Library/Frameworks/Python.framework/Versions/3.12/bin/python3

PYTHON ?= /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
PIP    ?= /Library/Frameworks/Python.framework/Versions/3.12/bin/pip3

REPO_ROOT := $(shell pwd)
USER_SERVICE := $(REPO_ROOT)/python/user-service
LIBS := $(REPO_ROOT)/python/libs
SCHEMA_DIR := $(REPO_ROOT)/schema
CLIENTS_DIR := $(LIBS)/clients

# PYTHONPATH: репозиторий + src сервиса + site-packages (фреймворк mybootstrap*)
export PYTHONPATH := $(REPO_ROOT):$(USER_SERVICE)/src:/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages

.PHONY: help install infra-up infra-down migrate-user seed-user run-user test-user \
        openapi openapi-user lint format clean

help:
	@echo "Цели:"
	@echo "  install       — зависимости user-service"
	@echo "  infra-up      — postgres, rabbitmq, redis, minio"
	@echo "  infra-down    — остановить infra"
	@echo "  migrate-user  — применить SQL-миграции user-service"
	@echo "  run-user      — запустить user-service"
	@echo "  test-user     — pytest user-service"
	@echo "  openapi       — сгенерировать OpenAPI + клиент/сущности в libs/clients"
	@echo "  openapi-user  — то же только для user-service"

install:
	$(PIP) install -r $(USER_SERVICE)/requirements.txt
	$(PIP) install -e $(USER_SERVICE)
	@echo "OK: зависимости установлены"

infra-up:
	docker compose -f infra/docker-compose.yml up -d
	@echo "Postgres :5432 | RabbitMQ :5672 (UI :15672) | Redis :6379 | MinIO :9000 (UI :9001)"

infra-down:
	docker compose -f infra/docker-compose.yml down

migrate-user:
	@echo "Применяем миграции user-service..."
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_users < $(USER_SERVICE)/sql/migrations/001_create_users.sql
	@echo "Миграции применены"

seed-user:
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_users < $(USER_SERVICE)/sql/seed/001_seed.sql

run-user:
	cd $(USER_SERVICE) && $(PYTHON) main.py

test-user:
	cd $(USER_SERVICE) && $(PYTHON) -m pytest tests/ -v

# --- OpenAPI ---
# 1) экспорт схемы в schema/user-service.json
# 2) dataclass-сущности → python/libs/clients/user_service/entities.py
# 3) async httpx-клиент → python/libs/clients/user_service/client.py

openapi: openapi-user

openapi-user:
	@mkdir -p $(SCHEMA_DIR)/openapi $(CLIENTS_DIR)/domain/user_service
	$(PYTHON) $(USER_SERVICE)/scripts/export_openapi.py
	$(PIP) install -q 'datamodel-code-generator'
	# DTO как dataclass → python/libs/clients/domain/user_service/entities.py
	datamodel-codegen \
		--input $(SCHEMA_DIR)/openapi/user-service.json \
		--input-file-type openapi \
		--output $(CLIENTS_DIR)/domain/user_service/entities.py \
		--output-model-type dataclasses.dataclass \
		--target-python-version 3.12 \
		--use-standard-collections \
		--use-union-operator \
		--snake-case-field
	@echo "Схема:   $(SCHEMA_DIR)/openapi/user-service.json"
	@echo "Entities:$(CLIENTS_DIR)/domain/user_service/entities.py"
	@echo "Client:  $(CLIENTS_DIR)/domain/user_service/client.py"

lint:
	$(PYTHON) -m ruff check python/user-service/src python/libs || true

format:
	$(PYTHON) -m ruff check --fix python/user-service/src python/libs || true

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
