# Catalog match — строки справочника по вольному описанию

← [Оглавление](index.md) · [milana](milana.md) · [products](products.md)

**Upstream:** milana-service `:8086` (гибрид). Прокси gateway: `POST /catalog/match` → `/milana/catalog/match`.  
Дешёвый matcher без LLM по-прежнему в place-service `:8083` (`POST /catalog/match` напрямую) — его вызывает Милана как recall.

Подбирает строки **закрытого справочника** (не 35k продуктов).

## Гибрид

1. **Recall** — алиасы `catalog_aliases` + поля title (place-service, без LLM).
2. **Precision** — DeepSeek видит порции справочника `{key, title}` и сам решает, что подходит («фоткаться» → Фотосессия).
3. Результаты объединяются, коды не из списка отбрасываются.

### `effort` — УсилиеПоиска

Максимум **строк справочника в одном вызове LLM**. Весь каталог режется на порции этого размера.

| effort | Поведение |
|--------|-----------|
| `0` | только алиасы, DeepSeek не зовётся |
| `50` (default в config `milana.catalog_match_effort`) | ~50 категорий товаров = один вызов |
| меньше размера справочника | несколько вызовов подряд, результаты merge |

Нужен `DEEPSEEK_API_KEY`. Если ключа нет — тихо остаётся recall.

## `GET /catalogs`

По-прежнему place-service.

| catalog | entity_type | fields |
|---------|-------------|--------|
| `product_categories` | `ProductCategoryInfo` | title, title_en |
| `place_categories` | `PlaceCategoryInfo` | title, title_en |
| `cities` | `City` | name, region |

## `POST /catalog/match`

| Поле | Обязательно | Описание |
|------|-------------|----------|
| `prompt` | да | Вольный текст |
| `catalog` | одно из двух | `product_categories` / `place_categories` / `cities` |
| `entity_type` | одно из двух | `ProductCategoryInfo` / `PlaceCategoryInfo` / `City` |
| `fields` | нет | Для recall (алиасы всегда) |
| `limit` | нет | 1..50, default 8 |
| `effort` | нет | УсилиеПоиска 0..80; default из config Миланы (`50`) |

### Ответ

```json
{
  "catalog": "product_categories",
  "entity_type": "ProductCategoryInfo",
  "prompt": "я люблю сладкое и фоткаться",
  "effort": 50,
  "used_llm": true,
  "items": [
    {
      "code": "photo_session",
      "title": "Фотосессия",
      "why": "фоткаться = фотосессия",
      "score": 9.4,
      "source": "llm"
    },
    {
      "code": "bakery_goods",
      "title": "Выпечка",
      "why": "запрос про сладкое / выпечку",
      "score": 8.5,
      "source": "both"
    }
  ]
}
```

`source`: `alias` | `llm` | `both`.

Мобильный `CatalogClient` ходит в `POST /catalog/match` (gateway → Милана), `effort` по умолчанию 50 для онбординга.

### Пример

```bash
curl -s http://localhost:8080/catalog/match \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "я люблю сладкое и фоткаться",
    "catalog": "product_categories",
    "fields": ["title"],
    "limit": 16,
    "effort": 50
  }'
```

Только алиасы: `"effort": 0`.
