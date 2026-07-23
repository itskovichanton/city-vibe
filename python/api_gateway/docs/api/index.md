# API Gateway — документация методов

Базовый URL для мобильного клиента: **`http://localhost:8080`**

Gateway — reverse proxy: сам почти не содержит бизнес-логики, пробрасывает запросы в микросервисы с теми же путями.

## Маршрутизация

| Префикс | Upstream | Порт | Документация темы |
|---------|----------|------|-------------------|
| `/health` | сам gateway (+ проверка backends) | 8080 | [infra](infra.md) |
| `/auth/*` | auth-service | 8082 | [auth](auth.md) |
| `/cities`, `/cities/*` | place-catalog | 8083 | [cities](cities.md) |
| `/users`, `/users/*` | user-service | 8081 | [users](users.md) |

**Не проксируется наружу:**

- `notification-service` (`:8084`) — consumer RabbitMQ, публичного mobile API нет
- `mock-notify` (`:8090`) — внутренний SMS mock
- Postgres / Redis / RabbitMQ / MinIO / Jaeger / MailHog — инфраструктура

## Темы

| Файл | Содержание |
|------|------------|
| [infra.md](infra.md) | Health-check gateway и backends |
| [auth.md](auth.md) | Регистрация, логин, OTP, пароль, JWT, Google |
| [cities.md](cities.md) | Справочник городов |
| [users.md](users.md) | Профиль, bio, онбординг, аватар |
| [conventions.md](conventions.md) | Обёртка ответов, JWT, ошибки, rate-limit |

## Интерактивная документация (все методы, включая прокси)

Нативный Swagger gateway (`http://localhost:8080/docs`) **неполный**: в коде catch-all proxy, поэтому OpenAPI gateway не перечисляет конкретные методы.

Полная агрегированная схема:

| Артефакт | Путь |
|----------|------|
| OpenAPI JSON | [`schema/openapi/city-vibe-mobile.json`](../../../../schema/openapi/city-vibe-mobile.json) |
| Пересборка | `make openapi-mobile` |
| Исходник схемы | [`scripts/export_mobile_openapi.py`](../../scripts/export_mobile_openapi.py) |

**Как открыть интерактивно:**

1. https://editor.swagger.io → Import file → `city-vibe-mobile.json`
2. Локально: `npx @redocly/cli preview-docs schema/openapi/city-vibe-mobile.json`
3. По частям у upstreams: http://localhost:8082/docs · http://localhost:8081/docs · http://localhost:8083/docs

## Быстрый старт

```bash
make start-all          # infra + миграции + все сервисы
curl http://localhost:8080/health
make stop-all
```
