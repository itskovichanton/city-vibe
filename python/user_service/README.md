# user-service

Сервис профилей и онбординга City Vibe.

## Структура (clean architecture)

```
src/user_service/
  presenter/   # FastAPI (контроллер + сервер) — как Spring MVC
  usecase/     # бизнес-сценарии
  repo/        # репозитории → возвращают DTO, не ORM
  entities/    # DTO запросов/ответов сервиса
  infra/       # SQLAlchemy, S3, сессии БД
sql/
  migrations/  # SQL-миграции
  seed/        # начальные данные
tests/
```

## Запуск

Из корня репозитория:

```bash
make infra-up
make migrate-user
make run-user
```

Swagger: http://localhost:8081/docs
OpenAPI: http://localhost:8081/openapi.json

## OpenAPI → клиент

```bash
make openapi-user
```

Артефакты:

- `schema/user-service.openapi.json`
- `python/libs/clients/user_service/entities.py` (dataclass)
- HTTP-клиент рядом в `python/libs/clients/user_service/`
