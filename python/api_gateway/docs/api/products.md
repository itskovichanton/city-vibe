# Products — товары и услуги мест

← [Оглавление](index.md) · [products-search](products-search.md)

**Префикс:** `/products`, `/product-categories`  
**Upstream:** place-service `:8083`

Продукт всегда принадлежит месту (`place_id`). Категории продуктов — отдельный справочник от категорий мест (ресторан ≠ еда).

## Справочник

| Method | Path | Описание |
|--------|------|----------|
| GET | `/product-categories` | Коды `food`, `yoga_class`, `concert`, … |

## Методы

| Method | Path | Описание |
|--------|------|----------|
| POST | `/products` | Создать продукт |
| GET | `/products` | Список; query: `place_id`, `category`, `limit` |
| GET | `/products/{id}` | Карточка (+ compact `place`: id, name, city_id, lat/lng) |
| PATCH | `/products/{id}` | Частичное обновление (`schedule: null` сбрасывает расписание) |
| DELETE | `/products/{id}` | Soft-delete |

## Обязательные поля при создании

`place_id`, `name`, `category` (код из `/product-categories`).

Опционально: `price` (рубли; `null` = бесплатно / «см. описание»), `description`, `schedule` (`WeeklySchedule`: `periods`, `exceptions`, разовые **`events`**).

## Пример create

```bash
curl -s http://localhost:8080/products -H 'Content-Type: application/json' -d '{
  "place_id": 1,
  "name": "Хатха-йога вечер",
  "description": "Групповое занятие 60 минут",
  "price": 700,
  "category": "yoga_class",
  "schedule": {
    "timezone": "Asia/Novosibirsk",
    "periods": [{"weekday": 1, "closed": false, "intervals": [{"open": "19:00", "close": "20:00"}]}],
    "exceptions": []
  }
}'
```

## Поиск

См. [products-search.md](products-search.md) — `POST /products/search`.  
NL через ИИ: [milana.md](milana.md) — шаги с `domain=product` внутри `POST /milana/places/search`.
