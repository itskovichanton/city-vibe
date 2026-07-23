# API Gateway — документация методов

Базовый URL: **`http://localhost:8080`**

## Маршрутизация

| Префикс | Upstream | Порт | Docs |
|---------|----------|------|------|
| `/health` | gateway | 8080 | [infra](infra.md) |
| `/auth/*` | auth-service | 8082 | [auth](auth.md) |
| `/users/*` | user-service | 8081 | [users](users.md) |
| `/cities/*` | place-service | 8083 | [cities](cities.md) |
| `/categories`, `/attr-schemas/*` | place-service | 8083 | [categories](categories.md) |
| `/places/*` | place-service | 8083 | [places](places.md) |
| `/pin-styles/*`, `/chat-themes/*` | design-service | 8085 | [design](design.md) |

## Темы

- [conventions.md](conventions.md)
- [infra.md](infra.md)
- [auth.md](auth.md)
- [cities.md](cities.md)
- [categories.md](categories.md)
- [places.md](places.md)
- [users.md](users.md)
- [design.md](design.md)

## Интерактивная OpenAPI

- Mobile aggregate: `schema/openapi/city-vibe-mobile.json` · `make openapi-mobile`
- Place: `schema/openapi/place-service.json`
- Design: `schema/openapi/design-service.json`
- Swagger сервисов: `:8083/docs`, `:8085/docs`, …
