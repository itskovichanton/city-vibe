# City Vibe — инфраструктура и запуск всей системы

## Компоненты Docker (`make infra-up`)

| Сервис | Порт | Назначение |
|--------|------|------------|
| Postgres | 5432 | БД: `cityvibe_users`, `cityvibe_auth`, `cityvibe_places`, `cityvibe_notifications` |
| RabbitMQ | 5672 / UI 15672 | События (`city_vibe.events`), user/pass `cityvibe` |
| Redis | 6379 | OTP, rate-limit, idempotency |
| MinIO | 9000 / UI 9001 | S3 (аватары) |
| Jaeger | UI 16686, OTLP 4317 | Трейсы |
| MailHog | SMTP 1025 / UI 8025 | Локальный catcher писем (dev) |
| mock-notify | 8090 | Mock SMS `POST /sms` |

## Быстрый старт всей системы

```bash
# из корня репозитория
make install
make start-all       # infra + миграции + seed + все 5 сервисов в фоне
# логи: .run/logs/   стоп: make stop-all   рестарт: make restart-all

# либо по отдельности (5 терминалов / IDE Run Configs):
make run-user          # :8081
make run-auth          # :8082
make run-place         # :8083
make run-notification  # :8084
make run-gateway       # :8080  ← точка входа для мобилки
```

Мобильное приложение ходит **только на gateway**: `http://<mac-ip>:8080`

В Jaeger UI (http://localhost:16686) сервисы: `user-service`, `auth-service`, `place-catalog`, `notification-service`, `api-gateway`.

Примеры:
- `GET  http://localhost:8080/cities`
- `POST http://localhost:8080/auth/register`
- `POST http://localhost:8080/auth/login`
- `GET  http://localhost:8080/health`

Swagger сервисов:
- Gateway health: http://localhost:8080/health
- Auth docs: http://localhost:8082/docs
- User docs: http://localhost:8081/docs
- Place docs: http://localhost:8083/docs

## SMTP (реальный email)

Файл: `python/notification_service/config.yml` → секция `smtp`:

```yaml
smtp:
  host: smtp.gmail.com          # или smtp.yandex.ru / smtp.mail.ru
  port: 587
  user: your@gmail.com
  password: "app-password"      # для Gmail — пароль приложения
  from: noreply@yourdomain.com
  use_tls: true
```

ENV-переопределение (если добавите в код/профили): можно продублировать через PROFILE.

**Локально без реальной почты:** оставьте `host: localhost`, `port: 1025`, `use_tls: false` —
письма появятся в MailHog UI http://localhost:8025

## SMS

Всегда через mock: `http://localhost:8090/sms`  
Логи: `docker logs -f cityvibe-mock-notify`

## Google Sign-In — что нужно от тебя

1. [Google Cloud Console](https://console.cloud.google.com/) → создать проект City Vibe  
2. APIs & Services → Credentials → **OAuth 2.0 Client IDs**:
   - **Android** client (package name + SHA-1)
   - **iOS** client (bundle id) — когда дойдёте
   - **Web** client (если нужен)  
3. В `python/auth_service/config.yml` и `python/api_gateway/config.yml` (jwt_secret общий):

```yaml
auth:
  google_client_ids:
    - "<ANDROID_CLIENT_ID>.apps.googleusercontent.com"
    - "<WEB_CLIENT_ID>.apps.googleusercontent.com"
```

4. Flutter: `google_sign_in` → получить `idToken` → `POST /auth/social/google` `{ "id_token": "..." }`

Пока client id = placeholder — Google login вернёт ошибку конфигурации.

## Если Postgres уже был поднят до новых БД

Init-скрипт отрабатывает только на пустом volume. Создать БД вручную:

```bash
docker compose -f infra/docker-compose.yml exec -T postgres \
  psql -U cityvibe -d cityvibe_users -c "CREATE DATABASE cityvibe_auth;"
docker compose -f infra/docker-compose.yml exec -T postgres \
  psql -U cityvibe -d cityvibe_users -c "CREATE DATABASE cityvibe_notifications;"
# cityvibe_places уже могла быть
make migrate-all && make seed-place
```

## JWT

Секрет должен совпадать у `auth_service` и `api_gateway`: `auth.jwt_secret`  
Access ~15 мин, refresh ~30 дней.

## Подключение к БД (Postgres)

| Сервис | Database | URL |
|--------|----------|-----|
| user-service | `cityvibe_users` | `postgresql://cityvibe:cityvibe@localhost:5432/cityvibe_users` |
| auth-service | `cityvibe_auth` | `postgresql://cityvibe:cityvibe@localhost:5432/cityvibe_auth` |
| place-catalog | `cityvibe_places` | `postgresql://cityvibe:cityvibe@localhost:5432/cityvibe_places` |
| notification-service | `cityvibe_notifications` | `postgresql://cityvibe:cityvibe@localhost:5432/cityvibe_notifications` |

CLI:
```bash
docker compose -f infra/docker-compose.yml exec -it postgres \
  psql -U cityvibe -d cityvibe_auth
```

Async SQLAlchemy в сервисах: `postgresql+asyncpg://cityvibe:cityvibe@localhost:5432/<db>` (см. `config.yml` → `db.url`).

## OpenAPI / Flutter

```bash
make openapi-all
# → schema/openapi/*.json
# Flutter-клиент генерировать ТОЛЬКО из:
#   schema/openapi/city-vibe-mobile.json
```

Это агрегированная схема gateway (auth + users + cities) — все методы, которые видит мобилка.
