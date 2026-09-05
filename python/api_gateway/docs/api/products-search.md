# Products search — многокритериальный поиск товаров и услуг

← [Оглавление](index.md) · [products](products.md)

**Method:** `POST /products/search`  
**Upstream:** place-service `:8083` (проксируется gateway)  
**Для:** мобильный клиент + вызов ИИ-агентом как команда

## Назначение

Поиск продуктов в городе: товар/услуга принадлежит месту, город берётся через join `places.city_id`.  
Обязателен только `city_id`. Нужен якорь: `category` / `q` / `place_id` / `place_name` / `place_category` / `date_from`.

`q` ищет по `name`/`description` **продукта и имени места** («Мечта» находит офферы кафе).

Attrs/JSON Schema у продуктов в v1 нет.

Расписание: `periods` (каждую неделю), `exceptions` (override дня), **`events`** (разовые слоты в timezone расписания).

## Обязательные поля

| Поле | Тип | Описание |
|------|-----|----------|
| `city_id` | int | ID города места |

## Опциональные поля

| Поле | Default | Описание |
|------|---------|----------|
| `category` | — | Код из `GET /product-categories` (`food`, `coffee`, `concert`, …) |
| `q` | — | ILIKE по продукту **и** `places.name` |
| `place_id` | — | Только продукты этого места |
| `place_name` | — | Подстрока имени места (если ещё нет `place_id`) |
| `place_category` | — | Категория места (`cafes`, `gyms`, …) |
| `price_from` / `price_to` | — | Диапазон цены; `null`-цена в диапазон **не** попадает |
| `limit` | `20` | Размер страницы (1…100) |
| `page` | `1` | Номер страницы |
| `sort_by` | — | `price` \| `distance` \| `created_at` \| `event_start` |
| `exclude_ids` | `[]` | Не возвращать эти **id продуктов** (max 200) |
| `exclude_place_ids` | `[]` | Не возвращать продукты этих **мест** (max 200) |
| `one_per_place` | `false` | Не больше одного оффера с площадки |
| `date_from` / `date_to` | — | Пересечение с `events.start/end` и незакрытыми `exceptions` |
| `include_past` | `false` | Если у продукта есть `events`, нужен слот с `end >= now` в TZ |
| `timezone` | — | IANA TZ для now / events (иначе TZ расписания / `Asia/Novosibirsk`) |
| `my_geo` | — | `{lat, lng}` — обязателен при `sort_by=distance`; distance по координатам **места** |
| `open_at` | — | AND-моменты; учитываются periods, exceptions **и events** |

## Пример тела

```json
{
  "city_id": 3,
  "category": "coffee",
  "q": "Мечта",
  "place_category": "cafes",
  "limit": 20,
  "page": 1,
  "sort_by": "distance",
  "one_per_place": true,
  "timezone": "Asia/Novosibirsk",
  "my_geo": {"lat": 54.924424, "lng": 82.999171}
}
```

Концерт по дате (`events`, не weekday exceptions):

```json
{
  "city_id": 3,
  "category": "concert",
  "date_from": "2026-10-01",
  "date_to": "2026-10-31",
  "sort_by": "event_start",
  "timezone": "Asia/Novosibirsk"
}
```

## open_at и events

`open_at`: день недели + `open` HH:MM. Продукт доступен, если покрывает period, exception этого weekday или event, чей локальный интервал содержит момент.

`date_from`/`date_to` матчат **календарные даты** `events` (и дату exception, если не `closed`).

`start`/`end` в events — naive local datetime, зона = `schedule.timezone`.

Код: `compile_open_at_filters` / `compile_date_range_filters` / `compile_include_past_filter` в `python/place_service/src/place_service/infra/schedule_filter.py`.

## Сортировка и гео

- `price` — ASC, **NULLS LAST**
- `created_at` — новые сначала
- `event_start` — ближайший `events.start`, NULLS LAST
- `distance` — Postgres `earthdistance` по `places.lat/lng`; нужен `my_geo`

## Ответ

```json
{
  "items": [
    {
      "id": 1,
      "place_id": 10,
      "name": "Комбо 2 кофе + круассан",
      "description": "...",
      "price": 250.0,
      "category": "coffee",
      "schedule": {},
      "place": {"id": 10, "name": "Кафе Мечта", "city_id": 3, "lat": 55.0, "lng": 83.0},
      "distance_m": 1234.5
    }
  ],
  "total": 4,
  "page": 1,
  "limit": 20,
  "pages": 1
}
```

`price` может быть `null` (бесплатно / «см. описание»).

(обёртка presenter: `{"result": {...}}`)

## curl

```bash
curl -s http://localhost:8080/products/search \
  -H 'Content-Type: application/json' \
  -d '{"city_id":3,"q":"Мечта","category":"coffee","limit":5}' | jq
```
