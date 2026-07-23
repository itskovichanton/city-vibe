# Places — места на карте

← [Оглавление](index.md)

**Префикс:** `/places`  
**Upstream:** place-service `:8083`

## Обязательные поля при создании

`name`, `about`, `category`, `owner_id`, `geo` (`latitude`/`longitude`).

Опционально: `attrs`, `schedule`, `pin_style_id`, `chat_theme_id`, `city_id`, `contacts`.

`attrs` строго валидируются JSON Schema категории (`GET /attr-schemas/{category}`).

`pin_style_id` / `chat_theme_id` — id из **design-service** (без FK между БД). `null` → клиент берёт `GET /pin-styles/default` и `GET /chat-themes/default`.

## Методы

| Method | Path | Описание |
|--------|------|----------|
| POST | `/places` | Создать место |
| GET | `/places` | Список; query: `owner_id`, `category`, `min_lat`,`min_lng`,`max_lat`,`max_lng`, `limit` |
| GET | `/places/{id}` | Карточка |
| PATCH | `/places/{id}` | Частичное обновление |
| DELETE | `/places/{id}` | Soft-delete |

## Пример create

```bash
curl -s http://localhost:8080/places -H 'Content-Type: application/json' -d '{
  "name": "Bar Neon",
  "about": "Коктейли и живая музыка",
  "category": "bars",
  "owner_id": 1,
  "geo": {"latitude": 55.75, "longitude": 37.62},
  "attrs": {"price_level": 2, "has_wifi": true},
  "schedule": {
    "timezone": "Europe/Moscow",
    "periods": [{"weekday": 0, "closed": false, "intervals": [{"open": "18:00", "close": "02:00"}]}],
    "exceptions": []
  },
  "pin_style_id": 1,
  "chat_theme_id": 1
}'
```

## «Мои места»

`GET /places?owner_id=<user_id>`

## Поиск

См. подробный гайд: [places-search.md](places-search.md) — `POST /places/search`.
