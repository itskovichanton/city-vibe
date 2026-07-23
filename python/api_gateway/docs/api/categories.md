# Categories & Attr schemas

← [Оглавление](index.md)

**Upstream:** place-service `:8083`

## `GET /categories`

Справочник категорий мест (seed из `PlaceCategory` enum + человекочитаемый `title`).

| Поле | Описание |
|------|----------|
| `code` | `bars`, `restaurants`, … |
| `title` | «Бары», … |
| `title_en` | English |
| `icon_url` | опционально |
| `sort_order` | порядок в UI |

Enum в коде (`python.libs.entities.place.PlaceCategory`) остаётся как набор допустимых кодов.

## `GET /attr-schemas`

Все JSON Schema для `Place.attrs` (1 схема на категорию).

## `GET /attr-schemas/{category_code}`

Схема одной категории. При create/patch place `attrs` валидируются **строго** (Draft 2020-12).
