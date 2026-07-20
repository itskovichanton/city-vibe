# City Vibe — корневой Makefile
# Python: предпочтительно /Library/Frameworks/Python.framework/Versions/3.12/bin/python3

PYTHON ?= /Library/Frameworks/Python.framework/Versions/3.12/bin/python3
PIP    ?= /Library/Frameworks/Python.framework/Versions/3.12/bin/pip3

REPO_ROOT := $(shell pwd)
USER_SERVICE := $(REPO_ROOT)/python/user_service
AUTH_SERVICE := $(REPO_ROOT)/python/auth_service
PLACE_CATALOG := $(REPO_ROOT)/python/place_catalog
NOTIFICATION_SERVICE := $(REPO_ROOT)/python/notification_service
API_GATEWAY := $(REPO_ROOT)/python/api_gateway
LIBS := $(REPO_ROOT)/python/libs
SCHEMA_DIR := $(REPO_ROOT)/schema
CLIENTS_DIR := $(LIBS)/clients

export PYTHONPATH := $(REPO_ROOT):$(USER_SERVICE)/src:$(AUTH_SERVICE)/src:$(PLACE_CATALOG)/src:$(NOTIFICATION_SERVICE)/src:$(API_GATEWAY)/src:/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12/site-packages

.PHONY: help install infra-up infra-down migrate-user migrate-auth migrate-place migrate-notification migrate-all \
        seed-user seed-place run-user run-auth run-place run-notification run-gateway test-user test-auth test-place \
        test-notification test-libs test-unit test-integration test-all openapi openapi-user openapi-auth openapi-place \
        openapi-gateway openapi-notification openapi-mobile openapi-all up-all start-all stop-all restart-all docs lint format clean

help:
	@echo "Цели:"
	@echo "  install            — зависимости всех сервисов"
	@echo "  infra-up           — postgres, rabbitmq, redis, minio, jaeger, mailhog, mock-notify"
	@echo "  migrate-all        — все SQL-миграции"
	@echo "  seed-place         — сид ~50 городов"
	@echo "  up-all             — infra + migrate + seed"
	@echo "  start-all          — up-all + запуск ВСЕХ микросервисов в фоне"
	@echo "  stop-all           — остановить все микросервисы"
	@echo "  restart-all        — stop-all + start-all"
	@echo "  run-*              — один сервис на переднем плане"
	@echo "  test-* / openapi-all"
	@echo "  docs               — infra/README.md"

install:
	$(PIP) install -r $(USER_SERVICE)/requirements.txt
	$(PIP) install -r $(AUTH_SERVICE)/requirements.txt
	$(PIP) install -r $(PLACE_CATALOG)/requirements.txt
	$(PIP) install -r $(NOTIFICATION_SERVICE)/requirements.txt
	$(PIP) install -r $(API_GATEWAY)/requirements.txt
	$(PIP) install pwdlib argon2-cffi PyJWT phonenumbers email-validator google-auth aiosmtplib jinja2 httpx fakeredis opentelemetry-instrumentation-httpx testcontainers
	@echo "OK: зависимости установлены"

infra-up:
	docker compose -f infra/docker-compose.yml up -d
	@echo "Postgres :5432 | RabbitMQ :5672 (UI :15672) | Redis :6379 | MinIO :9000"
	@echo "Jaeger UI :16686 | MailHog UI :8025 (SMTP :1025) | Mock-notify SMS :8090"
	@echo "См. infra/README.md — полный гайд запуска"

infra-down:
	docker compose -f infra/docker-compose.yml down

migrate-user:
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_users < $(USER_SERVICE)/sql/migrations/001_create_users.sql
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_users < $(USER_SERVICE)/sql/migrations/002_outbox.sql
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_users < $(USER_SERVICE)/sql/migrations/003_add_auth_fields.sql

migrate-auth:
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_auth < $(AUTH_SERVICE)/sql/migrations/001_create_auth.sql
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_auth < $(AUTH_SERVICE)/sql/migrations/002_outbox.sql

migrate-place:
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_places < $(PLACE_CATALOG)/sql/migrations/001_create_cities.sql

migrate-notification:
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_notifications < $(NOTIFICATION_SERVICE)/sql/migrations/001_notification_log.sql

migrate-all: migrate-user migrate-auth migrate-place migrate-notification
	@echo "Все миграции применены"

seed-user:
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_users < $(USER_SERVICE)/sql/seed/001_seed.sql

seed-place:
	docker compose -f infra/docker-compose.yml exec -T postgres \
		psql -U cityvibe -d cityvibe_places < $(PLACE_CATALOG)/sql/seed/001_seed_cities.sql

run-user:
	cd $(USER_SERVICE) && CITYVIBE_OTEL_SERVICE_NAME=user-service CITYVIBE_TRACING_ENABLED=true $(PYTHON) main.py

run-auth:
	cd $(AUTH_SERVICE) && CITYVIBE_OTEL_SERVICE_NAME=auth-service CITYVIBE_TRACING_ENABLED=true $(PYTHON) main.py

run-place:
	cd $(PLACE_CATALOG) && CITYVIBE_OTEL_SERVICE_NAME=place-catalog CITYVIBE_TRACING_ENABLED=true $(PYTHON) main.py

run-notification:
	cd $(NOTIFICATION_SERVICE) && CITYVIBE_OTEL_SERVICE_NAME=notification-service CITYVIBE_TRACING_ENABLED=true $(PYTHON) main.py

run-gateway:
	cd $(API_GATEWAY) && CITYVIBE_OTEL_SERVICE_NAME=api-gateway CITYVIBE_TRACING_ENABLED=true $(PYTHON) main.py

# Infra + миграции + сид + все 5 сервисов в фоне (логи в .run/logs/)
start-all: up-all
	@chmod +x $(REPO_ROOT)/scripts/start_all.sh $(REPO_ROOT)/scripts/stop_all.sh
	@$(REPO_ROOT)/scripts/start_all.sh

stop-all:
	@chmod +x $(REPO_ROOT)/scripts/stop_all.sh
	@$(REPO_ROOT)/scripts/stop_all.sh

restart-all: stop-all start-all

test-user:
	cd $(USER_SERVICE) && $(PYTHON) -m pytest tests/ -v

test-auth:
	cd $(AUTH_SERVICE) && $(PYTHON) -m pytest tests/ -v

test-place:
	cd $(PLACE_CATALOG) && $(PYTHON) -m pytest tests/ -v

test-notification:
	cd $(NOTIFICATION_SERVICE) && $(PYTHON) -m pytest tests/ -v --ignore=tests/integration || true

test-libs:
	cd $(REPO_ROOT) && $(PYTHON) -m pytest python/libs/infra/tests/ python/libs/clients/tests/ -v

test-unit: test-user test-auth test-place test-notification test-libs
	@echo "Unit tests OK"

test-integration:
	cd $(REPO_ROOT) && $(PYTHON) -m pytest python/tests/integration/ -v -m integration

test-all: test-unit test-integration
	@echo "All tests OK"

openapi: openapi-all

openapi-user:
	@mkdir -p $(SCHEMA_DIR)/openapi
	$(PYTHON) $(USER_SERVICE)/scripts/export_openapi.py

openapi-auth:
	@mkdir -p $(SCHEMA_DIR)/openapi
	$(PYTHON) $(AUTH_SERVICE)/scripts/export_openapi.py

openapi-place:
	@mkdir -p $(SCHEMA_DIR)/openapi
	$(PYTHON) $(PLACE_CATALOG)/scripts/export_openapi.py

openapi-gateway:
	@mkdir -p $(SCHEMA_DIR)/openapi
	$(PYTHON) $(API_GATEWAY)/scripts/export_openapi.py

openapi-notification:
	@mkdir -p $(SCHEMA_DIR)/openapi
	$(PYTHON) $(NOTIFICATION_SERVICE)/scripts/export_openapi.py

openapi-mobile:
	@mkdir -p $(SCHEMA_DIR)/openapi
	$(PYTHON) $(API_GATEWAY)/scripts/export_mobile_openapi.py

openapi-all: openapi-user openapi-auth openapi-place openapi-gateway openapi-notification openapi-mobile
	@echo "Схемы в $(SCHEMA_DIR)/openapi/"
	@echo "Flutter: schema/openapi/city-vibe-mobile.json"

up-all: infra-up migrate-all seed-place
	@echo "Infra+DB готовы. Дальше: make start-all  (или run-* по отдельности)"

docs:
	@echo "См. infra/README.md"

lint:
	$(PYTHON) -m ruff check python/ || true

format:
	$(PYTHON) -m ruff check --fix python/ || true

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
