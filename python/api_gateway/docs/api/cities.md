# Cities — справочник городов

← [Оглавление](index.md) · [Conventions](conventions.md)

**Префикс:** `/cities`, `/cities/{path}`  
**Upstream:** place-service (`http://localhost:8083`)

Публичные методы: JWT не обязателен. Используются при онбординге / регистрации (`city_id`).

Данные сидятся через `make seed-place` / `up-all` (~крупные города РФ).

---

## Модель `CityOut` / `CityResponse`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | Primary key |
| `name` | string | Название («Москва») |
| `slug` | string | Транслит-slug для URL |
| `region` | string | Регион / субъект |
| `geo` | object \| null | `{ "latitude": number, "longitude": number }` |
| `is_major` | bool | Крупный город (список `GET /cities` берёт major) |
| `sort_order` | int | Порядок сортировки в UI |
| `about` | string | Краткое описание |
| `deleted` | bool | Soft-delete (обычно не отдаётся в списке) |
| `created_at` | datetime \| null | |
| `updated_at` | datetime \| null | |

> В части OpenAPI/Swagger place-service могут фигурировать устаревшие поля `lat`/`lng`; канонический ответ DTO — вложенный `geo`.

---

## `GET /cities`

Список крупных городов для выбора в приложении.

### Rate limit (upstream)

`cities.list` ≈ 120.

### Параметры

Query/path — нет. Фильтрация на сервере: `list_major()` (только `is_major`).

### Headers

Не требуются.

### Response `200`

Массив городов (часто в обёртке `result`):

```json
{
  "result": [
    {
      "id": 1,
      "name": "Москва",
      "slug": "moskva",
      "region": "Москва",
      "geo": { "latitude": 55.75, "longitude": 37.62 },
      "is_major": true,
      "sort_order": 1,
      "about": "",
      "deleted": false,
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

### Пример

```bash
curl -s http://localhost:8080/cities | jq
```

### Заметки для клиента

- Кэшировать список на клиенте (меняется редко).
- `id` из этого списка передавать в `POST /auth/register` как `city_id`.

---

## `GET /cities/nearest`

Ближайший **крупный** город к GPS-координатам (PostgreSQL `earthdistance`).

### Rate limit (upstream)

`cities.nearest` ≈ 60.

### Query parameters

| Параметр | Тип | Обяз. | Описание |
|----------|-----|-------|----------|
| `lat` | float | да | Широта |
| `lng` | float | да | Долгота |

### Response `200`

Тот же `CityOut` / `CityResponse`, плюс опционально `distance_m` (метры до точки).

```json
{
  "result": {
    "id": 1,
    "name": "Москва",
    "slug": "moskva",
    "geo": { "latitude": 55.7558, "longitude": 37.6173 },
    "distance_m": 12450.3
  }
}
```

### Пример

```bash
curl -s "http://localhost:8080/cities/nearest?lat=55.75&lng=37.62" | jq
```

### Заметки для клиента

- Запрашивать после выдачи permission на геолокацию.
- Если отказали в GPS — оставить ручной выбор из `GET /cities`.

---

## `GET /cities/{city_id}`

Карточка одного города по id.

### Rate limit (upstream)

`cities.get` ≈ 120.

### Path parameters

| Параметр | Тип | Обяз. | Описание |
|----------|-----|-------|----------|
| `city_id` | int | да | ID города |

### Response `200` — один `CityOut`

### Ошибки

| Ситуация | Поведение |
|----------|-----------|
| Город не найден | `CoreException` not found: «Город id=… не найден» |

### Пример

```bash
curl -s http://localhost:8080/cities/1 | jq
```

---

## Связанные темы

- [auth](auth.md) — `city_id` в register / Google
- [users](users.md) — `city_id` в профиле
