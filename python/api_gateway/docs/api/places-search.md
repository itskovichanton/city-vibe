# Places search — многокритериальный поиск

← [Оглавление](index.md) · [places](places.md)

**Method:** `POST /places/search`  
**Upstream:** place-service `:8083` (проксируется gateway)  
**Для:** мобильный клиент + вызов ИИ-агентом как команда

## Назначение

Гибкий поиск мест в городе по категории с опциональными фильтрами:
имя, расписание (`open_at`), кастомные `attrs` (exact / between / or / and / not_in),
сортировка по рейтингу или расстоянию.

## Обязательные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `city_id` | int | ID города |
| `category` | string | Код категории (`restaurants`, `bars`, …) |

## Опциональные поля

| Поле | Default | Описание |
|------|---------|----------|
| `name` | — | Подстрока в `name` (ILIKE, без регистра) |
| `limit` | `20` | Размер страницы (1…100) |
| `page` | `1` | Номер страницы |
| `sort_by` | — | `rating` \| `distance` |
| `my_geo` | — | `{lat, lng}` — обязателен при `sort_by=distance`; также добавляет `distance_m` в ответ |
| `open_at` | — | Список моментов; место должно быть открыто во **все** (AND) |
| `attrs` | — | Фильтры по JSON attrs категории |

## Пример тела (рестораны)

```json
{
  "city_id": 3,
  "category": "restaurants",
  "name": "Сибир",
  "limit": 20,
  "page": 1,
  "sort_by": "distance",
  "open_at": [
    {"weekday": 6, "intervals": [{"open": "09:00"}]},
    {"weekday": 3, "intervals": [{"open": "18:00"}]}
  ],
  "my_geo": {"lat": 54.924424, "lng": 82.999171},
  "attrs": {
    "has_wifi": true,
    "kids_menu": false,
    "has_parking": true,
    "avg_bill_rub": {"operation": "between", "args": {"from": 200, "to": 5000}},
    "dress_code": {"operation": "or", "args": {"list": ["casual", "smart_casual"]}},
    "cuisine": {"operation": "not_in", "args": {"list": ["fast_food"]}}
  }
}
```

## Операции attrs (ООП)

| operation | args | Смысл |
|-----------|------|--------|
| _(скаляр)_ | — | Exact match (`attrs @> {key: value}`) |
| `between` | `from?`, `to?` | Числовой диапазон (границы опциональны) |
| `or` | `list: [...]` | Scalar ∈ list **или** пересечение с array-атрибутом |
| `and` | `list: [...]` | Все элементы list ⊆ array-атрибута |
| `not_in` | `list: [...]` | Scalar ∉ list **и** нет пересечения с array-атрибутом |

Вложенность операций **не** поддерживается. Новые операции — через `ATTR_OP_REGISTRY` / `@register_attr_operation`.

Код: `python/place_service/src/place_service/infra/attr_ops.py`

## open_at

Для каждого элемента: день недели + время `open` (HH:MM).  
Место открыто, если в `schedule.periods` есть день с `closed=false` и интервал, покрывающий это время (в т.ч. через полночь).  
Несколько элементов — **AND**.

## Сортировка и гео

- `rating` — по `(rating_up - rating_down)`, затем `rating_up`
- `distance` — метры через Postgres `earthdistance` (`cube` + `earthdistance`); нужен `my_geo`

## Ответ

```json
{
  "items": [ { "...Place...", "distance_m": 1234.5 } ],
  "total": 42,
  "page": 1,
  "limit": 20,
  "pages": 3
}
```

(обёртка presenter: `{"result": {...}}`)

## curl

```bash
curl -s http://localhost:8080/places/search \
  -H 'Content-Type: application/json' \
  -d '{"city_id":3,"category":"restaurants","limit":5,"sort_by":"rating"}' | jq
```
