# City Vibe

Монорепозиторий мобильного приложения City Vibe (личный гид по городу).

## Структура

```
infra/                  # docker-compose: postgres, rabbitmq, redis, minio (S3)
python/
  libs/
    entities/           # общие DTO + EventBus (RabbitMQ)
    clients/            # сгенерированные OpenAPI-клиенты и dataclass-сущности
  user-service/         # сервис профилей / онбординга
schema/                 # OpenAPI JSON
```

## Быстрый старт

```bash
make infra-up          # инфраструктура
make install           # зависимости
make migrate-user      # схема БД
make run-user          # user-service → :8081
make openapi-user      # схема + клиент в python/libs/clients
make test-user
```

Swagger: http://localhost:8081/docs

## Стек

- Python 3.12 + FastAPI + SQLAlchemy (async) + PostgreSQL
- RabbitMQ (event-driven, `EventBus`)
- S3 / MinIO (аватарки)
- IoC: mybootstrap_* (Spring-like `@bean`)
